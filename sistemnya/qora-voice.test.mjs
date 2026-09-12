// Qora voice-room fixes — plain-node tests (no JS runner in repo).
// Run: node sistemnya/qora-voice.test.mjs
// Loads sistemnya/qora-voice.jsx in a vm sandbox with stubs and exercises
// the pure helpers: qvJoinFinal (BUG A) + watchdog/tap/rec-error/restart
// helpers (BUG B). Zero paid calls, no backend, no provider changes.

import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = dirname(fileURLToPath(import.meta.url));
const SRC = join(ROOT, 'qora-voice.jsx');
const code = fs.readFileSync(SRC, 'utf8');

// Minimal stubs so the whole source file evaluates without a browser.
const stubReact = {
  useRef: (v) => ({ current: v }),
  useState: (v) => [v, () => {}],
  useEffect: () => {},
  createElement: (...a) => ({ __el: a }),
};
const sandbox = {
  console,
  React: stubReact,
  window: {},
  localStorage: { getItem: () => null, setItem: () => {} },
  fetch: async () => { throw new Error('no fetch in unit test'); },
  TextDecoder: TextDecoder,
  Uint8Array, DataView, ArrayBuffer,
  AbortController: globalThis.AbortController,
  setTimeout, clearTimeout, setInterval, clearInterval,
  Date, Math, JSON, Object, Array, String, Number, Boolean, RegExp, Error,
  Promise, crypto: globalThis.crypto,
  requestAnimationFrame: (fn) => 0,
  cancelAnimationFrame: () => {},
  _qv2Token: () => '',
  _qv2Base: () => '',
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(code, sandbox, { filename: 'qora-voice.jsx' });

const {
  qvJoinFinal, qvSplitWords,
  qvVoiceIdleExpired, qvVoiceOverallExpired,
  qvVoiceTapAction, qvRecErrorAction, qvVoiceRestartAllowed,
  QV2_VOICE_IDLE_MS, QV2_VOICE_OVERALL_MS, QV2_REC_MAX_RESTARTS,
  QV2_VOICE_DEBUG_MAX,
  qvDecideEmptySubmit, qvEmptySubmitHint,
  qvNextRestartCount,
  qvVoiceDebugLog, qvVoiceDebugDump, qvVoiceDebugReset, qvFormatEmptySubmitDebug,
} = sandbox;

let passed = 0;
function ok(name, fn) {
  fn();
  passed++;
  console.log('ok - ' + name);
}

// ── BUG A: qvJoinFinal ─────────────────────────────────────────────
ok('join: empty acc returns seg', () => {
  assert.equal(qvJoinFinal('', 'sudah'), 'sudah');
  assert.equal(qvJoinFinal(null, 'halo'), 'halo');
});

ok('join: empty seg returns acc', () => {
  assert.equal(qvJoinFinal('sudah', ''), 'sudah');
  assert.equal(qvJoinFinal('sudah', '   '), 'sudah');
});

ok('staircase collapses to longest final', () => {
  // Real Chrome re-segmentation: 'sudah' → 'sudah dari' → 'sudah dari kapan'
  let acc = '';
  acc = qvJoinFinal(acc, 'sudah');
  assert.equal(acc, 'sudah');
  acc = qvJoinFinal(acc, 'sudah dari');
  assert.equal(acc, 'sudah dari');
  acc = qvJoinFinal(acc, 'sudah dari kapan');
  assert.equal(acc, 'sudah dari kapan');
  // With trailing ellipsis variant from the bug report
  let acc2 = qvJoinFinal(qvJoinFinal('', 'sudah'), 'sudah dari');
  acc2 = qvJoinFinal(acc2, 'sudah dari kapan...');
  assert.equal(acc2, 'sudah dari kapan...');
});

ok('staircase does NOT blind-concatenate', () => {
  const bad = 'sudah sudah dari sudah dari kapan';
  const good = qvJoinFinal(qvJoinFinal('sudah', 'sudah dari'), 'sudah dari kapan');
  assert.notEqual(good, bad);
  assert.equal(good, 'sudah dari kapan');
});

ok('consecutive identical single-word finals collapse (live artifact)', () => {
  assert.equal(qvJoinFinal('sudah', 'sudah'), 'sudah');
  assert.equal(
    qvJoinFinal(qvJoinFinal(qvJoinFinal('', 'bisa'), 'bisa'), 'bisa ceritain nggak'),
    'bisa ceritain nggak'
  );
  assert.equal(
    qvJoinFinal('tiba-tiba', 'tiba-tiba atau bagaimana'),
    'tiba-tiba atau bagaimana'
  );
  // Within ONE final we never split: genuine stutter stays as-is.
  assert.equal(
    qvJoinFinal('', 'tiba-tiba tiba-tiba atau bagaimana'),
    'tiba-tiba tiba-tiba atau bagaimana'
  );
});

ok('genuine within-final repeat untouched', () => {
  assert.equal(
    qvJoinFinal('', 'sudah sudah saya mengerti'),
    'sudah sudah saya mengerti'
  );
});

ok('distinct finals appended', () => {
  assert.equal(
    qvJoinFinal('selamat pagi', 'saya sakit kepala'),
    'selamat pagi saya sakit kepala'
  );
  assert.equal(qvJoinFinal('a b c', 'x y z'), 'a b c x y z');
});

ok('case-insensitive overlap (halo|Halo Halo)', () => {
  assert.equal(qvJoinFinal('halo', 'Halo Halo'), 'Halo Halo');
  assert.equal(qvJoinFinal('Halo', 'halo dunia'), 'halo dunia');
});

ok('partial overlap joins suffix only', () => {
  assert.equal(
    qvJoinFinal('saya mau bertanya', 'bertanya tentang obat'),
    'saya mau bertanya tentang obat'
  );
});

ok('newer full revision replaces accumulator', () => {
  assert.equal(qvJoinFinal('sudah dari', 'sudah dari kapan'), 'sudah dari kapan');
});

ok('onresult uses join for finals, interim untouched', () => {
  // Source contract: finals go through qvJoinFinal, interim stays `+=`.
  assert.match(code, /if\s*\(e\.results\[i\]\.isFinal\)\s*fin\s*=\s*qvJoinFinal\(fin,\s*t\)/);
  assert.match(code, /else\s+inter\s*\+=\s*t/);
  // Simulate one onresult rebuild: 2 finals (staircase) + 1 interim.
  const fakeResults = [
    { isFinal: true, 0: { transcript: 'sudah' } },
    { isFinal: true, 0: { transcript: 'sudah dari' } },
    { isFinal: false, 0: { transcript: 'kapan' } },
  ];
  let fin = '', inter = '';
  for (let i = 0; i < fakeResults.length; i++) {
    const t = (fakeResults[i][0] || {}).transcript || '';
    if (fakeResults[i].isFinal) fin = qvJoinFinal(fin, t);
    else inter += t;
  }
  assert.equal(fin, 'sudah dari');
  assert.equal(inter, 'kapan');
});

// ── BUG B: watchdog constants ──────────────────────────────────────
ok('timeout values fit current provider (20s idle / 90s overall)', () => {
  assert.equal(QV2_VOICE_IDLE_MS, 20000);
  assert.equal(QV2_VOICE_OVERALL_MS, 90000);
});

ok('idle watchdog expires only after 20s silence, resets on frame', () => {
  assert.equal(qvVoiceIdleExpired(0, 19999), false);
  assert.equal(qvVoiceIdleExpired(0, 20000), true);
  // Healthy slow stream: a frame at t=19000 resets the clock.
  assert.equal(qvVoiceIdleExpired(19000, 39000 - 1), false);
  assert.equal(qvVoiceIdleExpired(19000, 39000), true);
  // Custom window still respected
  assert.equal(qvVoiceIdleExpired(0, 500, 1000), false);
  assert.equal(qvVoiceIdleExpired(0, 1000, 1000), true);
});

ok('overall cap expires only after 90s total', () => {
  assert.equal(qvVoiceOverallExpired(0, 89999), false);
  assert.equal(qvVoiceOverallExpired(0, 90000), true);
  assert.equal(qvVoiceOverallExpired(1000, 91000), true);
});

ok('tap action: listening submit, idle/error start, processing/speaking cancel', () => {
  assert.equal(qvVoiceTapAction('listening'), 'submit');
  assert.equal(qvVoiceTapAction('idle'), 'start');
  assert.equal(qvVoiceTapAction('error'), 'start');
  assert.equal(qvVoiceTapAction('processing'), 'cancel');
  assert.equal(qvVoiceTapAction('speaking'), 'cancel');
});

ok('rec error mapping: denials error, aborted ignore, baseline tolerance keeps listening', () => {
  assert.equal(qvRecErrorAction('not-allowed', false), 'mic_blocked');
  assert.equal(qvRecErrorAction('service-not-allowed', false), 'mic_blocked');
  assert.equal(qvRecErrorAction('aborted', false), 'ignore');
  assert.equal(qvRecErrorAction('no-speech', true), 'submit');
  assert.equal(qvRecErrorAction('no-speech', false), 'idle_hint');
  assert.equal(qvRecErrorAction('audio-capture', true), 'submit');
  assert.equal(qvRecErrorAction('audio-capture', false), 'idle_hint');
  // Baseline tolerance (pre-Astra revert): unknown/transient codes must NOT
  // kill the session — keep listening (ignore), debug-ring log only.
  assert.equal(qvRecErrorAction('network', true), 'ignore');
  assert.equal(qvRecErrorAction('network', false), 'ignore');
  assert.equal(qvRecErrorAction('unknown', false), 'ignore');
  assert.equal(qvRecErrorAction('', false), 'ignore');
  // Source contract: transient-kill path is gone (no stopRec+hint on network).
  assert.doesNotMatch(code, /Mic terganggu — tap lagi untuk bicara/);
  assert.match(code, /Baseline tolerance.*keep listening/s);
});

ok('onend restart cap is generous throw-only (default 10)', () => {
  assert.equal(QV2_REC_MAX_RESTARTS, 10);
  assert.equal(qvVoiceRestartAllowed(0), true);
  assert.equal(qvVoiceRestartAllowed(9), true);
  assert.equal(qvVoiceRestartAllowed(10), false);
  assert.equal(qvVoiceRestartAllowed(11), false);
});

ok('voice sender has idle+overall abort and cancel/timeout codes', () => {
  assert.match(code, /QV2_VOICE_IDLE_MS/);
  assert.match(code, /QV2_VOICE_OVERALL_MS/);
  assert.match(code, /reader\.cancel\(\)/);
  assert.match(code, /idle_timeout/);
  assert.match(code, /turn_timeout/);
  assert.match(code, /voiceError:\s*'cancelled'/);
});

ok('orb tap-cancel wired (no inert processing/speaking)', () => {
  assert.match(code, /dibatalkan — tap lagi untuk bicara/);
  assert.match(code, /turnGenRef\.current\+\+/);
  assert.doesNotMatch(code, /processing\/speaking:\s*inert/);
});

// ── FIX 1: empty-submit never fails silent ──────────────────────────
ok('empty-submit decision always lands on visible hint (never bare idle)', () => {
  assert.equal(typeof qvDecideEmptySubmit, 'function');
  assert.equal(typeof qvEmptySubmitHint, 'function');
  // No final AND no interim ever observed, auto-submit path (fromSilence=true):
  // previously '' (silent death) — now visible Indonesian hint.
  for (const fromSilence of [true, false]) {
    for (const hasHeard of [false, true]) {
      const d = qvDecideEmptySubmit({ finalText: '', hasHeard, fromSilence });
      assert.equal(d.action, 'hint');
      assert.equal(d.phase, 'idle');
      assert.equal(d.hint, 'Tidak terdengar — tap lagi dan bicara');
      assert.ok((d.hint || '').length > 0, 'hint must never be empty');
    }
  }
  // Non-empty final still submits.
  assert.equal(qvDecideEmptySubmit({ finalText: 'halo dok', hasHeard: true }).action, 'submit');
  assert.equal(qvDecideEmptySubmit({ finalText: '  halo  ', hasHeard: false }).action, 'submit');
  // Convenience wrapper never returns '' either.
  assert.equal(qvEmptySubmitHint(false, true), 'Tidak terdengar — tap lagi dan bicara');
  assert.equal(qvEmptySubmitHint(true, false), 'Tidak terdengar — tap lagi dan bicara');
  // Source contract: finishSubmit routes empty through the pure decision and
  // the old silent branch is gone.
  assert.match(code, /qvDecideEmptySubmit/);
  assert.match(code, /Tidak terdengar — tap lagi dan bicara/);
  assert.doesNotMatch(code, /setHint\(fromSilence \? ''/);
  // idle-with-hint tap still restarts (tap action map unchanged).
  assert.equal(qvVoiceTapAction('idle'), 'start');
  assert.equal(qvVoiceTapAction('error'), 'start');
});

// ── BASELINE REVERT: mic-capture lifecycle back to pre-Astra ─────────
// Tap → instant listening, 3000ms interim / 1200ms final patience, silence
// timer armed at rec.start() (no onstart gating, no start-timeout error).
// rec.onstart stays ONLY as a debug-ring event.
ok('baseline timers restored: interim 3000 / final 1200, no warmup gate', () => {
  // Warmup-gate helpers are gone (revert, not guard).
  assert.equal(typeof sandbox.qvShouldArmSubmitTimer, 'undefined');
  assert.equal(typeof sandbox.qvWarmupTimedOut, 'undefined');
  assert.equal(typeof sandbox.QV2_REC_START_TIMEOUT_MS, 'undefined');
  // Baseline two-tier values restored (were uniform 1200/1200).
  assert.match(code, /QV2_SILENCE_INTERIM_MS\s*=\s*3000/);
  assert.match(code, /QV2_SILENCE_FINAL_MS\s*=\s*1200/);
  assert.doesNotMatch(code, /QV2_SILENCE_INTERIM_MS\s*=\s*1200/);
  // Source contract: no warmup machinery, silence armed at rec.start().
  assert.match(code, /rec\.onstart\s*=/);
  assert.match(code, /qvVoiceDebugLog\('onstart'\)/);
  assert.match(code, /arm the silence timer at rec\.start\(\)/);
  assert.doesNotMatch(code, /QV2_REC_START_TIMEOUT_MS/);
  assert.doesNotMatch(code, /armStartTimeout/);
  assert.doesNotMatch(code, /clearStartTimer/);
  assert.doesNotMatch(code, /qvShouldArmSubmitTimer/);
  assert.doesNotMatch(code, /qvWarmupTimedOut/);
  assert.doesNotMatch(code, /Mic tidak mulai/);
  // startListening clears stale baseline timers and arms immediately.
  assert.match(code, /clearTimer\(\);\s*\n/);
  // rec.start() tail arms silence (baseline) — adaptive falls back to the
  // same interim window when no transcript yet.
  assert.match(code, /rec\.start\(\);\s*\n\s*ensureAudio\(\)/);
  assert.match(code, /else\s*\{\s*\n\s*armSilence\(\);\s*\n\s*\}/);
  // onstart is debug-only: body is just the debug log (no armSilence inside).
  const m = code.match(/rec\.onstart\s*=\s*function\s*\(\)\s*\{([\s\S]{0,400}?)\};/);
  assert.ok(m, 'rec.onstart handler exists');
  assert.doesNotMatch(m[1], /armSilence/);
  assert.doesNotMatch(m[1], /epDecide/);
});

// ── BASELINE REVERT: throw-only restart accounting (cap 10, clean never consumes) ──
ok('restart counter: throw increments, result/speech resets, clean unchanged (cap 10)', () => {
  assert.equal(typeof qvNextRestartCount, 'function');
  assert.equal(qvNextRestartCount(0, 'throw'), 1);
  assert.equal(qvNextRestartCount(9, 'throw'), 10);
  assert.equal(qvNextRestartCount(2, 'result'), 0);
  assert.equal(qvNextRestartCount(2, 'speech'), 0);
  assert.equal(qvNextRestartCount(0, 'result'), 0);
  assert.equal(qvNextRestartCount(1, 'clean'), 1);
  assert.equal(qvNextRestartCount(0, 'clean'), 0);
  assert.equal(qvNextRestartCount(9, 'clean'), 9);
  assert.equal(qvNextRestartCount(1, undefined), 1);
  // Clean onend loops NEVER consume the cap: 10 straight cleans stay at 0.
  let c = 0;
  for (let i = 0; i < 10; i++) c = qvNextRestartCount(c, 'clean');
  assert.equal(c, 0);
  assert.equal(qvVoiceRestartAllowed(c, QV2_REC_MAX_RESTARTS), true);
  // Generous cap 10 for genuine throw-loops.
  assert.equal(QV2_REC_MAX_RESTARTS, 10);
  assert.equal(qvVoiceRestartAllowed(9), true);
  assert.equal(qvVoiceRestartAllowed(10), false);
  // Source contract: throw-only counting via the pure helper; old blind
  // pre-increment (clean ends counting toward the cap) is gone.
  assert.match(code, /qvNextRestartCount\(restartRef\.current,\s*'throw'\)/);
  assert.match(code, /qvNextRestartCount\(restartRef\.current,\s*'result'\)/);
  assert.match(code, /qvNextRestartCount\(restartRef\.current,\s*'speech'\)/);
  assert.doesNotMatch(code, /restartRef\.current\+\+/);
  assert.match(code, /Clean ends NEVER consume/);
  assert.match(code, /Mic berhenti — tap lagi untuk bicara/);
});

// ── FIX 4: diagnostics ring buffer (privacy-safe, actionable) ───────
ok('debug buffer redacts transcripts, caps ~30, dumps JSON', () => {
  assert.equal(typeof qvVoiceDebugLog, 'function');
  assert.equal(typeof qvVoiceDebugDump, 'function');
  assert.equal(typeof qvFormatEmptySubmitDebug, 'function');
  assert.equal(QV2_VOICE_DEBUG_MAX, 30);
  qvVoiceDebugReset();
  const secretFinal = 'sudah dari kapan rahasia-payload-xyz-123';
  const secretInterim = 'kapan interim rahasia-payload-xyz-123';
  // Normal lifecycle usage: ev names only, never text content.
  qvVoiceDebugLog('start');
  qvVoiceDebugLog('onstart');
  qvVoiceDebugLog('result');
  qvVoiceDebugLog('final');
  qvVoiceDebugLog('error:network');
  qvVoiceDebugLog('end');
  qvVoiceDebugLog('restart');
  qvVoiceDebugLog('timeout');
  qvVoiceDebugLog('submit');
  qvVoiceDebugLog('empty_submit');
  let dump = qvVoiceDebugDump();
  assert.equal(typeof dump, 'string');
  const parsed = JSON.parse(dump);
  assert.ok(Array.isArray(parsed.events));
  assert.ok(parsed.counts && typeof parsed.counts === 'object');
  // No transcript strings leak into the buffer from normal usage.
  assert.doesNotMatch(dump, /rahasia-payload-xyz-123/);
  assert.doesNotMatch(dump, /sudah dari kapan/);
  // Every entry is {t, ev} with ev name only (no spaces / payload).
  for (const e of parsed.events) {
    assert.ok(typeof e.t === 'number');
    assert.ok(typeof e.ev === 'string');
    assert.doesNotMatch(e.ev, /\s/);
    assert.match(e.ev, /^(start|onstart|result|final|submit|empty_submit|error:[a-z\-_]+|end|restart|timeout)$/);
  }
  // Even a hostile caller passing a transcript-like string cannot leak the
  // full payload: whitespace guard collapses to head token.
  qvVoiceDebugLog(secretFinal + ' ' + secretInterim);
  dump = qvVoiceDebugDump();
  assert.doesNotMatch(dump, /rahasia-payload-xyz-123/);
  // Ring cap: push 40 more, buffer stays at ~30.
  qvVoiceDebugReset();
  for (let i = 0; i < 40; i++) qvVoiceDebugLog('result');
  const capped = JSON.parse(qvVoiceDebugDump());
  assert.equal(capped.events.length, 30);
  // Mirrored to window for live bug reports.
  assert.ok(Array.isArray(sandbox.window.__QORA_VOICE_DEBUG));
  assert.equal(sandbox.window.__QORA_VOICE_DEBUG.length, 30);
  // Empty-submit one-liner carries counts+timings, never text.
  const line = qvFormatEmptySubmitDebug({ results: 2, finals: 0, restarts: 1, elapsedMs: 1350, warmed: true, heard: false });
  assert.match(line, /empty_submit/);
  assert.match(line, /results=2/);
  assert.match(line, /elapsed_ms=1350/);
  assert.doesNotMatch(line, /rahasia-payload-xyz-123/);
  assert.doesNotMatch(line, /sudah dari kapan/);
  // Source contract: empty submit logs + console.debug summary; dump exposed.
  assert.match(code, /qvVoiceDebugLog\('empty_submit'\)/);
  assert.match(code, /qvVoiceDebugLog\('start'\)/);
  assert.match(code, /qvVoiceDebugLog\('onstart'\)/);
  assert.match(code, /console\.debug\(qvFormatEmptySubmitDebug/);
  assert.match(code, /function qvVoiceDebugDump/);
  assert.match(code, /window\.__QORA_VOICE_DEBUG/);
  qvVoiceDebugReset();
});

console.log(`\nAll ${passed} voice-fix tests passed.`);
