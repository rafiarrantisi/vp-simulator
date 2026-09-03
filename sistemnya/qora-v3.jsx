// ═══════════════════════════════════════════════════════════════════════
// Qora STEP 7 — Case Library + Practice Modes + Debrief UX (case_v3 / SKD 2026)
// ---------------------------------------------------------------------------
// Self-contained module for the rebuilt bank. Consumes the /api/v3/* live
// contract (STEP 6). Mounted by QoraDashboard when hash starts with #/v3.
//
// Design rules (STEP 7 §1 + STEP-6 rule 9): the grand visual identity, theme
// tokens, typography and brand tone are PRESERVED — only the information
// architecture / component composition of the library changes. All styling uses
// the existing CSS variables (var(--primary), var(--surface), ...) and the
// existing QAMoodBand / QIcon helpers from the shared scope.
// ═══════════════════════════════════════════════════════════════════════
// (uses global: React, qv2Fetch, QAMoodBand, QIcon, __t, QV2Stat, setHash-like)

function __v3T(k) { try { return (window.__t || function(x){return x;})(k); } catch (e) { return k; } }

function v3SetHash(path) {
  try { var want = '#/v3/' + path.replace(/^\/+/, ''); if (location.hash !== want) location.hash = want; } catch (e) {}
}
function v3HashParts() {
  try {
    const hashPath = (location.hash || '').split('?')[0];
    return hashPath.replace(/^#\/v3\/?/, '').split('/').filter(Boolean);
  } catch (e) { return []; }
}

// Per-screen error boundary — MUST be a class (function components can't catch
// child render errors). Renders a VISIBLE message instead of a silent blank.
class V3Boundary extends React.Component {
  constructor(props) { super(props); this.state = { err: null }; }
  static getDerivedStateFromError(e) { return { err: e }; }
  render() {
    if (this.state.err) {
      var e = this.state.err;
      return React.createElement('div', { style: { padding: 60, maxWidth: 640, margin: '0 auto', color: 'var(--text-2)', textAlign: 'center' } },
        React.createElement('div', { style: { fontSize: 18, fontWeight: 600, marginBottom: 8 } }, 'Something went wrong rendering this screen'),
        React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' } }, String((e && (e.message || e)) || e)),
        React.createElement('button', { onClick: function(){ try { v3SetHash(''); } catch(_e) {} }, style: { marginTop: 16, padding: '10px 18px', borderRadius: 10, border: 'none', background: 'var(--accent)', color: '#fff', cursor: 'pointer' } }, 'Back to library'));
    }
    return this.props.children;
  }
}

// ── helpers ──────────────────────────────────────────────────────────────
function v3SpecLabel(s) { return (s || '').replace(/[_-]/g, ' ').replace(/\b\w/g, function(c){return c.toUpperCase();}); }
function v3CatLabel(c) {
  if (c === 'tuntas') return 'Tuntas';
  if (c === 'initial_management_and_referral') return 'Tatalaksana awal dan rujuk';
  return v3SpecLabel(c);
}

// Small source drawer (STEP 7 §13).
function V3SourceDrawer({ open, sources, onClose }) {
  if (!open) return null;
  return React.createElement('div', { style: { position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' } },
    React.createElement('div', { onClick: function(){ return null; }, className: 'as', style: { width: 'min(560px, 100%)', maxHeight: '72vh', overflow: 'auto', background: 'var(--surface)', borderTopLeftRadius: 'var(--r-lg)', borderTopRightRadius: 'var(--r-lg)', padding: 20 } },
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 } },
        React.createElement('div', { style: { fontSize: 16, fontWeight: 800, color: 'var(--text-1)' } }, 'Sources'),
        React.createElement('button', { onClick: onClose, style: { border: 'none', background: 'none', color: 'var(--text-3)', fontSize: 20, cursor: 'pointer', fontFamily: 'Plus Jakarta Sans' } }, '×')),
      (sources && sources.length ? sources.map(function (s, i) {
        return React.createElement('div', { key: i, style: { padding: '12px 0', borderBottom: '1px solid var(--border)' } },
          React.createElement('div', { style: { fontSize: 13.5, fontWeight: 700, color: 'var(--text-1)' } }, s.title || 'Untitled'),
          React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 5 } },
            s.organization && React.createElement('span', { className: 'so', style: { fontSize: 11.5, color: 'var(--text-2)' } }, s.organization),
            s.year && React.createElement('span', { className: 'so', style: { fontSize: 11.5, color: 'var(--text-2)' } }, s.year),
            s.kind && React.createElement('span', { className: 'so', style: { fontSize: 11.5, color: 'var(--text-2)', textTransform: 'capitalize' } }, s.kind)),
          s.url
            ? React.createElement('a', { href: s.url, target: '_blank', rel: 'noopener noreferrer', style: { fontSize: 12.5, color: 'var(--primary)', textDecoration: 'none', marginTop: 6, display: 'inline-block' } }, 'View source ↗')
            : React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)', marginTop: 6 } }, 'No link recorded'));
      }) : React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)', padding: 8 } }, 'No sources available.'))));
}

// ── Library: family cards (STEP 7 §2-4, §6) ──────────────────────────────
function QoraV3Library() {
  const [families, setFamilies] = React.useState(null);
  const [specFilter, setSpecFilter] = React.useState('');
  const [catFilter, setCatFilter] = React.useState('');
  const [stage, setStage] = React.useState('koas');
  const [search, setSearch] = React.useState('');
  const [err, setErr] = React.useState('');

  React.useEffect(function () {
    qv2Fetch('/api/v3/families?learner_level=' + stage)
      .then(function (d) { setFamilies(d.families || []); })
      .catch(function (e) { setErr(String(e.message || e)); });
  }, [stage]);

  if (err) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } }, 'Error: ' + err);
  if (!families) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)' } }, 'Loading library…');

  const specs = Array.from(new Set((families || []).map(function (f) { return f.primarySpecialty; }).filter(Boolean))).sort();
  const cats = Array.from(new Set((families || []).map(function (f) { return (f.competencyCategories || []); }).flat())).sort();

  const shown = (families || []).filter(function (f) {
    if (specFilter && f.primarySpecialty !== specFilter) return false;
    if (catFilter && (f.competencyCategories || []).indexOf(catFilter) < 0) return false;
    if (search) {
      const q = search.toLowerCase();
      const hay = ((f.titleId || '') + ' ' + (f.titleEn || '') + ' ' + (f.presentingComplaints || []).join(' ')).toLowerCase();
      if (hay.indexOf(q) < 0) return false;
    }
    return true;
  });

  const renderCard = function (f, i) {
    const isPresentation = f.familyType === 'presentation';
    const bad = isPresentation ? 'Mixed' : (f.competencyCategories && f.competencyCategories[0]);
    return React.createElement('button', {
      key: f.id, onClick: function () { v3SetHash('session/setup/' + f.id); }, className: 'as', style: {
        textAlign: 'left', padding: 16, borderRadius: 'var(--r-lg)', border: '1px solid var(--border)',
        background: 'var(--surface)', boxShadow: 'var(--sh-sm)', cursor: 'pointer', fontFamily: 'Plus Jakarta Sans',
        display: 'flex', flexDirection: 'column', gap: 8,
      },
    },
      React.createElement('div', { style: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 } },
        React.createElement('div', { style: { fontSize: 15.5, fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.25 } }, f.titleEn || f.titleId),
        React.createElement('span', { style: { fontSize: 10, fontWeight: 700, letterSpacing: 0.4, textTransform: 'uppercase', color: 'var(--primary)', border: '1px solid var(--primary-l, var(--border))', background: 'var(--primary-l, var(--surface))', borderRadius: 999, padding: '3px 9px', flexShrink: 0 } },
          isPresentation ? 'Presentation' : v3CatLabel(bad))),
      React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)' } }, v3SpecLabel(f.primarySpecialty)),
      isPresentation
        ? React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)' } }, 'Random differential practice · diagnosis hidden')
        : React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)' } },
            (f.competencyCategories || []).map(v3CatLabel).join(' · ')),
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 } },
        React.createElement(QIcon, { n: 'target', s: 13 }),
        React.createElement('span', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)' } },
          String(f.eligibleVariantCount || 0) + ' patient variation' + ((f.eligibleVariantCount || 0) === 1 ? '' : 's') + ' available')));
  };

  function chip(val, lab, active, onSet) {
    return React.createElement('button', { key: String(val || 'all'), onClick: function(){ onSet(val); }, style: {
      padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: active ? 700 : 500,
      fontFamily: 'Plus Jakarta Sans', cursor: 'pointer',
      border: '1px solid ' + (active ? 'var(--primary)' : 'var(--border)'),
      background: active ? 'var(--primary-l)' : 'var(--surface)',
      color: active ? 'var(--primary)' : 'var(--text-2)',
    } }, lab);
  }

  var stageOpts = [['koas', 'Clinical (Koas)'], ['preclinical', 'Preclinical']];
  var specOpts = [['', 'All specialties']].concat(specs.map(function (s) { return [s, v3SpecLabel(s)]; }));
  var catOpts = [['', 'All competency']].concat(cats.map(function (c) { return [c, v3CatLabel(c)]; }));

  return React.createElement('div', { style: { maxWidth: 'min(1080px, calc(100% - 24px))', margin: '0 auto', padding: '24px 16px' } },
    React.createElement(QAMoodBand, { scene: 'senja', kicker: 'SKD 2026 CASE LIBRARY', title: 'Practice Library', sub: families.length + ' families · different patients appear on replay' }),
    React.createElement('div', { className: 'au', style: { position: 'relative', zIndex: 5, marginTop: -56 } },
      React.createElement('input', { value: search, onChange: function(e){ setSearch(e.target.value); }, placeholder: 'Search disease or complaint…', style: { width: '100%', boxSizing: 'border-box', marginBottom: 10, padding: '11px 14px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } }),
      React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 } }, stageOpts.map(function (o) { return chip(o[0], o[1], stage === o[0], setStage); })),
      React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 } }, specOpts.map(function (o) { return chip(o[0], o[1], specFilter === o[0], setSpecFilter); })),
      React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 } }, catOpts.map(function (o) { return chip(o[0], o[1], catFilter === o[0], setCatFilter); }))),
    shown.length === 0 && React.createElement('div', { style: { padding: '32px 20px', textAlign: 'center', fontSize: 13, color: 'var(--text-3)', background: 'var(--surface)', borderRadius: 'var(--r-lg)', border: '1px dashed var(--border)' } }, 'No matching families.'),
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 } },
      shown.map(renderCard)));
}

// ── Family → targeted entry / pre-session (STEP 7 §4) ────────────────────
function QoraV3Family({ familyId }) {
  const [fam, setFam] = React.useState(null);
  const [targeted, setTargeted] = React.useState('practice');
  React.useEffect(function () {
    qv2Fetch('/api/v3/families?learner_level=koas')
      .then(function (d) {
        const f = (d.families || []).find(function (x) { return x.id === familyId; });
        setFam(f || {});
      })
      .catch(function (e) { setFam({}); });
  }, [familyId]);
  if (!fam) return React.createElement('div', { style: { padding: 40 } }, 'Loading…');
  const isPresentation = fam.familyType === 'presentation';
  return React.createElement('div', { style: { maxWidth: 'min(720px, calc(100% - 24px))', margin: '0 auto', padding: '24px 16px' } },
    React.createElement('button', { onClick: function(){ v3SetHash(''); }, style: { border: 'none', background: 'none', color: 'var(--text-3)', fontSize: 13, cursor: 'pointer', fontFamily: 'Plus Jakarta Sans', marginBottom: 12, display: 'inline-flex', alignItems: 'center', gap: 5 } }, '← ' + 'Library'),
    React.createElement(QAMoodBand, { scene: 'pagi', kicker: isPresentation ? 'PRESENTATION' : 'DISEASE FAMILY', title: fam.titleEn || fam.titleId }),

    React.createElement('div', { className: 'as', style: { position: 'relative', zIndex: 5, marginTop: -40, padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)' } },
      React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 14 } }, v3SpecLabel(fam.primarySpecialty) + ' · ' + (fam.eligibleVariantCount || 0) + ' eligible patient variations'),

      isPresentation
        ? React.createElement('div', { style: { fontSize: 13.5, color: 'var(--text-3)', marginBottom: 18, lineHeight: 1.6 } },
            'This session tests a presenting complaint, not a known diagnosis. The diagnosis stays hidden until you finish.')
        : React.createElement('div', { style: { fontSize: 13.5, color: 'var(--text-3)', marginBottom: 18, lineHeight: 1.6 } },
            'A different patient presentation may appear each time.'),
      // mode toggle
      React.createElement('div', { style: { display: 'flex', gap: 8, marginBottom: 18 } },
        [['practice', 'Practice'], ['osce', 'OSCE']].map(function (m) {
          return React.createElement('button', { key: m[0], onClick: function(){ setTargeted(m[0]); }, style: { flex: 1, padding: '11px', borderRadius: 12, fontSize: 13.5, fontWeight: targeted === m[0] ? 700 : 500, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', border: '1px solid ' + (targeted === m[0] ? 'var(--primary)' : 'var(--border)'), background: targeted === m[0] ? 'var(--primary)' : 'var(--surface)', color: targeted === m[0] ? '#fff' : 'var(--text-2)' } }, m[1]);
        })),
      React.createElement('button', { onClick: function(){ v3SetHash('session/setup/' + encodeURIComponent(fam.id)); }, style: { width: '100%', padding: '13px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } },
        isPresentation || targeted === 'osce' ? 'Start blind practice' : 'Start practising')));
}

// ── Pre-session setup (reuses QV2SessionSetup verbatim: mode/lang/mic/billing) ─
function QoraV3Setup({ familyId, onExit }) {
  const [fam, setFam] = React.useState(null);
  React.useEffect(function () {
    qv2Fetch('/api/v3/families?learner_level=koas')
      .then(function (d) {
        const f = (d.families || []).find(function (x) { return x.id === familyId; });
        setFam(f || {});
      })
      .catch(function () { setFam({}); });
  }, [familyId]);
  if (!fam) return React.createElement('div', { style: { padding: 40 } }, 'Loading…');
  const isPresentation = fam.familyType === 'presentation';
  const brief = fam.firstImpression || (isPresentation
    ? 'This session tests a presenting complaint — the diagnosis stays hidden until you finish.'
    : 'A different patient presentation may appear each time.');
  const caseSummary = {
    id: familyId, mode: isPresentation ? 'osce' : 'practice',
    first_impression: brief, presentation: brief,
    estimated_minutes: isPresentation ? 15 : 10,
  };
  return React.createElement(QV2SessionSetup, {
    caseSummary: caseSummary, onBack: onExit,
    onStart: function (opts) {
      var m = opts.mode === 'osce' ? 'blind' : 'targeted';
      v3SetHash('session/' + encodeURIComponent(familyId) + '/' + m + '?lang=' + encodeURIComponent(opts.language || 'en'));
    },
  });
}

// ── Live AI-patient chat (mirrors QV2Session: brief → chat + mic + timer +
//    task panel → time-up → assessment → debrief) ─────────────────────────
function QoraV3Session({ sessionStart, onExit }) {
  const [sid, setSid] = React.useState(null);
  const [data, setData] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [messages, setMessages] = React.useState([]);
  const [input, setInput] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [stage, setStage] = React.useState('brief');
  const [dxInput, setDxInput] = React.useState('');
  const [diffInput, setDiffInput] = React.useState('');
  const [rxInput, setRxInput] = React.useState('');
  const [stabilized, setStabilized] = React.useState(null);
  const [referral, setReferral] = React.useState(null);
  const [secs, setSecs] = React.useState(15 * 60);
  const [timerOn, setTimerOn] = React.useState(false);
  const [timeUp, setTimeUp] = React.useState(false);
  const endRef = React.useRef(null);

  const mode = (sessionStart && sessionStart[1]) || 'targeted';
  const familyId = (sessionStart && sessionStart[0]) || null;
  const blind = mode === 'blind';
  const lang = new URLSearchParams((window.location.hash || '').split('?')[1] || '').get('lang') || 'en';
  const isOsce = blind;

  React.useEffect(function () {
    qv2Fetch('/api/v3/sessions', {
      method: 'POST',
      body: { family_id: familyId, learner_level: 'koas', interaction_mode: mode, language: lang },
    }).then(function (d) {
      setSid(d.sessionId); setData(d);
      setStage(isOsce ? 'brief' : 'chat');
      setTimerOn(isOsce);
    }).catch(function (e) { setErr(String(e.message || e)); });
  }, [familyId, mode, lang]);

  React.useEffect(function () {
    if (!timerOn || timeUp) return;
    var iv = setInterval(function () {
      if (timeUp) return;
      setSecs(function (s) { if (s <= 1) { setTimeUp(true); return 0; } return s - 1; });
    }, 1000);
    return function () { clearInterval(iv); };
  }, [timerOn, timeUp]);

  React.useEffect(function () {
    if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, busy]);

  function sendText(text) {
    var value = (text == null ? input : text).trim();
    if (!value || busy || !sid) return;
    if (text == null) setInput('');
    setBusy(true);
    setMessages(function (m) { return m.concat([{ role: 'user', text: value }]); });
    return qv2Fetch('/api/v3/sessions/' + sid + '/turns', { method: 'POST', body: { text: value } })
      .then(function (r) {
        setMessages(function (m) { return m.concat([{ role: 'patient', text: r.reply }]); });
        setBusy(false);
      })
      .catch(function (e) { setMessages(function (m) { return m.concat([{ role: 'patient', text: '…' }]); }); setErr(String(e.message || e)); setBusy(false); });
  }

  function submit() {
    if (!sid) return;
    qv2Fetch('/api/v3/sessions/' + sid + '/score', {
      method: 'POST',
      body: { diagnosis_submitted: dxInput, stabilized: stabilized, gave_referral: referral },
    }).then(function () { v3SetHash('result/' + sid); })
      .catch(function (e) { setErr(String(e.message || e)); });
  }

  if (err) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } }, 'Error: ' + err);
  if (!data) return React.createElement('div', { style: { padding: 60, textAlign: 'center', color: 'var(--text-3)' } }, 'Starting a new session…');

  const persona = (data.candidateView && data.candidateView.persona) || {};
  const brief = data.openingBrief || (data.candidateView && data.candidateView.candidate_brief) || '';
  const btn = { padding: '12px 16px', borderRadius: 12, fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' };

  if (stage === 'brief') {
    return React.createElement('div', { style: { maxWidth: 'min(720px, calc(100% - 24px))', margin: '0 auto', padding: '24px 16px' } },
      React.createElement(QAMoodBand, { scene: 'malam', kicker: 'BLIND OSCE', title: 'Candidate brief' }),
      React.createElement('div', { className: 'as', style: { position: 'relative', zIndex: 5, marginTop: -40, padding: 24, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)' } },
        React.createElement('div', { style: { fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, color: 'var(--text-3)', marginBottom: 10 } }, 'Presenting complaint (diagnosis hidden)'),
        React.createElement('div', { style: { fontSize: 16, lineHeight: 1.7, color: 'var(--text-1)', marginBottom: 18 } }, brief),
        React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)', marginBottom: 20, fontStyle: 'italic' } }, 'Take a focused history, then give a working diagnosis + differentials and a management plan.'),
        React.createElement('button', { onClick: function () { setStage('chat'); }, style: { width: '100%', padding: 13, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Begin interview →')));
  }

  const taskPanel = typeof QV2TaskPanel === 'function'
    ? React.createElement(QV2TaskPanel, {
        mode: isOsce ? 'osce' : 'practice', secs: secs, timerOn: timerOn,
        onToggleTimer: function () { setTimerOn(function (t) { return !t; }); },
      })
    : React.createElement('div', { style: { padding: 16, borderRadius: 12, background: 'var(--surface)', border: '1px solid var(--border)' } },
        React.createElement('b', null, 'Session tasks'),
        React.createElement('div', { style: { marginTop: 8, fontSize: 12, color: 'var(--text-2)' } }, isOsce ? 'Focused history · exam · diagnosis · management' : 'Rapport · focused history · red flags · ICE · diagnosis'));
  const wide = (typeof window !== 'undefined' && window.matchMedia('(min-width: 900px)').matches);
  return React.createElement('div', { style: { maxWidth: 'min(1100px, calc(100% - 20px))', margin: '0 auto', padding: '20px 12px 40px' } },
    React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 } },
      React.createElement('div', { style: { fontSize: 17, fontWeight: 800, color: 'var(--text-1)' } }, blind ? 'OSCE Exam' : 'Practice'),
      React.createElement('button', { onClick: onExit, style: { padding: '7px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 12.5, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Exit session')),
    React.createElement('div', { style: { display: 'flex', gap: 16, alignItems: 'flex-start' } },
      wide && taskPanel,
      React.createElement('div', { style: { flex: 1, minWidth: 0 } },
        React.createElement('div', { className: 'as', style: { padding: 12, borderRadius: 14, background: 'var(--surface)', border: '1px solid var(--border)', display: 'flex', flexWrap: 'wrap', gap: 14, alignItems: 'center', marginBottom: 12 } },
          React.createElement('div', { style: { fontSize: 11, fontWeight: 800, color: 'var(--text-1)', textTransform: 'uppercase', letterSpacing: 0.4 } }, 'Vitals'),
          (persona.vitals || []).slice(0, 8).map(function (v, i) {
            return React.createElement('div', { key: i, style: { fontSize: 12, color: 'var(--text-2)' } },
              React.createElement('span', { style: { color: 'var(--text-3)', marginRight: 5 } }, String(v.name || 'vital').replace(/_/g, ' ')),
              React.createElement('b', { style: { fontWeight: 700 } }, String(v.value) + (v.unit ? ' ' + v.unit : '')));
          })),
        React.createElement('div', { style: { maxHeight: '62vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, padding: '4px 2px' } },
          messages.map(function (m, i) {
            const isUser = m.role === 'user';
            return React.createElement('div', { key: i, style: { display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' } },
              React.createElement('div', { style: Object.assign({ maxWidth: '80%', padding: '11px 14px', borderRadius: 16, fontSize: 14, lineHeight: 1.5, fontFamily: 'Plus Jakarta Sans', whiteSpace: 'pre-wrap' }, isUser ? { background: 'var(--primary)', color: '#fff', borderTopRightRadius: 4 } : { background: 'var(--surface)', color: 'var(--text-1)', border: '1px solid var(--border)', borderTopLeftRadius: 4 }) },
                m.text));
          }),
          busy && React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)', padding: '4px 4px' } }, '…'),
          React.createElement('div', { ref: endRef })),
        React.createElement('div', { style: { marginTop: 10, display: 'flex', alignItems: 'center', gap: 10 } },
          typeof QV2MicButton === 'function'
            ? React.createElement(QV2MicButton, { onTranscript: function (t) { sendText(t); }, onAutoSend: function (t) { return sendText(t); }, disabled: busy, sessionLang: lang, compact: false })
            : React.createElement('button', { type: 'button', onClick: function () { setErr('Voice input is unavailable in this browser. Type your question instead.'); }, style: Object.assign({}, btn, { minWidth: 80, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)' }) }, 'Mic'),
          React.createElement('input', { value: input, onChange: function (e) { setInput(e.target.value); }, onKeyDown: function (e) { if (e.key === 'Enter' && !busy) sendText(); }, placeholder: 'Type your question…', disabled: busy, style: { flex: 1, boxSizing: 'border-box', padding: '13px 15px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } }),
          React.createElement('button', { onClick: function () { sendText(); }, disabled: busy || !input.trim(), style: Object.assign({}, btn, { border: 'none', background: 'var(--primary)', color: '#fff' }) }, 'Send')),
        React.createElement('button', { onClick: function () { setStage('assess'); }, style: Object.assign({}, btn, { width: '100%', marginTop: 12, border: '1px solid var(--primary)', background: 'var(--surface)', color: 'var(--primary)' }) }, 'Finish interview — write your assessment'))),
      !wide && React.createElement('div', { style: { flex: 1, maxWidth: 320 } }, taskPanel)),

    timeUp && React.createElement(QV2TimeUpModal, {
      onFinish: function () { setTimeUp(false); setStage('assess'); },
      onContinue: function () { setTimeUp(false); },
    }),

    stage === 'assess' && React.createElement('div', { className: 'as', style: { position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, overflow: 'auto' } },
      React.createElement('div', { style: { width: 'min(600px, 100%)', padding: 24, borderRadius: 'var(--r-2xl)', background: 'var(--surface)', boxShadow: 'var(--sh-xl)' } },
        React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', marginBottom: 14 } }, 'Your assessment'),
        React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)', marginBottom: 14, fontStyle: 'italic' } }, blind ? 'Diagnosis is hidden — commit to your clinical reasoning here.' : 'Summarise your working diagnosis, differentials and management.'),
        React.createElement(V3Field, { label: 'Working diagnosis', value: dxInput, set: setDxInput, ph: 'e.g. dengue with warning signs' }),
        React.createElement(V3Field, { label: 'Differentials', value: diffInput, set: setDiffInput, ph: 'list differentials (optional)' }),
        React.createElement(V3Field, { label: 'Initial management / prescription', value: rxInput, set: setRxInput, ph: 'treatment, fluids, actions' }),
        React.createElement('div', { style: { display: 'flex', gap: 8, margin: '12px 0' } },
          React.createElement('button', { onClick: function () { setStabilized(true); }, style: Object.assign({}, btn, { flex: 1, border: '1px solid var(--border)', background: stabilized === true ? 'var(--primary)' : 'var(--surface)', color: stabilized === true ? '#fff' : 'var(--text-2)' }) }, 'Stabilised'),
          React.createElement('button', { onClick: function () { setStabilized(false); }, style: Object.assign({}, btn, { flex: 1, border: '1px solid var(--border)', background: stabilized === false ? '#C0392B' : 'var(--surface)', color: stabilized === false ? '#fff' : 'var(--text-2)' }) }, 'No stabilisation')),
        React.createElement('div', { style: { display: 'flex', gap: 8, marginBottom: 16 } },
          React.createElement('button', { onClick: function () { setReferral(true); }, style: Object.assign({}, btn, { flex: 1, border: '1px solid var(--border)', background: referral === true ? 'var(--primary)' : 'var(--surface)', color: referral === true ? '#fff' : 'var(--text-2)' }) }, 'Referral arranged'),
          React.createElement('button', { onClick: function () { setReferral(false); }, style: Object.assign({}, btn, { flex: 1, border: '1px solid var(--border)', background: referral === false ? '#C0392B' : 'var(--surface)', color: referral === false ? '#fff' : 'var(--text-2)' }) }, 'No referral')),
        React.createElement('div', { style: { display: 'flex', gap: 10 } },
          React.createElement('button', { onClick: function () { setStage('chat'); }, style: Object.assign({}, btn, { flex: 1, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)' }) }, '← Back to interview'),
          React.createElement('button', { onClick: submit, style: Object.assign({}, btn, { flex: 1, border: 'none', background: 'var(--primary)', color: '#fff' }) }, 'Submit → debrief'))));
}

function V3Field({ label, value, set, ph }) {
  return React.createElement('label', { style: { display: 'block', marginBottom: 10 } },
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 4 } }, label),
    React.createElement('input', { value: value, onChange: function (e) { set(e.target.value); }, placeholder: ph, style: { width: '100%', boxSizing: 'border-box', padding: '11px 13px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } }));
}
// ── Debrief (STEP 7 §12 hero ordering) ────────────────────────────────────
function QoraV3Result({ sessionId, onExit }) {
  const [rep, setRep] = React.useState(null);
  const [sourceOpen, setSourceOpen] = React.useState(false);
  const [err, setErr] = React.useState('');

  React.useEffect(function () {
    // score is idempotent — POST returns the stored report on repeat
    qv2Fetch('/api/v3/sessions/' + sessionId + '/score', { method: 'POST', body: {} })
      .then(function (r) { setRep(r); })
      .catch(function (e) { setErr(String(e.message || e)); });
  }, [sessionId]);

  if (err && !rep) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } }, 'Error: ' + err);
  if (!rep) return React.createElement('div', { style: { padding: 60, textAlign: 'center', color: 'var(--text-3)' } }, 'Preparing feedback…');

  const dims = rep.by_dimension || {};
  const safety = rep.safety_flags || [];
  const cat = (rep.competency_mapping && rep.competency_mapping.category) || '';
  const sources = (rep.debrief && rep.debrief.sources) || [];
  const misses = (rep.debrief && rep.debrief.biggest_misses) || [];
  const famId = rep.familyId;

  function anotherPatient() {
    // Rule 5 + STEP-6 rule 5: request a genuinely different eligible variant.
    if (!famId) { v3SetHash(''); return; }
    const payload = { family_id: famId, current_variant_id: rep.variantId, learner_level: 'koas' };
    qv2Fetch('/api/v3/another-patient', { method: 'POST', body: payload })
      .then(function (np) {
        // start a targeted practice with the chosen (different) variant
        v3SetHash('session/start/' + encodeURIComponent(famId) + '/targeted');
      })
      .catch(function () { v3SetHash('session/start/' + encodeURIComponent(famId) + '/targeted'); });
  }

  return React.createElement('div', { style: { maxWidth: 'min(760px, calc(100% - 24px))', margin: '0 auto', padding: '20px 16px 60px' } },
    React.createElement(QAMoodBand, { scene: 'lentera', kicker: cat ? v3CatLabel(cat) : 'SKD 2026', title: 'Debrief', sub: 'Score · safety · what mattered' }),

    React.createElement('div', { className: 'as', style: { position: 'relative', zIndex: 5, marginTop: -56, padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)' } },
      // 1. Verdict summary
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } },
        'Overall score: ' + (rep.score && Math.round(rep.score * 100) / 100)),
      rep.debrief && React.createElement('div', { style: { fontSize: 13.5, color: 'var(--text-3)', marginBottom: 14 } },
        'Target · ' + (rep.debrief.overall_summary && rep.debrief.overall_summary.target_diagnosis || '—')),

      // 2. Safety flags
      (safety.length > 0) && React.createElement('div', { style: { marginBottom: 14, padding: 12, borderRadius: 12, background: 'rgba(192,57,43,0.08)', border: '1px solid rgba(192,57,43,0.3)' } },
        React.createElement('div', { style: { fontSize: 12, fontWeight: 800, color: '#B03A2E', marginBottom: 6 } }, 'Safety flags'),
        safety.map(function (f, i) {
          return React.createElement('div', { key: i, style: { fontSize: 12.5, color: 'var(--text-1)', padding: '3px 0' } },
            '• ' + v3SpecLabel(f.gate) + (f.critical ? ' (critical)' : ''));
        })),

      // 3. Domain scores
      React.createElement('div', { style: { fontSize: 13, fontWeight: 800, color: 'var(--text-1)', margin: '12px 0 8px' } }, 'Domains'),
      React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 8, marginBottom: 16 } },
        Object.keys(dims).map(function (k) {
          const sc = Math.round((dims[k].score || 0) * 100);
          return React.createElement('div', { key: k, style: { padding: 10, borderRadius: 12, background: 'var(--surface-2, var(--surface))', border: '1px solid var(--border)' } },
            React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)', textTransform: 'capitalize' } }, v3SpecLabel(k)),
            React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)' } }, sc + '%'));
        })),

      // 4/5. Strengths + misses
      React.createElement('div', { style: { fontSize: 13, fontWeight: 800, color: 'var(--text-1)', marginBottom: 6 } }, 'Biggest misses'),
      misses.length
        ? misses.map(function (m, i) {
            return React.createElement('div', { key: i, style: { fontSize: 12.5, color: 'var(--text-1)', padding: '5px 0' } },
              '• ' + m.fact + (m.why_matters ? ' — ' + m.why_matters : ''));
          })
        : React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', marginBottom: 8 } }, 'No critical misses recorded.'),

      // 10. Source-backed answer + source drawer
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border)' } },
        React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)' } }, 'Answer key & sources'),
        sources.length > 0 && React.createElement('button', { onClick: function(){ setSourceOpen(true); }, style: { padding: '8px 14px', borderRadius: 10, border: '1px solid var(--primary)', background: 'var(--surface)', color: 'var(--primary)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'View source')),

      // 11. Next action
      React.createElement('div', { style: { display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' } },
        React.createElement('button', { onClick: function(){ v3SetHash('session/start/' + encodeURIComponent(famId) + '/targeted'); }, style: { flex: 1, minWidth: 120, padding: '12px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 12.5, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Retry same'),
        React.createElement('button', { onClick: anotherPatient, style: { flex: 1, minWidth: 160, padding: '12px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--surface)', color: 'var(--primary)', fontSize: 12.5, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Another patient · same disease'),
        React.createElement('button', { onClick: function(){ v3SetHash(''); }, style: { flex: 1, minWidth: 120, padding: '12px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 12.5, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Library'))),

    React.createElement(V3SourceDrawer, { open: sourceOpen, sources: sources, onClose: function(){ setSourceOpen(false); } }));
}

// ── Router (mounted by QoraDashboard when #/v3) ───────────────────────────
function QoraV3App() {
  const [route, setRoute] = React.useState(v3HashParts());
  React.useEffect(function () {
    const fn = function () { setRoute(v3HashParts()); };
    window.addEventListener('hashchange', fn);
    return function () { window.removeEventListener('hashchange', fn); };
  }, []);
  const r = route || [];
  // #/v3                          -> library
  // #/v3/family/<familyId>        -> family entry
  // #/v3/session/setup/<fam>      -> pre-session setup (mode/lang/mic)
  // #/v3/session/<fam>/<mode>     -> live AI-patient chat (party to v2)
  // #/v3/result/<sid>             -> debrief (loads persisted report)
  if (r[0] === 'family') return React.createElement(QoraV3Family, { familyId: r[1] });
  if (r[0] === 'session' && r[1] === 'setup') return React.createElement(V3Boundary, { key: 'v3st-' + (r[2]||''), onReset: function(){ v3SetHash(''); } },
    React.createElement(QoraV3Setup, { familyId: r[2], onExit: function(){ v3SetHash(''); } }));
  if (r[0] === 'session') return React.createElement(V3Boundary, { key: 'v3ss-' + ((r[1]||'') + '/' + (r[2]||'')), onReset: function(){ v3SetHash(''); } },
    React.createElement(QoraV3Session, { sessionStart: [r[1], r[2]], onExit: function(){ v3SetHash(''); } }));
  if (r[0] === 'result') return React.createElement(V3Boundary, { key: 'v3re-' + (r[1]||''), onReset: function(){ v3SetHash(''); } },
    React.createElement(QoraV3Result, { sessionId: r[1], onExit: function(){ v3SetHash(''); } }));
  return React.createElement(QoraV3Library, null);
}