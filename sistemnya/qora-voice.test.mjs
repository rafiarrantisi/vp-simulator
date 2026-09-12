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

ok('rec error mapping never leaves phase stuck listening', () => {
  assert.equal(qvRecErrorAction('not-allowed', false), 'mic_blocked');
  assert.equal(qvRecErrorAction('service-not-allowed', false), 'mic_blocked');
  assert.equal(qvRecErrorAction('aborted', false), 'ignore');
  assert.equal(qvRecErrorAction('no-speech', true), 'submit');
  assert.equal(qvRecErrorAction('no-speech', false), 'idle_hint');
  assert.equal(qvRecErrorAction('audio-capture', true), 'submit');
  assert.equal(qvRecErrorAction('audio-capture', false), 'idle_hint');
  // e.g. network with/without partial final
  assert.equal(qvRecErrorAction('network', true), 'submit');
  assert.equal(qvRecErrorAction('network', false), 'idle_hint');
});

ok('onend restart capped (default 3)', () => {
  assert.equal(QV2_REC_MAX_RESTARTS, 3);
  assert.equal(qvVoiceRestartAllowed(0), true);
  assert.equal(qvVoiceRestartAllowed(2), true);
  assert.equal(qvVoiceRestartAllowed(3), false);
  assert.equal(qvVoiceRestartAllowed(4), false);
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

console.log(`\nAll ${passed} voice-fix tests passed.`);
