// ============================================================
// Qora — v2 multi-specialty experience (pivot-v4 Phase 5)
// ------------------------------------------------------------
// Self-contained screen consuming /api/v2/* (catalogue -> answer-
// restrained chat -> calibrated score + answer-key reveal).
// ADDITIVE: reuses design.css tokens only (no design.css change,
// CSS hash index-Bj97HpXF.css preserved). Requires the backend
// (window.OPHTHA_API_BASE) + a logged-in user. Same pattern as
// dev-dashboard.jsx. Copy stays English (the pivot's market).
// ============================================================

function _qv2Base() {
  return (typeof window !== 'undefined' && window.OPHTHA_API_BASE) || '';
}
function _qv2Token() {
  try {
    const raw = localStorage.getItem('ophtha_api_auth');
    const a = raw ? JSON.parse(raw) : null;
    return a && a.token ? a.token : '';
  } catch (e) { return ''; }
}
async function qv2Fetch(path, opts) {
  opts = opts || {};
  const headers = { 'Content-Type': 'application/json' };
  const tok = _qv2Token();
  if (tok) headers['Authorization'] = 'Bearer ' + tok;
  const res = await fetch(_qv2Base() + path, {
    method: opts.method || 'GET', headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let json = null;
  try { json = await res.json(); } catch (e) { json = null; }
  if (!res.ok || (json && json.success === false)) {
    throw new Error((json && (json.error || (json.detail && json.detail.message))) || ('HTTP ' + res.status));
  }
  return json ? json.data : null;
}

const QV2_SPEC_LABEL = {
  internal_medicine: 'Internal medicine', surgery: 'Surgery', paediatrics: 'Paediatrics',
  obstetrics_gynaecology: 'Obs & Gynae', psychiatry: 'Psychiatry', neurology: 'Neurology',
  ent: 'ENT', dermatology: 'Dermatology', ophthalmology: 'Ophthalmology', emergency: 'Emergency',
};

function QV2Pill({ children, tone }) {
  const t = tone || 'primary';
  return React.createElement('span', { style: {
    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 999,
    background: `var(--${t}-l, var(--primary-l))`, color: `var(--${t}, var(--primary))`,
    textTransform: 'uppercase', letterSpacing: '0.04em',
  } }, children);
}

// ---- Catalogue ----
function QV2Catalogue({ onPick }) {
  const [cases, setCases] = React.useState(null);
  const [specs, setSpecs] = React.useState([]);
  const [filter, setFilter] = React.useState('');
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    qv2Fetch('/api/v2/cases')
      .then(d => { setCases(d.cases || []); setSpecs(d.specialties || []); })
      .catch(e => setErr(String(e.message || e)));
  }, []);

  if (err) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } },
    'Could not load cases: ' + err + '. (Sign in and ensure the backend is configured.)');
  if (!cases) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)' } }, 'Loading cases…');

  const shown = filter ? cases.filter(c => c.specialty === filter) : cases;
  return React.createElement('div', { className: 'au', style: { maxWidth: 1080, margin: '0 auto', padding: '24px 20px' } },
    React.createElement('div', { style: { marginBottom: 6, fontSize: 22, fontWeight: 800, color: 'var(--text-1)' } }, 'Case library'),
    React.createElement('div', { style: { marginBottom: 18, fontSize: 13, color: 'var(--text-2)' } },
      shown.length + ' cases across ' + specs.length + ' specialties · the patient only answers what you ask.'),
    // specialty filter chips
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 } },
      [['', 'All']].concat(specs.map(s => [s, QV2_SPEC_LABEL[s] || s])).map(([val, lab]) =>
        React.createElement('button', { key: val || 'all', onClick: () => setFilter(val), style: {
          padding: '6px 14px', borderRadius: 999, fontSize: 12.5, fontWeight: filter === val ? 700 : 500,
          fontFamily: 'Poppins', cursor: 'pointer',
          border: '1px solid ' + (filter === val ? 'var(--primary)' : 'var(--border)'),
          background: filter === val ? 'var(--primary-l)' : 'var(--surface)',
          color: filter === val ? 'var(--primary)' : 'var(--text-2)',
        } }, lab))),
    // cards grid
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 } },
      shown.map((c, i) => React.createElement('button', {
        key: c.id, onClick: () => onPick(c), className: 'as', style: {
          textAlign: 'left', padding: 16, borderRadius: 'var(--r-lg)', border: '1px solid var(--border)',
          background: 'var(--surface)', boxShadow: 'var(--sh-sm)', cursor: 'pointer', fontFamily: 'Poppins',
          display: 'flex', flexDirection: 'column', gap: 8, animationDelay: (i % 8) * 0.04 + 's',
        },
      },
        React.createElement('div', { style: { display: 'flex', gap: 6, flexWrap: 'wrap' } },
          React.createElement(QV2Pill, { tone: 'primary' }, QV2_SPEC_LABEL[c.specialty] || c.specialty),
          c.mode === 'osce_full' ? React.createElement(QV2Pill, { tone: 'violet' }, 'OSCE') : React.createElement(QV2Pill, { tone: 'teal' }, 'Anamnesis')),
        React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.3 } }, c.presentation),
        React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)' } }, c.chief_complaint),
        React.createElement('div', { style: { marginTop: 'auto', display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-3)', fontWeight: 600 } },
          React.createElement('span', null, '◆ Difficulty ' + (c.difficulty || '–')),
          React.createElement('span', null, '⏱ ~' + (c.estimated_minutes || '–') + ' min')))))
  );
}

// ---- Session chat ----
function QV2Session({ caseSummary, onScored, onExit }) {
  const [sessionId, setSessionId] = React.useState(null);
  const [messages, setMessages] = React.useState([]); // {role, text}
  const [input, setInput] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const endRef = React.useRef(null);

  React.useEffect(() => {
    qv2Fetch('/api/v2/sessions', { method: 'POST', body: { case_id: caseSummary.id } })
      .then(d => { setSessionId(d.sessionId); setMessages([{ role: 'patient', text: d.openingLine || '…' }]); })
      .catch(e => setErr(String(e.message || e)));
  }, [caseSummary.id]);

  React.useEffect(() => { if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || busy || !sessionId) return;
    setInput(''); setBusy(true);
    setMessages(m => m.concat([{ role: 'user', text }]));
    try {
      const d = await qv2Fetch('/api/v2/sessions/' + sessionId + '/turns', { method: 'POST', body: { text } });
      setMessages(m => m.concat([{ role: 'patient', text: d.reply }]));
    } catch (e) { setMessages(m => m.concat([{ role: 'patient', text: '(error: ' + (e.message || e) + ')' }])); }
    setBusy(false);
  }

  async function finish() {
    if (!sessionId) return;
    setBusy(true);
    try { const report = await qv2Fetch('/api/v2/sessions/' + sessionId + '/score', { method: 'POST', body: {} }); onScored(report); }
    catch (e) { setErr(String(e.message || e)); setBusy(false); }
  }

  return React.createElement('div', { style: { maxWidth: 760, margin: '0 auto', padding: '16px 16px 0', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 } },
      React.createElement('button', { onClick: onExit, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '← Library'),
      React.createElement(QV2Pill, { tone: 'primary' }, QV2_SPEC_LABEL[caseSummary.specialty] || caseSummary.specialty),
      React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)' } }, caseSummary.presentation)),
    err && React.createElement('div', { style: { color: 'var(--red-d)', fontSize: 12, marginBottom: 8 } }, err),
    React.createElement('div', { style: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10, padding: '8px 2px' } },
      messages.map((m, i) => React.createElement('div', { key: i, className: 'af', style: {
        alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '78%',
        padding: '10px 14px', borderRadius: 16, fontSize: 13.5, lineHeight: 1.5,
        background: m.role === 'user' ? 'var(--primary)' : 'var(--surface)',
        color: m.role === 'user' ? '#fff' : 'var(--text-1)',
        border: m.role === 'user' ? 'none' : '1px solid var(--border)', boxShadow: 'var(--sh-xs)',
      } }, m.text)),
      busy && React.createElement('div', { style: { alignSelf: 'flex-start', fontSize: 12, color: 'var(--text-3)' } }, '…'),
      React.createElement('div', { ref: endRef })),
    React.createElement('div', { style: { display: 'flex', gap: 8, padding: '12px 0 16px' } },
      React.createElement('input', {
        value: input, onChange: e => setInput(e.target.value),
        onKeyDown: e => { if (e.key === 'Enter') send(); },
        placeholder: 'Ask the patient a question…', disabled: busy,
        style: { flex: 1, padding: '11px 14px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13.5, fontFamily: 'Poppins', color: 'var(--text-1)' },
      }),
      React.createElement('button', { onClick: send, disabled: busy, style: { padding: '0 18px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Send'),
      React.createElement('button', { onClick: finish, disabled: busy, style: { padding: '0 16px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Finish & score'))
  );
}

// ---- Result + answer-key reveal ----
function QV2ItemRow({ item, status }) {
  const icon = status === 'hit' ? '✅' : status === 'partial' ? '🟡' : status === 'miss' ? '⬜' : '·';
  return React.createElement('div', { style: { display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12.5, color: 'var(--text-2)', padding: '3px 0' } },
    React.createElement('span', null, icon),
    React.createElement('span', { style: item && item.critical ? { fontWeight: 600, color: 'var(--text-1)' } : null },
      (item && item.item ? item.item : item) + (item && item.critical ? '  •critical' : '')));
}

function QV2Result({ report, caseSummary, onAgain, onLibrary }) {
  const ak = report.answer_key || {};
  const dims = report.per_dimension || {};
  // map item text -> status from per_item (loose lowercase contains match)
  const statusFor = (text) => {
    const t = String(text || '').toLowerCase();
    const hit = (report.per_item || []).find(p => t && (t.includes(String(p.item || '').toLowerCase()) || String(p.item || '').toLowerCase().includes(t)));
    return hit ? hit.status : null;
  };
  return React.createElement('div', { className: 'au', style: { maxWidth: 820, margin: '0 auto', padding: '24px 20px' } },
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)' } }, 'Debrief'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 18 } }, caseSummary.presentation),
    // overall + dimensions
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 18, padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)', marginBottom: 16 } },
      React.createElement('div', { style: { fontSize: 38, fontWeight: 800, color: 'var(--primary)', minWidth: 56, textAlign: 'center' } }, (report.overall != null ? report.overall : 0)),
      React.createElement('div', { style: { flex: 1 } },
        Object.keys(dims).map(k => {
          const d = dims[k]; const pct = d.max ? Math.round((d.score / d.max) * 100) : 0;
          return React.createElement('div', { key: k, style: { marginBottom: 6 } },
            React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--text-2)', fontWeight: 600, marginBottom: 2 } },
              React.createElement('span', null, k.replace(/_/g, ' ')),
              React.createElement('span', null, d.score + '/' + d.max)),
            React.createElement('div', { style: { height: 6, borderRadius: 999, background: 'var(--surface-3)' } },
              React.createElement('div', { style: { width: pct + '%', height: '100%', borderRadius: 999, background: 'var(--primary)' } })));
        }))),
    report.summary && React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6, padding: 14, borderRadius: 'var(--r-md)', background: 'var(--primary-ll)', marginBottom: 18 } }, report.summary),
    // answer key
    React.createElement('div', { style: { fontSize: 16, fontWeight: 800, color: 'var(--text-1)', margin: '6px 0 10px' } }, '🗝 Model answer (what a complete workup includes)'),
    (ak.anamnesis_checklist || []).map(g => React.createElement('div', { key: g.group, style: { marginBottom: 12 } },
      React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 } }, g.group.replace(/_/g, ' ')),
      (g.items || []).map((it, i) => React.createElement(QV2ItemRow, { key: i, item: it, status: statusFor(it.item) })))),
    React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--red-d)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '8px 0 4px' } }, 'Red flags to screen'),
    (ak.red_flags || []).map((it, i) => React.createElement(QV2ItemRow, { key: i, item: it, status: statusFor(it.item) })),
    React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '12px 0 4px' } }, 'Working diagnosis & differentials'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-1)', fontWeight: 700 } }, (ak.expected_ddx && ak.expected_ddx.working_diagnosis) || '–'),
    React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)' } }, ((ak.expected_ddx && ak.expected_ddx.differentials) || []).join(' · ')),
    // actions
    React.createElement('div', { style: { display: 'flex', gap: 10, marginTop: 22 } },
      React.createElement('button', { onClick: onAgain, style: { padding: '10px 18px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Try another case'),
      React.createElement('button', { onClick: onLibrary, style: { padding: '10px 18px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Back to library'))
  );
}

// One-time answer-restraint explainer (the product's core idea).
function QV2Onboarding({ onDone }) {
  const [step, setStep] = React.useState(0);
  const slides = [
    { icon: '🗣️', title: 'The patient only answers what you ask', body: "Like a real lay patient, they won't volunteer the full story. Greet them and they greet back — they won't list symptoms until you ask." },
    { icon: '🔍', title: "Elicit, don't receive", body: 'Work the history systematically — onset, character, red flags, ideas/concerns/expectations. Every question you ask is what gets scored.' },
    { icon: '🗝️', title: 'Then see the full answer key', body: 'After you finish you get per-item hit/miss against the hidden checklist, plus the complete model answer — checklist, red flags, differentials and management.' },
  ];
  const s = slides[step], last = step === slides.length - 1;
  return React.createElement('div', { style: { position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(26,29,46,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, animation: 'overlayIn 0.2s ease' } },
    React.createElement('div', { className: 'as', style: { maxWidth: 420, width: '100%', padding: 28, borderRadius: 'var(--r-2xl)', background: 'var(--surface)', boxShadow: 'var(--sh-xl)', textAlign: 'center' } },
      React.createElement('div', { style: { fontSize: 40, marginBottom: 14 } }, s.icon),
      React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', marginBottom: 10 } }, s.title),
      React.createElement('div', { style: { fontSize: 14, color: 'var(--text-2)', lineHeight: 1.65, marginBottom: 22 } }, s.body),
      React.createElement('div', { style: { display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 18 } },
        slides.map((_, i) => React.createElement('div', { key: i, style: { width: i === step ? 20 : 7, height: 7, borderRadius: 999, background: i === step ? 'var(--primary)' : 'var(--border-2)', transition: 'all .2s' } }))),
      React.createElement('div', { style: { display: 'flex', gap: 10 } },
        React.createElement('button', { onClick: onDone, style: { padding: '11px 16px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-3)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Skip'),
        React.createElement('button', { onClick: () => last ? onDone() : setStep(step + 1), style: { flex: 1, padding: '11px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, last ? 'Start practising' : 'Next'))));
}

function QoraV2Screen() {
  const [view, setView] = React.useState('catalogue'); // catalogue | session | result
  const [picked, setPicked] = React.useState(null);
  const [report, setReport] = React.useState(null);
  const [onboard, setOnboard] = React.useState(() => { try { return !localStorage.getItem('qora_onboarded'); } catch (e) { return true; } });
  const dismiss = () => { try { localStorage.setItem('qora_onboarded', '1'); } catch (e) {} setOnboard(false); };

  let body;
  if (view === 'session' && picked) {
    body = React.createElement(QV2Session, { caseSummary: picked, onScored: (r) => { setReport(r); setView('result'); }, onExit: () => setView('catalogue') });
  } else if (view === 'result' && report && picked) {
    body = React.createElement(QV2Result, { report, caseSummary: picked, onAgain: () => setView('catalogue'), onLibrary: () => setView('catalogue') });
  } else {
    body = React.createElement(QV2Catalogue, { onPick: (c) => { setPicked(c); setReport(null); setView('session'); } });
  }
  return React.createElement(React.Fragment, null, onboard ? React.createElement(QV2Onboarding, { onDone: dismiss }) : null, body);
}

window.QoraV2Screen = QoraV2Screen;
