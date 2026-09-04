// ============================================================
// Qora — Mentor (PRD_QORA_MENTOR)
// ------------------------------------------------------------
// Conversational learning-journey system:
//   QMentorScreen      — top-level screen (chat → proposal → dashboard)
//   QMentorChat        — Phase 1 story input ("Ceritain ke Qora…")
//   QJourneyProposal   — LLM-proposed journey display + customize
//   QJourneyDashboard  — active journey tracking (day lock/unlock)
// ADDITIVE: design.css tokens only (no CSS change, no new CSS file).
// Consumes /api/v2/mentor/* via qv2Fetch (auth + refresh handled there).
// Loaded AFTER qora-enhancements.jsx in bundle LOAD_ORDER.
// ============================================================

var _mt = window.__t || function (k) { return k; };

// ── shared UI bits (design tokens only) ─────────────────────────────────
var _mtCard = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', boxShadow: 'var(--sh-sm)' };
var _mtBtn = function (kind) {
  var base = { padding: '10px 18px', borderRadius: 12, border: 'none', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', transition: 'all 0.18s ease' };
  if (kind === 'primary') return Object.assign({}, base, { background: 'var(--primary)', color: '#fff' });
  if (kind === 'ghost') return Object.assign({}, base, { background: 'var(--surface)', color: 'var(--text-2)', border: '1px solid var(--border)' });
  if (kind === 'danger') return Object.assign({}, base, { background: 'var(--red-l)', color: 'var(--red-d)', border: '1px solid var(--red)' });
  return base;
};

function _mtBar(fillPct, height) {
  return React.createElement('div', { style: { height: height || 8, borderRadius: 99, background: 'var(--surface-3)', overflow: 'hidden' } },
    React.createElement('div', { style: { width: Math.max(0, Math.min(100, fillPct)) + '%', height: '100%', borderRadius: 99, background: 'var(--primary)', transition: 'width 0.5s ease' } }));
}

// ── Premium UI kit for the redesigned mentor flows ─────────────────────
// Real buttons (class-based, so hover/press/focus work via the qora-ui
// <style> in index.html — design.css untouched).
function _QBtn(props) {
  var cls = 'qbtn qbtn-' + (props.kind || 'p') + (props.lg ? ' qbtn-lg' : '') + (props.blk ? ' qbtn-blk' : '');
  return React.createElement('button', { type: 'button', className: cls, disabled: props.disabled, onClick: props.onClick, style: props.style || {}, title: props.title }, props.children);
}
function _QPill(props) {
  return React.createElement('span', { className: 'qpill qpill-' + (props.kind || 'lock') }, props.children);
}
// Feather-style stroke icons (tiny string markup, parsed to real SVG nodes).
var _MTL = {
  spark: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  play: '<path d="M5 4l14 8-14 8z"/>',
  lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  ar: '<path d="M5 12h14M12 5l7 7-7 7"/>',
  al: '<path d="M19 12H5M12 19l-7-7 7-7"/>',
  edit: '<path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5z"/>',
  chevr: '<path d="M9 18l6-6-6-6"/>',
  chevl: '<path d="M15 18l-6-6 6-6"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6"/>',
};
function _Mtl(props) {
  var S = props.s || 18;
  return React.createElement('svg', { width: S, height: S, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true, style: { flexShrink: 0 } }, _parseMtl(_MTL[props.n] || ''));
}
function _parseMtl(str) {
  var out = [], re = /<(path|circle|rect|line)([^>]*)>/g, m, i;
  while ((m = re.exec(str)) !== null) {
    var tag = m[1], attrs = m[2], a = {}, are = /([a-zA-Z0-9]+)="([^"]*)"/g, am;
    while ((am = are.exec(attrs)) !== null) a[am[1]] = am[2];
    i = out.length;
    if (tag === 'path') out.push(React.createElement('path', { key: i, d: a.d }));
    else if (tag === 'circle') out.push(React.createElement('circle', { key: i, cx: a.cx, cy: a.cy, r: a.r }));
    else if (tag === 'rect') out.push(React.createElement('rect', { key: i, x: a.x, y: a.y, width: a.width, height: a.height, rx: a.rx }));
    else if (tag === 'line') out.push(React.createElement('line', { key: i, x1: a.x1, y1: a.y1, x2: a.x2, y2: a.y2 }));
  }
  return out;
}

// ── QMentorChat: Phase 1 story input ────────────────────────────────────
function QMentorChat(props) {
  var [story, setStory] = React.useState('');
  var [busy, setBusy] = React.useState(false);
  var [err, setErr] = React.useState('');
  function submit() {
    var s = story.trim();
    if (!s || busy) return;
    setBusy(true); setErr('');
    qv2Fetch('/api/v2/mentor/story', { method: 'POST', body: { story: s } })
      .then(function (j) { props.onJourney(j); })
      .catch(function (e) { setErr(e.message || 'Gagal membuat rencana'); setBusy(false); });
  }
  return React.createElement('div', { className: 'au', style: { maxWidth: 640, margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 14, marginBottom: 6 } },
      React.createElement('div', { className: 'hdr-badge' }, React.createElement(_Mtl, { n: 'spark', s: 22 })),
      React.createElement('div', null,
        React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.15 } }, _mt('mentor.title')),
        React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', marginTop: 2, fontWeight: 600 } }, _mt('mentor.subtitle')))),
    React.createElement('div', Object.assign({}, _mtCard, { padding: 16 }),
      React.createElement('div', { style: { fontSize: 11, fontWeight: 800, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 } }, _mt('mentor.tell_qora')),
      React.createElement('textarea', {
        value: story, onChange: function (e) { setStory(e.target.value); },
        placeholder: _mt('mentor.chat_placeholder'),
        rows: 3, maxLength: 2000,
        style: { width: '100%', boxSizing: 'border-box', resize: 'none', padding: '12px 14px', borderRadius: 16, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 14, fontFamily: 'Plus Jakarta Sans', outline: 'none' },
      }),
      err && React.createElement('div', { style: { marginTop: 8, fontSize: 12, color: 'var(--red-d)', background: 'var(--red-l)', padding: '8px 12px', borderRadius: 10 } }, '⚠️ ' + err),
      busy && React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, fontSize: 12.5, color: 'var(--primary)', fontWeight: 600, background: 'var(--primary-l)', padding: '9px 14px', borderRadius: 12 } },
        React.createElement('span', { style: { width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', display: 'inline-block', animation: 'pulse 1.1s ease-in-out infinite' } }),
        React.createElement('span', { style: { width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', display: 'inline-block', animation: 'pulse 1.1s ease-in-out 0.2s infinite' } }),
        React.createElement('span', { style: { width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', display: 'inline-block', animation: 'pulse 1.1s ease-in-out 0.4s infinite' } }),
        _mt('mentor.thinking')),
      React.createElement('div', { style: { marginTop: 12 } },
        React.createElement(_QBtn, { kind: 'p', blk: true, lg: true, onClick: submit, disabled: busy || !story.trim() },
          busy
            ? React.createElement('span', { style: { display: 'inline-flex', gap: 4, alignItems: 'center' } },
                [0, 1, 2].map(function (i) {
                  return React.createElement('span', { key: i, style: { width: 5, height: 5, borderRadius: '50%', background: '#fff', display: 'inline-block', animation: 'pulse 1.1s ease-in-out ' + (i * 0.2) + 's infinite' } });
                }))
            : _mt('mentor.send')))));
}

// ── Shared: horizontal day carousel (revision §4.3) ──────────
function _dayCardState(st) {
  if (st === 'completed') return { pill: 'ok', fg: 'var(--teal-d)', border: 'var(--teal)', bg: 'var(--teal-l)' };
  if (st === 'available' || st === 'in_progress') return { pill: 'now', fg: 'var(--primary)', border: 'var(--primary)', bg: 'var(--primary-l)' };
  return { pill: 'lock', fg: 'var(--text-3)', border: 'var(--border)', bg: 'var(--surface-2)' };
}

function QDayCarousel(props) {
  var isTablet = (typeof useIsTablet === 'function') ? useIsTablet() : false;
  var ref = React.useRef(null);
  function scrollByDir(dir) {
    var el = ref.current;
    if (!el) return;
    try { el.scrollBy({ left: dir * (el.clientWidth * 0.7), behavior: 'smooth' }); } catch (e) { el.scrollLeft += dir * 300; }
  }
  var ls = props.cases || [];
  return React.createElement('div', { style: { position: 'relative' } },
    React.createElement('div', { ref: ref, style: {
      display: 'flex', gap: 12, overflowX: 'auto', padding: '4px 2px 14px',
      scrollSnapType: 'x mandatory', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'thin',
    } },
      ls.map(function (c) {
        // Status: trust real statuses on an ACTIVE journey; for a proposed
        // journey the cases carry a non-actionable status, so fall back to
        // day-based progression (Day 1 available, the rest locked).
        var st = c.status;
        if (['completed', 'available', 'in_progress'].indexOf(st) < 0) {
          st = (c.day > 1 ? 'locked' : 'available');
        }
        var s = _dayCardState(st);
        var clickable = st === 'available' || st === 'in_progress';
        var pillLabel = st === 'completed'
          ? (props.doneLabel || 'Selesai')
          : clickable
            ? _mt('mentor.available_now')
            : _mt('mentor.locked').replace('{d}', Math.max(1, (c.day || 2) - 1));
        return React.createElement('button', {
          key: c.day + '-' + st, className: 'daycard as',
          onClick: function () { if (clickable && props.onStart) props.onStart(c); },
          disabled: !clickable,
          style: {
            minWidth: 'min(220px, 80vw)', scrollSnapAlign: 'start', flexShrink: 0, appearance: 'none',
            padding: 16, borderRadius: 'var(--r-lg)', textAlign: 'left',
            background: s.bg, border: '1.5px solid ' + s.border,
            boxShadow: clickable ? 'var(--sh-sm)' : 'none',
            cursor: clickable ? 'pointer' : 'default',
            opacity: st === 'locked' ? 0.72 : 1,
            transition: 'transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease',
            display: 'flex', flexDirection: 'column', gap: 9,
          },
        },
          React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 } },
            React.createElement('span', { style: { fontSize: 11, fontWeight: 800, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--text-1)' } }, 'Day ' + c.day),
            React.createElement(_QPill, { kind: s.pill }, pillLabel)),
          React.createElement('div', { style: { fontSize: 14.5, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.35 } },
            c.focus_area || c.case_id),
          React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-3)', fontWeight: 500 } },
            React.createElement(_Mtl, { n: 'clock', s: 13 }), '~' + (c.estimated_minutes || 15) + ' min'),
          (clickable || st === 'completed') && React.createElement('div', { style: { marginTop: 2, display: 'inline-flex', alignItems: 'center', gap: 6, color: s.fg, fontSize: 12, fontWeight: 700 } },
            React.createElement(_Mtl, { n: st === 'completed' ? 'check' : 'play', s: 14 }),
            st === 'completed' ? (c.score != null ? 'Skor ' + c.score + '%' : (props.doneLabel || 'Selesai')) : _mt('mentor.start_case')));
      })),
    !isTablet && React.createElement('div', { style: { display: 'flex', gap: 8, justifyContent: 'center', marginTop: 4 } },
      React.createElement('button', { onClick: function () { scrollByDir(-1); }, style: { width: 36, height: 36, borderRadius: '50%', border: '1px solid var(--border)', background: 'var(--surface)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-2)' }, 'aria-label': 'Previous' },
        React.createElement(_Mtl, { n: 'al', s: 16 })),
      React.createElement('button', { onClick: function () { scrollByDir(1); }, style: { width: 36, height: 36, borderRadius: '50%', border: '1px solid var(--border)', background: 'var(--surface)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-2)' }, 'aria-label': 'Next' },
        React.createElement(_Mtl, { n: 'ar', s: 16 }))));
}

// ── Shared: "why this plan" as scannable bullet cards (§4.5) ──
function QReasonCard(props) {
  var text = String(props.reasoning || '');
  var raw = text.split(/\n|•|;/).map(function (s) { return s.trim(); }).filter(function (s) { return s.length > 2; });
  var points = raw.length > 1 ? raw
    : text.split(/(?<=[.!?])\s+/).map(function (s) { return s.trim(); }).filter(function (s) { return s.length > 2; }).slice(0, 6);
  if (!points.length) points = [text];
  return React.createElement('div', { style: { marginTop: 14, padding: '16px 18px', borderRadius: 'var(--r-lg)', background: 'var(--violet-l)', border: '1px solid var(--violet)' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 7, fontSize: 11, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--violet)', marginBottom: 10 } },
      React.createElement(_Mtl, { n: 'spark', s: 15 }), _mt('mentor.reasoning')),
    React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 7 } },
      points.map(function (pt, i) {
        return React.createElement('div', { key: i, style: { display: 'flex', gap: 9, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.55 } },
          React.createElement('span', { style: { color: 'var(--violet)', fontWeight: 800, flexShrink: 0 } }, '•'),
          pt);
      })));
}

// ── QJourneyProposal ────────────────────────────────────────────────────
function QJourneyProposal(props) {
  var j = props.journey;
  var proposal = j.proposal || {};
  var cases = j.cases || [];
  var [fb, setFb] = React.useState('');
  var [busy, setBusy] = React.useState(false);
  var [changes, setChanges] = React.useState([]);
  var [err, setErr] = React.useState('');

  function customize() {
    if (!fb.trim() || busy) return;
    setBusy(true); setErr('');
    qv2Fetch('/api/v2/mentor/journeys/' + j.id + '/customize', { method: 'POST', body: { feedback: fb } })
      .then(function (d) {
        setChanges(d.changes || []);
        props.onUpdated(d.updated_proposal);
        setFb(''); setBusy(false);
      })
      .catch(function (e) { setErr(e.message || 'Gagal menyesuaikan'); setBusy(false); });
  }

  var r = j.readiness || {};
  // Bar width must match the number shown — readiness is displayed as an
  // absolute percentage, so the bar uses the same value (§4.2).
  var startVal = Math.max(0, Math.min(100, r.start || 0));

  function startCase(c) {
    try { window.location.hash = '#/cases/' + c.case_id; } catch (e) {}
  }

  return React.createElement('div', { className: 'au', style: { maxWidth: 720, margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', Object.assign({}, _mtCard, { padding: 20 }),
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 } },
        React.createElement('div', { className: 'hdr-badge' }, React.createElement(_Mtl, { n: 'spark', s: 22 })),
        React.createElement('div', null,
          React.createElement('div', { style: { fontSize: 19, fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.2 } }, _mt('mentor.your_journey')),
          React.createElement('div', { style: { fontSize: 13.5, fontWeight: 600, color: 'var(--text-3)', marginTop: 2 } }, proposal.package_name || j.package_name || ''))),
      React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 18 } },
        React.createElement('span', { className: 'qchip' },
          React.createElement(_Mtl, { n: 'clock', s: 13 }), _mt('mentor.days').replace('{d}', proposal.duration_days || cases.length || '').replace('{m}', '45-60'))),
      React.createElement('div', { style: { marginBottom: 18 } },
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 } },
          React.createElement('span', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)' } }, _mt('mentor.readiness_start')),
          React.createElement('span', { style: { fontSize: 26, fontWeight: 800, color: 'var(--primary)', lineHeight: 1 } }, startVal + '%')),
        _mtBar(startVal, 10)),
      React.createElement(QDayCarousel, { cases: cases, onStart: startCase, doneLabel: 'Selesai' }),
      proposal.reasoning && React.createElement(QReasonCard, { reasoning: proposal.reasoning }),
      changes.length > 0 && React.createElement('div', { style: { marginTop: 10, fontSize: 11, color: 'var(--teal-d)', background: 'var(--teal-l)', padding: '8px 12px', borderRadius: 10 } },
        _mt('mentor.changes') + ': ' + changes.join(', ')),
      err && React.createElement('div', { style: { marginTop: 10, fontSize: 12, color: 'var(--red-d)', background: 'var(--red-l)', padding: '8px 12px', borderRadius: 10 } }, err),
      React.createElement('div', { style: { marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' } },
        React.createElement(_QBtn, { kind: 'p', lg: true, onClick: props.onAccept, style: { flex: 1, minWidth: 180 } }, _mt('mentor.accept')),
        React.createElement(_QBtn, { kind: 'g', lg: true, onClick: function () { props.onCancel(); }, style: { minWidth: 120 } }, _mt('mentor.cancel')))),
    React.createElement('div', Object.assign({}, _mtCard, { marginTop: 12, padding: 16 }),
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 7, fontSize: 11, fontWeight: 800, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 } },
        React.createElement(_Mtl, { n: 'edit', s: 14 }), _mt('mentor.customize')),
      React.createElement('div', { style: { display: 'flex', gap: 8, flexWrap: 'wrap' } },
        React.createElement('input', {
          value: fb, onChange: function (e) { setFb(e.target.value); },
          placeholder: _mt('mentor.customize_feedback'),
          onKeyDown: function (e) { if (e.key === 'Enter') customize(); },
          style: { flex: 1, minWidth: 'min(220px, 100%)', padding: '10px 12px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 13, fontFamily: 'Plus Jakarta Sans', outline: 'none' },
        }),
        React.createElement(_QBtn, { kind: 'g', onClick: customize, disabled: busy || !fb.trim() }, busy ? '…' : _mt('mentor.customize')))));
}

// ── QJourneyDashboard: guided active journey (FASE 10) ─────────────────
// Order: Journey Header → Today's Mission → Coach Insight → Journey
// Timeline → secondary actions. Same Qora GDV, no new visual language:
// one mood band, one primary CTA (mission), quiet destructive action.
function QMHeroMobile(props) {
  // Fixed-height cropped art: the aspect-locked band cannot fit kicker +
  // title on a 390px viewport (caption would clip), so mobile gets its own
  // compact hero with the same lentera artwork + legibility scrim.
  return React.createElement('div', { style: { position: 'relative', borderRadius: 'var(--r-xl)', overflow: 'hidden', height: 196, boxShadow: 'var(--shadow-band)' } },
    React.createElement('div', { style: { position: 'absolute', inset: 0, overflow: 'hidden' } },
      React.createElement('div', { style: { width: '170%', marginLeft: '-35%', height: '100%' } },
        React.createElement(QAMoodScene, { scene: 'lentera' }))),
    React.createElement('div', { style: { position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(20,10,40,0) 25%, rgba(20,10,40,.58) 100%)' } }),
    React.createElement('div', { style: { position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: '16px 20px', color: '#fff' } },
      React.createElement('div', { style: { fontSize: 10, letterSpacing: '.18em', fontWeight: 700, opacity: .82, marginBottom: 5 } }, props.kicker),
      React.createElement('div', { style: { fontSize: 22, margin: 0, fontWeight: 800, letterSpacing: '-.02em', textShadow: '0 2px 18px rgba(20,10,40,.35)', lineHeight: 1.2 } }, props.title),
      React.createElement('div', { style: { marginTop: 5, fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.88)', fontVariantNumeric: 'tabular-nums', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, (props.sub || ''))));
}
function QJourneyDashboard(props) {
  var j = props.journey;
  var cases = j.cases || [];
  var progress = j.progress || {};
  var r = j.readiness || {};
  var total = progress.total || 0;
  var currentVal = Math.max(0, Math.min(100, r.current != null ? r.current : (r.start || 0)));
  var ctx = j.context || {};
  var goalLine = ctx.goal && ctx.goal !== 'general'
    ? _mt('mentor.goal_line').replace('{goal}', String(ctx.goal).toUpperCase()).replace('{d}', ctx.timeline_days || total || '?')
    : null;

  var [mission, setMission] = React.useState(null);
  var [recap, setRecap] = React.useState(null);
  var [verdict, setVerdict] = React.useState(null);
  React.useEffect(function () {
    var alive = true;
    if (j.status === 'active') {
      qv2Fetch('/api/v2/mentor/journeys/' + j.id + '/mission').then(function (m) { if (alive) setMission(m); }).catch(function () {});
      qv2Fetch('/api/v2/mentor/journeys/' + j.id + '/recap').then(function (c) { if (alive) setRecap(c); }).catch(function () {});
    }
    if (j.status === 'completed') {
      qv2Fetch('/api/v2/mentor/journeys/' + j.id + '/report').then(function (rep) { if (alive) setVerdict(rep); }).catch(function () {});
    }
    return function () { alive = false; };
  }, [j.id, j.status, (progress.completed || 0)]);

  function startCase(c) {
    // Navigate via hash ONLY — the App's hashchange listener maps
    // #/cases/<id> → cases screen, and QoraV2Screen reads the full hash
    // on mount (calling onNav('cases') would clobber the case id).
    try { window.location.hash = '#/cases/' + c.case_id; } catch (e) {}
  }

  var missionCase = mission && mission.case_id ? { case_id: mission.case_id } : null;
  // Static breakpoint read (same 768px as the shell): hero selection must
  // not depend on hook scope across the concatenated bundle.
  var isMobileM = false;
  try { isMobileM = window.matchMedia('(max-width: 768px)').matches; } catch (e) {}

  return React.createElement('div', { style: { maxWidth: 720, margin: '0 auto', padding: '24px 16px calc(40px + env(safe-area-inset-bottom, 0px))' } },
    // 1 · Journey Header (GDV §4 lentera band; goal/date line, no target %)
    // Mobile gets the cropped art hero — the aspect-locked band clips text.
    isMobileM
      ? React.createElement(QMHeroMobile, { kicker: 'HARI ' + (j.current_day || 1) + ' DARI ' + (total || 5),
          title: j.package_name || _mt('mentor.title'), sub: goalLine || '' })
      : React.createElement(QAMoodBand, { scene: 'lentera', kicker: 'HARI ' + (j.current_day || 1) + ' DARI ' + (total || 5), title: j.package_name || _mt('mentor.title'),
        sub: goalLine || '' }),
    React.createElement('div', { className: 'au', style: { position: 'relative', zIndex: 5, marginTop: isMobileM ? 12 : -56 } },
    React.createElement('div', { style: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', boxShadow: 'var(--sh-sm)', padding: 20 } },
      // workload completion (planned %, honest progress — NOT readiness)
      React.createElement('div', { style: { marginBottom: 16 } },
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 } },
          React.createElement('span', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)' } },
            _mt('mentor.progress').replace('{d}', j.current_day || 1).replace('{n}', total).replace('{p}', progress.percent || 0)),
          React.createElement('span', { style: { fontSize: 22, fontWeight: 800, color: 'var(--primary)', lineHeight: 1, fontVariantNumeric: 'tabular-nums' } }, (progress.percent || 0) + '%')),
        _mtBar(progress.percent || 0, 10)),
      // readiness now (evidence-driven; target % intentionally not shown)
      React.createElement('div', { style: { marginBottom: 4 } },
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 } },
          React.createElement('span', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)' } },
            _mt('mentor.readiness') + ': ' + currentVal + '%'),
          React.createElement('span', { style: { fontSize: 11, color: 'var(--text-3)', fontWeight: 600 } },
            _mt('mentor.readiness_start') + ': ' + (r.start != null ? r.start : '–') + '%')),
        _mtBar(currentVal, 10)))),
    // 2 · Today's Mission (focus, time, encounters, why, CTA)
    mission && mission.state === 'ready' && React.createElement('div', { className: 'as', style: Object.assign({}, _mtCard, { marginTop: 12, padding: 18, border: '1.5px solid var(--primary)' }) },
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 } },
        React.createElement(_Mtl, { n: 'play', s: 13 }), _mt('mentor.mission') + ' · Day ' + mission.day),
      React.createElement('div', { style: { fontSize: 15, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, mission.focus || mission.case_id),
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-2)', fontWeight: 600, marginBottom: 8, fontVariantNumeric: 'tabular-nums' } },
        React.createElement(_Mtl, { n: 'clock', s: 13 }),
        _mt('mentor.mission_meta').replace('{n}', mission.encounters || 1).replace('{m}', mission.expected_minutes || 45)),
      React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 12 } },
        React.createElement('span', { style: { fontWeight: 700, color: 'var(--text-1)' } }, _mt('mentor.why_this_case') + ': '), mission.why),
      React.createElement(_QBtn, { kind: 'p', blk: true, onClick: function () { startCase(missionCase || mission); } }, _mt('mentor.start_case'))),
    // 3 · Coach Insight (latest evidence-grounded feedback, persisted server-side)
    j.coach_insight && React.createElement('div', { className: 'as', style: Object.assign({}, _mtCard, { marginTop: 12, padding: 16, background: 'var(--violet-l)', border: '1px solid var(--violet)' }) },
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 7, fontSize: 11, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--violet)', marginBottom: 8 } },
        React.createElement(_Mtl, { n: 'spark', s: 15 }), _mt('mentor.coach_insight')),
      React.createElement('div', { style: { fontSize: 13.5, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, j.coach_insight.headline || ''),
      j.coach_insight.detail && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.6 } }, j.coach_insight.detail)),
    // recap strip (end-of-day: done, time, tomorrow focus)
    recap && (recap.cases_completed || 0) > 0 && React.createElement('div', { style: { marginTop: 12, fontSize: 12, color: 'var(--text-2)', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' } },
      React.createElement(_Mtl, { n: 'check', s: 14 }),
      React.createElement('span', null, _mt('mentor.recap') + ': ' + recap.cases_completed + '/' + (recap.cases_total || total) +
        (recap.next_focus ? ' · ' + recap.next_focus : ''))),
    // 4 · Journey Timeline
    React.createElement('div', { className: 'as', style: Object.assign({}, _mtCard, { marginTop: 12, padding: 18 }) },
      React.createElement('div', { style: { fontSize: 13, fontWeight: 800, color: 'var(--text-1)', marginBottom: 10 } }, _mt('mentor.timeline')),
      React.createElement(QDayCarousel, { cases: cases, onStart: startCase, doneLabel: 'Selesai' })),
    // end-of-journey verdict: plan complete ≠ ready (honest, concrete next step)
    j.status === 'completed' && verdict && React.createElement('div', { className: 'as', style: Object.assign({}, _mtCard, { marginTop: 12, padding: 18 }) },
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 } },
        React.createElement('span', { className: 'qpill qpill-now' },
          verdict.verdict === 'ready' ? _mt('mentor.verdict_ready') : _mt('mentor.verdict_completed'))),
      React.createElement('div', { style: { fontSize: 13.5, fontWeight: 700, color: 'var(--text-1)', marginBottom: 6, lineHeight: 1.5 } }, verdict.note || ''),
      verdict.next_recommendation && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.6 } },
        React.createElement('span', { style: { fontWeight: 700, color: 'var(--text-1)' } }, _mt('mentor.next_recommendation') + ': '), verdict.next_recommendation)),
    // 5 · secondary actions (report ghost; abandon quiet — never prominent red)
    React.createElement('div', { style: { marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' } },
      props.onReport
        ? React.createElement(_QBtn, { kind: 'g', onClick: props.onReport }, _mt('mentor.view_report'))
        : React.createElement('span', null),
      React.createElement('button', { onClick: props.onAbandon, style: { background: 'transparent', border: 'none', color: 'var(--text-3)', fontSize: 12.5, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', textDecoration: 'underline', padding: '10px 4px', minHeight: 44 } }, _mt('mentor.stop_journey'))));
}

// ── QAutopsyCard: reasoning autopsy display (PRD §4.2.5) ────────────────
function QAutopsyCard(props) {
  var a = props.autopsy || {};
  var errors = a.errors_detected || [];
  var [tab, setTab] = React.useState('pathway');
  var tabs = [['pathway', _mt('mentor.autopsy_tab_pathway')], ['expert', _mt('mentor.autopsy_tab_expert')], ['errors', _mt('mentor.autopsy_tab_errors')]];
  var sevColor = { critical: 'var(--red)', moderate: 'var(--amber)', minor: 'var(--text-3)' };
  var sevIcon = { critical: '🔴', moderate: '🟡', minor: '⚪' };

  return React.createElement('div', { className: 'af', style: Object.assign({}, _mtCard, { padding: 18, marginTop: 16 }) },
    React.createElement('div', { style: { fontSize: 16, fontWeight: 800, color: 'var(--text-1)', marginBottom: 10 } }, '🔬 ' + _mt('mentor.autopsy_title')),
    React.createElement('div', { style: { display: 'flex', gap: 4, borderBottom: '1px solid var(--border)', marginBottom: 12 } },
      tabs.map(function (t) {
        return React.createElement('button', {
          key: t[0], onClick: function () { setTab(t[0]); },
          style: {
            padding: '7px 14px', border: 'none', background: 'transparent', cursor: 'pointer',
            fontSize: 12.5, fontWeight: tab === t[0] ? 700 : 500, fontFamily: 'Plus Jakarta Sans',
            color: tab === t[0] ? 'var(--primary)' : 'var(--text-2)',
            borderBottom: tab === t[0] ? '2px solid var(--primary)' : '2px solid transparent',
          },
        }, t[1]);
      })),
    tab === 'pathway' && React.createElement('div', null,
      React.createElement('div', { style: { fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 } }, _mt('mentor.autopsy_your_pathway')),
      React.createElement('ol', { style: { margin: 0, paddingLeft: 18, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 } },
        (a.user_pathway || []).map(function (s, i) {
          return React.createElement('li', { key: i }, s);
        }))),
    tab === 'expert' && React.createElement('div', null,
      React.createElement('div', { style: { fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 } }, _mt('mentor.autopsy_expert_pathway')),
      React.createElement('ol', { style: { margin: 0, paddingLeft: 18, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 } },
        (a.expert_pathway || []).map(function (s, i) {
          return React.createElement('li', { key: i }, s);
        }))),
    tab === 'errors' && React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
      errors.length === 0 && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--teal-d)', background: 'var(--teal-l)', padding: '10px 14px', borderRadius: 10 } },
        '✅ ' + _mt('mentor.autopsy_no_errors')),
      errors.map(function (e, i) {
        var c = sevColor[e.severity] || 'var(--text-3)';
        return React.createElement('div', {
          key: i,
          style: {
            padding: '10px 14px', borderRadius: 'var(--r-md)', fontSize: 12.5, color: 'var(--text-2)',
            background: e.severity === 'critical' ? 'var(--red-l)' : e.severity === 'moderate' ? 'var(--amber-l)' : 'var(--surface-2)',
            border: '1px solid ' + c,
          },
        },
          React.createElement('div', { style: { fontWeight: 700, color: 'var(--text-1)', marginBottom: 2 } },
            (sevIcon[e.severity] || '•') + ' ' + (e.type || '').replace(/_/g, ' ') + ' · ' + (e.severity || '')),
          e.description && React.createElement('div', null, e.description),
          e.evidence && React.createElement('div', { style: { marginTop: 4, fontSize: 11.5, fontStyle: 'italic', color: 'var(--text-3)' } }, '“' + e.evidence + '”'));
      })),
    a.pearl && React.createElement('div', { style: { marginTop: 12, padding: '10px 14px', borderRadius: 'var(--r-md)', background: 'var(--teal-l)', border: '1px solid var(--teal)', fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.6 } },
      React.createElement('div', { style: { fontWeight: 800, color: 'var(--teal-d)', marginBottom: 2 } }, '💎 ' + _mt('mentor.autopsy_pearl')),
      a.pearl),
    React.createElement('div', { style: { marginTop: 10, fontSize: 11.5, color: 'var(--text-3)' } },
      _mt('mentor.autopsy_readiness_impact') + ': ' + (a.readiness_impact > 0 ? '+' : '') + (a.readiness_impact || 0) + '%'));
}

// ── QContinuityBanner: returning patient (PRD §4.3.6) ───────────────────
function QContinuityBanner(props) {
  var p = props.pending;
  if (!p) return null;
  var story = p.story_so_far || {};
  return React.createElement('div', { className: 'au', style: { maxWidth: 640, margin: '16px auto 0', padding: '0 16px' } },
    React.createElement('div', { style: { padding: 16, borderRadius: 'var(--r-lg)', background: 'var(--violet-l)', border: '1px solid var(--violet)', boxShadow: 'var(--sh-sm)' } },
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 } },
        React.createElement('span', { style: { fontSize: 18 } }, '🔄'),
        React.createElement('span', { style: { fontSize: 14, fontWeight: 800, color: 'var(--text-1)' } }, _mt('mentor.returning_patient')),
        React.createElement('span', { style: { marginLeft: 'auto', padding: '2px 10px', borderRadius: 999, background: 'var(--violet)', color: '#fff', fontSize: 11, fontWeight: 700 } },
          'Visit ' + p.visit_number + ' of ' + p.total_visits)),
      React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 } },
        '👤 ' + p.name + (p.age ? ', ' + p.age : '')),
      React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 10 } },
        React.createElement('div', null, '📋 ' + _mt('mentor.story_so_far') + ': ' + (story.previous_diagnosis || '') + ' — ' + (story.reason || '')),
        story.new_symptoms && story.new_symptoms.length > 0 &&
          React.createElement('div', null, '🆕 ' + _mt('mentor.new_complaint') + ': ' + story.new_symptoms.join(', '))),
      React.createElement('button', Object.assign({ onClick: function () {
        try { window.location.hash = '#/cases/' + p.next_case_id; } catch (e) {}
      } }, _mtBtn('primary')), '▶ ' + _mt('mentor.start_visit').replace('{n}', p.visit_number))));
}

// ── QReadinessGauge: circular readiness meter (PRD §4.4.3) ──────────────
function QReadinessGauge(props) {
  var score = props.score || 0;
  var color = props.color || 'var(--primary)';
  var r = 52, c = 2 * Math.PI * r;
  var fill = Math.max(0, Math.min(100, score)) / 100 * c;
  return React.createElement('div', { style: { position: 'relative', width: 130, height: 130 } },
    React.createElement('svg', { width: 130, height: 130, viewBox: '0 0 130 130' },
      React.createElement('circle', { cx: 65, cy: 65, r: r, fill: 'none', stroke: 'var(--surface-3)', strokeWidth: 12 }),
      React.createElement('circle', { cx: 65, cy: 65, r: r, fill: 'none', stroke: color, strokeWidth: 12, strokeLinecap: 'round', strokeDasharray: c, strokeDashoffset: c - fill, transform: 'rotate(-90 65 65)', style: { transition: 'stroke-dashoffset 0.8s ease' } })),
    React.createElement('div', { style: { position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' } },
      React.createElement('div', { style: { fontSize: 38, fontWeight: 800, color: color, lineHeight: 1 } }, score),
      React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)', fontWeight: 600, marginTop: 2 } }, '%')));
}

// ── QReadinessReport: full readiness report (PRD §4.4.3) ────────────────
function QReadinessReport(props) {
  var r = props.data;
  var readiness = r.readiness || {};
  var dims = readiness.dimensions || {};
  var interp = readiness.interpretation || {};
  return React.createElement('div', { className: 'au', style: { maxWidth: 640, margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', Object.assign({}, _mtCard, { padding: 20 }),
      React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', marginBottom: 14 } }, '📊 ' + _mt('mentor.readiness_report')),
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 18, marginBottom: 14 } },
        React.createElement(QReadinessGauge, { score: readiness.score || 0, color: interp.color || 'var(--primary)' }),
        React.createElement('div', { style: { flex: 1 } },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: interp.color || 'var(--text-1)', marginBottom: 4 } }, interp.label || ''),
          React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)' } },
            _mt('mentor.confidence') + ': ' + (readiness.confidence || '—') + ' · ' + _mt('mentor.sessions') + ': ' + (readiness.session_count || 0)))),
      React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 } }, _mt('mentor.dimension_breakdown')),
      React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 7 } },
        Object.keys(dims).map(function (k) {
          var pct = dims[k];
          var col = pct >= 75 ? 'var(--green)' : pct >= 60 ? 'var(--amber)' : 'var(--red)';
          return React.createElement('div', { key: k },
            React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-2)', marginBottom: 2 } },
              React.createElement('span', { style: { fontWeight: 600, color: 'var(--text-1)' } }, k.replace(/_/g, ' ')),
              React.createElement('span', { style: { fontWeight: 700, color: col } }, pct + '%')),
            _mtBar(pct, 6));
        })),
      r.weakest && React.createElement('div', { style: { marginTop: 14, padding: '10px 14px', borderRadius: 'var(--r-md)', background: 'var(--red-l)', border: '1px solid var(--red)', fontSize: 12.5, color: 'var(--text-2)' } },
        React.createElement('div', { style: { fontWeight: 800, color: 'var(--red-d)', marginBottom: 4 } }, '🔴 ' + _mt('mentor.weakest_area')),
        _mt('mentor.weakest_text').replace('{d}', (r.weakest.dimension || '').replace(/_/g, ' ')).replace('{p}', r.weakest.pct)),
      // FASE 10: explainable readiness — state/confidence/evidence + strong/needs-work
      (function () {
        var ev = readiness.evidence || {};
        var lines = [];
        if ((readiness.strengths || []).length) lines.push('Strong: ' + readiness.strengths.map(function (s) { return String(s).replace(/_/g, ' '); }).join(', '));
        if ((readiness.needs_work || []).length) lines.push('Needs work: ' + readiness.needs_work.map(function (s) { return String(s).replace(/_/g, ' '); }).join(', '));
        if (!lines.length) return null;
        return React.createElement('div', { style: { marginTop: 12, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 } },
          lines.map(function (ln, i) { return React.createElement('div', { key: i }, ln); }),
          React.createElement('div', { style: { marginTop: 4, fontSize: 11.5, color: 'var(--text-3)', fontVariantNumeric: 'tabular-nums' } },
            'Evidence: ' + (ev.sessions || 0) + ' sessions · ' + (ev.osce_sessions || 0) + ' OSCE · ' + (ev.domains_covered || 0) + ' domains'));
      })(),
      r.recommendations && r.recommendations.length > 0 && React.createElement('div', { style: { marginTop: 12, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 } },
        React.createElement('div', { style: { fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 } }, '📌 ' + _mt('mentor.recommended_actions')),
        r.recommendations.map(function (rec, i) { return React.createElement('div', { key: i }, (i + 1) + '. ' + rec); })),
      React.createElement('div', { style: { marginTop: 12, fontSize: 11, color: 'var(--text-3)', fontStyle: 'italic', lineHeight: 1.6 } }, '⚠️ ' + (r.disclaimer || ''))));
}


function QMentorScreen(props) {
  var [loading, setLoading] = React.useState(true);
  var [journey, setJourney] = React.useState(null);
  var [view, setView] = React.useState('chat'); // chat | proposal | dashboard | report
  var [pending, setPending] = React.useState(null);
  var [report, setReport] = React.useState(null);
  var [err, setErr] = React.useState('');

  function load() {
    setLoading(true);
    qv2Fetch('/api/v2/mentor/journeys')
      .then(function (d) {
        var list = d && d.journeys ? d.journeys : [];
        var active = list.filter(function (j) { return j.status === 'active'; })[0] || null;
        var proposed = list.filter(function (j) { return j.status === 'proposed'; })[0] || null;
        if (active) { setJourney(active); setView('dashboard'); }
        else if (proposed) { setJourney(proposed); setView('proposal'); }
        else setView('chat');
      })
      .catch(function () { setView('chat'); })
      .finally(function () { setLoading(false); });
    qv2Fetch('/api/v2/mentor/continuity/pending')
      .then(function (d) { setPending(d && d.pending ? d.pending : null); })
      .catch(function () {});
  }
  React.useEffect(function () { load(); }, []);

  function onJourney(j) { setJourney(j); setView('proposal'); }
  function accept() {
    qv2Fetch('/api/v2/mentor/journeys/' + journey.id + '/accept', { method: 'POST', body: {} })
      .then(function (j) { setJourney(j); setView('dashboard'); })
      .catch(function (e) { setErr(e.message || 'Gagal mulai journey'); });
  }
  function onUpdated(j) { setJourney(j); setView('proposal'); }
  function cancel() { setJourney(null); setView('chat'); }
  function abandon() {
    qv2Fetch('/api/v2/mentor/journeys/' + journey.id + '/abandon', { method: 'POST' })
      .then(function () { setJourney(null); setView('chat'); })
      .catch(function (e) { setErr(e.message || 'Gagal menghentikan'); });
  }
  function openReport() {
    setLoading(true);
    qv2Fetch('/api/v2/mentor/readiness/report')
      .then(function (d) { setReport(d); setView('report'); })
      .catch(function (e) { setErr(e.message || 'Gagal memuat laporan'); })
      .finally(function () { setLoading(false); });
  }

  if (loading) return React.createElement('div', { style: { padding: 60, textAlign: 'center', color: 'var(--text-3)', fontSize: 13 } }, _mt('common.loading'));
  if (view === 'report' && report) {
    return React.createElement(React.Fragment, null,
      React.createElement('div', { style: { maxWidth: 640, margin: '0 auto', padding: '16px 16px 0' } },
        React.createElement(_QBtn, { kind: 'g', onClick: function () { setView('dashboard'); } }, '← ' + _mt('mentor.back_to_journey'))),
      React.createElement(QReadinessReport, { data: report }));
  }
  if (view === 'proposal' && journey) {
    return React.createElement(React.Fragment, null,
      err && React.createElement('div', { style: { maxWidth: 640, margin: '0 auto', padding: '16px 16px 0', fontSize: 12, color: 'var(--red-d)' } }, err),
      React.createElement(QJourneyProposal, { journey: journey, onAccept: accept, onUpdated: onUpdated, onCancel: cancel }));
  }
  if (view === 'dashboard' && journey) {
    return React.createElement(React.Fragment, null,
      err && React.createElement('div', { style: { maxWidth: 640, margin: '0 auto', padding: '16px 16px 0', fontSize: 12, color: 'var(--red-d)' } }, err),
      React.createElement(QContinuityBanner, { pending: pending }),
      React.createElement(QJourneyDashboard, { journey: journey, onNav: props.onNav, onAbandon: abandon, onReport: openReport }));
  }
  return React.createElement(React.Fragment, null,
    React.createElement(QContinuityBanner, { pending: pending }),
    React.createElement(QMentorChat, { onJourney: onJourney }));
}
