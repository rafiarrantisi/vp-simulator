// ── Qora Voice Mode (voice-first room, same session/engine as Text) ──────
// Presentation layer only: recognition → existing send() pipeline → Gemini
// TTS streaming → AudioContext playback. Transcript stays server-side and in
// `messages` (drawer); bubbles are NOT the main UI here.
//
// State machine: idle | listening | processing | speaking | error.
// No barge-in v1: mic is inert while processing/speaking. After speaking
// ends the mic auto-starts (hands-free turns); first turn needs one tap
// (creates/resumes AudioContext inside the user gesture).
// All lifecycles (recognition, timers, streams, audio) die on unmount.

var QV2_VOICE_SILENCE_MS = 3000; // inactivity fallback auto-submit
var QV2_TTS_SR = 24000; // int16 mono, matches backend framing

function _qvLang(lang) {
  var m = { en: 'en-US', id: 'id-ID', ms: 'ms-MY', tl: 'tl-PH', vi: 'vi-VN', th: 'th-TH' };
  return m[lang] || 'en-US';
}

function _qvSR() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

// ---- Streaming PCM player (framed: u32be length + int16le mono 24k) ----
function qvPlayTtsStream(opts) {
  // opts: {text, sessionId, ctx, analyser, onFirstAudio, onDone, onError}
  // Returns {cancelled(), done: Promise<'clean'|'truncated'>}.
  var cancelled = false;
  var controller = null;
  try { controller = new AbortController(); } catch (e) { controller = null; }
  var sources = [];
  var state = { firstFired: false, clean: false, queued: 0, playing: 0 };

  function stopSources() {
    sources.forEach(function (s) { try { s.stop(); } catch (e) {} try { s.disconnect(); } catch (e2) {} });
    sources = [];
  }
  function cancel() {
    cancelled = true;
    try { if (controller) controller.abort(); } catch (e) {}
    stopSources();
  }
  function pcmToBuffer(ctx, bytes) {
    var n = Math.floor(bytes.length / 2);
    var buf = ctx.createBuffer(1, n, QV2_TTS_SR);
    var ch = buf.getChannelData(0);
    var dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    for (var i = 0; i < n; i++) ch[i] = dv.getInt16(i * 2, true) / 32768;
    return buf;
  }
  var done = (async function () {
    var tok = (typeof _qv2Token === 'function') ? _qv2Token() : '';
    var headers = { 'Content-Type': 'application/json' };
    if (tok) headers['Authorization'] = 'Bearer ' + tok;
    var base = (typeof _qv2Base === 'function') ? _qv2Base() : '';
    var res;
    try {
      res = await fetch(base + '/api/ai/tts/stream', {
        method: 'POST', headers: headers,
        body: JSON.stringify({ text: opts.text, session_id: opts.sessionId }),
        signal: controller ? controller.signal : undefined,
      });
    } catch (e) {
      if (cancelled) return 'cancelled';
      throw e;
    }
    if (!res.ok || !res.body) throw new Error('HTTP ' + res.status);
    var reader = res.body.getReader();
    var pending = new Uint8Array(0);
    function feed(more) {
      var cat = new Uint8Array(pending.length + more.length);
      cat.set(pending, 0); cat.set(more, pending.length);
      pending = cat;
    }
    var ctx = opts.ctx, analyser = opts.analyser;
    var playAt = ctx.currentTime + 0.05;
    try {
      for (;;) {
        var rd = await reader.read();
        if (rd.done) break;
        if (cancelled) return 'cancelled';
        feed(rd.value);
        while (pending.length >= 4) {
          var dv = new DataView(pending.buffer, pending.byteOffset, pending.byteLength);
          var len = dv.getUint32(0, false);
          if (len === 0) {
            state.clean = true;
            try { await reader.cancel(); } catch (e) {}
            pending = new Uint8Array(0);
            break;
          }
          if (pending.length < 4 + len) break;
          var pcm = pending.slice(4, 4 + len);
          pending = pending.slice(4 + len);
          var buf = pcmToBuffer(ctx, pcm);
          var src = ctx.createBufferSource();
          src.buffer = buf;
          if (analyser) src.connect(analyser);
          else src.connect(ctx.destination);
          var dur = buf.duration;
          src.start(Math.max(playAt, ctx.currentTime + 0.01));
          playAt = Math.max(playAt, ctx.currentTime + 0.01) + dur;
          sources.push(src);
          state.queued++;
          if (!state.firstFired) {
            state.firstFired = true;
            try { if (opts.onFirstAudio) opts.onFirstAudio(); } catch (e) {}
          }
          src.onended = function () { state.playing++; };
        }
        if (state.clean) break;
      }
    } catch (e) {
      if (cancelled) return 'cancelled';
      throw e;
    }
    if (!state.clean) return 'truncated'; // stream died without terminator
    // Wait until scheduled audio actually finished.
    var waitMs = Math.max(0, (playAt - ctx.currentTime) * 1000) + 150;
    await new Promise(function (r) { setTimeout(r, waitMs); });
    if (cancelled) return 'cancelled';
    return 'clean';
  })();
  return {
    cancel: cancel,
    done: done.then(function (how) {
      if (how !== 'clean' && how !== 'cancelled') {
        try { if (opts.onError) opts.onError(new Error('audio stream truncated')); } catch (e) {}
      } else if (how === 'clean') {
        try { if (opts.onDone) opts.onDone(); } catch (e) {}
      }
      return how;
    }, function (e) {
      stopSources();
      try { if (opts.onError) opts.onError(e); } catch (e2) {}
      throw e;
    }),
  };
}

// ---- Voice orb (analyser-driven when speaking, CSS pulse when listening) --
function QV2VoiceOrb(props) {
  var phase = props.phase; // idle|listening|processing|speaking|error
  var analyserRef = props.analyserRef;
  var levelRef = React.useRef(0);
  var dotRef = React.useRef(null);
  var ringRef = React.useRef(null);
  React.useEffect(function () {
    var raf = 0, alive = true;
    var buf = new Uint8Array(64);
    function tick() {
      if (!alive) return;
      var lvl = 0;
      try {
        var an = analyserRef && analyserRef.current;
        if (phase === 'speaking' && an) {
          an.getByteTimeDomainData(buf);
          var sum = 0;
          for (var i = 0; i < buf.length; i++) { var v = (buf[i] - 128) / 128; sum += v * v; }
          lvl = Math.min(1, Math.sqrt(sum / buf.length) * 3.2);
        }
      } catch (e) {}
      levelRef.current = levelRef.current + (lvl - levelRef.current) * 0.35;
      var s = 1 + levelRef.current * 0.28;
      try {
        if (dotRef.current) dotRef.current.style.transform = 'scale(' + s.toFixed(3) + ')';
        if (ringRef.current) {
          ringRef.current.style.opacity = String(0.25 + levelRef.current * 0.6);
          ringRef.current.style.transform = 'scale(' + (1 + levelRef.current * 0.55).toFixed(3) + ')';
        }
      } catch (e) {}
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return function () { alive = false; try { cancelAnimationFrame(raf); } catch (e) {} };
  }, [phase]);
  var glow = phase === 'listening' ? '0 0 0 10px rgba(92,63,150,0.14), 0 0 44px rgba(92,63,150,0.35)'
    : phase === 'speaking' ? '0 0 0 8px rgba(46,160,140,0.12), 0 0 40px rgba(46,160,140,0.30)'
    : phase === 'processing' ? '0 0 0 6px rgba(120,120,150,0.10)'
    : '0 8px 28px rgba(30,20,60,0.16)';
  var bg = phase === 'speaking' ? 'radial-gradient(circle at 35% 30%, #3ddbb9, #1f8f7a 70%)'
    : 'radial-gradient(circle at 35% 30%, #9a76db, #5c3f96 70%)';
  return React.createElement('div', { style: { position: 'relative', width: 196, height: 196, margin: '0 auto' } },
    React.createElement('div', { ref: ringRef, style: { position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid var(--primary)', opacity: 0.25, pointerEvents: 'none' } }),
    React.createElement('div', { ref: dotRef, className: phase === 'listening' ? 'qv2-orb-pulse' : '', style: { position: 'absolute', inset: 18, borderRadius: '50%', background: bg, boxShadow: glow, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 54 } },
      phase === 'speaking' ? '◉' : (phase === 'listening' ? '●' : (phase === 'processing' ? '…' : '🎙'))));
}

// ---- Voice room -----------------------------------------------------------
function QV2VoiceRoom(props) {
  // props: {sessionId, language, messages, busy, err, voiceCap,
  //         onSendText(text)->Promise<string|null>, onSwitchToText,
  //         onExam, onAssess, onExit, caseTitle}
  var sessionId = props.sessionId;
  var lang = _qvLang(props.language);
  var st = React.useState('idle'); // idle|listening|processing|speaking|error
  var phase = st[0], setPhase = st[1];
  var inter = React.useState('');
  var interim = inter[0], setInterim = inter[1];
  var vErr = React.useState('');
  var ver = vErr[0], setVErr = vErr[1];
  var drawer = React.useState(false);
  var drawerOpen = drawer[0], setDrawer = drawer[1];
  var hint = React.useState('');
  var hintMsg = hint[0], setHint = hint[1];
  var recRef = React.useRef(null);
  var timerRef = React.useRef(null);
  var finalRef = React.useRef('');
  var wantRef = React.useRef(false); // recognition should be alive
  var submittedRef = React.useRef(false);
  var phaseRef = React.useRef('idle');
  var playerRef = React.useRef(null);
  var ctxRef = React.useRef(null);
  var analyserRef = React.useRef(null);
  var autoRef = React.useRef(false); // auto-listen next turn
  var unmountedRef = React.useRef(false);
  phaseRef.current = phase;

  function clearTimer() {
    try { if (timerRef.current) clearTimeout(timerRef.current); } catch (e) {}
    timerRef.current = null;
  }
  function armSilence() {
    clearTimer();
    timerRef.current = setTimeout(function () {
      // 3s without new utterance content → auto-submit.
      finishSubmit(true);
    }, QV2_VOICE_SILENCE_MS);
  }
  function stopRec() {
    wantRef.current = false;
    clearTimer();
    var r = recRef.current;
    recRef.current = null;
    try { if (r) r.stop(); } catch (e) {}
  }
  function ensureAudio() {
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      if (!ctxRef.current) {
        ctxRef.current = new AC({ sampleRate: QV2_TTS_SR });
        analyserRef.current = ctxRef.current.createAnalyser();
        analyserRef.current.fftSize = 128;
        analyserRef.current.connect(ctxRef.current.destination);
      }
      if (ctxRef.current.state === 'suspended') ctxRef.current.resume().catch(function () {});
      return ctxRef.current;
    } catch (e) { return null; }
  }
  function startListening(auto) {
    if (unmountedRef.current) return;
    if (phaseRef.current === 'listening') return;
    if (phaseRef.current === 'processing' || phaseRef.current === 'speaking') return;
    if (!sessionId) {
      // Session (and its opening line) isn't ready yet — mic now would
      // record into the void. Stay idle until the room is actually live.
      setHint('Menyiapkan sesi…');
      return;
    }
    var SR = _qvSR();
    if (!SR) {
      setVErr('Voice input is not supported in this browser — switching to text keeps this session.');
      setTimeout(function () { try { if (props.onSwitchToText) props.onSwitchToText(); } catch (e) {} }, 1600);
      return;
    }
    setVErr(''); setHint(''); setInterim('');
    finalRef.current = ''; submittedRef.current = false;
    var rec;
    try { rec = new SR(); } catch (e) {
      setPhase('error'); setVErr('Could not start microphone.');
      return;
    }
    recRef.current = rec;
    wantRef.current = true;
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    rec.onresult = function (e) {
      if (submittedRef.current) return;
      // REBUILD finals from the full results array every event (never append
      // deltas): Chrome re-delivers prior finals across events with
      // continuous=true, and appending caused the "halo Halo Halo…" echo.
      var fin = '', inter = '';
      try {
        for (var i = 0; i < e.results.length; i++) {
          var t = ((e.results[i][0] || {}).transcript || '');
          if (e.results[i].isFinal) fin += t + ' ';
          else inter += t;
        }
      } catch (err2) {}
      finalRef.current = fin.trim();
      setInterim(((finalRef.current + ' ' + inter).trim()));
      // Any utterance content (interim or final) resets the 3s clock.
      if ((fin + inter).trim()) armSilence();
    };
    rec.onerror = function (e) {
      var code = (e && e.error) || '';
      if (code === 'not-allowed' || code === 'service-not-allowed') {
        stopRec();
        setPhase('error');
        setVErr('Microphone blocked — allow mic access, or continue in text mode.');
        return;
      }
      if (code === 'aborted') return; // our own stop()
      if (code === 'no-speech' || code === 'audio-capture') {
        // Treat like silence: submit what we have, if anything.
        if ((finalRef.current || '').trim()) { finishSubmit(true); return; }
        stopRec();
        if (phaseRef.current === 'listening') {
          setPhase('idle');
          setHint(auto ? '' : 'No speech detected — tap the mic and try again.');
        }
        return;
      }
    };
    rec.onend = function () {
      // Chrome ends recognition on pauses by itself: if we still want to
      // listen and nothing was submitted, restart; else finalize.
      if (unmountedRef.current || submittedRef.current || !wantRef.current) return;
      if ((finalRef.current || '').trim()) { finishSubmit(true); return; }
      try {
        if (recRef.current === rec) {
          rec.start();
          armSilence();
          return;
        }
      } catch (e) {}
      if (phaseRef.current === 'listening') setPhase('idle');
    };
    try {
      rec.start();
      ensureAudio(); // unlock audio inside the tap gesture
      setPhase('listening');
      armSilence();
    } catch (e) {
      setPhase('error'); setVErr('Could not start microphone.');
    }
  }
  function finishSubmit(fromSilence) {
    if (submittedRef.current) return;
    submittedRef.current = true;
    var text = (finalRef.current || '').trim();
    stopRec();
    setInterim('');
    if (!text) {
      setPhase('idle');
      setHint(fromSilence ? '' : 'Nothing heard — tap the mic and try again.');
      return;
    }
    submitUtterance(text);
  }
  async function submitUtterance(text) {
    if (unmountedRef.current) return;
    setPhase('processing'); setVErr('');
    var reply = null;
    try {
      reply = await props.onSendText(text);
    } catch (e) {
      reply = null;
    }
    if (unmountedRef.current) return;
    if (!reply || /^\s*\(error:/.test(reply)) {
      setPhase('error');
      setVErr('Could not reach the patient. Your words are saved in the transcript — retry audio or continue in text.');
      return;
    }
    // Patient text ready → stream voice with the card's server-side voice.
    var ctx = ensureAudio();
    if (!ctx) {
      // No audio output possible: fall back to showing the text.
      setPhase('error');
      setVErr('Audio output unavailable here — the reply is in the transcript drawer.');
      setDrawer(true);
      return;
    }
    setPhase('speaking');
    var player = qvPlayTtsStream({
      text: reply, sessionId: sessionId, ctx: ctx, analyser: analyserRef.current,
      onFirstAudio: function () {},
      onDone: function () {},
      onError: function () {},
    });
    playerRef.current = player;
    var how = 'truncated';
    try { how = await player.done; } catch (e) { how = 'error'; }
    playerRef.current = null;
    if (unmountedRef.current) return;
    if (how === 'clean') {
      setPhase('idle');
      // Hands-free: mic auto-starts for the next turn. Deferred a tick so
      // the idle render commits first (startListening reads phaseRef).
      setTimeout(function () {
        if (!unmountedRef.current) startListening(true);
      }, 80);
    } else if (how === 'cancelled') {
      setPhase('idle');
    } else {
      setPhase('error');
      setVErr('Patient audio cut off — the full reply is in the transcript drawer.');
      setDrawer(true);
    }
  }
  function onMicTap() {
    if (phase === 'listening') { finishSubmit(false); return; } // manual submit
    if (phase === 'idle' || phase === 'error') { setVErr(''); startListening(false); return; }
    // processing/speaking: inert (no barge-in v1)
  }
  function stopAll() {
    stopRec();
    try { if (playerRef.current) playerRef.current.cancel(); } catch (e) {}
    playerRef.current = null;
  }
  // Full lifecycle cleanup: mic, timers, streams, audio.
  React.useEffect(function () {
    unmountedRef.current = false;
    autoRef.current = true;
    return function () {
      unmountedRef.current = true;
      autoRef.current = false;
      stopRec();
      try { if (playerRef.current) playerRef.current.cancel(); } catch (e) {}
      playerRef.current = null;
      try { if (ctxRef.current) ctxRef.current.close().catch(function () {}); } catch (e) {}
      ctxRef.current = null; analyserRef.current = null;
    };
  }, [sessionId]);

  var phaseLabel = phase === 'listening' ? 'Listening… tap mic to send now'
    : phase === 'processing' ? 'Patient is thinking…'
    : phase === 'speaking' ? 'Patient is speaking…'
    : phase === 'error' ? 'Something needs attention'
    : 'Tap the mic and speak';
  var msgs = props.messages || [];
  // Pinned patient condition (the opening line) — shown as a header card,
  // NOT as chat text. Mic stays disabled until the session + opening exist.
  var opening = '';
  for (var oi = 0; oi < msgs.length; oi++) {
    if (msgs[oi] && msgs[oi].role === 'patient' && (msgs[oi].text || '').trim()) { opening = msgs[oi].text.trim(); break; }
  }
  var roomReady = !!sessionId && !!opening;
  return React.createElement('div', { style: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '26px 16px 20px', minHeight: 'calc(100dvh - 220px)' } },
    // Switch + exit row
    React.createElement('div', { style: { width: '100%', maxWidth: 560, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 } },
      React.createElement('button', { onClick: props.onExit, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '← Library'),
      React.createElement('button', { onClick: props.onSwitchToText, style: { padding: '6px 12px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface-2)', fontSize: 12, fontWeight: 700, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '💬 Text mode')),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-2)', marginBottom: 2 } }, props.caseTitle || ''),
    opening
      ? React.createElement('div', { style: { maxWidth: 560, marginTop: 8, marginBottom: 4, padding: '10px 16px', borderRadius: 14, background: 'var(--surface)', border: '1px solid var(--border)', fontSize: 13, lineHeight: 1.55, color: 'var(--text-1)', textAlign: 'center', fontStyle: 'italic' } }, '“' + opening + '”')
      : React.createElement('div', { style: { marginTop: 8, marginBottom: 4, fontSize: 12.5, color: 'var(--text-3)' } }, 'Menyiapkan pasien…'),
    React.createElement(QV2VoiceOrb, { phase: phase, analyserRef: analyserRef }),
    React.createElement('div', { style: { marginTop: 14, fontSize: 14, fontWeight: 700, color: 'var(--text-1)', minHeight: 20, textAlign: 'center' } }, phaseLabel),
    React.createElement('div', { style: { marginTop: 6, fontSize: 13, color: 'var(--text-2)', fontStyle: 'italic', minHeight: 20, maxWidth: 560, textAlign: 'center', lineHeight: 1.5 } },
      phase === 'listening' ? ('“' + (interim || '…') + '”') : ''),
    ver && React.createElement('div', { style: { marginTop: 10, maxWidth: 560, padding: '10px 14px', borderRadius: 12, background: 'var(--red-l)', color: 'var(--red-d)', fontSize: 12.5, lineHeight: 1.5, textAlign: 'center' } }, '⚠️ ' + ver),
    hintMsg && !ver && React.createElement('div', { style: { marginTop: 10, fontSize: 12.5, color: 'var(--text-3)' } }, hintMsg),
    // Mic primary action (disabled until the room is live)
    React.createElement('button', {
      onClick: onMicTap,
      disabled: !roomReady || phase === 'processing' || phase === 'speaking' || props.busy,
      'aria-label': phase === 'listening' ? 'Send now' : 'Speak',
      style: {
        marginTop: 18, width: 84, height: 84, borderRadius: '50%', border: 'none', cursor: (!roomReady || phase === 'processing' || phase === 'speaking') ? 'default' : 'pointer',
        background: phase === 'listening' ? 'var(--red, #e5484d)' : 'var(--primary)', color: '#fff', fontSize: 32,
        boxShadow: phase === 'listening' ? '0 0 0 8px rgba(229,72,77,0.18), var(--sh-md)' : 'var(--sh-md)',
        opacity: (!roomReady || phase === 'processing' || phase === 'speaking') ? 0.55 : 1,
      },
    }, phase === 'listening' ? '■' : (phase === 'processing' ? '…' : '🎙')),
    React.createElement('div', { style: { marginTop: 8, fontSize: 11.5, color: 'var(--text-3)' } },
      !roomReady ? 'Menyiapkan sesi…' : (phase === 'listening' ? 'Auto-sends after 3s of silence' : (phase === 'idle' ? 'Hands-free: mic restarts after each reply' : ''))),
    // Secondary actions
    React.createElement('div', { style: { marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' } },
      React.createElement('button', { onClick: function () { setDrawer(true); }, style: { padding: '8px 14px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '📝 Transcript (' + msgs.length + ')'),
      props.onExam && React.createElement('button', { onClick: props.onExam, disabled: phase !== 'idle', style: { padding: '8px 14px', borderRadius: 999, border: '1px solid var(--primary)', background: 'var(--primary-l)', fontSize: 12.5, fontWeight: 700, color: 'var(--primary)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: phase !== 'idle' ? 0.55 : 1 } }, 'Exam →'),
      React.createElement('button', { onClick: props.onAssess, disabled: phase !== 'idle', style: { padding: '8px 14px', borderRadius: 999, border: '1px solid var(--primary)', background: 'var(--surface)', fontSize: 12.5, fontWeight: 700, color: 'var(--primary)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: phase !== 'idle' ? 0.55 : 1 } }, 'Assess →')),
    props.err && React.createElement('div', { style: { marginTop: 12, fontSize: 12, color: 'var(--red-d)' } }, String(props.err)),
    // Transcript drawer (default closed)
    drawerOpen && React.createElement('div', { style: { position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(15,12,30,0.5)', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }, onClick: function () { setDrawer(false); } },
      React.createElement('div', { onClick: function (e) { e.stopPropagation(); }, style: { width: '100%', maxWidth: 640, maxHeight: '72dvh', overflowY: 'auto', background: 'var(--surface)', borderRadius: '20px 20px 0 0', padding: '18px 18px calc(20px + env(safe-area-inset-bottom, 0px))' } },
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 } },
          React.createElement('div', { style: { fontSize: 15, fontWeight: 800, color: 'var(--text-1)' } }, 'Transcript'),
          React.createElement('button', { onClick: function () { setDrawer(false); }, style: { border: 'none', background: 'var(--surface-2)', borderRadius: 999, width: 30, height: 30, fontSize: 14, cursor: 'pointer', color: 'var(--text-2)' } }, '✕')),
        msgs.length === 0 && React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)' } }, 'No turns yet — tap the mic to begin.'),
        msgs.map(function (m, i) {
          var mine = m.role === 'user';
          return React.createElement('div', { key: i, style: { display: 'flex', justifyContent: mine ? 'flex-end' : 'flex-start', marginBottom: 8 } },
            React.createElement('div', { style: { maxWidth: '85%', padding: '9px 13px', borderRadius: 14, fontSize: 13, lineHeight: 1.5, background: mine ? 'var(--primary)' : 'var(--surface-2)', color: mine ? '#fff' : 'var(--text-1)' } }, m.text || '…'));
        }))));
}
