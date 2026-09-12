// ── Qora Voice Mode (voice-first room, same session/engine as Text) ──────
// Phase-2: recognition → ONE POST voice-stream (server runs the patient
// engine + TTS and returns typed frames) → progressive PCM playback.
// Transcript stays server-side and in `messages` (drawer); bubbles are NOT
// the main UI here. Voice NEVER auto-falls-back to the text turns endpoint
// (that would run a second inference); errors show winner text + manual
// retry on the SAME client_turn_id (server replays, no new inference).
//
// State machine: idle | listening | processing | speaking | error.
// No barge-in v1: tap during processing/speaking CANCELS the turn (abort
// fetch, stop audio, idle + 'dibatalkan' hint, NO auto relisten). After a
// CLEAN speaking turn the mic auto-starts (hands-free); after a cancel it
// stays idle until the next tap. First turn needs one tap (creates/resumes
// AudioContext inside the user gesture).
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

// Shared PCM converter (int16le mono 24k → AudioBuffer). Used by the legacy
// TTS player below AND the Phase-2 voice-turn player — one math, two callers.
function qvPcmToBuffer(ctx, bytes) {
  var n = Math.floor(bytes.length / 2);
  var buf = ctx.createBuffer(1, n, QV2_TTS_SR);
  var ch = buf.getChannelData(0);
  var dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  for (var i = 0; i < n; i++) ch[i] = dv.getInt16(i * 2, true) / 32768;
  return buf;
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
    return qvPcmToBuffer(ctx, bytes); // shared converter (see above)
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

// ── Phase-2 server-orchestrated voice turn (ADR §4.2/§4.3) ───────────────
// One POST /api/v2/sessions/{id}/turns/voice-stream per utterance replaces
// the old text-turn + TTS round trips. Wire format (typed framed binary):
//   type:u8 + length:u32be + payload — types 1 metadata / 2 final-text /
//   3 PCM / 4 error / 5 done, protocol version 1. Incremental parsing is
//   MANDATORY: one reader.read() is NOT one frame (see qvFeedVoiceFrames).
// Error handling rule: NEVER auto-fallback to the text turns endpoint (that
// would run a second inference). Show the winner text when the server
// persisted one; manual retry reuses the SAME client_turn_id (server
// replays the durable winner with no new inference).
var QV2_VOICE_PROTO = 1;
var QV2_VF_META = 1, QV2_VF_TEXT = 2, QV2_VF_PCM = 3, QV2_VF_ERR = 4, QV2_VF_DONE = 5;
var QV2_VOICE_MAX_FRAME = 1048576; // 1 MiB (backend parity)
var QV2_VOICE_MAX_JSON = 65536; // 64 KiB control-frame cap (backend parity)

// ── Voice-turn timeouts (fit CURRENT provider, not ADR future numbers) ───
// LLM total guard is 20s + TTS streaming on top. IDLE fires only when NO
// frame/byte arrives for 20s (resets on every chunk, so healthy slow
// streams NEVER trip). OVERALL caps the whole turn at 90s (fetch + stream
// + DONE audio-schedule wait). Both reject with {voiceError} so the caller
// shows error-with-retry UI (no auto re-inference, same client_turn_id).
var QV2_VOICE_IDLE_MS = 20000;
var QV2_VOICE_OVERALL_MS = 90000;
// Consecutive rec.start() THROW cap (onend loop guard). Baseline behavior is
// unbounded restart-on-clean-end: clean ends NEVER consume this cap — only
// rec.start() THROWS increment (via qvNextRestartCount). Generous cap (10)
// guards genuine throw-loops before idle+hint; result/speech resets to 0.
var QV2_REC_MAX_RESTARTS = 10;
var QV2_VOICE_DEBUG_MAX = 30;

// Privacy-safe mic lifecycle ring buffer: {t, ev} with ev NAMES only —
// NEVER transcripts, audio, or text content. Mirrored to
// window.__QORA_VOICE_DEBUG (last ~30) + per-session counters for actionable
// bug reports. See qvVoiceDebugLog / qvVoiceDebugDump.
var qvVoiceDebugEvents = [];
var qvVoiceDebugCounts = { start: 0, onstart: 0, result: 0, final: 0, submit: 0, empty_submit: 0, end: 0, restart: 0, timeout: 0, error: 0 };
function qvVoiceDebugLog(ev) {
  var name = String(ev || '').slice(0, 48);
  // Redaction guard: ev must be a bare lifecycle token (no spaces, no
  // transcript payload). Anything with whitespace is collapsed to its
  // head token so transcript strings can NEVER leak into the buffer.
  // Allowed: start, onstart, result, final, submit, empty_submit,
  // error:<code>, end, restart, timeout (+ speech mapped to result).
  try {
    if (/[\s]/.test(name)) name = name.split(/\s+/)[0];
    if (!name) return;
  } catch (e) { return; }
  var entry = { t: Date.now(), ev: name };
  try {
    qvVoiceDebugEvents.push(entry);
    if (qvVoiceDebugEvents.length > QV2_VOICE_DEBUG_MAX)
      qvVoiceDebugEvents.splice(0, qvVoiceDebugEvents.length - QV2_VOICE_DEBUG_MAX);
    var key = name.split(':')[0];
    if (qvVoiceDebugCounts[key] !== undefined) qvVoiceDebugCounts[key]++;
    else if (key === 'speech') qvVoiceDebugCounts.result++;
    try {
      if (typeof window !== 'undefined' && window) {
        window.__QORA_VOICE_DEBUG = qvVoiceDebugEvents;
        window.__QORA_VOICE_DEBUG_COUNTS = qvVoiceDebugCounts;
      }
    } catch (eW) {}
  } catch (e2) {}
}
function qvVoiceDebugDump() {
  try {
    return JSON.stringify({ events: qvVoiceDebugEvents.slice(), counts: qvVoiceDebugCounts });
  } catch (e) { return '{"events":[],"counts":{}}'; }
}
function qvVoiceDebugReset() {
  try {
    qvVoiceDebugEvents = [];
    qvVoiceDebugCounts = { start: 0, onstart: 0, result: 0, final: 0, submit: 0, empty_submit: 0, end: 0, restart: 0, timeout: 0, error: 0 };
    try {
      if (typeof window !== 'undefined' && window) {
        window.__QORA_VOICE_DEBUG = qvVoiceDebugEvents;
        window.__QORA_VOICE_DEBUG_COUNTS = qvVoiceDebugCounts;
      }
    } catch (eW) {}
  } catch (e) {}
}
// One-line empty-submit summary (counts + timings, NEVER text content).
function qvFormatEmptySubmitDebug(o) {
  o = o || {};
  try {
    var parts = ['empty_submit',
      'results=' + (o.results | 0),
      'finals=' + (o.finals | 0),
      'restarts=' + (o.restarts | 0),
      'elapsed_ms=' + (o.elapsedMs | 0),
      'warmed=' + (o.warmed ? 1 : 0),
      'heard=' + (o.heard ? 1 : 0)];
    return '[qv-voice] ' + parts.join(' ');
  } catch (e) { return '[qv-voice] empty_submit'; }
}

// Word-level overlap-join for accumulated FINAL transcripts. Chrome with
// continuous=true re-emits prior finals re-segmented (e.g. 'sudah' then
// 'sudah dari' then 'sudah dari kapan...'); blind concatenation yields the
// staircase 'sudah sudah dari sudah dari kapan...'. Join with largest
// case-insensitive word overlap; a newer revision that covers the whole
// accumulator REPLACEs it; a deliberate single-word repeat is preserved.
function qvSplitWords(s) {
  return String(s || '').trim().split(/\s+/).filter(Boolean);
}
function qvJoinFinal(acc, seg) {
  var a = String(acc || '').trim();
  var s = String(seg || '').trim();
  if (!s) return a;
  if (!a) return s;
  var aw = qvSplitWords(a);
  var sw = qvSplitWords(s);
  if (!aw.length) return s;
  if (!sw.length) return a;
  var al = aw.map(function (w) { return w.toLowerCase(); });
  var sl = sw.map(function (w) { return w.toLowerCase(); });
  var maxK = Math.min(aw.length, sw.length);
  var k = 0;
  for (var kk = maxK; kk >= 1; kk--) {
    var ok = true;
    for (var j = 0; j < kk; j++) {
      if (al[aw.length - kk + j] !== sl[j]) { ok = false; break; }
    }
    if (ok) { k = kk; break; }
  }
  if (k === 0) return (a + ' ' + s).replace(/\s+/g, ' ').trim();
  // NOTE (12 Sep 2026, live data): consecutive identical single-word finals
  // inside ONE utterance ('bisa'|'bisa'|'bisa ceritain') are Chrome
  // re-segmentation artifacts, NOT deliberate emphasis — always join them.
  // Genuine repeats survive because they arrive inside a single final
  // transcript ('sudah sudah'), which this cross-final join never splits.
  // Newer revision covers the whole accumulator — it wins.
  if (k >= aw.length) return s;
  return (aw.join(' ') + ' ' + sw.slice(k).join(' ')).replace(/\s+/g, ' ').trim();
}

// Pure timeout/tap/recognition helpers (unit-tested via plain node; the
// component below is the only caller).
function qvVoiceIdleExpired(lastTs, nowTs, idleMs) {
  var im = (typeof idleMs === 'number' && idleMs > 0) ? idleMs : QV2_VOICE_IDLE_MS;
  return (nowTs - lastTs) >= im;
}
function qvVoiceOverallExpired(startTs, nowTs, overallMs) {
  var om = (typeof overallMs === 'number' && overallMs > 0) ? overallMs : QV2_VOICE_OVERALL_MS;
  return (nowTs - startTs) >= om;
}
function qvVoiceTapAction(phase) {
  if (phase === 'listening') return 'submit';
  if (phase === 'idle' || phase === 'error') return 'start';
  if (phase === 'processing' || phase === 'speaking') return 'cancel';
  return 'none';
}
function qvRecErrorAction(code, hasFinal) {
  if (code === 'not-allowed' || code === 'service-not-allowed') return 'mic_blocked';
  if (code === 'aborted') return 'ignore';
  if (code === 'no-speech' || code === 'audio-capture') return hasFinal ? 'submit' : 'idle_hint';
  // Baseline tolerance (pre-Astra): unknown/transient codes (e.g. network)
  // must NOT kill the session — keep listening, debug-ring log only. The
  // caller ignores them; denials above stay error, no-speech stays handled.
  return 'ignore';
}
function qvVoiceRestartAllowed(failures, maxFailures) {
  var m = (typeof maxFailures === 'number' && maxFailures >= 0) ? maxFailures : QV2_REC_MAX_RESTARTS;
  return failures < m;
}
// Empty-submit decision (never fail silent): no final → visible hint state,
// NOT bare idle. hasHeard = any interim/final/audio ever observed this
// session; fromSilence kept for caller compat but NEVER yields ''.
function qvDecideEmptySubmit(o) {
  o = o || {};
  var hasFinal = !!String(o.finalText || '').trim();
  if (hasFinal) return { action: 'submit' };
  return { action: 'hint', phase: 'idle', hint: 'Tidak terdengar — tap lagi dan bicara' };
}
function qvEmptySubmitHint(hasHeard, fromSilence) {
  var d = qvDecideEmptySubmit({ finalText: '', hasHeard: !!hasHeard, fromSilence: !!fromSilence });
  return d.hint || 'Tidak terdengar — tap lagi dan bicara';
}
// Restart accounting (baseline unbounded + throw-only cap): ONLY rec.start()
// THROWS count toward the cap; ANY result/speech resets to 0; clean onend
// loops leave the count unchanged so they keep working. Cap (10) still
// guards genuine throw-loops.
function qvNextRestartCount(failures, event) {
  var f = (typeof failures === 'number' && failures >= 0) ? failures : 0;
  if (event === 'throw') return f + 1;
  if (event === 'result' || event === 'speech') return 0;
  return f;
}

// ── Adaptive endpointing flag (ADR §3.2) ─────────────────────────────────
// DEFAULT OFF (owner decision 12 Sep 2026): baseline 3000ms interim /
// 1200ms final auto-submit for everyone. Opt-in to adaptive endpointing via
//   localStorage['qora.voice.adaptive'] = '1'
// or window.__QORA_VOICE_ADAPTIVE = true.
function qvVoiceAdaptive() {
  try {
    if (typeof window !== 'undefined' && window.__QORA_VOICE_ADAPTIVE === true) return true;
    if (typeof localStorage !== 'undefined' && localStorage.getItem('qora.voice.adaptive') === '1') return true;
  } catch (e) {}
  return false;
}

// Conservative endpoint thresholds (ADR §3.2, Table T). The python mirror in
// backend/tests/test_voice_phase2_server_orch.py asserts IDENTICAL values —
// change both sides together.
var QV2_EP_FINAL_QUIET = 500, QV2_EP_FINAL_STABLE = 100;
var QV2_EP_INTERIM_QUIET = 800, QV2_EP_INTERIM_STABLE = 400;
var QV2_EP_STOP_GRACE = 250, QV2_EP_HESITATION_HOLD = 1200, QV2_EP_MANUAL_FLUSH = 250;

// Hesitation-tail heuristic (hold, not a clinical parser): utterance ending
// in a conjunction/filler likely continues after a thinking pause.
function qvIsHesitation(text) {
  try {
    var t = (' ' + String(text || '').toLowerCase().replace(/[.,!?;:]+$/, '') + ' ');
    var tails = [' dan ', ' tapi ', ' atau ', ' anu ', ' eh ', ' ehm ', ' maksudnya ',
      ' jadi ', ' kalau ', ' karena ', ' terus ', ' lalu '];
    for (var i = 0; i < tails.length; i++) {
      if (t.slice(-tails[i].length) === tails[i]) return true;
    }
  } catch (e) {}
  return false;
}

// Pure endpoint decision (no timers, no mic, no DOM — unit-tested via the
// python mirror). Input: recognition-event-derived state. Returns
// {action: 'wait'|'submit'|'stop_then_submit', inMs, reason}. Timers are
// armed by the caller; speechstart (resume) cancels any pending submit.
function qvEndpointNext(o) {
  o = o || {};
  if (o.resumed) return { action: 'wait', inMs: -1, reason: 'resume_cancels_submit' };
  if (o.manual) return { action: 'submit', inMs: Math.min(QV2_EP_MANUAL_FLUSH, o.quietMs || 0), reason: 'manual_flush' };
  var fin = String(o.finalText || '').trim(), inter = String(o.interimText || '').trim();
  if (fin && !inter) {
    if (o.hesitation) return { action: 'wait', inMs: QV2_EP_HESITATION_HOLD, reason: 'hesitation_hold' };
    if ((o.quietMs || 0) >= QV2_EP_FINAL_QUIET && (o.finalStableMs || 0) >= QV2_EP_FINAL_STABLE)
      return { action: 'submit', inMs: 0, reason: 'final_quiet' };
    return { action: 'wait', inMs: Math.max(QV2_EP_FINAL_QUIET - (o.quietMs || 0), QV2_EP_FINAL_STABLE - (o.finalStableMs || 0), 0), reason: 'final_armed' };
  }
  if (inter) {
    if (o.hesitation) return { action: 'wait', inMs: QV2_EP_HESITATION_HOLD, reason: 'hesitation_hold' };
    if ((o.quietMs || 0) >= QV2_EP_INTERIM_QUIET && (o.interimStableMs || 0) >= QV2_EP_INTERIM_STABLE)
      return { action: 'stop_then_submit', inMs: QV2_EP_STOP_GRACE, reason: 'interim_stable' };
    return { action: 'wait', inMs: Math.max(QV2_EP_INTERIM_QUIET - (o.quietMs || 0), QV2_EP_INTERIM_STABLE - (o.interimStableMs || 0), 0), reason: 'interim_armed' };
  }
  return { action: 'wait', inMs: -1, reason: 'no_transcript' };
}

// Future audio-activity guard plugin slot (ADR §3.2 local guard). v1: null —
// recognition events only, NO second mic stream (getUserMedia worklet guard
// is future work gated on a capture-compat cohort test). When a guard lands,
// it only supplies {lastActivityTs} consumed below; the state machine above
// is unchanged.
var qvAudioGuard = null;

// ---- Incremental framed parser (backend app/voice/frames.py parity) -----
function qvFeedVoiceFrames(st, more) {
  // st: {pending: Uint8Array} (mutated). Returns [{type, payload}].
  // Throws {voiceFrameError} on oversize/unknown (caller → text fallback).
  var cat = new Uint8Array(st.pending.length + more.length);
  cat.set(st.pending, 0); cat.set(more, st.pending.length);
  st.pending = cat;
  var out = [];
  for (;;) {
    if (st.pending.length < 5) return out;
    var dv = new DataView(st.pending.buffer, st.pending.byteOffset, st.pending.byteLength);
    var type = dv.getUint8(0), len = dv.getUint32(1, false);
    if (type !== QV2_VF_META && type !== QV2_VF_TEXT && type !== QV2_VF_PCM &&
        type !== QV2_VF_ERR && type !== QV2_VF_DONE)
      throw { voiceFrameError: 'unknown_frame_' + type };
    var cap = (type === QV2_VF_PCM) ? QV2_VOICE_MAX_FRAME : QV2_VOICE_MAX_JSON;
    if (len > cap) throw { voiceFrameError: 'frame_too_large' };
    if (st.pending.length < 5 + len) return out;
    out.push({ type: type, payload: st.pending.slice(5, 5 + len) });
    st.pending = st.pending.slice(5 + len);
  }
}
function qvVoiceJson(payload) {
  try {
    return JSON.parse(new TextDecoder().decode(payload));
  } catch (e) { return {}; }
}
function qvNewClientTurnId() {
  try {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) return 'ct-' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
  } catch (e) {}
  return 'ct-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
}

// ---- Single-flight voice sender (one fetch per client_turn_id) ----------
var qvVoiceFlight = {}; // client_turn_id -> Promise (no double-inference)
function qvSendVoiceTurn(opts) {
  // opts: {sessionId, clientTurnId, transcript, telemetry, ctx, analyser,
  //        signal, onPhase('speaking'), onFirstAudio}
  var key = String(opts.clientTurnId || '');
  if (key && qvVoiceFlight[key]) return qvVoiceFlight[key];
  var p = _qvSendVoiceTurnOnce(opts).then(function (r) { delete qvVoiceFlight[key]; return r; },
    function (e) { delete qvVoiceFlight[key]; throw e; });
  if (key) qvVoiceFlight[key] = p;
  return p;
}
function _qvSendVoiceTurnOnce(opts) {
  // Resolves {ok:true, text, meta} after clean done (audio fully scheduled);
  // resolves {ok:false, text, truncated:true} when the winner text arrived
  // but audio did not (text fallback, NO re-inference); rejects {http} or
  // {voiceError} otherwise. Timeouts: IDLE (no frame/byte for
  // QV2_VOICE_IDLE_MS, resets on every chunk) + OVERALL
  // (QV2_VOICE_OVERALL_MS total cap). Both abort the fetch/reader, stop
  // partial audio, and reject with {voiceError:'idle_timeout'|'turn_timeout'}
  // so the caller shows error-with-retry on the SAME client_turn_id.
  // External abort (opts.signal, e.g. orb tap-cancel) rejects with
  // {voiceError:'cancelled', cancelled:true} so the caller can stay idle
  // with a 'dibatalkan' hint instead of error UI.
  return (async function () {
    var tok = (typeof _qv2Token === 'function') ? _qv2Token() : '';
    var headers = { 'Content-Type': 'application/json' };
    if (tok) headers['Authorization'] = 'Bearer ' + tok;
    var base = (typeof _qv2Base === 'function') ? _qv2Base() : '';
    var extSignal = opts.signal;
    function isCancelled() {
      try { return !!(extSignal && extSignal.aborted); } catch (e) { return false; }
    }
    // Internal controller merges external cancel + timeout aborts so a
    // hanging fetch (no headers) also unblocks. External abort forwards in.
    var intCtl = null;
    try { intCtl = new AbortController(); } catch (e) { intCtl = null; }
    var intSignal = intCtl ? intCtl.signal : extSignal;
    var extHandler = null;
    if (extSignal && intCtl && !isCancelled()) {
      extHandler = function () { try { intCtl.abort(); } catch (e) {} };
      try { extSignal.addEventListener('abort', extHandler); } catch (e2) {}
    }
    if (isCancelled() && intCtl) { try { intCtl.abort(); } catch (e3) {} }
    var startTs = Date.now();
    var lastTs = startTs;
    var reader = null;
    var st = { pending: new Uint8Array(0) };
    var meta = null, text = '', pcmBytes = 0, pcmChunks = 0;
    var ctx = opts.ctx, analyser = opts.analyser;
    var sources = [];
    var playAt = ctx.currentTime + 0.05;
    var firstFired = false;
    function stopSources() {
      for (var si = 0; si < sources.length; si++) {
        try { sources[si].stop(); } catch (e) {}
        try { sources[si].disconnect(); } catch (e2) {}
      }
      sources = [];
    }
    function schedulePcm(bytes) {
      var buf = qvPcmToBuffer(ctx, bytes);
      var src = ctx.createBufferSource();
      src.buffer = buf;
      if (analyser) src.connect(analyser);
      else src.connect(ctx.destination);
      var dur = buf.duration;
      src.start(Math.max(playAt, ctx.currentTime + 0.01));
      playAt = Math.max(playAt, ctx.currentTime + 0.01) + dur;
      sources.push(src);
      if (!firstFired) {
        firstFired = true;
        try { if (opts.onPhase) opts.onPhase('speaking'); } catch (e) {}
        try { if (opts.onFirstAudio) opts.onFirstAudio(); } catch (e2) {}
      }
    }
    // Stop scheduled audio as soon as any abort fires (tap-cancel or
    // timeout) so a cancelled turn goes silent immediately.
    if (intSignal) {
      try {
        intSignal.addEventListener('abort', function () { try { stopSources(); } catch (e) {} });
      } catch (e4) {}
    }
    var idleFired = false, overallFired = false;
    var idleTimer = null, overallTimer = null;
    function clearVoiceTimers() {
      try { if (idleTimer) clearTimeout(idleTimer); } catch (e) {}
      try { if (overallTimer) clearTimeout(overallTimer); } catch (e2) {}
      idleTimer = null; overallTimer = null;
    }
    function armIdle() {
      try { if (idleTimer) clearTimeout(idleTimer); } catch (e) {}
      idleTimer = setTimeout(function () {
        idleFired = true;
        try { if (reader) reader.cancel(); } catch (e2) {}
        try { if (intCtl) intCtl.abort(); } catch (e3) {}
      }, QV2_VOICE_IDLE_MS);
    }
    overallTimer = setTimeout(function () {
      overallFired = true;
      try { if (reader) reader.cancel(); } catch (e) {}
      try { if (intCtl) intCtl.abort(); } catch (e2) {}
    }, QV2_VOICE_OVERALL_MS);
    armIdle();
    try {
      var res = await fetch(base + '/api/v2/sessions/' + encodeURIComponent(opts.sessionId) + '/turns/voice-stream', {
        method: 'POST', headers: headers,
        body: JSON.stringify({ client_turn_id: opts.clientTurnId, transcript: opts.transcript,
          client_telemetry: opts.telemetry || undefined }),
        signal: intSignal,
      });
      if (isCancelled()) throw { voiceError: 'cancelled', cancelled: true, text: text };
      if (overallFired || qvVoiceOverallExpired(startTs, Date.now(), QV2_VOICE_OVERALL_MS))
        throw { voiceError: 'turn_timeout', text: text };
      if (idleFired) throw { voiceError: 'idle_timeout', text: text };
      lastTs = Date.now();
      armIdle(); // headers arrived = progress
      if (!res.ok || !res.body) {
        var errText = '';
        try { errText = await res.text(); } catch (e) {}
        throw { http: res.status, body: (errText || '').slice(0, 200) };
      }
      reader = res.body.getReader();
      for (;;) {
        var rd = await reader.read();
        if (isCancelled()) throw { voiceError: 'cancelled', cancelled: true, text: text };
        if (overallFired) throw { voiceError: 'turn_timeout', text: text };
        if (idleFired) throw { voiceError: 'idle_timeout', text: text };
        var now = Date.now();
        if (qvVoiceOverallExpired(startTs, now, QV2_VOICE_OVERALL_MS))
          throw { voiceError: 'turn_timeout', text: text };
        if (rd.done) break;
        // Any byte chunk = progress: reset the IDLE watchdog so healthy
        // slow streams (LLM 20s guard + TTS) NEVER trip it.
        lastTs = now;
        armIdle();
        var frames;
        try { frames = qvFeedVoiceFrames(st, rd.value); }
        catch (fe) { throw { voiceError: (fe && fe.voiceFrameError) || 'frame_error', text: text }; }
        for (var i = 0; i < frames.length; i++) {
          var f = frames[i];
          if (f.type === QV2_VF_META) { meta = qvVoiceJson(f.payload); }
          else if (f.type === QV2_VF_TEXT) { text = String(qvVoiceJson(f.payload).text || ''); }
          else if (f.type === QV2_VF_PCM) { schedulePcm(f.payload); pcmBytes += f.payload.length; pcmChunks++; }
          else if (f.type === QV2_VF_ERR) {
            var ej = qvVoiceJson(f.payload);
            throw { voiceError: String(ej.code || 'server_error'), text: text };
          } else if (f.type === QV2_VF_DONE) {
            // DONE wait is bounded audio-schedule time, not frame silence:
            // idle watchdog stops here, overall cap still applies.
            try { if (idleTimer) clearTimeout(idleTimer); } catch (eIdle) {}
            idleTimer = null;
            var waitMs = Math.max(0, (playAt - ctx.currentTime) * 1000) + 150;
            var remain = QV2_VOICE_OVERALL_MS - (Date.now() - startTs);
            if (remain <= 0) throw { voiceError: 'turn_timeout', text: text };
            if (waitMs > remain) {
              // Audio would outlive the overall cap: wait only until the
              // cap, then surface timeout-with-retry (winner text kept).
              await new Promise(function (_, rej) {
                var t = setTimeout(function () { rej({ voiceError: 'turn_timeout', text: text }); }, Math.max(0, remain));
                if (intSignal) {
                  var onAb = function () {
                    try { clearTimeout(t); } catch (e2) {}
                    if (isCancelled()) rej({ voiceError: 'cancelled', cancelled: true, text: text });
                    else rej({ voiceError: 'turn_timeout', text: text });
                  };
                  try {
                    if (intSignal.aborted) onAb();
                    else intSignal.addEventListener('abort', onAb, { once: true });
                  } catch (e3) {}
                }
              });
            } else {
              await new Promise(function (res2, rej2) {
                var done2 = false;
                var t2 = setTimeout(function () { if (!done2) { done2 = true; res2(); } }, waitMs);
                if (intSignal) {
                  var onAb2 = function () {
                    if (done2) return; done2 = true;
                    try { clearTimeout(t2); } catch (e2) {}
                    if (isCancelled()) rej2({ voiceError: 'cancelled', cancelled: true, text: text });
                    else if (overallFired) rej2({ voiceError: 'turn_timeout', text: text });
                    else rej2({ voiceError: 'cancelled', cancelled: true, text: text });
                  };
                  try {
                    if (intSignal.aborted) onAb2();
                    else intSignal.addEventListener('abort', onAb2, { once: true });
                  } catch (e3) {}
                }
              });
              if (isCancelled()) throw { voiceError: 'cancelled', cancelled: true, text: text };
              if (overallFired) throw { voiceError: 'turn_timeout', text: text };
            }
            clearVoiceTimers();
            try { if (extSignal && intCtl && extHandler) extSignal.removeEventListener('abort', extHandler); } catch (e5) {}
            return { ok: true, text: text, meta: meta, pcmBytes: pcmBytes, pcmChunks: pcmChunks };
          }
        }
      }
    } catch (e) {
      clearVoiceTimers();
      try { if (extSignal && intCtl && extHandler) extSignal.removeEventListener('abort', extHandler); } catch (eRem) {}
      if (e && e.cancelled) { try { stopSources(); } catch (eS) {} throw e; }
      if (isCancelled()) { try { stopSources(); } catch (eS2) {} throw { voiceError: 'cancelled', cancelled: true, text: text }; }
      if (e && (e.http || e.voiceError)) {
        if (e.voiceError === 'cancelled' || e.voiceError === 'idle_timeout' || e.voiceError === 'turn_timeout') {
          try { stopSources(); } catch (eS3) {}
        }
        throw e;
      }
      if (overallFired) { try { stopSources(); } catch (eS4) {} throw { voiceError: 'turn_timeout', text: text }; }
      if (idleFired) { try { stopSources(); } catch (eS5) {} throw { voiceError: 'idle_timeout', text: text }; }
      // Fetch/reader AbortError without flags (timeout abort racing) maps
      // to the matching timeout when elapsed time says so.
      try {
        var nm = String((e && (e.name || e.message)) || e || '');
        if (/abort/i.test(nm)) {
          var el = Date.now() - startTs;
          if (el >= QV2_VOICE_OVERALL_MS) throw { voiceError: 'turn_timeout', text: text };
          if ((Date.now() - lastTs) >= QV2_VOICE_IDLE_MS) throw { voiceError: 'idle_timeout', text: text };
        }
      } catch (eMap) {
        if (eMap && (eMap.voiceError === 'turn_timeout' || eMap.voiceError === 'idle_timeout')) throw eMap;
      }
      throw { voiceError: String((e && e.message) || e || 'stream_failed'), text: text };
    }
    clearVoiceTimers();
    try { if (extSignal && intCtl && extHandler) extSignal.removeEventListener('abort', extHandler); } catch (eFin) {}
    // Stream ended without done: truncated. Winner text (if any) still usable.
    if (text) return { ok: false, text: text, truncated: true, pcmBytes: pcmBytes };
    throw { voiceError: 'truncated', text: '' };
  })();
}

// ---- Voice orb: the SINGLE interaction object (no mic-icon literal) -----
// idle: breathe + "tap to speak" · listening: stop square + ping ring (tap
// submits) · processing: soft dots (tap CANCELS) · speaking: analyser scale
// + eq bars (tap CANCELS) · error: "!". Tap during processing/speaking
// CANCELS the turn (abort fetch, stop audio, idle + 'dibatalkan' hint, NO
// auto relisten) — no barge-in v1, but never inert.
function QV2VoiceOrb(props) {
  var phase = props.phase; // idle|listening|processing|speaking|error
  var analyserRef = props.analyserRef;
  var onTap = props.onTap;
  var disabled = !!props.disabled;
  var dimmed = !!props.dimmed;
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
      try {
        if (dotRef.current) dotRef.current.style.transform = 'scale(' + (1 + lvl * 0.28).toFixed(3) + ')';
        if (ringRef.current) {
          ringRef.current.style.opacity = String(0.25 + lvl * 0.6);
          ringRef.current.style.transform = 'scale(' + (1 + lvl * 0.55).toFixed(3) + ')';
        }
      } catch (e) {}
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return function () { alive = false; try { cancelAnimationFrame(raf); } catch (e) {} };
  }, [phase]);
  var bg = phase === 'speaking' ? 'radial-gradient(circle at 35% 30%, #3ddbb9, #1f8f7a 70%)'
    : phase === 'error' ? 'radial-gradient(circle at 35% 30%, #e88, #b44 70%)'
    : 'radial-gradient(circle at 35% 30%, #9a76db, #5c3f96 70%)';
  var inner = null;
  if (phase === 'listening') {
    inner = React.createElement('div', { style: { width: 30, height: 30, borderRadius: 9, background: '#fff' } });
  } else if (phase === 'processing') {
    inner = React.createElement('div', { className: 'qv2-orb-dots', style: { display: 'flex', gap: 6 } },
      React.createElement('span', null, '•'), React.createElement('span', null, '•'), React.createElement('span', null, '•'));
  } else if (phase === 'speaking') {
    inner = React.createElement('div', { className: 'qv2-eq' },
      [0, 1, 2, 3, 4].map(function (i) { return React.createElement('span', { key: i }); }));
  } else if (phase === 'error') {
    inner = React.createElement('div', { style: { color: '#fff', fontSize: 44, fontWeight: 800 } }, '!');
  } else {
    inner = React.createElement('div', { style: { color: 'rgba(255,255,255,0.92)', fontSize: 11, fontWeight: 800, letterSpacing: '0.22em', textAlign: 'center', lineHeight: 1.9 } }, 'TAP', React.createElement('br', null), 'TO SPEAK');
  }
  return React.createElement('div', { style: { position: 'relative', width: 196, height: 196, margin: '0 auto' } },
    React.createElement('div', { ref: ringRef, className: phase === 'listening' ? 'qv2-orb-ring-ping' : '', style: { position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid ' + (phase === 'speaking' ? '#2ea08c' : 'var(--primary)'), opacity: 0.25, pointerEvents: 'none' } }),
    React.createElement('button', {
      ref: dotRef, onClick: disabled ? undefined : onTap, disabled: disabled,
      'aria-label': phase === 'listening' ? 'Send now'
        : (phase === 'processing' || phase === 'speaking') ? 'Cancel voice turn' : 'Speak',
      className: phase === 'idle' && !disabled ? 'qv2-orb-idle' : (disabled ? 'qv2-orb-off' : ''),
      style: {
        position: 'absolute', inset: 18, borderRadius: '50%', border: 'none',
        background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
        cursor: disabled ? 'default' : 'pointer', opacity: dimmed ? 0.55 : 1, padding: 0,
      },
    }, inner));
}

// ---- Voice room -----------------------------------------------------------
function QV2VoiceRoom(props) {
  // props: {sessionId, language, messages, busy, err, voiceCap,
  //         onSendText(text)->Promise<string|null> (legacy; voice path no
  //           longer calls it — kept for prop compat),
  //         onVoiceCommit(userText, replyText) (voice winner bubbles, no
  //           inference — the server already persisted both turns),
  //         onSwitchToText, onExam, onAssess, onExit, caseTitle}
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
  var lastVoiceRef = React.useRef(null); // {id, text} last voice turn — manual retry reuses id
  var epRef = React.useRef(null); // adaptive endpoint tracker (null when flag off)
  var epReasonRef = React.useRef(''); // endpoint reason → server telemetry
  var voiceCtlRef = React.useRef(null); // AbortController for in-flight voice turn
  var turnGenRef = React.useRef(0); // voice-turn generation: tap-cancel bumps, late results ignored
  var restartRef = React.useRef(0); // rec.start() THROW count only (clean onend loops don't count)
  var heardRef = React.useRef(false); // any interim/final/audio observed this session
  var sessStartRef = React.useRef(0); // session start ts for empty-submit diagnostics
  var resultCountRef = React.useRef(0); // per-session result events (debug summary)
  var finalCountRef = React.useRef(0); // per-session non-empty finals (debug summary)
  phaseRef.current = phase;

  function clearTimer() {
    try { if (timerRef.current) clearTimeout(timerRef.current); } catch (e) {}
    timerRef.current = null;
  }
  // Baseline two-tier silence (pre-Astra, smooth): interim (still forming
  // words, thinking pauses OK) gets full 3000ms patience; once the browser
  // finalizes a sentence, 1200ms is enough. Manual tap anytime.
  var QV2_SILENCE_INTERIM_MS = 3000;
  var QV2_SILENCE_FINAL_MS = 1200;
  function armSilence(ms) {
    clearTimer();
    timerRef.current = setTimeout(function () {
      // No new utterance content for the window → auto-submit.
      finishSubmit(true);
    }, (typeof ms === 'number' && ms > 0) ? ms : QV2_SILENCE_INTERIM_MS);
  }
  function stopRec() {
    wantRef.current = false;
    clearTimer();
    try { if (epRef.current && epRef.current.timer) clearTimeout(epRef.current.timer); } catch (e) {}
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
  // ── Adaptive endpointing (flag-gated; baseline below untouched) ──────
  // Recognition-events-only state machine (ADR §3.2). qvAudioGuard (future
  // local audio-activity guard) is null in v1 — NO second mic stream.
  function epDecide(manual) {
    var ep = epRef.current;
    if (!ep || submittedRef.current) return;
    if (ep.timer) { try { clearTimeout(ep.timer); } catch (e) {} ep.timer = null; }
    if (ep.flushArmed && !manual) return; // manual flush owns the timer
    var now = Date.now();
    var text = ((ep.finalText || '') + ' ' + (ep.interimText || '')).trim();
    var d = qvEndpointNext({ finalText: ep.finalText, interimText: ep.interimText,
      finalStableMs: now - ep.finalAt, interimStableMs: now - ep.interimAt,
      quietMs: now - ep.lastAudioTs, resumed: false, manual: !!manual,
      hesitation: qvIsHesitation(text) });
    if (d.action === 'submit') {
      epReasonRef.current = d.reason;
      if (d.inMs > 0) ep.timer = setTimeout(function () { finishSubmit(true); }, d.inMs);
      else finishSubmit(true);
    } else if (d.action === 'stop_then_submit') {
      epReasonRef.current = d.reason;
      try { var r = recRef.current; if (r) r.stop(); } catch (e2) {}
      ep.stopped = true;
      ep.timer = setTimeout(function () { finishSubmit(true); }, Math.max(0, d.inMs));
    } else if (d.inMs >= 0) {
      epReasonRef.current = d.reason;
      ep.timer = setTimeout(function () { epDecide(false); }, Math.min(d.inMs, 1200) + 50);
    }
  }
  function epObserveResult(fin, inter) {
    var ep = epRef.current;
    if (!ep || submittedRef.current) return;
    var now = Date.now();
    ep.lastAudioTs = now; // utterance content resets the activity clock
    if (fin !== ep.finalText) { ep.finalText = fin; ep.finalAt = now; }
    if (inter !== ep.interimText) { ep.interimText = inter; ep.interimAt = now; }
    setInterim(((fin + ' ' + inter).trim()));
    if (ep.flushArmed && fin.trim()) {
      // Manual flush grace: a fresh final arrived — send now, don't wait.
      try { clearTimeout(ep.timer); } catch (e) {}
      ep.timer = null;
      finishSubmit(false);
      return;
    }
    epDecide(false);
  }
  function epManualFlush() {
    // Manual orb send: drop silence wait, stop() the recognizer, allow a
    // final ≤250ms grace for a late final — never cut one that arrives.
    if (submittedRef.current) return;
    var ep = epRef.current;
    epReasonRef.current = 'manual_flush';
    try { var r = recRef.current; if (r) r.stop(); } catch (e) {}
    if (ep.timer) { try { clearTimeout(ep.timer); } catch (e2) {} ep.timer = null; }
    ep.flushArmed = true;
    ep.timer = setTimeout(function () { finishSubmit(false); }, QV2_EP_MANUAL_FLUSH);
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
    epReasonRef.current = '';
    try { restartRef.current = 0; } catch (eR0) {}
    // Stale-timer clear: a pending silence timer from a prior session must
    // NEVER fire into the new one.
    clearTimer();
    try { if (epRef.current && epRef.current.timer) clearTimeout(epRef.current.timer); } catch (eEp0) {}
    try { heardRef.current = false; } catch (eH0) {}
    try { sessStartRef.current = Date.now(); } catch (eS0) {}
    try { resultCountRef.current = 0; } catch (eC0) {}
    try { finalCountRef.current = 0; } catch (eC1) {}
    try { qvVoiceDebugLog('start'); } catch (eDbg0) {}
    // Adaptive tracker lives only when the flag is on; null otherwise so the
    // baseline path below runs byte-identical to the shipped behavior.
    epRef.current = qvVoiceAdaptive()
      ? { lastAudioTs: Date.now(), finalText: '', finalAt: Date.now(),
          interimText: '', interimAt: Date.now(), timer: null,
          stopped: false, flushArmed: false }
      : null;
    var rec;
    try { rec = new SR(); } catch (e) {
      try { qvVoiceDebugLog('error:start-throw'); } catch (eDbgT) {}
      setPhase('error'); setVErr('Could not start microphone.');
      return;
    }
    recRef.current = rec;
    wantRef.current = true;
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    // Baseline: silence timer arms at rec.start() below (instant listening,
    // no onstart gating). onstart stays ONLY as a debug-ring event.
    rec.onstart = function () {
      try { qvVoiceDebugLog('onstart'); } catch (eDbg) {}
    };
    rec.onresult = function (e) {
      if (submittedRef.current) return;
      // Flaky-net safe: ANY result resets the throw-loop counter (pure helper).
      try { restartRef.current = qvNextRestartCount(restartRef.current, 'result'); } catch (eR) { try { restartRef.current = 0; } catch (eR2) {} }
      try { resultCountRef.current = (resultCountRef.current | 0) + 1; } catch (eC) {}
      try { qvVoiceDebugLog('result'); } catch (eDbgR) {}
      // REBUILD finals from the full results array every event (never append
      // deltas): Chrome re-delivers prior finals re-segmented across events
      // with continuous=true. Blind concatenation caused BOTH the old
      // "halo Halo Halo…" echo AND the staircase duplication ('sudah' then
      // 'sudah dari' then 'sudah dari kapan...' → 'sudah sudah dari ...').
      // Fix: word-level overlap-join (qvJoinFinal); interim is untouched.
      var fin = '', inter = '';
      try {
        for (var i = 0; i < e.results.length; i++) {
          var t = ((e.results[i][0] || {}).transcript || '');
          if (e.results[i].isFinal) fin = qvJoinFinal(fin, t);
          else inter += t;
        }
      } catch (err2) {}
      fin = fin.trim(); inter = inter;
      finalRef.current = fin;
      if ((fin + ' ' + inter).trim()) {
        try { heardRef.current = true; } catch (eH) {}
        try { qvVoiceDebugLog('final'); } catch (eDbgF) {}
        try { finalCountRef.current = (finalCountRef.current | 0) + 1; } catch (eC2) {}
      }
      if (epRef.current) { epObserveResult(fin, inter); return; }
      setInterim(((finalRef.current + ' ' + inter).trim()));
      // Any utterance content resets the clock: interim (user still shaping
      // the sentence, may pause to think) gets full patience; a fresh final
      // means the sentence landed — send quickly.
      if (fin.trim()) armSilence(QV2_SILENCE_FINAL_MS);
      else if (inter.trim()) armSilence(QV2_SILENCE_INTERIM_MS);
    };
    // Speech edge resets the throw-loop counter on BOTH paths (flaky-net
    // safe). Mapped to the 'result' debug token (allowed names only).
    function qvOnSpeechStart() {
      if (submittedRef.current) return;
      try { restartRef.current = qvNextRestartCount(restartRef.current, 'speech'); } catch (eRs) {}
      try { heardRef.current = true; } catch (eHs) {}
      try { qvVoiceDebugLog('result'); } catch (eDbgS) {}
    }
    if (epRef.current) {
      // Adaptive recognition events (baseline speech handler below is separate).
      rec.onspeechstart = function () {
        qvOnSpeechStart();
        var ep = epRef.current;
        if (!ep || submittedRef.current) return;
        ep.lastAudioTs = Date.now();
        ep.stopped = false;
        // Resume-cancels-submit: speaking again drops any pending submit.
        if (!ep.flushArmed && ep.timer) { try { clearTimeout(ep.timer); } catch (e) {} ep.timer = null; }
      };
      rec.onspeechend = function () {
        var ep = epRef.current;
        if (!ep || submittedRef.current) return;
        ep.lastAudioTs = Date.now(); // detection edge; quiet accrues from here
        epDecide(false);
      };
    } else {
      rec.onspeechstart = function () { qvOnSpeechStart(); };
    }
    rec.onerror = function (e) {
      var code = (e && e.error) || '';
      try { qvVoiceDebugLog('error:' + String(code || 'unknown').slice(0, 24)); } catch (eDbgE) {}
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
          // Never fail silent (live dead-mic): always a visible hint, even
          // for auto sessions (previously '' when auto=true).
          setPhase('idle');
          setHint('Tidak terdengar — tap lagi dan bicara');
          try { qvVoiceDebugLog('empty_submit'); } catch (eDbgEs) {}
        }
        return;
      }
      // Baseline tolerance (pre-Astra): unknown/transient codes (e.g.
      // network) must NOT kill the session — keep listening, debug-ring log
      // only (logged above). Denials stay error, no-speech stays handled.
      return;
    };
    rec.onend = function () {
      // Baseline unbounded restart-on-clean-end (pre-Astra): Chrome ends
      // recognition on pauses by itself — if we still want to listen and
      // nothing was submitted, restart. Clean ends NEVER consume the cap;
      // ONLY rec.start() THROWS do (generous cap 10 guards throw-loops).
      try { qvVoiceDebugLog('end'); } catch (eDbgEnd) {}
      if (unmountedRef.current || submittedRef.current || !wantRef.current) return;
      if ((finalRef.current || '').trim()) { finishSubmit(true); return; }
      if (!qvVoiceRestartAllowed(restartRef.current, QV2_REC_MAX_RESTARTS)) {
        stopRec();
        if (phaseRef.current === 'listening') {
          setPhase('idle');
          setHint('Mic berhenti — tap lagi untuk bicara.');
        }
        return;
      }
      try {
        if (recRef.current === rec) {
          rec.start();
          try { qvVoiceDebugLog('restart'); } catch (eDbgRs) {}
          if (epRef.current) {
            epRef.current.lastAudioTs = Date.now();
            epDecide(false);
          } else armSilence();
          return;
        }
      } catch (e2) {
        // rec.start() threw (mic dead / InvalidStateError on rapid
        // stop->start): ONLY throws count toward the cap (pure helper).
        try { restartRef.current = qvNextRestartCount(restartRef.current, 'throw'); } catch (eRc) {}
        try { qvVoiceDebugLog('error:start-throw'); } catch (eDbgT2) {}
        try { stopRec(); } catch (e3) {}
        if (phaseRef.current === 'listening') {
          // Never fail silent: visible hint even before the cap trips.
          setPhase('idle');
          setHint('Mic berhenti — tap lagi untuk bicara.');
        }
        return;
      }
      if (phaseRef.current === 'listening') setPhase('idle');
    };
    try {
      rec.start();
      ensureAudio(); // unlock audio inside the tap gesture
      setPhase('listening');
      // Baseline: arm the silence timer at rec.start() time (tap → instant
      // listening, 3000ms interim / 1200ms final patience). No onstart
      // gating, no start-timeout error. Adaptive path re-arms via epDecide.
      if (epRef.current) {
        try { epRef.current.lastAudioTs = Date.now(); } catch (eEpT) {}
        try { epDecide(false); } catch (eEpD) {}
        // Fallback: if adaptive left no timer (no transcript yet), ensure the
        // baseline interim window still auto-submits empty → visible hint.
        try {
          if (!epRef.current.timer) {
            (function (ep) {
              ep.timer = setTimeout(function () {
                if (!submittedRef.current && !((ep.finalText + ' ' + ep.interimText).trim())) finishSubmit(true);
              }, QV2_SILENCE_INTERIM_MS);
            })(epRef.current);
          }
        } catch (eEpF) {}
      } else {
        armSilence();
      }
    } catch (e) {
      try { qvVoiceDebugLog('error:start-throw'); } catch (eDbgTC) {}
      setPhase('error'); setVErr('Could not start microphone.');
    }
  }
  function finishSubmit(fromSilence) {
    if (submittedRef.current) return;
    submittedRef.current = true;
    var text = (finalRef.current || '').trim();
    var heard = false;
    try { heard = !!heardRef.current || !!text; } catch (eH) {}
    stopRec();
    setInterim('');
    if (!text) {
      // Never fail silent: empty submit (no final AND no interim ever
      // observed) lands on a VISIBLE hint state, not bare idle.
      // idle-with-hint tap still restarts via onMicTap.
      var dec = null;
      try { dec = qvDecideEmptySubmit({ finalText: '', hasHeard: heard, fromSilence: !!fromSilence }); } catch (eD) {}
      var hintText = (dec && dec.hint) || 'Tidak terdengar — tap lagi dan bicara';
      try { qvVoiceDebugLog('empty_submit'); } catch (eDbgE2) {}
      try {
        if (typeof console !== 'undefined' && console.debug) {
          var elapsed = 0;
          try { elapsed = Date.now() - (sessStartRef.current || Date.now()); } catch (eEl) {}
          console.debug(qvFormatEmptySubmitDebug({
            results: (resultCountRef.current | 0),
            finals: (finalCountRef.current | 0),
            restarts: (restartRef.current | 0),
            elapsedMs: elapsed,
            // Baseline: no warmup gate — mic assumed open at rec.start()
            // (instant listening), so diagnostics mark warmed.
            warmed: true,
            heard: heard,
          }));
        }
      } catch (eDbg) {}
      setPhase('idle');
      setHint(hintText);
      return;
    }
    try { qvVoiceDebugLog('submit'); } catch (eDbgS2) {}
    submitUtterance(text);
  }
  async function submitUtterance(text) {
    if (unmountedRef.current) return;
    setPhase('processing'); setVErr(''); setHint('');
    var cid = qvNewClientTurnId();
    lastVoiceRef.current = { id: cid, text: text };
    var myGen = 0;
    try { turnGenRef.current++; myGen = turnGenRef.current; } catch (eG) {}
    // Patient audio needs the output context; unlock resumes it.
    var ctx = ensureAudio();
    if (!ctx) {
      setPhase('error');
      setVErr('Audio output unavailable here — your words are saved; continue in text mode.');
      return;
    }
    var ctl = null;
    try { ctl = new AbortController(); } catch (e) {}
    voiceCtlRef.current = ctl;
    var res = null, failed = null;
    try {
      res = await qvSendVoiceTurn({
        sessionId: sessionId, clientTurnId: cid, transcript: text,
        telemetry: { endpoint_reason: epReasonRef.current || 'unknown',
          adaptive: qvVoiceAdaptive() ? 1 : 0,
          manual: /manual/.test(epReasonRef.current || '') ? 1 : 0 },
        ctx: ctx, analyser: analyserRef.current,
        signal: ctl ? ctl.signal : undefined,
        onPhase: function (p) { if (!unmountedRef.current && p === 'speaking') setPhase('speaking'); },
        onFirstAudio: function () {},
      });
    } catch (e) {
      failed = e || {};
    }
    voiceCtlRef.current = null;
    if (unmountedRef.current) return;
    // Tap-cancel wins over late results: stay idle with the cancel hint,
    // NO error UI and NO auto relisten.
    try { if (turnGenRef.current !== myGen) return; } catch (eGen) {}
    if (failed && (failed.cancelled || failed.voiceError === 'cancelled')) return;
    if (res && res.ok) {
      // Winner text is already audible; commit bubbles + hands-free next turn.
      // Each voice id commits bubbles at most once (retries replay audio).
      try { if (props.onVoiceCommit) props.onVoiceCommit(text, res.text); } catch (e2) {}
      try { lastVoiceRef.current.committed = true; } catch (e4) {}
      setPhase('idle');
      setTimeout(function () {
        if (!unmountedRef.current) {
          try { if (turnGenRef.current !== myGen) return; } catch (eG2) {}
          startListening(true);
        }
      }, 80);
      return;
    }
    // Failure WITHOUT auto re-inference: the frontend must never POST the
    // text turns endpoint here (that would run a second inference for the
    // same utterance). When the server persisted a winner, its text still
    // arrives — show it; otherwise keep the user's words for manual retry
    // on the SAME client_turn_id (server replays, no new inference).
    // Timeout codes (idle_timeout/turn_timeout) land here as error-with-retry.
    var winnerText = (res && res.text) || (failed && failed.text) || '';
    if (winnerText) {
      try { if (props.onVoiceCommit) props.onVoiceCommit(text, winnerText); } catch (e3) {}
      try { lastVoiceRef.current.committed = true; } catch (e5) {}
    }
    var code = (failed && (failed.http || failed.voiceError)) || 'stream_failed';
    setPhase('error');
    setVErr('Patient audio cut off (' + code + ') — ' +
      (winnerText ? 'the full reply is in the transcript drawer. '
                  : 'your words are kept — ') +
      'tap Retry audio or continue in text.');
  }
  function retryLastVoice() {
    // Manual retry reuses the SAME client_turn_id (idempotent server replay).
    var last = lastVoiceRef.current;
    if (!last || !last.text || phaseRef.current === 'processing' || phaseRef.current === 'speaking') return;
    if (unmountedRef.current) return;
    setPhase('processing'); setVErr(''); setHint('');
    var myGen = 0;
    try { turnGenRef.current++; myGen = turnGenRef.current; } catch (eG) {}
    var ctx = ensureAudio();
    if (!ctx) {
      setPhase('error');
      setVErr('Audio output unavailable here — the reply is in the transcript drawer.');
      return;
    }
    var ctl = null;
    try { ctl = new AbortController(); } catch (e) {}
    voiceCtlRef.current = ctl;
    qvSendVoiceTurn({
      sessionId: sessionId, clientTurnId: last.id, transcript: last.text,
      telemetry: { endpoint_reason: 'manual_retry', adaptive: qvVoiceAdaptive() ? 1 : 0, manual: 1 },
      ctx: ctx, analyser: analyserRef.current,
      signal: ctl ? ctl.signal : undefined,
      onPhase: function (p) { if (!unmountedRef.current && p === 'speaking') setPhase('speaking'); },
      onFirstAudio: function () {},
    }).then(function (res) {
      voiceCtlRef.current = null;
      if (unmountedRef.current) return;
      try { if (turnGenRef.current !== myGen) return; } catch (eG2) {}
      // Same-winner replay: commit bubbles only if this voice id never did
      // (first attempt may already have shown the winner text).
      if (res && res.text && !(last.committed)) {
        try { if (props.onVoiceCommit) props.onVoiceCommit(last.text, res.text); } catch (e2) {}
        try { last.committed = true; } catch (e4) {}
      }
      setPhase('idle');
      setTimeout(function () {
        if (!unmountedRef.current) {
          try { if (turnGenRef.current !== myGen) return; } catch (eG3) {}
          startListening(true);
        }
      }, 80);
    }, function (e) {
      voiceCtlRef.current = null;
      if (unmountedRef.current) return;
      try { if (turnGenRef.current !== myGen) return; } catch (eG4) {}
      if (e && (e.cancelled || e.voiceError === 'cancelled')) return;
      var w = (e && e.text) || '';
      if (w && !(last.committed)) {
        try { if (props.onVoiceCommit) props.onVoiceCommit(last.text, w); } catch (e2) {}
        try { last.committed = true; } catch (e3) {}
      }
      setPhase('error');
      setVErr('Retry failed (' + ((e && (e.http || e.voiceError)) || 'stream_failed') + ') — ' +
        (w ? 'the reply text is in the transcript drawer.' : 'tap Retry audio again or continue in text.'));
    });
  }
  function onMicTap() {
    if (phase === 'listening') {
      // Manual submit: adaptive mode flushes recognition (≤250ms grace for
      // a late final); baseline submits immediately (shipped behavior).
      if (epRef.current) { epManualFlush(); return; }
      finishSubmit(false);
      return;
    }
    if (phase === 'idle' || phase === 'error') { setVErr(''); setHint(''); startListening(false); return; }
    // processing/speaking: TAP CANCELS the turn (new UX — previously inert).
    // Abort the fetch via the existing voiceCtl, stop recognition + player
    // via stopAll, go idle with a cancel hint, NO auto relisten.
    if (phase === 'processing' || phase === 'speaking') {
      try { turnGenRef.current++; } catch (eG) {}
      try { stopAll(); } catch (eS) {}
      setVErr('');
      setPhase('idle');
      setHint('dibatalkan — tap lagi untuk bicara');
      return;
    }
  }
  function stopAll() {
    stopRec();
    try { if (voiceCtlRef.current) voiceCtlRef.current.abort(); } catch (e) {}
    voiceCtlRef.current = null;
    try { if (playerRef.current) playerRef.current.cancel(); } catch (e2) {}
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
      try { if (voiceCtlRef.current) voiceCtlRef.current.abort(); } catch (e) {}
      voiceCtlRef.current = null;
      try { if (playerRef.current) playerRef.current.cancel(); } catch (e2) {}
      playerRef.current = null;
      try { if (ctxRef.current) ctxRef.current.close().catch(function () {}); } catch (e3) {}
      ctxRef.current = null; analyserRef.current = null;
    };
  }, [sessionId]);

  var phaseLabel = phase === 'listening' ? 'Listening… tap the orb to send now'
    : phase === 'processing' ? 'Patient is thinking… tap orb to cancel'
    : phase === 'speaking' ? 'Patient is speaking… tap orb to cancel'
    : phase === 'error' ? 'Something needs attention'
    : (!roomReady ? 'Menyiapkan sesi…' : 'Ready when you are');
  var msgs = props.messages || [];
  // Pinned patient condition (the opening line) — shown as a header card,
  // NOT as chat text. Mic stays disabled until the session + opening exist.
  var opening = '';
  for (var oi = 0; oi < msgs.length; oi++) {
    if (msgs[oi] && msgs[oi].role === 'patient' && (msgs[oi].text || '').trim()) { opening = msgs[oi].text.trim(); break; }
  }
  var roomReady = !!sessionId && !!opening;
  // Center column: orb vertically centered with room to breathe while it
  // pulses; status caption pinned to the bottom above the footer.
  return React.createElement('div', { style: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '18px 16px 12px', minHeight: 'calc(100dvh - 220px)' } },
    // Switch + exit row
    React.createElement('div', { style: { width: '100%', maxWidth: 560, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 } },
      React.createElement('button', { onClick: props.onExit, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '← Library'),
      React.createElement('button', { onClick: props.onSwitchToText, style: { padding: '6px 12px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface-2)', fontSize: 12, fontWeight: 700, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '💬 Text mode')),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-2)', marginBottom: 2 } }, props.caseTitle || ''),
    opening
      ? React.createElement('div', { style: { maxWidth: 560, marginTop: 8, marginBottom: 4, padding: '10px 16px', borderRadius: 14, background: 'var(--surface)', border: '1px solid var(--border)', fontSize: 13, lineHeight: 1.55, color: 'var(--text-1)', textAlign: 'center', fontStyle: 'italic' } }, '“' + opening + '”')
      : React.createElement('div', { style: { marginTop: 8, marginBottom: 4, fontSize: 12.5, color: 'var(--text-3)' } }, 'Menyiapkan pasien…'),
    // Breathing room: orb floats centered with 60px clearance for its pulse.
    // Orb stays tappable in processing/speaking so tap can CANCEL the turn.
    React.createElement('div', { style: { flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0', minHeight: 300 } },
      React.createElement(QV2VoiceOrb, { phase: phase, analyserRef: analyserRef, onTap: onMicTap, dimmed: !roomReady, disabled: !roomReady || props.busy })),
    React.createElement('div', { style: { marginTop: 14, fontSize: 14, fontWeight: 700, color: 'var(--text-1)', minHeight: 20, textAlign: 'center' } }, phaseLabel),
    React.createElement('div', { style: { marginTop: 6, fontSize: 13, color: 'var(--text-2)', fontStyle: 'italic', minHeight: 20, maxWidth: 560, textAlign: 'center', lineHeight: 1.5 } },
      phase === 'listening' ? ('“' + (interim || '…') + '”') : ''),
    ver && React.createElement('div', { style: { marginTop: 10, maxWidth: 560, padding: '10px 14px', borderRadius: 12, background: 'var(--red-l)', color: 'var(--red-d)', fontSize: 12.5, lineHeight: 1.5, textAlign: 'center' } },
      React.createElement('div', null, '⚠️ ' + ver),
      // Manual retry reuses the SAME client_turn_id (idempotent server
      // replay, no new inference) — never an automatic text-turn POST.
      React.createElement('div', { style: { marginTop: 8, display: 'flex', gap: 8, justifyContent: 'center' } },
        React.createElement('button', { onClick: function () { retryLastVoice(); }, style: { padding: '6px 14px', borderRadius: 999, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 12, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '↻ Retry audio'),
        React.createElement('button', { onClick: function () { setDrawer(true); }, style: { padding: '6px 14px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 12, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '📝 Transcript'))),
    hintMsg && !ver && React.createElement('div', { style: { marginTop: 10, fontSize: 12.5, color: 'var(--text-3)' } }, hintMsg),
    React.createElement('div', { style: { marginTop: 8, fontSize: 11.5, color: 'var(--text-3)' } },
      !roomReady ? '' : (phase === 'listening' ? 'Pauses auto-send — tap orb to send now'
        : (phase === 'processing' || phase === 'speaking') ? 'Tap orb to cancel' : '')),
    // Secondary actions — one tap straight to assessment (physical exam
    // lives as a tab inside, skippable by leaving it empty).
    React.createElement('div', { style: { marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' } },
      React.createElement('button', { onClick: function () { setDrawer(true); }, style: { padding: '8px 14px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '📝 Transcript (' + msgs.length + ')'),
      React.createElement('button', { onClick: props.onAssess, disabled: phase !== 'idle', style: { padding: '8px 18px', borderRadius: 999, border: 'none', background: 'var(--primary)', fontSize: 12.5, fontWeight: 700, color: '#fff', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: phase !== 'idle' ? 0.55 : 1 } }, 'Selesai →')),
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
