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
async function qv2Fetch(path, opts, _retried) {
  opts = opts || {};
  const headers = { 'Content-Type': 'application/json' };
  const tok = _qv2Token();
  if (tok) headers['Authorization'] = 'Bearer ' + tok;
  const res = await fetch(_qv2Base() + path, {
    method: opts.method || 'GET', headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 401 && !_retried && typeof window !== 'undefined' && window._qoraRefreshToken) {
    const nt = await window._qoraRefreshToken();
    if (nt) return qv2Fetch(path, opts, true);
  }
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
  ophthalmology: 'Ophthalmology', emergency: 'Emergency', ent: 'ENT', dermatology: 'Dermatology',
};
// Indonesian specialty labels — used when the detected region is Indonesia so
// the catalogue pills match the user's language (Aug 2026).
const QV2_SPEC_LABEL_ID = {
  internal_medicine: 'Penyakit Dalam', surgery: 'Bedah', paediatrics: 'Pediatri',
  obstetrics_gynaecology: 'Obgyn', psychiatry: 'Psikiatri', neurology: 'Neurologi',
  ophthalmology: 'Mata', emergency: 'IGD', ent: 'THT', dermatology: 'Kulit',
};
function _qv2SpecLabel(sp) {
  try {
    if (typeof window !== 'undefined' && window.localStorage && window.localStorage.getItem('qora_region') === 'indo') {
      return QV2_SPEC_LABEL_ID[sp] || QV2_SPEC_LABEL[sp] || sp;
    }
  } catch (e) {}
  return QV2_SPEC_LABEL[sp] || sp;
}
// Localised case title: follows the user's region — Indonesian for indo,
// English otherwise (presentation_id only exists for Indonesian).
function _qv2Title(c) {
  if (!c) return '';
  var indo = false;
  try { indo = typeof window !== 'undefined' && window.localStorage && window.localStorage.getItem('qora_region') === 'indo'; } catch (e) {}
  if (indo) return c.presentation_id || c.presentation || '';
  return c.presentation || c.presentation_id || '';
}

function QV2Pill({ children, tone }) {
  const t = tone || 'primary';
  return React.createElement('span', { style: {
    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 999,
    background: `var(--${t}-l, var(--primary-l))`, color: `var(--${t}, var(--primary))`,
    textTransform: 'uppercase', letterSpacing: '0.04em',
  } }, children);
}

// ---- Catalogue ----
function QV2Catalogue({ onPick, onProgress }) {
  const [cases, setCases] = React.useState(null);
  const [specs, setSpecs] = React.useState([]);
  const [filter, setFilter] = React.useState('');
  const [diff, setDiff] = React.useState('');
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    qv2Fetch('/api/v2/cases')
      .then(d => { setCases(d.cases || []); setSpecs(d.specialties || []); })
      .catch(e => setErr(String(e.message || e)));
  }, []);

  var _t = window.__t || function(k) { return k; };
  if (err) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } },
    _t('common.error') + ': ' + err);
  if (!cases) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)' } }, _t('common.loading'));

  const shown = cases.filter(c => (!filter || c.specialty === filter) && (!diff || String(c.difficulty) === String(diff)));
  const DIFF_LABEL = { '1': _t('cases.difficulty_1'), '2': _t('cases.difficulty_2'), '3': _t('cases.difficulty_3') };
  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(1080px, calc(100% - 24px))', margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 6 } },
      React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)' } }, _t('cases.title')),
      onProgress && React.createElement('button', { onClick: onProgress, style: { padding: '7px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer', whiteSpace: 'nowrap' } }, '\uD83D\uDCCA ' + _t('dashboard.your_progress'))),
    React.createElement('div', { style: { marginBottom: 16, fontSize: 13, color: 'var(--text-2)' } },
      shown.length + (shown.length === cases.length ? '' : ' of ' + cases.length) + ' cases across ' + specs.length + ' specialties'),
    // specialty filter chips
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 } },
      [['', _t('cases.filter_all')]].concat(specs.map(s => [s, _qv2SpecLabel(s)])).map(([val, lab]) =>
        React.createElement('button', { key: val || 'all', onClick: () => setFilter(val), style: {
          padding: '6px 14px', borderRadius: 999, fontSize: 12.5, fontWeight: filter === val ? 700 : 500,
          fontFamily: 'Poppins', cursor: 'pointer',
          border: '1px solid ' + (filter === val ? 'var(--primary)' : 'var(--border)'),
          background: filter === val ? 'var(--primary-l)' : 'var(--surface)',
          color: filter === val ? 'var(--primary)' : 'var(--text-2)',
        } }, lab))),
    // difficulty filter chips
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 } },
      [['', _t('cases.filter_all') + ' ' + _t('cases.title')], ['1', _t('cases.difficulty_1')], ['2', _t('cases.difficulty_2')], ['3', _t('cases.difficulty_3')]].map(([val, lab]) =>
        React.createElement('button', { key: 'd' + (val || 'all'), onClick: () => setDiff(val), title: DIFF_LABEL[val] || 'All difficulty levels', style: {
          padding: '6px 14px', borderRadius: 999, fontSize: 12.5, fontWeight: diff === val ? 700 : 500,
          fontFamily: 'Poppins', cursor: 'pointer',
          border: '1px solid ' + (diff === val ? 'var(--violet, var(--primary))' : 'var(--border)'),
          background: diff === val ? 'var(--violet-l, var(--primary-l))' : 'var(--surface)',
          color: diff === val ? 'var(--violet, var(--primary))' : 'var(--text-2)',
        } }, lab))),
    // empty state
    shown.length === 0 && React.createElement('div', { style: { padding: '32px 20px', textAlign: 'center', fontSize: 13, color: 'var(--text-3)', background: 'var(--surface)', borderRadius: 'var(--r-lg)', border: '1px dashed var(--border)' } }, _t('cases.no_results')),
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
          React.createElement(QV2Pill, { tone: 'primary' }, _qv2SpecLabel(c.specialty)),
          c.mode === 'osce_full' ? React.createElement(QV2Pill, { tone: 'violet' }, 'OSCE') : React.createElement(QV2Pill, { tone: 'teal' }, 'Anamnesis')),
        React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.3 } }, _qv2Title(c)),
        React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)', fontStyle: 'italic' } }, c.first_impression_id || c.first_impression || c.chief_complaint),
        React.createElement('div', { style: { marginTop: 'auto', display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-3)', fontWeight: 600 } },
          React.createElement('span', null, '◆ Difficulty ' + (c.difficulty || '–')),
          React.createElement('span', null, '⏱ ~' + (c.estimated_minutes || '–') + ' min')))))
  );
}

// ---- Assessment (DDx + management) ----
function QV2AssessField({ label, value, set, ph, area }) {
  return React.createElement('label', { style: { display: 'block', marginBottom: 12 } },
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 5 } }, label),
    React.createElement(area ? 'textarea' : 'input', {
      value, onChange: (e) => set(e.target.value), placeholder: ph, rows: area ? 3 : undefined,
      style: { width: '100%', padding: '10px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13.5, fontFamily: 'Poppins', color: 'var(--text-1)', resize: area ? 'vertical' : 'none' },
    }));
}

// Reusable searchable, categorized picker with category dropdown + free-text custom add (§4.8).
function QV2Picker({ catalog, selected, onToggle, max, search, setSearch, unit }) {
  const [cat, setCat] = React.useState('');
  const [custom, setCustom] = React.useState('');
  const q = (search || '').toLowerCase().trim();
  const cats = Object.keys(catalog || {});
  let visible = [];
  if (q) {
    cats.forEach((c) => (catalog[c] || []).forEach((it) => { if (it.toLowerCase().includes(q)) visible.push(it); }));
  } else if (cat) {
    visible = catalog[cat] || [];
  }
  const addCustom = () => {
    const v = custom.trim();
    if (!v) return;
    if (selected.indexOf(v) < 0) onToggle(v);
    setCustom('');
  };
  const removeSel = (it) => onToggle(it);
  return React.createElement('div', null,
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 } },
      React.createElement('input', { value: search, onChange: (e) => setSearch(e.target.value), placeholder: 'Search ' + (unit || 'items') + '…',
        style: { flex: 1, padding: '9px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Poppins', color: 'var(--text-1)' } }),
      React.createElement('span', { style: { fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap', color: max && selected.length >= max ? 'var(--red-d)' : 'var(--text-2)' } }, max ? (selected.length + ' / ' + max + ' selected') : (selected.length + ' selected'))),
    React.createElement('div', { style: { display: 'flex', gap: 8, marginBottom: 12 } },
      React.createElement('select', { value: cat, onChange: (e) => setCat(e.target.value),
        style: { flex: 1, padding: '9px 10px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Poppins', color: 'var(--text-1)' } },
        React.createElement('option', { value: '' }, 'Choose a category…'),
        cats.map((c) => React.createElement('option', { key: c, value: c }, c + ' (' + (catalog[c] || []).length + ')'))),
      React.createElement('input', { value: custom, onChange: (e) => setCustom(e.target.value), onKeyDown: (e) => { if (e.key === 'Enter') { e.preventDefault(); addCustom(); } }, placeholder: 'Or type your own…',
        style: { flex: 1, padding: '9px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Poppins', color: 'var(--text-1)' } }),
      React.createElement('button', { onClick: addCustom, disabled: !custom.trim() || (max && selected.length >= max), style: { padding: '0 14px', borderRadius: 10, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: (!custom.trim() || (max && selected.length >= max)) ? 0.5 : 1 } }, 'Add')),
    selected.length > 0 && React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 } },
      selected.map((it) => React.createElement('button', { key: it, onClick: () => removeSel(it), title: 'Remove', style: {
        padding: '5px 10px', borderRadius: 999, fontSize: 12, fontFamily: 'Poppins', cursor: 'pointer', fontWeight: 600,
        border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)' } }, '✓ ' + it + ' ✕'))),
    visible.length > 0
      ? React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6 } },
          visible.map((it) => {
            const on = selected.indexOf(it) >= 0;
            const capped = !!max && !on && selected.length >= max;
            return React.createElement('button', { key: it, onClick: () => onToggle(it), disabled: capped, style: {
              padding: '6px 12px', borderRadius: 999, fontSize: 12, fontFamily: 'Poppins', cursor: capped ? 'not-allowed' : 'pointer',
              fontWeight: on ? 700 : 500, opacity: capped ? 0.45 : 1,
              border: '1px solid ' + (on ? 'var(--primary)' : 'var(--border)'),
              background: on ? 'var(--primary-l)' : 'var(--surface)',
              color: on ? 'var(--primary)' : 'var(--text-2)',
            } }, (on ? '✓ ' : '') + it);
          }))
      : React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', padding: '8px 2px' } },
          q ? 'No matches — try a different search, or type your own above.' : 'Pick a category above or search — no need to scroll through everything.'));
}

const QV2_MAX_INVESTIGATIONS = 8;

function QV2Assess({ caseSummary, isOsce, busy, transcript, onBack, onSubmit }) {
  const [tab, setTab] = React.useState('diagnosis');
  const [dx1, setDx1] = React.useState('');
  const [dx2, setDx2] = React.useState('');
  const [dx3, setDx3] = React.useState('');
  const [reasoning, setReasoning] = React.useState('');
  const [inv, setInv] = React.useState([]);
  const [invSearch, setInvSearch] = React.useState('');
  const [tx, setTx] = React.useState([]);
  const [txSearch, setTxSearch] = React.useState('');
  const [edukasi, setEdukasi] = React.useState('');

  const toggle = (set, max) => (item) => set((cur) => cur.indexOf(item) >= 0 ? cur.filter((x) => x !== item) : (max && cur.length >= max ? cur : cur.concat([item])));
  const submit = () => onSubmit({ dx1, dx2, dx3, reasoning }, { penunjang: inv.join(', '), terapi: tx.join(', '), edukasi });

  const tabs = [['conversation', _t('session.assess_tab_conversation')], ['investigations', _t('session.assess_tab_investigations')], ['diagnosis', _t('session.assess_tab_diagnosis')], ['therapy', _t('session.assess_tab_therapy')]];

  const conversationTab = React.createElement('div', { style: { maxHeight: 380, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 } },
    (transcript || []).filter((m) => m.role === 'user' || m.role === 'patient').map((m, i) => React.createElement('div', { key: i, style: {
      alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%', padding: '8px 12px', borderRadius: 14, fontSize: 12.5, lineHeight: 1.5,
      background: m.role === 'user' ? 'var(--primary)' : 'var(--surface)', color: m.role === 'user' ? '#fff' : 'var(--text-1)',
      border: m.role === 'user' ? 'none' : '1px solid var(--border)',
    } }, m.text || m.content || '')),
    (!transcript || !transcript.length) && React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)' } }, 'No conversation recorded.'));

  const diagnosisTab = React.createElement('div', null,
    React.createElement(QV2AssessField, { label: _t('session.working_diagnosis'), value: dx1, set: setDx1, ph: _t('session.working_diagnosis') }),
    React.createElement(QV2AssessField, { label: _t('session.differential_2'), value: dx2, set: setDx2, ph: _t('session.differential_2') }),
    React.createElement(QV2AssessField, { label: _t('session.differential_3'), value: dx3, set: setDx3, ph: _t('session.differential_3') }),
    React.createElement(QV2AssessField, { label: _t('session.clinical_reasoning'), value: reasoning, set: setReasoning, ph: _t('session.clinical_reasoning'), area: true }));

  const investigationsTab = React.createElement('div', null,
    React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', marginBottom: 12 } }, 'Optional — select the investigations you would order (up to ' + QV2_MAX_INVESTIGATIONS + '), or type your own. Over-ordering is not rewarded. Leave empty if unsure.'),
    React.createElement(QV2Picker, { catalog: window.QORA_INVESTIGATIONS || {}, selected: inv, onToggle: toggle(setInv, QV2_MAX_INVESTIGATIONS), max: QV2_MAX_INVESTIGATIONS, search: invSearch, setSearch: setInvSearch, unit: 'investigations' }));

  const therapyTab = React.createElement('div', null,
    React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', marginBottom: 12 } }, 'Optional — ' + _t('session.select_therapy') + ' You can also type your own.'),
    React.createElement(QV2Picker, { catalog: window.QORA_THERAPIES || {}, selected: tx, onToggle: toggle(setTx, 0), search: txSearch, setSearch: setTxSearch, unit: 'treatments' }),
      React.createElement(QV2AssessField, { label: _t('session.patient_education'), value: edukasi, set: setEdukasi, ph: 'What you would tell the patient...', area: true }));

  const panel = tab === 'conversation' ? conversationTab : tab === 'investigations' ? investigationsTab : tab === 'therapy' ? therapyTab : diagnosisTab;

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(720px, calc(100% - 16px))', margin: '0 auto', padding: 16 } },
    React.createElement('button', { onClick: onBack, style: { marginBottom: 14, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '← Back to interview'),
    React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, _t('session.your_assessment')),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 16 } }, 'Commit your workup before the answer key is revealed.'),
    React.createElement('div', { style: { display: 'flex', gap: 4, marginBottom: 18, borderBottom: '1px solid var(--border)', flexWrap: 'wrap' } },
      tabs.map(([val, lab]) => React.createElement('button', { key: val, onClick: () => setTab(val), style: {
        padding: '9px 14px', border: 'none', borderBottom: '2px solid ' + (tab === val ? 'var(--primary)' : 'transparent'),
        background: 'none', color: tab === val ? 'var(--primary)' : 'var(--text-2)', fontSize: 13, fontWeight: tab === val ? 700 : 500, fontFamily: 'Poppins', cursor: 'pointer',
      } }, lab + (val === 'investigations' && inv.length ? ' (' + inv.length + ')' : '') + (val === 'therapy' && tx.length ? ' (' + tx.length + ')' : '')))),
    panel,
    React.createElement('button', { onClick: submit, disabled: busy, style: { width: '100%', marginTop: 20, padding: 13, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: busy ? 0.7 : 1 } }, busy ? 'Scoring…' : 'Finish & reveal answer key'));
}

// ---- Session chat ----
// ---- Examination media viewer (specialty-agnostic) ----
// Mirrors the legacy eye-photo bar but generic over image/scan/ecg/etc. Fetches
// /api/v2/cases/{id}/media; auto-hides when a case has no media (zero visual
// change for text-only cases). Design tokens only — no design.css change.
const QV2_MEDIA_ICON = { image: '🖼', photo: '🖼', scan: '🩻', xray: '🩻', ultrasound: '🩻', ecg: '📈', fundus: '👁', slitlamp: '👁' };

function _qv2ResolveMedia(src) {
  if (!src) return '';
  if (/^https?:\/\//i.test(src)) return src;
  if (src.charAt(0) === '/') {
    const base = _qv2Base();
    return (base && src.indexOf('/api/') === 0) ? base + src : src;
  }
  if (src.indexOf('./') === 0) return src;
  return './' + src; // relative asset served by the frontend (public/exam-media/…)
}

function QV2MediaModal({ media, onClose }) {
  const [idx, setIdx] = React.useState(0);
  const [loaded, setLoaded] = React.useState(false);
  const count = media.length;
  const cur = media[idx] || media[0];
  React.useEffect(() => { setLoaded(false); }, [idx]);
  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      else if (e.key === 'ArrowRight' && count > 1) setIdx(i => (i + 1) % count);
      else if (e.key === 'ArrowLeft' && count > 1) setIdx(i => (i - 1 + count) % count);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [count, onClose]);
  return React.createElement('div', { onClick: onClose, style: { position: 'fixed', inset: 0, zIndex: 1001, background: 'rgba(26,29,46,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, animation: 'overlayIn 0.2s ease' } },
    React.createElement('div', { onClick: (e) => e.stopPropagation(), style: { background: 'var(--surface)', borderRadius: 18, padding: 18, maxWidth: 'min(900px, 92vw)', width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--sh-xl)', border: '1px solid var(--border)' } },
      React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 } },
        React.createElement('span', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', flex: 1 } }, (QV2_MEDIA_ICON[cur.type] || '🔬') + ' ' + (cur.label || 'Examination media')),
        count > 1 && React.createElement('span', { style: { fontSize: 11, color: 'var(--text-3)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' } }, (idx + 1) + ' / ' + count),
        React.createElement('button', { onClick: onClose, style: { padding: '6px 12px', fontSize: 12, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '✕ Close')),
      React.createElement('div', { style: { position: 'relative', flex: 1, background: 'var(--surface-2)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', minHeight: 260 } },
        !loaded && React.createElement('div', { style: { position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-3)', fontSize: 12 } }, 'Loading…'),
        React.createElement('img', { src: _qv2ResolveMedia(cur.src), alt: cur.caption || cur.label || 'Examination media', onLoad: () => setLoaded(true), onError: () => setLoaded(true), style: { maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain', display: 'block', opacity: loaded ? 1 : 0, transition: 'opacity 0.2s ease' } }),
        count > 1 && React.createElement('button', { onClick: () => setIdx(i => (i - 1 + count) % count), 'aria-label': 'Previous', style: { position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', width: 36, height: 36, borderRadius: '50%', background: 'rgba(0,0,0,0.55)', color: '#fff', border: 'none', fontSize: 18, cursor: 'pointer' } }, '‹'),
        count > 1 && React.createElement('button', { onClick: () => setIdx(i => (i + 1) % count), 'aria-label': 'Next', style: { position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', width: 36, height: 36, borderRadius: '50%', background: 'rgba(0,0,0,0.55)', color: '#fff', border: 'none', fontSize: 18, cursor: 'pointer' } }, '›')),
      cur.caption && React.createElement('div', { style: { marginTop: 12, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.5 } }, cur.caption),
      count > 1 && React.createElement('div', { style: { marginTop: 8, fontSize: 10, color: 'var(--text-3)', textAlign: 'center' } }, '← → to navigate · Esc to close')));
}

function QV2MediaBar({ caseId }) {
  const [media, setMedia] = React.useState([]);
  const [open, setOpen] = React.useState(false);
  React.useEffect(() => {
    let alive = true;
    qv2Fetch('/api/v2/cases/' + encodeURIComponent(caseId) + '/media')
      .then(d => { if (alive) setMedia((d && d.media) || []); })
      .catch(() => { if (alive) setMedia([]); });
    return () => { alive = false; };
  }, [caseId]);
  if (!media.length) return null;
  return React.createElement(React.Fragment, null,
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', marginBottom: 10, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 } },
      React.createElement('span', { style: { fontSize: 11, color: 'var(--text-3)', fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase' } }, 'Examination'),
      React.createElement('div', { style: { flex: 1 } }),
      React.createElement('button', { onClick: () => setOpen(true), style: { padding: '6px 12px', fontSize: 12, fontWeight: 600, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-1)', fontFamily: 'Poppins', cursor: 'pointer' } }, '🔬 View examination media' + (media.length > 1 ? ' (' + media.length + ')' : ''))),
    open && React.createElement(QV2MediaModal, { media, onClose: () => setOpen(false) }));
}

// ---- Responsive helper ---- 
function useIsWide(px) {
  const q = '(min-width: ' + (px || 900) + 'px)';
  const [wide, setWide] = React.useState(() => typeof window !== 'undefined' && window.matchMedia(q).matches);
  React.useEffect(() => {
    const mq = window.matchMedia(q);
    const on = () => setWide(mq.matches);
    mq.addEventListener ? mq.addEventListener('change', on) : mq.addListener(on);
    return () => { mq.removeEventListener ? mq.removeEventListener('change', on) : mq.removeListener(on); };
  }, [q]);
  return wide;
}
function useIsMobile() { return !useIsWide(768); }
function useIsTablet() { return !useIsWide(1024); }

// ---- Session setup: mode selection + preparation (instruksi §4.3 + §4.5) ----
function QV2ModeCard({ active, onClick, tone, badge, title, body }) {
  return React.createElement('button', { onClick, className: 'as', style: {
    flex: 1, minWidth: 220, textAlign: 'left', padding: 18, borderRadius: 'var(--r-lg)', cursor: 'pointer', fontFamily: 'Poppins',
    background: active ? 'var(--' + tone + '-l, var(--primary-l))' : 'var(--surface)',
    border: '2px solid ' + (active ? 'var(--' + tone + ', var(--primary))' : 'var(--border)'),
    boxShadow: active ? 'var(--sh-md)' : 'var(--sh-xs)', transition: 'all .15s ease',
  } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 } },
      React.createElement(QV2Pill, { tone: active ? tone : 'primary' }, badge),
      active && React.createElement('span', { style: { fontSize: 11.5, color: 'var(--' + tone + ', var(--primary))', fontWeight: 700 } }, '✓ Selected')),
    React.createElement('div', { style: { fontSize: 16, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, title),
    React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.5 } }, body));
}

function QV2PrepRow({ icon, title, body, status, tone }) {
  return React.createElement('div', { style: { display: 'flex', gap: 12, alignItems: 'center', padding: 12, borderRadius: 'var(--r-md)', background: 'var(--surface-2)', border: '1px solid var(--border)' } },
    React.createElement('div', { style: { fontSize: 20 } }, icon),
    React.createElement('div', { style: { flex: 1 } },
      React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)' } }, title),
      React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)', lineHeight: 1.5 } }, body)),
    status && React.createElement('span', { style: { fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap', padding: '3px 9px', borderRadius: 999, background: 'var(--' + (tone || 'primary') + '-l, var(--primary-l))', color: 'var(--' + (tone || 'primary') + ', var(--primary))' } }, status));
}

function QV2SessionSetup({ caseSummary, onStart, onBack }) {
  const [mode, setMode] = React.useState(caseSummary.mode === 'osce_full' ? 'osce' : 'practice');
  // Default the session language from the detected region (indo -> id) so the
  // mic uses id-ID out of the box; the profile's preferred_language overrides
  // async below. (Aug 2026 fix: defaulting to 'en' made Indonesian voice input
  // use en-US and fail to transcribe.)
  const [lang, setLang] = React.useState(function () {
    try { return (typeof window !== 'undefined' && window.localStorage && window.localStorage.getItem('qora_region') === 'indo') ? 'id' : 'en'; }
    catch (e) { return 'en'; }
  });
  const [micState, setMicState] = React.useState('idle'); // idle | requesting | granted | denied
  const [stt, setStt] = React.useState(null); // null=checking | 'browser' | 'server' | false
  React.useEffect(() => {
    if (typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)) { setStt('browser'); return; }
    setStt(false); // browser STT only — no server transcription
  }, []);
  // Load preferred language from profile
  React.useEffect(function () {
    qv2Fetch('/api/users/me').then(function (d) {
      if (d && d.preferred_language) setLang(d.preferred_language);
    }).catch(function () {});
  }, []);
  // Check billing status — if free limit reached, show upsell instead of starting
  var billState = React.useState(null);
  var billing = billState[0];
  var setBilling = billState[1];
  React.useEffect(function () {
    qv2Fetch('/api/billing/me').then(function (d) {
      setBilling(d);
      if (d && d.usage && d.usage.sessions >= (d.free_session_limit || 3) && !d.unlimited) {
        setBilling(Object.assign({}, d, { limitReached: true }));
      }
    }).catch(function () {});
  }, []);
  async function requestMic() {
    setMicState('requesting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());
      setMicState('granted');
    } catch (e) { setMicState('denied'); }
  }
  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(640px, calc(100% - 16px))', margin: '0 auto', padding: '24px 16px 60px' } },
    React.createElement('button', { onClick: onBack, style: { marginBottom: 16, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '\u2190 Library'),
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, 'Get ready for your session'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 22, fontStyle: 'italic' } }, caseSummary.first_impression_id || caseSummary.first_impression || caseSummary.presentation_id || caseSummary.presentation),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, 'Choose a mode'),
    React.createElement('div', { style: { display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' } },
      React.createElement(QV2ModeCard, { active: mode === 'practice', onClick: () => setMode('practice'), tone: 'teal', badge: 'Practice', title: 'Anamnesis practice', body: 'Relaxed learning. A task guide and history hints help you along. The timer is optional.' }),
      React.createElement(QV2ModeCard, { active: mode === 'osce', onClick: () => setMode('osce'), tone: 'violet', badge: 'OSCE', title: 'OSCE exam', body: 'Exam conditions — no hints. A countdown runs; when it ends you finish or continue for a penalty.' })),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, 'Choose session language'),
    React.createElement('div', { className: 'as d2', style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24 } },
      [['en','English'],['id','Bahasa Indonesia'],['ms','Bahasa Melayu'],['tl','Tagalog'],['vi','Tiếng Việt'],['th','ภาษาไทย']].map(function(p) {
        var code = p[0], label = p[1];
        return React.createElement('button', { key: code, onClick: function() { setLang(code); }, style: {
          padding: '8px 16px', borderRadius: 999, fontSize: 12.5, fontFamily: 'Poppins', cursor: 'pointer', fontWeight: lang === code ? 700 : 500,
          border: '1px solid ' + (lang === code ? 'var(--primary)' : 'var(--border)'),
          background: lang === code ? 'var(--primary-l)' : 'var(--surface)',
          color: lang === code ? 'var(--primary)' : 'var(--text-2)',
        } }, (lang === code ? '✓ ' : '') + label);
      })),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, 'Session preparation'),
    React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 18 } },
      React.createElement('div', { style: { display: 'flex', gap: 12, alignItems: 'center', padding: 12, borderRadius: 'var(--r-md)', background: 'var(--surface-2)', border: '1px solid var(--border)' } },
        React.createElement('div', { style: { fontSize: 20 } }, '🎙️'),
        React.createElement('div', { style: { flex: 1 } },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)' } }, 'Microphone access'),
          React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)', lineHeight: 1.5 } }, 'Optional — talk to the patient by voice. You can always type instead.')),
        micState === 'granted'
          ? React.createElement('span', { style: { fontSize: 11, fontWeight: 700, padding: '4px 10px', borderRadius: 999, background: 'var(--teal-l, var(--primary-l))', color: 'var(--teal, var(--primary))' } }, '✓ Allowed')
          : React.createElement('button', { onClick: requestMic, disabled: micState === 'requesting', style: { fontSize: 12, fontWeight: 700, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontFamily: 'Poppins', cursor: 'pointer' } }, micState === 'denied' ? 'Blocked — retry' : micState === 'requesting' ? 'Requesting…' : 'Allow')),
      React.createElement(QV2PrepRow, { icon: '🔊', title: 'Speech-to-text', body: stt === null ? 'Checking…' : (stt === 'browser' ? 'Ready — using your browser’s built-in speech recognition (no upload).' : stt === 'server' ? 'Ready — speech is transcribed on the server.' : 'Unavailable in this browser — you can still type your questions.'), status: stt === null ? 'Checking…' : (stt ? 'Ready' : 'Text only'), tone: stt ? 'teal' : 'primary' }),
      React.createElement(QV2PrepRow, { icon: '🔒', title: 'Privacy & security', body: 'Your audio is processed securely and is not stored without your explicit consent.' }),
      React.createElement(QV2PrepRow, { icon: '🎧', title: 'Audio quality', body: 'For best results, use a quiet room and check your microphone works.' })),
    React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', marginBottom: 16 } }, micState === 'granted' ? '✓ All set — you can start now.' : 'You can start now and enable the mic later.'),
    billing && billing.limitReached
      ? React.createElement('div', { style: { padding: 16, borderRadius: 12, border: '1px solid var(--amber)', background: 'var(--amber-l)', marginBottom: 12 } },
          React.createElement('div', { style: { fontSize: 13.5, fontWeight: 700, color: 'var(--amber-d)', marginBottom: 4 } }, '⚡ Free session limit reached'),
          React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', marginBottom: 12 } }, 'You have used all ' + (billing.free_session_limit || 3) + ' free sessions this period. Upgrade to keep practising without limits.'),
          React.createElement('div', { style: { display: 'flex', gap: 8 } },
            React.createElement('button', { onClick: function () { if (window.__goBilling) window.__goBilling(); }, style: { padding: '10px 18px', borderRadius: 10, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Upgrade plan'),
            React.createElement('button', { onClick: onBack, style: { padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Back to library')))
      : React.createElement('button', { onClick: () => onStart({ mode: mode, micReady: micState === 'granted', sttReady: !!stt, language: lang }), style: { width: '100%', padding: 14, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', boxShadow: 'var(--sh-md)' } }, 'Start session →'));
}

// ---- In-session task panel (instruksi §4.6) ----
function QV2TaskPanel({ mode, secs, timerOn, onToggleTimer }) {
  const mm = String(Math.floor(secs / 60)).padStart(2, '0');
  const ss = String(secs % 60).padStart(2, '0');
  const low = timerOn && secs < 60;
  const tasks = mode === 'osce'
    ? ['Take a focused history (anamnesis)', 'State the local/physical examination findings', 'Request appropriate investigations', 'Give a working diagnosis + 2 differentials', 'Propose management & safety-netting']
    : ['Introduce yourself & build rapport', 'Take a focused history (anamnesis)', 'Screen for red-flag symptoms', 'Explore Ideas, Concerns & Expectations', 'Reach a working diagnosis'];
  return React.createElement('div', { style: { width: 250, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 14 } },
    React.createElement('div', { style: { padding: 16, borderRadius: 'var(--r-lg)', textAlign: 'center', background: low ? 'var(--red-l)' : 'var(--surface)', border: '1px solid ' + (low ? 'var(--red)' : 'var(--border)') } },
      React.createElement('div', { style: { fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 6 } }, 'Time remaining'),
      React.createElement('div', { style: { fontSize: 30, fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: low ? 'var(--red-d)' : 'var(--text-1)' } }, timerOn ? mm + ':' + ss : '—:—'),
      React.createElement('button', { onClick: onToggleTimer, style: { marginTop: 8, fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, timerOn ? 'Pause timer' : 'Start timer')),
    React.createElement('div', { style: { padding: 16, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)' } },
      React.createElement('div', { style: { fontSize: 12, fontWeight: 800, color: 'var(--text-1)', marginBottom: 10 } }, '📋 Your tasks'),
      tasks.map((t, i) => React.createElement('div', { key: i, style: { display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12, color: 'var(--text-2)', padding: '4px 0', lineHeight: 1.4 } },
        React.createElement('span', { style: { color: 'var(--text-3)', fontWeight: 700 } }, (i + 1) + '.'),
        React.createElement('span', null, t)))),
    mode === 'practice' && React.createElement('div', { style: { padding: 16, borderRadius: 'var(--r-lg)', background: 'var(--primary-ll, var(--surface-2))', border: '1px dashed var(--primary)' } },
      React.createElement('div', { style: { fontSize: 12, fontWeight: 800, color: 'var(--primary)', marginBottom: 8 } }, '💡 History hints'),
      React.createElement('div', { style: { fontSize: 11.5, color: 'var(--text-2)', lineHeight: 1.7 } }, 'Onset · Site · Character · Radiation · Severity · Timing · Aggravating / relieving · Associated symptoms · Past medical history · Medications & allergies · Family & social · Ideas, Concerns, Expectations')));
}

// ---- Time-up choice (instruksi §4.3) ----
function QV2TimeUpModal({ onFinish, onContinue }) {
  return React.createElement('div', { style: { position: 'fixed', inset: 0, zIndex: 1002, background: 'rgba(26,29,46,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, animation: 'overlayIn 0.2s ease' } },
    React.createElement('div', { className: 'as', style: { maxWidth: 'min(400px, calc(100% - 40px))', width: '100%', padding: 22, borderRadius: 'var(--r-2xl)', background: 'var(--surface)', boxShadow: 'var(--sh-xl)', textAlign: 'center' } },
      React.createElement('div', { style: { fontSize: 38, marginBottom: 10 } }, '⏰'),
      React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', marginBottom: 8 } }, "Time's up"),
      React.createElement('div', { style: { fontSize: 13.5, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 22 } }, 'Your OSCE time has ended. Finish now and go to your assessment, or keep going — continuing past time applies a small score penalty.'),
      React.createElement('div', { style: { display: 'flex', gap: 10 } },
        React.createElement('button', { onClick: onContinue, style: { flex: 1, padding: 12, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Continue (−penalty)'),
        React.createElement('button', { onClick: onFinish, style: { flex: 1, padding: 12, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Finish now'))));
}

// ---- Voice input button (voice-first experience) ----
// Always use backend transcription (Groq Whisper) for consistency across all browsers
// Features: big circular button, pulse animation, silence detection, auto-send, auto-reactivate
const QV2_SILENCE_THRESHOLD = 30;  // dB level below which we consider silence
const QV2_SILENCE_DURATION = 2500;  // ms of silence before auto-send

function QV2MicButton({ onTranscript, onAutoSend, disabled, sessionLang, compact }) {
  // Self-contained browser STT (Web Speech API only — no server upload, no Groq).
  const [state, setState] = React.useState('idle'); // idle | listening | error
  const [errMsg, setErrMsg] = React.useState('');
  const recRef = React.useRef(null);
  const sz = compact ? 60 : 80;
  const iconSz = compact ? 26 : 32;

  const LANG_MAP = { en: 'en-US', id: 'id-ID', ms: 'ms-MY', tl: 'tl-PH', vi: 'vi-VN', th: 'th-TH' };

  function stopRec() {
    if (recRef.current) {
      try { recRef.current.stop(); } catch (e) {}
      recRef.current = null;
    }
    setState('idle');
  }

  function startRec() {
    if (disabled) return;
    const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (!SR) {
      setErrMsg('Voice input is not supported in this browser. Use Chrome/Edge/Safari, or type instead.');
      setState('error');
      return;
    }
    setErrMsg('');
    const rec = new SR();
    recRef.current = rec;
    rec.lang = LANG_MAP[sessionLang] || 'en-US';
    rec.continuous = false;
    rec.interimResults = false;

    rec.onresult = async (e) => {
      const t = ((e.results && e.results[0] && e.results[0][0] && e.results[0][0].transcript) || '').trim();
      if (!t) return;
      setState('idle');
      if (onTranscript) onTranscript(t);
      if (onAutoSend) await onAutoSend(t);
    };
    rec.onerror = (e) => {
      if (e.error === 'not-allowed') setErrMsg('Microphone blocked — allow mic access for this site, then tap again.');
      else if (e.error === 'no-speech') setErrMsg('No speech detected — try again.');
      else if (e.error !== 'aborted') setErrMsg('Voice input error (' + (e.error || 'unknown') + ').');
      setState('idle');
    };
    rec.onend = () => { if (recRef.current === rec) setState('idle'); };

    setState('listening');
    try { rec.start(); } catch (e) { setErrMsg('Could not start voice input.'); setState('idle'); }
  }

  const isListening = state === 'listening';
  const onClick = () => { if (isListening) stopRec(); else startRec(); };

  return React.createElement('div', { style: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, padding: '12px 0' } },
    React.createElement('button', {
      onClick,
      disabled: !!disabled,
      title: isListening ? 'Stop recording' : (disabled ? 'Waiting for the patient to reply…' : 'Start recording'),
      style: {
        width: sz,
        height: sz,
        borderRadius: '50%',
        border: isListening ? '3px solid var(--red)' : '3px solid var(--border)',
        background: isListening ? 'var(--red-l)' : disabled ? 'var(--surface-2)' : 'var(--surface)',
        color: isListening ? 'var(--red)' : disabled ? 'var(--text-3)' : 'var(--text-2)',
        fontSize: iconSz,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        transition: 'all 0.2s ease',
        position: 'relative',
        overflow: 'visible',
      }
    },
      isListening ? '⏹' : '🎙️',
      isListening && React.createElement('div', {
        style: {
          position: 'absolute',
          top: -6,
          left: -6,
          right: -6,
          bottom: -6,
          borderRadius: '50%',
          border: '2px solid var(--red)',
          animation: 'pulse 1.5s ease-in-out infinite',
          pointerEvents: 'none',
        }
      })
    ),
    React.createElement('div', {
      style: { fontSize: 12, color: 'var(--text-2)', fontWeight: 500 }
    },
      isListening ? 'Listening… (tap to stop)' : (disabled ? 'Patient is replying…' : 'Tap to speak')),
    errMsg && React.createElement('div', {
      style: { fontSize: 11, color: 'var(--red)', marginTop: 4, maxWidth: 240, textAlign: 'center' }
    }, errMsg)
  );
}

function QV2Session({ caseSummary, mode, language, onScored, onExit, initialSessionId, onSessionReady }) {
  const [sessionId, setSessionId] = React.useState(initialSessionId || null);
  const [messages, setMessages] = React.useState([]); // {role, text}
  const [input, setInput] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [stage, setStage] = React.useState('chat'); // chat | pf | assess
  const [pf, setPf] = React.useState({ notes: '', areas: [] });
  const isOsce = mode === 'osce';
  const [secs, setSecs] = React.useState((caseSummary.estimated_minutes || 15) * 60);
  const [timerOn, setTimerOn] = React.useState(isOsce); // OSCE auto-starts the countdown
  const [timeUp, setTimeUp] = React.useState(false);
  const [overtime, setOvertime] = React.useState(false);
  const endRef = React.useRef(null);
  const wide = useIsWide(900);
  const isMobile = useIsMobile();

  // Mic control state
  const [micState, setMicState] = React.useState('idle'); // idle | listening | processing | error
  const [micErrMsg, setMicErrMsg] = React.useState('');
  const mediaRecorderRef = React.useRef(null);
  const audioChunksRef = React.useRef([]);
  const silenceTimerRef = React.useRef(null);
  const lastSoundTimeRef = React.useRef(Date.now());
  const shouldAutoReactivateRef = React.useRef(false);

  async function handleMicStart() {
    try {
      setMicErrMsg('');
      setMicState('listening');
      lastSoundTimeRef.current = Date.now();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Setup audio analysis for silence detection
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 512;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      let audioContextRef = audioContext;

      function checkSilence() {
        if (micState !== 'listening') {
          audioContextRef.close();
          return;
        }
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((sum, val) => sum + val, 0) / dataArray.length;

        if (avg > QV2_SILENCE_THRESHOLD) {
          lastSoundTimeRef.current = Date.now();
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else if (audioChunksRef.current.length > 0 && Date.now() - lastSoundTimeRef.current > QV2_SILENCE_DURATION) {
          // Silence detected, stop and process
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
          handleMicStop();
          return;
        }

        if (micState === 'listening') {
          silenceTimerRef.current = setTimeout(checkSilence, 200);
        }
      }

      silenceTimerRef.current = setTimeout(checkSilence, 500);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        if (audioChunksRef.current.length === 0) {
          setMicState('idle');
          return;
        }

        setMicState('processing');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob);

        try {
          const tok = _qv2Token();
          const res = await fetch(_qv2Base() + '/api/ai/transcribe', {
            method: 'POST',
            headers: tok ? { Authorization: 'Bearer ' + tok } : {},
            body: formData,
          });

          const json = await res.json();
          if (res.ok && json.data && json.data.transcript) {
            const transcript = json.data.transcript.trim();
            setInput(transcript);
            // Auto-send
            if (transcript) {
              await send(transcript);
              // Auto-reactivate mic after patient responds
              shouldAutoReactivateRef.current = true;
            }
          } else {
            setMicErrMsg('Transcription failed');
            setMicState('error');
          }
        } catch (e) {
          setMicErrMsg('Upload failed');
          setMicState('error');
        } finally {
          if (!shouldAutoReactivateRef.current) {
            setMicState('idle');
          }
        }
      };

      mediaRecorder.start(100);
    } catch (e) {
      setMicErrMsg('Mic access denied');
      setMicState('error');
    }
  }

  function handleMicStop() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    setMicState('idle');
  }

  React.useEffect(() => {
    // Restore an in-flight session (hash routing: refresh keeps you in chat)
    // or start a fresh one.
    if (initialSessionId) {
      qv2Fetch('/api/v2/sessions/' + initialSessionId + '/turns')
        .then(d => {
          const turns = (d && d.turns) || [];
          setMessages(turns.map(t => ({ role: t.role, text: t.content || t.text || '' })));
          if (!turns.length && d && d.opening_line) setMessages([{ role: 'patient', text: d.opening_line }]);
        })
        .catch(e => setErr(String(e.message || e)));
      return;
    }
    qv2Fetch('/api/v2/sessions', { method: 'POST', body: { case_id: caseSummary.id, language: language || 'en' } })
      .then(d => {
        setSessionId(d.sessionId);
        setMessages([{ role: 'patient', text: d.openingLine || '…' }]);
        try { sessionStorage.setItem('qora_session_meta', JSON.stringify({ sessionId: d.sessionId, caseId: caseSummary.id, mode: mode, language: language || 'en' })); } catch (e) {}
        if (onSessionReady) onSessionReady(d.sessionId);
      })
      .catch(e => setErr(String(e.message || e)));
  }, [caseSummary.id]);

  React.useEffect(() => { if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Update the trailing (streaming) patient bubble in place.
  const patchPatient = (t, streaming) => setMessages(m => {
    const c = m.slice();
    for (let i = c.length - 1; i >= 0; i--) {
      if (c[i].role === 'patient') { c[i] = { role: 'patient', text: t, streaming }; break; }
    }
    return c;
  });

  async function send(textArg) {
    const text = (typeof textArg === 'string' ? textArg : input).trim();
    if (!text || busy || !sessionId) return;
    setInput(''); setBusy(true);
    setMessages(m => m.concat([{ role: 'user', text }, { role: 'patient', text: '', streaming: true }]));
    try {
      const doStream = async (retried) => {
        const tok = _qv2Token();
        const r = await fetch(_qv2Base() + '/api/v2/sessions/' + sessionId + '/turns/stream', {
          method: 'POST',
          headers: Object.assign({ 'Content-Type': 'application/json' }, tok ? { Authorization: 'Bearer ' + tok } : {}),
          body: JSON.stringify({ text }),
        });
        if (r.status === 401 && !retried && typeof window !== 'undefined' && window._qoraRefreshToken) {
          const nt = await window._qoraRefreshToken();
          if (nt) return doStream(true);
        }
        return r;
      };
      const res = await doStream(false);
      if (!res.ok || !res.body) throw new Error('HTTP ' + res.status);
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let acc = '';
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        acc += dec.decode(chunk.value, { stream: true });
        patchPatient(acc, true);
      }
      patchPatient(acc.trim() || '…', false);
    } catch (e) {
      // Fallback to the non-streaming endpoint if streaming is unavailable.
      try {
        const d = await qv2Fetch('/api/v2/sessions/' + sessionId + '/turns', { method: 'POST', body: { text } });
        patchPatient((d && d.reply) || '…', false);
      } catch (e2) {
        patchPatient('(error: ' + (e2.message || e2) + ')', false);
      }
    }
    setBusy(false);
  }

  async function score(ddx, mgmt) {
    if (!sessionId) return;
    setBusy(true);
    try { const report = await qv2Fetch('/api/v2/sessions/' + sessionId + '/score', { method: 'POST', body: { ddx, management: mgmt, mode: mode, overtime: overtime, pf_notes: pf.notes || null, pf_areas: (pf.areas && pf.areas.length) ? pf.areas : null } }); try { sessionStorage.removeItem('qora_session_meta'); } catch (e) {} onScored(report); }
    catch (e) { setErr(String(e.message || e)); setBusy(false); }
  }

  React.useEffect(() => {
    if (!timerOn || (stage !== 'chat' && stage !== 'pf')) return undefined;
    const id = setInterval(() => setSecs((s) => {
      if (s <= 1) { if (isOsce && !overtime) setTimeUp(true); return 0; }
      return s - 1;
    }), 1000);
    return () => clearInterval(id);
  }, [timerOn, stage, isOsce, overtime]);

  if (stage === 'pf') {
    return React.createElement(QV2PhysicalExam, { caseSummary, sessionId, language: language, onBack: () => setStage('chat'), onContinue: (pfData) => { setPf(pfData); setStage('assess'); } });
  }

  if (stage === 'assess') {
    return React.createElement(QV2Assess, { caseSummary, isOsce, busy, transcript: messages, onBack: () => setStage('chat'), onSubmit: score });
  }

  const mmss = String(Math.floor(secs / 60)).padStart(2, '0') + ':' + String(secs % 60).padStart(2, '0');

  const chatColumn = React.createElement('div', { style: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 140px)' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 } },
      React.createElement('button', { onClick: onExit, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '← Library'),
      React.createElement(QV2Pill, { tone: isOsce ? 'violet' : 'teal' }, isOsce ? 'OSCE' : 'Practice'),
      React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, _qv2Title(caseSummary)),
      !wide && React.createElement('button', { onClick: () => setTimerOn((v) => !v), title: 'Session timer', style: { padding: '4px 10px', borderRadius: 999, border: '1px solid var(--border)', background: timerOn ? (secs < 60 ? 'var(--red-l)' : 'var(--surface-2)') : 'var(--surface)', color: timerOn ? (secs < 60 ? 'var(--red-d)' : 'var(--text-1)') : 'var(--text-3)', fontSize: 12, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, timerOn ? ('⏱ ' + mmss) : '⏱ Timer')),
    React.createElement(QV2MediaBar, { caseId: caseSummary.id }),
    err && React.createElement('div', { style: { color: 'var(--red-d)', fontSize: 12, marginBottom: 8 } }, err),
    React.createElement('div', { style: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10, padding: '8px 2px' } },
      messages.map((m, i) => React.createElement('div', { key: i, className: 'af', style: {
        alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '78%',
        padding: '10px 14px', borderRadius: 16, fontSize: 13.5, lineHeight: 1.5,
        background: m.role === 'user' ? 'var(--primary)' : 'var(--surface)',
        color: m.role === 'user' ? '#fff' : 'var(--text-1)',
        border: m.role === 'user' ? 'none' : '1px solid var(--border)', boxShadow: 'var(--sh-xs)',
      } }, m.streaming && !m.text
        ? React.createElement('span', { className: 'qv2-typing', style: { color: 'var(--text-3)' } }, '● ● ●')
        : (m.streaming ? m.text + ' ▋' : m.text))),
      React.createElement('div', { ref: endRef })),
    React.createElement('div', { style: { padding: '12px 0 16px', display: 'flex', flexDirection: 'column', gap: 10 } },
      React.createElement('div', { style: { display: 'flex', justifyContent: 'center' } },
        React.createElement(QV2MicButton, { onTranscript: (t) => setInput(t), onAutoSend: (t) => send(t), disabled: busy, sessionLang: language, compact: isMobile })),
      React.createElement('div', { style: { display: 'flex', gap: 8 } },
        React.createElement('input', {
          value: input, onChange: e => setInput(e.target.value),
          onKeyDown: e => { if (e.key === 'Enter') send(); },
          placeholder: 'Or type a question…', disabled: busy,
          style: { flex: 1, padding: '11px 14px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13.5, fontFamily: 'Poppins', color: 'var(--text-1)' },
        }),
        React.createElement('button', { onClick: () => setStage(isOsce ? 'pf' : 'assess'), disabled: busy, style: { padding: '0 16px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, isOsce ? 'Exam →' : 'Assess →'))));

  return React.createElement('div', { style: { maxWidth: 'min(' + (wide ? 1200 : 760) + 'px, calc(100% - 16px))', margin: '0 auto', padding: isMobile ? '12px 10px 0' : '16px 16px 0', display: 'flex', gap: 20, alignItems: 'flex-start' } },
    wide && React.createElement('div', { style: { width: 240, flexShrink: 0, marginLeft: -40 } },
      React.createElement(QV2TaskPanel, { mode: mode, secs: secs, timerOn: timerOn, onToggleTimer: () => setTimerOn((v) => !v) })),
    chatColumn,
    timeUp && React.createElement(QV2TimeUpModal, {
      onFinish: () => { setTimeUp(false); setStage('assess'); },
      onContinue: () => { setTimeUp(false); setOvertime(true); },
    }));
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
  var _t = window.__t || function(k) { return k; };
  // Confetti on mount
  React.useEffect(function () {
    if (typeof window.confetti === 'function') {
      var score = report.overall || 0;
      window.confetti({ particleCount: score >= 80 ? 120 : score >= 60 ? 60 : 20, spread: score >= 80 ? 100 : 70, origin: { y: 0.6 } });
    }
  }, []);
  // map item text -> status from per_item (loose lowercase contains match)
  const statusFor = (text) => {
    const t = String(text || '').toLowerCase();
    const hit = (report.per_item || []).find(p => t && (t.includes(String(p.item || '').toLowerCase()) || String(p.item || '').toLowerCase().includes(t)));
    return hit ? hit.status : null;
  };
  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(820px, calc(100% - 16px))', margin: '0 auto', padding: '24px 16px' } },
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
    (ak.investigations && (ak.investigations.appropriate || []).length) ? React.createElement('div', { key: 'inv', style: { marginTop: 12 } },
      React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '4px 0' } }, 'Appropriate investigations'),
      (ak.investigations.appropriate || []).map((iv, i) => React.createElement('div', { key: i, style: { fontSize: 12.5, color: 'var(--text-2)', padding: '2px 0' } }, '• ' + iv.name + (iv.expected ? ' → ' + iv.expected : '')))) : null,
    (ak.management && ((ak.management.pharmacological || []).concat(ak.management.non_pharmacological || [], ak.management.education_safety_netting || [])).length) ? React.createElement('div', { key: 'mgmt', style: { marginTop: 12 } },
      React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '4px 0' } }, 'Management'),
      (ak.management.pharmacological || []).concat(ak.management.non_pharmacological || [], ak.management.education_safety_netting || []).map((m, i) => React.createElement('div', { key: i, style: { fontSize: 12.5, color: 'var(--text-2)', padding: '2px 0' } }, '• ' + m))) : null,
    // actions
    React.createElement('div', { style: { display: 'flex', gap: 10, marginTop: 22 } },
      React.createElement('button', { onClick: onAgain, style: { padding: '10px 18px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Try another case'),
      React.createElement('button', { onClick: onLibrary, style: { padding: '10px 18px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Back to library'))
  );
}

// ---- Progress / skill view (gamification, pivot-v4 §8.6) ----
function QV2SkillBar({ label, pct }) {
  return React.createElement('div', { style: { marginBottom: 8 } },
    React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-2)', fontWeight: 600, marginBottom: 3 } },
      React.createElement('span', null, label),
      React.createElement('span', null, pct + '%')),
    React.createElement('div', { style: { height: 7, borderRadius: 999, background: 'var(--surface-3)' } },
      React.createElement('div', { style: { width: pct + '%', height: '100%', borderRadius: 999, background: 'var(--primary)' } })));
}

function QV2Stat({ label, val }) {
  return React.createElement('div', { style: { flex: 1, padding: 16, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)', textAlign: 'center' } },
    React.createElement('div', { style: { fontSize: 26, fontWeight: 800, color: 'var(--primary)' } }, val),
    React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)', fontWeight: 600 } }, label));
}

// Achievements + progress-to-next (§14).
function QV2Badges({ badges }) {
  if (!badges || !badges.length) return null;
  const earned = badges.filter((b) => b.earned);
  const next = badges.filter((b) => !b.earned).sort((a, b) => b.progress - a.progress).slice(0, 3);
  return React.createElement('div', null,
    React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', margin: '4px 0 10px' } }, '🏅 Achievements (' + earned.length + '/' + badges.length + ')'),
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: next.length ? 16 : 0 } },
      earned.length ? earned.map((b) => React.createElement('div', { key: b.id, title: b.name, style: { display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 999, background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 12, fontWeight: 700 } },
        React.createElement('span', { style: { fontSize: 15 } }, b.icon), b.name))
        : React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)' } }, 'Complete a case to earn your first badge.')),
    next.length ? React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 10 } },
      next.map((b) => React.createElement('div', { key: b.id, style: { display: 'flex', alignItems: 'center', gap: 10 } },
        React.createElement('span', { style: { fontSize: 16, opacity: 0.5 } }, b.icon),
        React.createElement('div', { style: { flex: 1 } },
          React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--text-2)', fontWeight: 600, marginBottom: 2 } },
            React.createElement('span', null, b.name),
            React.createElement('span', null, Math.round(b.value) + ' / ' + b.goal)),
          React.createElement('div', { style: { height: 5, borderRadius: 999, background: 'var(--surface-3)' } },
            React.createElement('div', { style: { width: (b.progress * 100) + '%', height: '100%', borderRadius: 999, background: 'var(--primary)' } })))))) : null);
}

function QV2Progress({ onBack }) {
  const [p, setP] = React.useState(null);
  const [err, setErr] = React.useState('');
  React.useEffect(() => { qv2Fetch('/api/v2/progress').then(setP).catch((e) => setErr(String(e.message || e))); }, []);
  if (err) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } }, 'Could not load progress: ' + err);
  if (!p) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)' } }, 'Loading progress…');
  const dimLabel = { history_coverage: 'History coverage', red_flags: 'Red-flag screening', ice_fife: 'ICE / FIFE', questioning_technique: 'Questioning technique', communication: 'Communication', diagnostic_reasoning: 'Diagnostic reasoning', investigations: 'Investigation selection', management: 'Management', clinical_safety: 'Clinical safety' };
  const dims = p.dimensionAverages || {};
  const specs = p.specialtyCounts || {};
  const dimKeys = Object.keys(dims);
  const specKeys = Object.keys(specs);
  const goal = p.dailyGoal || { done: 0, target: 1 };
  const goalMet = goal.done >= goal.target;
  return React.createElement('div', { className: 'au', style: { maxWidth: 820, margin: '0 auto', padding: '24px 20px' } },
    React.createElement('button', { onClick: onBack, style: { marginBottom: 14, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '← Library'),
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 16 } }, 'Your progress'),
    // daily goal banner
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', borderRadius: 'var(--r-lg)', marginBottom: 18, background: goalMet ? 'var(--teal-l, var(--primary-l))' : 'var(--primary-ll, var(--surface-2))', border: '1px solid ' + (goalMet ? 'var(--teal, var(--primary))' : 'var(--border)') } },
      React.createElement('span', { style: { fontSize: 22 } }, goalMet ? '✅' : '🎯'),
      React.createElement('div', { style: { flex: 1 } },
        React.createElement('div', { style: { fontSize: 13.5, fontWeight: 700, color: 'var(--text-1)' } }, goalMet ? "Daily goal complete — nice work!" : 'Daily goal'),
        React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)' } }, goalMet ? 'Come back tomorrow to keep your streak alive.' : 'Complete ' + goal.target + ' case today to keep your streak going.')),
      React.createElement('div', { style: { fontSize: 13, fontWeight: 800, color: goalMet ? 'var(--teal, var(--primary))' : 'var(--primary)' } }, goal.done + ' / ' + goal.target)),
    React.createElement('div', { style: { display: 'flex', gap: 12, marginBottom: 22, flexWrap: 'wrap' } },
      React.createElement(QV2Stat, { label: 'XP', val: p.xp || 0 }),
      React.createElement(QV2Stat, { label: 'Streak', val: (p.streak || 0) + 'd' }),
      React.createElement(QV2Stat, { label: 'Sessions', val: p.totalSessions || 0 }),
      React.createElement(QV2Stat, { label: 'Cases', val: p.completedCases || 0 })),
    React.createElement('div', { style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', marginBottom: 22 } },
      React.createElement(QV2Badges, { badges: p.badges })),
    React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, 'Skill by dimension'),
    dimKeys.length
      ? dimKeys.map((k) => React.createElement(QV2SkillBar, { key: k, label: dimLabel[k] || k, pct: dims[k] }))
      : React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)' } }, 'Complete a case to see your skill breakdown.'),
    React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', margin: '20px 0 10px' } }, 'Specialty coverage'),
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8 } },
      specKeys.length
        ? specKeys.map((s) => React.createElement('span', { key: s, style: { fontSize: 12, fontWeight: 600, padding: '5px 12px', borderRadius: 999, background: 'var(--primary-l)', color: 'var(--primary)' } }, (QV2_SPEC_LABEL[s] || s) + ' · ' + specs[s]))
        : React.createElement('span', { style: { fontSize: 13, color: 'var(--text-3)' } }, 'No specialties practised yet.')));
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

// ---- Dashboard (Qora style, inspired by OphthaSim) ----
function QoraDashboard({ onNav, onStartCase }) {
  const [p, setP] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [recent, setRecent] = React.useState([]);
  const [me, setMe] = React.useState(null);
  const isMobile = useIsMobile();
  React.useEffect(() => {
    qv2Fetch('/api/v2/progress').then(setP).catch(e => setErr(String(e.message || e)));
    qv2Fetch('/api/v2/sessions?limit=5').then(d => setRecent((d && d.sessions) || [])).catch(() => {});
    qv2Fetch('/api/users/me').then(setMe).catch(() => {});
  }, []);
  const firstName = me && me.full_name ? String(me.full_name).trim().split(/\s+/)[0] : '';
  if (err) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)', textAlign: 'center' } },
    'Could not load dashboard: ' + err);
  if (!p) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)', textAlign: 'center' } }, 'Loading dashboard…');

  const level = p.level || Math.floor((p.xp || 0) / 200) + 1;
  const levelProgress = ((p.xp || 0) % 200) / 200 * 100;
  const levelNames = ['Student','Intern','Resident','Senior Resident','Consultant','Specialist','Senior Specialist','Professor'];
  const levelName = levelNames[Math.min(level - 1, levelNames.length - 1)] || 'Student';
  const totalSessions = p.totalSessions || 0;
  const completedCases = p.completedCases || 0;
  const dims = p.dimensionAverages || {};
  const hasDims = Object.keys(dims).length > 0;
  const specs = p.specialtyCounts || {};
  const specKeys = Object.keys(specs);
  const avgScore = hasDims ? Math.round(Object.values(dims).reduce((a, b) => a + b, 0) / Object.keys(dims).length) : 0;

  // Recent sessions helper
  const specLabel = { internal_medicine: 'Internal medicine', surgery: 'Surgery', paediatrics: 'Paediatrics', obstetrics_gynaecology: 'Obs & Gynae', psychiatry: 'Psychiatry', neurology: 'Neurology', ent: 'ENT', dermatology: 'Dermatology', ophthalmology: 'Ophthalmology', emergency: 'Emergency' };

  return React.createElement('div', { style: { maxWidth: 'min(1100px, calc(100% - 16px))', margin: '0 auto', padding: isMobile ? '20px 10px 60px' : '32px 24px 60px' } },
    // Hero
    React.createElement('div', { className: 'au', style: {
      background: 'linear-gradient(135deg, var(--primary) 0%, #7C3AED 100%)',
      borderRadius: 24, padding: isMobile ? '26px 20px' : '36px 40px', marginBottom: 28,
      position: 'relative', overflow: 'hidden', color: '#fff',
    }},
      React.createElement('div', { style: { position: 'absolute', right: -60, top: -60, width: 320, height: 320, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.08)' } }),
      React.createElement('div', { style: { position: 'absolute', right: -20, top: -20, width: 220, height: 220, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.12)' } }),
      React.createElement('div', { style: { position: 'absolute', right: 40, top: 20, width: 140, height: 140, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.15)' } }),
      React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative', flexDirection: isMobile ? 'column' : 'row', gap: 18 } },
        React.createElement('div', { style: { maxWidth: 520, minWidth: 0 } },
          React.createElement('div', { style: { display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.15)', borderRadius: 10, padding: '5px 12px', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16, backdropFilter: 'blur(8px)' } },
            React.createElement('span', { style: { fontSize: 13 } }, '👨‍⚕️'), ' Clinical Interview Trainer'),
          React.createElement('h1', { style: { fontSize: 'clamp(24px, 7vw, 30px)', fontWeight: 800, lineHeight: 1.2, marginBottom: 10 } },
            'Welcome back' + (firstName ? ', ' + firstName : '') + '! 👋'),
          React.createElement('p', { style: { fontSize: 14, opacity: 0.82, marginBottom: 28, lineHeight: 1.6 } },
            'Practise taking a structured history across every specialty. Each virtual patient brings a new clinical challenge.'),
          React.createElement('div', { style: { display: 'flex', gap: 12, flexWrap: 'wrap' } },
            React.createElement('button', { onClick: () => onNav('cases'), style: { padding: '11px 22px', borderRadius: 12, border: 'none', background: '#fff', color: 'var(--primary)', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.15)' } }, '▶ Start new case'),
            completedCases > 0 && React.createElement('button', { onClick: () => onNav('cases'), style: { padding: '11px 22px', borderRadius: 12, border: '1.5px solid rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.9)', fontSize: 14, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Continue practising'))),
        // XP card
        React.createElement('div', { style: { background: 'rgba(255,255,255,0.12)', backdropFilter: 'blur(12px)', borderRadius: 20, padding: '18px 22px', minWidth: isMobile ? 0 : 200, width: isMobile ? '100%' : 'auto', border: '1px solid rgba(255,255,255,0.2)' } },
          React.createElement('div', { style: { fontSize: 11, opacity: 0.7, fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.07em' } }, 'Your Progress'),
          React.createElement('div', { style: { fontSize: 28, fontWeight: 800, lineHeight: 1 } }, 'Lv ' + level),
          React.createElement('div', { style: { fontSize: 12, opacity: 0.75, marginBottom: 14 } }, levelName),
          React.createElement('div', { style: { background: 'rgba(255,255,255,0.2)', borderRadius: 999, height: 6, marginBottom: 6 } },
            React.createElement('div', { style: { height: '100%', borderRadius: 999, background: '#fff', width: levelProgress + '%', transition: 'width 1s var(--ease-panel)' } })),
          React.createElement('div', { style: { fontSize: 11, opacity: 0.65, textAlign: 'right' } }, (p.xp || 0) + ' XP')))),

    // Stats Row
    React.createElement('div', { className: 'au', style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(150px, 100%), 1fr))', gap: 12, marginBottom: 24 } },
      React.createElement(QDStat, { label: 'Cases completed', value: completedCases, icon: '📋', color: 'var(--primary)', sub: 'across ' + specKeys.length + ' specialties' }),
      React.createElement(QDStat, { label: 'Total sessions', value: totalSessions, icon: '🔥', color: 'var(--amber)', sub: 'practice encounters' }),
      React.createElement(QDStat, { label: 'Avg score', value: avgScore + '%', icon: '📈', color: 'var(--teal)', sub: hasDims ? 'across all dimensions' : 'complete a case to see' }),
      React.createElement(QDStat, { label: 'Streak', value: p.streak ? p.streak + 'd' : '0d', icon: '🏅', color: 'var(--gold)', sub: p.streak ? 'days in a row' : 'start your streak' })),

    // Two-column: Recent + Specialties
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(320px, 100%), 1fr))', gap: 20 } },
      // Recent Activity
      React.createElement('div', null,
        React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' } },
          React.createElement('span', null, '\uD83D\uDCCB ' + _t('dashboard.recent_sessions')),
          recent.length > 0 && React.createElement('button', { onClick: () => onNav('sessions'), style: { padding: '4px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 11, color: 'var(--primary)', fontFamily: 'Poppins', cursor: 'pointer', fontWeight: 600 } }, _t('dashboard.browse_cases'))),
        recent.length === 0 && React.createElement('div', { style: { padding: '28px 20px', textAlign: 'center', fontSize: 13, color: 'var(--text-3)', background: 'var(--surface)', borderRadius: 16, border: '1px dashed var(--border)' } },
          'Complete your first case to see activity here.'),
        React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
          recent.slice(0, 5).map((s, i) => React.createElement('div', { key: s.sessionId || i, className: 'as', style: { display: 'flex', alignItems: 'center', gap: 14, padding: 14, borderRadius: 14, background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-xs)' } },
            React.createElement('div', { style: { width: 42, height: 42, borderRadius: 12, background: 'var(--primary-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 } },
              s.specialty === 'emergency' ? '🚑' : s.specialty === 'surgery' ? '🔪' : s.specialty === 'paediatrics' ? '👶' : s.specialty === 'psychiatry' ? '🧠' : s.specialty === 'ophthalmology' ? '👁' : '🩺'),
            React.createElement('div', { style: { flex: 1, minWidth: 0 } },
              React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 2 } }, s.presentation || 'Case'),
              React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, (specLabel[s.specialty] || s.specialty) + (s.score != null ? ' · Score: ' + s.score : ' · In progress'))))))),

      // Right column: specialties + dimensions + radar
      React.createElement('div', null,
        // Skill radar chart
        hasDims && React.createElement('div', { className: 'as', style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)', marginBottom: 16 } },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12, textAlign: 'center' } }, '\uD83D\uDCCA ' + _t('dashboard.skill_breakdown')),
          React.createElement(QSkillRadar, { dims: dims, size: 200 })),
        // Achievements
        (p.badges && p.badges.some((b) => b.earned)) ? React.createElement('div', { className: 'as', style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', marginBottom: 16 } },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, '🏅 Achievements'),
          React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8 } },
            p.badges.filter((b) => b.earned).slice(0, 10).map((b) => React.createElement('span', { key: b.id, title: b.name, style: { fontSize: 20 } }, b.icon)))) : null,
        // Specialty coverage
        React.createElement('div', { className: 'as', style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', marginBottom: 16 } },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, '🎯 Specialty coverage'),
          specKeys.length === 0 && React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)' } }, 'No specialties practised yet.'),
          React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6 } },
            specKeys.map(s => React.createElement('span', { key: s, style: { fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 999, background: 'var(--primary-l)', color: 'var(--primary)' } },
              (specLabel[s] || s) + ' · ' + specs[s])))),
        // Skill dimensions
        hasDims && React.createElement('div', { className: 'as', style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)' } },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, '📊 Skill breakdown'),
          Object.keys(dims).map(k => {
            const dimLabel = { history_coverage: 'History', red_flags: 'Red flags', ice_fife: 'ICE/FIFE', questioning_technique: 'Questioning', communication: 'Communication', diagnostic_reasoning: 'Reasoning', investigations: 'Investigations', management: 'Management', clinical_safety: 'Safety' };
            const pct = dims[k];
            return React.createElement('div', { key: k, style: { marginBottom: 8 } },
              React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-2)', fontWeight: 600, marginBottom: 2 } },
                React.createElement('span', null, dimLabel[k] || k),
                React.createElement('span', null, Math.round(pct) + '%')),
              React.createElement('div', { style: { height: 5, borderRadius: 999, background: 'var(--surface-3)' } },
                React.createElement('div', { style: { width: pct + '%', height: '100%', borderRadius: 999, background: 'var(--primary)', transition: 'width 0.6s ease' } })));
          })))));
}

function QDStat({ label, value, icon, color, sub }) {
  return React.createElement('div', { className: 'as', style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)' } },
    React.createElement('div', { style: { fontSize: 22, marginBottom: 6 } }, icon),
    React.createElement('div', { style: { fontSize: 24, fontWeight: 800, color } }, value),
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-1)', marginTop: 1 } }, label),
    React.createElement('div', { style: { fontSize: 10, color: 'var(--text-3)', marginTop: 2 } }, sub));
}

function QoraV2Screen() {
  const [view, setView] = React.useState('catalogue'); // catalogue | setup | session | result | progress
  const [picked, setPicked] = React.useState(null);
  const [sessionMode, setSessionMode] = React.useState('practice');
  const [sessionLanguage, setSessionLanguage] = React.useState('en');
  const [report, setReport] = React.useState(null);
  const [initialSessionId, setInitialSessionId] = React.useState(null);
  const [onboard, setOnboard] = React.useState(() => { try { return !localStorage.getItem('qora_onboarded'); } catch (e) { return true; } });
  const dismiss = () => { try { localStorage.setItem('qora_onboarded', '1'); } catch (e) {} setOnboard(false); };

  // ── Hash routing (Aug 2026): every screen has a URL so refresh/back keep
  //    your place — #/cases, #/cases/<id>, #/session/<sid>, #/result, #/progress.
  function setHash(path) {
    try { var want = '#/' + path; if (location.hash !== want) location.hash = want; } catch (e) {}
  }
  function hashParts() {
    try { return (location.hash || '').replace(/^#\/?/, '').split('/').filter(Boolean); } catch (e) { return []; }
  }

  const applyRoute = React.useCallback(function (parts) {
    var p0 = parts[0], p1 = parts[1];
    if (p0 === 'session' && p1) {
      var meta = null;
      try { meta = JSON.parse(sessionStorage.getItem('qora_session_meta') || 'null'); } catch (e) {}
      setInitialSessionId(p1);
      var cid = (meta && meta.caseId) || null;
      var fetchCase = function (caseId, lang) {
        qv2Fetch('/api/v2/cases/' + caseId).then(function (d) { setPicked(d); if (lang) setSessionLanguage(lang); if (meta && meta.mode) setSessionMode(meta.mode); setView('session'); }).catch(function () { setView('catalogue'); setHash('cases'); });
      };
      if (cid) { fetchCase(cid, (meta && meta.language) || 'en'); }
      else {
        qv2Fetch('/api/v2/sessions/' + p1 + '/turns').then(function (d) { if (d && d.case_id) fetchCase(d.case_id, d.language || 'en'); else throw new Error('no case'); }).catch(function () { setView('catalogue'); setHash('cases'); });
      }
      return;
    }
    if (p0 === 'cases' && p1) {
      qv2Fetch('/api/v2/cases/' + p1).then(function (d) { setPicked(d); setReport(null); setView('setup'); }).catch(function () { setView('catalogue'); setHash('cases'); });
      return;
    }
    if (p0 === 'result') {
      var saved = null;
      try { saved = JSON.parse(sessionStorage.getItem('qora_last_report') || 'null'); } catch (e) {}
      if (saved && saved.report && saved.caseId) {
        qv2Fetch('/api/v2/cases/' + saved.caseId).then(function (d) { setPicked(d); setReport(saved.report); setView('result'); }).catch(function () { setView('catalogue'); setHash('cases'); });
      } else { setView('catalogue'); setHash('cases'); }
      return;
    }
    if (p0 === 'progress') { setView('progress'); return; }
    setView('catalogue');
  }, []);

  React.useEffect(function () { applyRoute(hashParts()); }, []);
  React.useEffect(function () {
    var fn = function () { applyRoute(hashParts()); };
    window.addEventListener('hashchange', fn);
    return function () { window.removeEventListener('hashchange', fn); };
  }, [applyRoute]);

  let body;
  if (view === 'setup' && picked) {
    body = React.createElement(QV2SessionSetup, { caseSummary: picked, onStart: (opts) => { setSessionMode(opts.mode); setSessionLanguage(opts.language || 'en'); setReport(null); setInitialSessionId(null); setView('session'); }, onBack: () => { setView('catalogue'); setHash('cases'); } });
  } else if (view === 'session' && picked) {
    body = React.createElement(QV2Session, { caseSummary: picked, mode: sessionMode, language: sessionLanguage, initialSessionId: initialSessionId, onSessionReady: (sid) => setHash('session/' + sid), onScored: (r) => { setReport(r); try { sessionStorage.setItem('qora_last_report', JSON.stringify({ report: r, caseId: picked.id })); } catch (e) {} setView('result'); setHash('result'); }, onExit: () => { try { sessionStorage.removeItem('qora_session_meta'); } catch (e) {} setView('catalogue'); setHash('cases'); } });
  } else if (view === 'result' && report && picked) {
    body = React.createElement(QV2Result, { report, caseSummary: picked, onAgain: () => { try { sessionStorage.removeItem('qora_last_report'); } catch (e) {} setView('catalogue'); setHash('cases'); }, onLibrary: () => { try { sessionStorage.removeItem('qora_last_report'); } catch (e) {} setView('catalogue'); setHash('cases'); } });
  } else if (view === 'progress') {
    body = React.createElement(QV2Progress, { onBack: () => { setView('catalogue'); setHash('cases'); } });
  } else {
    body = React.createElement(QV2Catalogue, { onPick: (c) => { setPicked(c); setReport(null); setInitialSessionId(null); setView('setup'); setHash('cases/' + c.id); }, onProgress: () => { setView('progress'); setHash('progress'); } });
  }
  return React.createElement(React.Fragment, null, onboard ? React.createElement(QV2Onboarding, { onDone: dismiss }) : null, body);
}

// ---- User profile (view + edit) ----
const QP_AVATARS = ['👤', '🧑‍⚕️', '👩‍⚕️', '👨‍⚕️', '🩺', '🧠', '👁️', '🫀', '🦴', '🧬', '⚕️', '🎓'];
const QP_COLORS = ['#5865F2', '#7C3AED', '#0EA5E9', '#10B981', '#F59E0B', '#EF4444', '#EC4899', '#14B8A6'];

function QP_Field({ label, value, set, ph }) {
  return React.createElement('label', { style: { display: 'block', marginBottom: 14 } },
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 5 } }, label),
    React.createElement('input', {
      value: value || '', onChange: (e) => set(e.target.value), placeholder: ph,
      style: { width: '100%', padding: '11px 13px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Poppins', color: 'var(--text-1)' },
    }));
}

function QoraProfile({ onNav }) {
  const [me, setMe] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  var _t = window.__t || function(k) { return k; };
  const [form, setForm] = React.useState({ full_name: '', school: '', year: '', avatar_emoji: '👤', avatar_color: '#5865F2' });
  React.useEffect(() => {
    qv2Fetch('/api/users/me')
      .then((d) => { setMe(d); setForm({ full_name: d.full_name || '', school: d.school || '', year: d.year || '', avatar_emoji: d.avatar_emoji || '👤', avatar_color: d.avatar_color || '#5865F2' }); })
      .catch((e) => setErr(String(e.message || e)));
  }, []);
  const set = (k) => (v) => { setForm((f) => Object.assign({}, f, { [k]: v })); setSaved(false); };
  async function save() {
    setSaving(true); setErr('');
    try { const d = await qv2Fetch('/api/users/me', { method: 'PATCH', body: form }); setMe(d); setSaved(true); }
    catch (e) { setErr(String(e.message || e)); }
    setSaving(false);
  }
  if (err && !me) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } }, _t('common.error') + ': ' + err);
  if (!me) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)' } }, _t('common.loading'));
  const level = Math.floor((me.xp || 0) / 200) + 1;
  return React.createElement('div', { className: 'au', style: { maxWidth: 720, margin: '0 auto', padding: '28px 20px 60px' } },
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 18 } }, _t('profile.title')),
    React.createElement('div', { className: 'as', style: { display: 'flex', alignItems: 'center', gap: 16, padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)', marginBottom: 18 } },
      React.createElement('div', { style: { width: 64, height: 64, borderRadius: '50%', background: form.avatar_color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 30, flexShrink: 0 } }, form.avatar_emoji),
      React.createElement('div', { style: { flex: 1, minWidth: 0 } },
        React.createElement('div', { style: { fontSize: 17, fontWeight: 800, color: 'var(--text-1)' } }, form.full_name || 'Unnamed'),
        React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)' } }, me.email),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)', marginTop: 2, textTransform: 'capitalize' } }, me.role))),
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 } },
      [['XP', me.xp || 0], ['Level', level], ['Streak', (me.streak || 0) + 'd'], ['Sessions', me.total_sessions || 0]].map(([lab, val]) =>
        React.createElement(QV2Stat, { key: lab, label: lab, val: val }))),
    React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, _t('profile.edit')),
    React.createElement(QP_Field, { label: _t('profile.name'), value: form.full_name, set: set('full_name'), ph: 'Your name' }),
    React.createElement(QP_Field, { label: _t('profile.school'), value: form.school, set: set('school'), ph: 'e.g. University of ...' }),
    React.createElement(QP_Field, { label: _t('profile.year'), value: form.year, set: set('year'), ph: 'e.g. Year 4 / Clerkship' }),
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', margin: '4px 0 6px' } }, 'Avatar'),
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 } },
      QP_AVATARS.map((em) => React.createElement('button', { key: em, onClick: () => set('avatar_emoji')(em), style: { width: 40, height: 40, borderRadius: 10, fontSize: 20, cursor: 'pointer', background: form.avatar_emoji === em ? 'var(--primary-l)' : 'var(--surface)', border: '1px solid ' + (form.avatar_emoji === em ? 'var(--primary)' : 'var(--border)') } }, em))),
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 } },
      QP_COLORS.map((col) => React.createElement('button', { key: col, onClick: () => set('avatar_color')(col), 'aria-label': 'Avatar colour ' + col, style: { width: 30, height: 30, borderRadius: '50%', background: col, cursor: 'pointer', border: form.avatar_color === col ? '3px solid var(--text-1)' : '2px solid var(--surface)', boxShadow: '0 0 0 1px var(--border)' } }))),
    err && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--red-d)', marginBottom: 12 } }, err),
    React.createElement('div', { style: { display: 'flex', gap: 10, alignItems: 'center' } },
      React.createElement('button', { onClick: save, disabled: saving, style: { padding: '11px 22px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: saving ? 0.7 : 1 } }, saving ? 'Saving\u2026' : _t('common.save')),
      React.createElement('button', { onClick: () => onNav && onNav('dashboard'), style: { padding: '11px 18px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, _t('common.back')),
      saved && React.createElement('span', { style: { fontSize: 12.5, color: 'var(--teal, var(--primary))', fontWeight: 600 } }, '\u2713 ' + _t('common.save') + 'd')));
}

// ---- Pricing / upgrade (Midtrans Snap primary, Xendit fallback; §7.3) ----
const QORA_PLAN_FEATURES = {
  free: ['A few free cases each month', 'Preview every specialty', 'Instant scoring + answer key'],
  monthly: ['Unlimited practice (fair use)', 'Full case library, all specialties', 'OSCE mode, timer & task panel', 'Full model-answer reveal', 'Progress, streaks & badges'],
  annual: ['Everything in Monthly', 'Best value vs paying monthly', 'Priority access to new cases'],
  exam_pass: ['Unlimited practice for one month', 'Built for exam season', 'Full OSCE arc + answer keys'],
};
const QORA_PLAN_BADGE = { annual: 'Best value', exam_pass: 'Exam season' };

// Load Midtrans Snap.js once (sandbox or production depends on the client key origin).
function _loadSnap() {
  return new Promise(function (resolve, reject) {
    if (window.snap && window.snap.pay) return resolve();
    var existing = document.getElementById('midtrans-snap-script');
    if (existing) {
      var iv = setInterval(function () {
        if (window.snap && window.snap.pay) { clearInterval(iv); resolve(); }
      }, 100);
      setTimeout(function () { clearInterval(iv); reject(new Error('Snap load timeout')); }, 8000);
      return;
    }
    var sc = document.createElement('script');
    sc.src = 'https://app.midtrans.com/snap/snap.js';
    sc.async = true; sc.defer = true; sc.id = 'midtrans-snap-script';
    sc.onload = function () { resolve(); };
    sc.onerror = function () { reject(new Error('Failed to load Snap')); };
    document.head.appendChild(sc);
  });
}

function QoraPricing({ onNav }) {
  const [data, setData] = React.useState(null); // {plans, provider, billing_enforced}
  const [me, setMe] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [busy, setBusy] = React.useState('');
  React.useEffect(() => {
    qv2Fetch('/api/billing/plans').then(setData).catch((e) => setErr(String(e.message || e)));
    qv2Fetch('/api/billing/me').then(setMe).catch(() => {});
  }, []);
  async function upgrade(planId) {
    setBusy(planId); setErr('');
    try {
      // Primary: Midtrans Snap popup (Indonesia).
      try {
        const r = await qv2Fetch('/api/billing/midtrans/checkout/' + planId, { method: 'POST' });
        if (r && r.snap_token) {
          await _loadSnap();
          if (window.snap && window.snap.pay) {
            window.snap.pay(r.snap_token, {
              onSuccess: function () { window.location.href = '/billing/success'; },
              onPending: function () { setErr('Payment pending — complete it to activate your plan.'); setBusy(''); },
              onError: function () { setErr('Payment failed — please try again.'); setBusy(''); },
              onClose: function () { setBusy(''); },
            });
            return;
          }
          // No Snap (blocked?) -> fall through to redirect_url
          if (r.redirect_url) { window.location.href = r.redirect_url; return; }
        }
      } catch (e) {
        if (!/not configured|503/i.test(String((e && e.message) || e))) throw e;
        // Midtrans not configured -> fall back to Xendit below.
      }
      // Fallback: Xendit hosted invoice.
      const r2 = await qv2Fetch('/api/billing/xendit/checkout/' + planId, { method: 'POST' });
      if (r2 && r2.checkout_url) { window.location.href = r2.checkout_url; return; }
      setErr('Checkout is not available yet.');
    } catch (e) {
      setErr(/not configured|503/i.test(String(e.message || e)) ? 'Payments are not enabled yet — check back soon.' : String(e.message || e));
    }
    setBusy('');
  }
  if (err && !data) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)' } }, 'Could not load plans: ' + err);
  if (!data) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)' } }, 'Loading plans…');
  const plans = data.plans || [];
  const paymentsLive = !!data.provider;
  const currentPlan = (me && me.plan) || 'free';
  return React.createElement('div', { className: 'au', style: { maxWidth: 980, margin: '0 auto', padding: '28px 20px 60px' } },
    onNav && React.createElement('button', { onClick: () => onNav('dashboard'), style: { marginBottom: 16, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '← Back'),
    React.createElement('div', { style: { textAlign: 'center', marginBottom: 6 } },
      React.createElement('div', { style: { fontSize: 26, fontWeight: 800, color: 'var(--text-1)' } }, 'Practise without limits'),
      React.createElement('div', { style: { fontSize: 14, color: 'var(--text-2)', marginTop: 6 } }, 'Upgrade for unlimited cases across every specialty.')),
    !data.billing_enforced && React.createElement('div', { style: { textAlign: 'center', fontSize: 12.5, color: 'var(--text-3)', marginBottom: 18 } }, 'Everything is currently unlocked while Qora is in beta.'),
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 16, marginTop: 22 } },
      plans.map((p) => {
        const isCurrent = p.id === currentPlan;
        const isFree = p.id === 'free';
        const badge = QORA_PLAN_BADGE[p.id];
        const feats = QORA_PLAN_FEATURES[p.id] || [];
        const featured = p.id === 'annual';
        return React.createElement('div', { key: p.id, className: 'as', style: {
          position: 'relative', display: 'flex', flexDirection: 'column', padding: 22, borderRadius: 'var(--r-xl)',
          background: 'var(--surface)', boxShadow: featured ? 'var(--sh-lg)' : 'var(--sh-sm)',
          border: '2px solid ' + (featured ? 'var(--primary)' : 'var(--border)'),
        } },
          badge && React.createElement('div', { style: { position: 'absolute', top: -11, left: 22, fontSize: 10, fontWeight: 800, letterSpacing: '0.05em', textTransform: 'uppercase', color: '#fff', background: 'var(--primary)', padding: '3px 10px', borderRadius: 999 } }, badge),
          React.createElement('div', { style: { fontSize: 15, fontWeight: 800, color: 'var(--text-1)', marginBottom: 8 } }, p.label),
          React.createElement('div', { style: { display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 4 } },
            React.createElement('span', { style: { fontSize: 30, fontWeight: 800, color: 'var(--text-1)' } }, isFree ? 'Free' : (p.display_price || ('$' + p.price))),
            !isFree && React.createElement('span', { style: { fontSize: 12, color: 'var(--text-3)' } }, p.interval === 'year' ? '/ year' : p.interval === 'one_time' ? 'one-off' : '/ month')),
          React.createElement('div', { style: { flex: 1, margin: '12px 0' } },
            feats.map((f, i) => React.createElement('div', { key: i, style: { display: 'flex', gap: 8, fontSize: 12.5, color: 'var(--text-2)', padding: '3px 0', lineHeight: 1.4 } },
              React.createElement('span', { style: { color: 'var(--primary)', fontWeight: 700 } }, '✓'), f))),
          isCurrent
            ? React.createElement('button', { disabled: true, style: { padding: 11, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-3)', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'default' } }, 'Current plan')
            : isFree
              ? React.createElement('button', { disabled: true, style: { padding: 11, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-3)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'default' } }, 'Included')
              : React.createElement('button', { onClick: () => upgrade(p.id), disabled: busy === p.id || !paymentsLive, title: paymentsLive ? '' : 'Payments coming soon', style: { padding: 11, borderRadius: 12, border: 'none', background: paymentsLive ? 'var(--primary)' : 'var(--surface-2)', color: paymentsLive ? '#fff' : 'var(--text-3)', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: paymentsLive ? 'pointer' : 'default' } }, busy === p.id ? 'Redirecting…' : paymentsLive ? 'Upgrade' : 'Coming soon'));
      })),
    err && React.createElement('div', { style: { textAlign: 'center', fontSize: 12.5, color: 'var(--red-d)', marginTop: 16 } }, err),
    React.createElement('div', { style: { textAlign: 'center', fontSize: 11, color: 'var(--text-3)', marginTop: 24 } }, 'Secure checkout via Xendit. A study aid, not a medical device.'));
}

window.QoraV2Screen = QoraV2Screen;
window.QoraDashboard = QoraDashboard;
window.QoraProfile = QoraProfile;
window.QoraPricing = QoraPricing;
