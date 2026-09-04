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
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), opts.timeout || 30000);
  let res;
  try {
    res = await fetch(_qv2Base() + path, {
      method: opts.method || 'GET', headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
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

// Fase 5 §35 — fire a pilot behavioural event (fire-and-forget, never blocks UI).
function _pilotEvent(event, extra) {
  try {
    if (typeof window === 'undefined') return;
    qv2Fetch('/api/v2/pilot/events', { method: 'POST', timeout: 8000,
      body: Object.assign({ event: event }, extra || {}) }).catch(function () {});
  } catch (e) { /* analytics must never break the app */ }
}

// ============================================================
// Qora logo (GDV identity) + line icon set (GDV §7)
// ============================================================
function QoraLogo({ h }) {
  return React.createElement('svg', { width: h * 2.6, height: h, viewBox: '-58 -58 190 160', xmlns: 'http://www.w3.org/2000/svg', 'aria-label': 'Qora', style: { display: 'block' } },
    React.createElement('path', { d: 'M -7.6 43.3 A 44 44 0 0 1 7.6 -43.3', fill: 'none', stroke: '#9A76DB', 'stroke-width': 6 }),
    React.createElement('circle', { cx: 0, cy: 0, r: 30, fill: 'none', stroke: '#5C3F96', 'stroke-width': 13 }),
    React.createElement('circle', { cx: 0, cy: 0, r: 10, fill: 'none', stroke: '#C97A15', 'stroke-width': 4 }),
    React.createElement('path', { d: 'M 18 18 C 36 34 44 44 44 56', fill: 'none', stroke: '#5C3F96', 'stroke-width': 13 }),
    React.createElement('circle', { cx: 42, cy: 78, r: 9, fill: '#9A76DB' }),
    React.createElement('text', { x: 41, y: 16, fill: '#5C3F96', 'font-family': "'Plus Jakarta Sans',sans-serif", style: { fontSize: 46, fontWeight: 700, letterSpacing: '-0.5px' } }, 'ora'));
}

// GDV §7 line icons — 24×24 grid, 1.75 stroke, rounded caps. Colour u700.
const QICON_PATHS = {
  settings: 'M12 3.5a8.5 8.5 0 0 1 8.5 8.5 8.5 8.5 0 0 1-8.5 8.5 8.5 8.5 0 0 1-8.5-8.5 8.5 8.5 0 0 1 8.5-8.5zM12 9.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z',
  home: 'M4 11.5 12 4.5l8 7v8a1 1 0 0 1-1 1h-4.5v-5h-5v5H5a1 1 0 0 1-1-1z',
  cases: 'M5 3.5h14a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-15a1 1 0 0 1 1-1zM9 8.5h6M9 12.5h6M9 16.5h4',
  mentor: 'M12 4v7l4.5 3M4.5 12a7.5 7.5 0 1 0 3-6M4.5 4v4H8.5',
  history: 'M12 4v8l5 3M4.5 12a7.5 7.5 0 1 0 3-6M4.5 4v4H8.5',
  user: 'M12 4.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7zM5.5 19.5c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6',
  back: 'M15 5.5 8.5 12 15 18.5',
  forward: 'M9 5.5 15.5 12 9 18.5',
  check: 'M4.5 12.5 9.5 17.5 19.5 7.5',
  close: 'M6 6l12 12M18 6 6 18',
  plus: 'M12 5v14M5 12h14',
  clock: 'M12 5a7 7 0 1 1 0 14 7 7 0 0 1 0-14zM12 8v4.5l3 2',
  important: 'M12 5a7 7 0 1 1 0 14 7 7 0 0 1 0-14zM12 8.5V12M12 15h.01',
  search: 'M10.5 4.5a6 6 0 1 1 0 12 6 6 0 0 1 0-12zM15.5 15.5 20 20',
  mic: 'M12 3.5a3.5 3.5 0 0 1 3.5 3.5v4.5a3.5 3.5 0 0 1-7 0V7a3.5 3.5 0 0 1 3.5-3.5zM5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V20',
  play: 'M8 5.5 18.5 12 8 18.5z',
  pause: 'M8.5 5.5v13M15.5 5.5v13',
  send: 'M4.5 12 19.5 4.5 15.5 19.5 12 13.5z',
  award: 'M12 3.5 14.6 9l6 .9-4.3 4.2 1 6-5.3-2.8L6.7 20l1-6L3.4 9.9 9.4 9z',
  streak: 'M6 20v-6M12 20V9M18 20v-8',
  flame: 'M12 3.5c3.5 2.5 5 5 5 8.5a5 5 0 0 1-10 0c0-1.8.6-3.2 1.6-4.6.6 1.2 1.5 2 2.4 2.1V6.5c0-1-.9-2.4-1.2-3z',
  chart: 'M6 20v-6M12 20V9M18 20v-8',
  target: 'M12 4.5a7.5 7.5 0 1 1 0 15 7.5 7.5 0 0 1 0-15zM12 8.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7zM12 11.5a.5.5 0 1 1 0 1 .5.5 0 0 1 0-1z',
  flag: 'M6 21V4.5M6 5c4 0 4 3 8 3 4 0 4-3 8-3v11c-4 0-4 3-8 3-4 0-4-3-8-3',
  star: 'M12 4 14.5 9l5.5.8-4 3.9.9 5.5L12 17.5 7.1 19.2 8 13.7 4 9.8 9.5 9z',
  spark: 'M12 4v3M12 17v3M4 12h3M17 12h3M6.5 6.5l2 2M15.5 15.5l2 2M17.5 6.5l-2 2M8.5 15.5l-2 2',
  lock: 'M7.5 10V8.5a4.5 4.5 0 0 1 9 0V10M6 10h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1z',
  camera: 'M4.5 7.5h3l2-2h5l2 2h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1zM12 11a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z',
  trophy: 'M8 4.5h8V14a4 4 0 0 1-8 0zM8 6H5.5a1 1 0 0 0-1 1 3.5 3.5 0 0 0 3.5 3.5M16 6h2.5a1 1 0 0 1 1 1 3.5 3.5 0 0 1-3.5 3.5M12 18v2.5M8 21.5h8',
};
function QIcon({ n, s, color }) {
  var d = QICON_PATHS[n] || '';
  if (!d) return React.createElement('span', { style: { fontSize: s || 18 } }, '•');
  return React.createElement('svg', { width: s || 20, height: s || 20, viewBox: '0 0 24 24', fill: 'none', stroke: color || 'currentColor', strokeWidth: 1.75, strokeLinecap: 'round', strokeLinejoin: 'round', style: { flexShrink: 0 } },
    React.createElement('path', { d: d }));
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
  const [q, setQ] = React.useState('');
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

  const _qq = (q || '').toLowerCase().trim();
  const shown = cases.filter(c => (!filter || c.specialty === filter) && (!diff || String(c.difficulty) === String(diff)) && (!_qq || ((c.presentation || '') + ' ' + (c.first_impression || '') + ' ' + (c.first_impression_id || '') + ' ' + (c.specialty || '')).toLowerCase().includes(_qq)));
  const DIFF_LABEL = { '1': _t('cases.difficulty_1'), '2': _t('cases.difficulty_2'), '3': _t('cases.difficulty_3') };
  return React.createElement('div', { style: { maxWidth: 'min(1080px, calc(100% - 24px))', margin: '0 auto', padding: '24px 16px' } },
    // GDV §4: pita suasana "Senja" — siluet rak arsip
    React.createElement(QAMoodBand, { scene: 'senja', kicker: (specs.length ? specs.length + ' SPECIALTIES' : 'CASE LIBRARY'),
      title: _t('cases.title'),
      sub: shown.length + (shown.length === cases.length ? '' : ' of ' + cases.length) + ' cases across ' + specs.length + ' specialties',
      children: onProgress && React.createElement('button', { onClick: onProgress, style: { marginTop: 14, padding: '8px 16px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.42)', background: 'rgba(255,255,255,0.16)', color: '#fff', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', backdropFilter: 'blur(10px)', display: 'inline-flex', alignItems: 'center', gap: 6 } }, React.createElement(QIcon, { n: 'chart', s: 15 }), _t('dashboard.your_progress')) }),
    // Filter chips overlap the mood band
    React.createElement('div', { className: 'au', style: { position: 'relative', zIndex: 5, marginTop: -56 } },
      // search (existing visual language: rounded surface input; keeps 100+ families usable)
      React.createElement('div', { style: { marginBottom: 10 } },
        React.createElement('input', { value: q, onChange: (e) => setQ(e.target.value), placeholder: 'Search cases…',
          style: { width: '100%', padding: '9px 14px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } })),
      // specialty filter chips
      React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 } },
        [['', _t('cases.filter_all')]].concat(specs.map(s => [s, _qv2SpecLabel(s)])).map(([val, lab]) =>
          React.createElement('button', { key: val || 'all', onClick: () => setFilter(val), style: {
            padding: '6px 14px', borderRadius: 999, fontSize: 12.5, fontWeight: filter === val ? 700 : 500,
            fontFamily: 'Plus Jakarta Sans', cursor: 'pointer',
            border: '1px solid ' + (filter === val ? 'var(--primary)' : 'var(--border)'),
            background: filter === val ? 'var(--primary-l)' : 'var(--surface)',
            color: filter === val ? 'var(--primary)' : 'var(--text-2)',
          } }, lab))),
    // difficulty filter chips
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 } },
      [['', _t('cases.filter_all') + ' ' + _t('cases.title')], ['1', _t('cases.difficulty_1')], ['2', _t('cases.difficulty_2')], ['3', _t('cases.difficulty_3')]].map(([val, lab]) =>
        React.createElement('button', { key: 'd' + (val || 'all'), onClick: () => setDiff(val), title: DIFF_LABEL[val] || 'All difficulty levels', style: {
          padding: '6px 14px', borderRadius: 999, fontSize: 12.5, fontWeight: diff === val ? 700 : 500,
          fontFamily: 'Plus Jakarta Sans', cursor: 'pointer',
          border: '1px solid ' + (diff === val ? 'var(--violet, var(--primary))' : 'var(--border)'),
          background: diff === val ? 'var(--violet-l, var(--primary-l))' : 'var(--surface)',
          color: diff === val ? 'var(--violet, var(--primary))' : 'var(--text-2)',
        } }, lab))),
      // close overlap wrapper
      ),
    // empty state
    shown.length === 0 && React.createElement('div', { style: { padding: '32px 20px', textAlign: 'center', fontSize: 13, color: 'var(--text-3)', background: 'var(--surface)', borderRadius: 'var(--r-lg)', border: '1px dashed var(--border)' } }, _t('cases.no_results')),
    // cards grid
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 } },
      shown.map((c, i) => React.createElement('button', {
        key: c.id, onClick: () => onPick(c), className: 'as', style: {
          textAlign: 'left', padding: 16, borderRadius: 'var(--r-lg)', border: '1px solid var(--border)',
          background: 'var(--surface)', boxShadow: 'var(--sh-sm)', cursor: 'pointer', fontFamily: 'Plus Jakarta Sans',
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
          React.createElement('span', null, '⏱ ~' + (c.estimated_minutes || '–') + ' min'),
          (c.eligible_variant_count >= 1) && React.createElement('span', null, '▦ ' + c.eligible_variant_count + ' cases')))))
  );
}

// ---- Assessment (DDx + management) ----
function QV2AssessField({ label, value, set, ph, area }) {
  return React.createElement('label', { style: { display: 'block', marginBottom: 12 } },
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 5 } }, label),
    React.createElement(area ? 'textarea' : 'input', {
      value, onChange: (e) => set(e.target.value), placeholder: ph, rows: area ? 3 : undefined,
      style: { width: '100%', padding: '10px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13.5, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)', resize: area ? 'vertical' : 'none' },
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
  const isMobile = useIsMobile();
  return React.createElement('div', null,
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 } },
      React.createElement('input', { value: search, onChange: (e) => setSearch(e.target.value), placeholder: 'Search ' + (unit || 'items') + '…',
        style: { flex: 1, minWidth: 0, padding: '9px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } }),
      React.createElement('span', { style: { fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap', color: max && selected.length >= max ? 'var(--red-d)' : 'var(--text-2)' } }, max ? (selected.length + ' / ' + max + ' selected') : (selected.length + ' selected'))),
    React.createElement('div', { style: { display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' } },
      React.createElement('select', { value: cat, onChange: (e) => setCat(e.target.value),
        style: { flex: isMobile ? '1 1 100%' : 1, padding: '9px 10px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } },
        React.createElement('option', { value: '' }, 'Choose a category…'),
        cats.map((c) => React.createElement('option', { key: c, value: c }, c + ' (' + (catalog[c] || []).length + ')'))),
      React.createElement('input', { value: custom, onChange: (e) => setCustom(e.target.value), onKeyDown: (e) => { if (e.key === 'Enter') { e.preventDefault(); addCustom(); } }, placeholder: 'Or type your own…',
        style: { flex: 1, minWidth: 0, padding: '9px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' } }),
      React.createElement('button', { onClick: addCustom, disabled: !custom.trim() || (max && selected.length >= max), style: { padding: '0 14px', borderRadius: 10, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: (!custom.trim() || (max && selected.length >= max)) ? 0.5 : 1 } }, 'Add')),
    selected.length > 0 && React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 } },
      selected.map((it) => React.createElement('button', { key: it, onClick: () => removeSel(it), title: 'Remove', style: {
        padding: '5px 10px', borderRadius: 999, fontSize: 12, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', fontWeight: 600,
        border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)' } }, '✓ ' + it + ' ✕'))),
    visible.length > 0
      ? React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6 } },
          visible.map((it) => {
            const on = selected.indexOf(it) >= 0;
            const capped = !!max && !on && selected.length >= max;
            return React.createElement('button', { key: it, onClick: () => onToggle(it), disabled: capped, style: {
              padding: '6px 12px', borderRadius: 999, fontSize: 12, fontFamily: 'Plus Jakarta Sans', cursor: capped ? 'not-allowed' : 'pointer',
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

function QV2Assess({ caseSummary, isOsce, busy, err, transcript, onBack, onSubmit }) {
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
  const [localErr, setLocalErr] = React.useState('');

  const toggle = (set, max) => (item) => set((cur) => cur.indexOf(item) >= 0 ? cur.filter((x) => x !== item) : (max && cur.length >= max ? cur : cur.concat([item])));

  const submit = () => {
    // Fase 3 §J — submit lock: a working diagnosis is required before the score
    // commits; empty assessment must not lock a meaningless result.
    const dx = String(dx1 || '').trim();
    if (!dx) {
      setLocalErr(_t('session.require_working_dx'));
      return;
    }
    setLocalErr('');
    onSubmit({ dx1, dx2, dx3, reasoning }, { penunjang: inv.join(', '), terapi: tx.join(', '), edukasi });
  };

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
    React.createElement('button', { onClick: onBack, style: { marginBottom: 14, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '← Back to interview'),
    React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, _t('session.your_assessment')),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 16 } }, 'Commit your workup before the answer key is revealed.'),
    React.createElement('div', { style: { display: 'flex', gap: 4, marginBottom: 18, borderBottom: '1px solid var(--border)', flexWrap: 'wrap' } },
      tabs.map(([val, lab]) => React.createElement('button', { key: val, onClick: () => setTab(val), style: {
        padding: '9px 14px', border: 'none', borderBottom: '2px solid ' + (tab === val ? 'var(--primary)' : 'transparent'),
        background: 'none', color: tab === val ? 'var(--primary)' : 'var(--text-2)', fontSize: 13, fontWeight: tab === val ? 700 : 500, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer',
      } }, lab + (val === 'investigations' && inv.length ? ' (' + inv.length + ')' : '') + (val === 'therapy' && tx.length ? ' (' + tx.length + ')' : '')))),
    panel,
    !busy && err && React.createElement('div', { style: { marginTop: 14, padding: '10px 12px', borderRadius: 10, background: 'var(--red-l)', color: 'var(--red-d)', fontSize: 12.5, lineHeight: 1.5 } },
      '⚠️ ' + String(err) + ' — ' + _t('session.score_retry_hint')),
    localErr && React.createElement('div', { style: { marginTop: 14, padding: '10px 12px', borderRadius: 10, background: 'var(--amber-l, var(--red-l))', border: '1px solid var(--amber)', color: 'var(--amber-d, var(--red-d))', fontSize: 12.5, lineHeight: 1.5 } },
      '⚠️ ' + localErr),
    React.createElement('button', { onClick: submit, disabled: busy, style: { width: '100%', marginTop: 20, padding: 13, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: busy ? 0.7 : 1 } }, busy ? 'Scoring…' : 'Finish & reveal answer key'));
}

// ---- Session chat ----
// ---- OSCE candidate brief (Fase 3 §8 stage A) ----
// A proper OSCE "station" opening: candidate instruction + the only realistic
// initial info (the patient's visible first impression) — diagnosis stays hidden.
function QV2StationBrief({ caseSummary, mode, language, onBegin, onExit }) {
  const isId = language === 'id';
  const stationTitle = caseSummary.presentation_id || caseSummary.presentation || caseSummary.title || 'OSCE Station';
  const imp = caseSummary.first_impression_id || caseSummary.first_impression;
  const isOsce = mode === 'osce';
  const tasks = isOsce
    ? ['Take a focused history (anamnesis)', 'State the local/physical examination findings', 'Request appropriate investigations', 'Give a working diagnosis + 2 differentials', 'Propose management & safety-netting']
    : ['Take a focused history', 'Screen for red-flag symptoms', 'Explore Ideas, Concerns & Expectations', 'Give a working diagnosis', 'Propose management'];

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(660px, calc(100% - 16px))', margin: '0 auto', padding: 16 } },
    React.createElement('button', { onClick: onExit, style: { marginBottom: 14, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, isId ? '← Keluar' : '← Exit'),
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 } },
      React.createElement('span', { style: { fontSize: 10, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', padding: '4px 10px', borderRadius: 999, background: 'var(--primary-l)', color: 'var(--primary)' } }, isOsce ? 'OSCE Station' : 'Practice Station'),
      React.createElement('div', { style: { fontSize: 13, color: 'var(--text-3)' } }, '· ' + (caseSummary.specialty || ''))),
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 6, lineHeight: 1.3 } }, stationTitle),
    imp && React.createElement('div', { style: { fontSize: 13.5, color: 'var(--text-2)', fontStyle: 'italic', marginBottom: 18, lineHeight: 1.6 } },
      (isId ? 'Kondisi pasien saat Anda masuk: ' : 'What you see as you enter: ') + imp),

    React.createElement('div', { style: { padding: 16, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', marginBottom: 16 } },
      React.createElement('div', { style: { fontSize: 12, fontWeight: 800, color: 'var(--text-1)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' } }, isId ? '📋 Instruksi kandidat' : '📋 Candidate instruction'),
      tasks.map(function (t, i) {
        return React.createElement('div', { key: i, style: { display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 13, color: 'var(--text-2)', padding: '4px 0', lineHeight: 1.5 } },
          React.createElement('span', { style: { color: 'var(--primary)', fontWeight: 800 } }, (i + 1) + '.'),
          React.createElement('span', null, t));
      }),
      React.createElement('div', { style: { marginTop: 10, padding: 10, borderRadius: 10, background: 'var(--surface-2)', border: '1px dashed var(--border)', fontSize: 12, color: 'var(--text-3)', lineHeight: 1.5 } },
        isOsce
          ? (isId ? '🔒 Diagnosis Anda dirahasiakan. Rencana penatalaksanaan & kunci jawaban hanya terungkap saat Anda mengunci submisi.' : '🔒 The diagnosis is hidden. The answer key is only revealed after you commit your submission.')
          : (isId ? 'Mode latihan — Anda boleh melanjutkan kapan pun; tidak ada penalti waktu.' : 'Practice mode — proceed at your own pace; no time penalty.'))),

    React.createElement('button', { onClick: onBegin, style: { width: '100%', padding: 14, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', boxShadow: 'var(--sh-md)' } },
      isId ? (isOsce ? '🚪 Mulai stasiun →' : '🚪 Mulai →') : (isOsce ? '🚪 Begin station →' : '🚪 Begin →')));
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
        React.createElement('button', { onClick: onClose, style: { padding: '6px 12px', fontSize: 12, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '✕ Close')),
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
      React.createElement('button', { onClick: () => setOpen(true), style: { padding: '6px 12px', fontSize: 12, fontWeight: 600, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-1)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '🔬 View examination media' + (media.length > 1 ? ' (' + media.length + ')' : ''))),
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

// Shared dimension labels (rubric v2 — includes physical_exam added Aug 2026).
const QV2_DIM_LABEL = {
  history_coverage: 'History coverage', red_flags: 'Red-flag screening',
  ice_fife: 'ICE / FIFE', questioning_technique: 'Questioning technique',
  communication: 'Communication', physical_exam: 'Physical Exam',
  diagnostic_reasoning: 'Diagnostic reasoning', investigations: 'Investigation selection',
  management: 'Management', clinical_safety: 'Clinical safety',
  coverage: 'Coverage', fife: 'FIFE', redFlags: 'Red flags',
};

// ---- Session setup: mode selection + preparation (instruksi §4.3 + §4.5) ----
function QV2ModeCard({ active, onClick, tone, badge, title, body }) {
  return React.createElement('button', { onClick, className: 'as', style: {
    flex: 1, minWidth: 220, textAlign: 'left', padding: 18, borderRadius: 'var(--r-lg)', cursor: 'pointer', fontFamily: 'Plus Jakarta Sans',
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
    React.createElement('button', { onClick: onBack, style: { marginBottom: 16, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '\u2190 Library'),
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, 'Get ready for your session'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 22, fontStyle: 'italic' } }, caseSummary.first_impression_id || caseSummary.first_impression || caseSummary.presentation_id || caseSummary.presentation),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, 'Choose a mode'),
    React.createElement('div', { style: { display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' } },
      React.createElement(QV2ModeCard, { active: mode === 'practice', onClick: () => setMode('practice'), tone: 'teal', badge: 'Practice', title: 'Anamnesis practice', body: 'Relaxed learning — history only, no physical exam step. A task guide and history hints help you along. The timer is optional.' }),
      React.createElement(QV2ModeCard, { active: mode === 'osce', onClick: () => setMode('osce'), tone: 'violet', badge: 'OSCE', title: 'OSCE exam', body: 'Exam conditions — no hints. Includes the physical examination step. A countdown runs; when it ends you finish or continue for a penalty.' })),
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, 'Choose session language'),
    React.createElement('div', { className: 'as d2', style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24 } },
      [['en','English'],['id','Bahasa Indonesia'],['ms','Bahasa Melayu'],['tl','Tagalog'],['vi','Tiếng Việt'],['th','ภาษาไทย']].map(function(p) {
        var code = p[0], label = p[1];
        return React.createElement('button', { key: code, onClick: function() { setLang(code); }, style: {
          padding: '8px 16px', borderRadius: 999, fontSize: 12.5, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', fontWeight: lang === code ? 700 : 500,
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
          : React.createElement('button', { onClick: requestMic, disabled: micState === 'requesting', style: { fontSize: 12, fontWeight: 700, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, micState === 'denied' ? 'Blocked — retry' : micState === 'requesting' ? 'Requesting…' : 'Allow')),
      React.createElement(QV2PrepRow, { icon: '🔊', title: 'Speech-to-text', body: stt === null ? 'Checking…' : (stt === 'browser' ? 'Ready — using your browser’s built-in speech recognition (no upload).' : stt === 'server' ? 'Ready — speech is transcribed on the server.' : 'Unavailable in this browser — you can still type your questions.'), status: stt === null ? 'Checking…' : (stt ? 'Ready' : 'Text only'), tone: stt ? 'teal' : 'primary' }),
      React.createElement(QV2PrepRow, { icon: '🔒', title: 'Privacy & security', body: 'Your audio is processed securely and is not stored without your explicit consent.' }),
      React.createElement(QV2PrepRow, { icon: '🎧', title: 'Audio quality', body: 'For best results, use a quiet room and check your microphone works.' })),
    React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', marginBottom: 16 } }, micState === 'granted' ? '✓ All set — you can start now.' : 'You can start now and enable the mic later.'),
    billing && billing.limitReached
      ? React.createElement('div', { style: { padding: 16, borderRadius: 12, border: '1px solid var(--amber)', background: 'var(--amber-l)', marginBottom: 12 } },
          React.createElement('div', { style: { fontSize: 13.5, fontWeight: 700, color: 'var(--amber-d)', marginBottom: 4 } }, '⚡ Free session limit reached'),
          React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', marginBottom: 12 } }, 'You have used all ' + (billing.free_session_limit || 3) + ' free sessions this period. Upgrade to keep practising without limits.'),
          React.createElement('div', { style: { display: 'flex', gap: 8 } },
            React.createElement('button', { onClick: function () { if (window.__goBilling) window.__goBilling(); }, style: { padding: '10px 18px', borderRadius: 10, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Upgrade plan'),
            React.createElement('button', { onClick: onBack, style: { padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Back to library')))
      : React.createElement('button', { onClick: () => onStart({ mode: mode, micReady: micState === 'granted', sttReady: !!stt, language: lang }), style: { width: '100%', padding: 14, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', boxShadow: 'var(--sh-md)' } }, 'Start session →'));
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
      React.createElement('button', { onClick: onToggleTimer, style: { marginTop: 8, fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 999, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, timerOn ? 'Pause timer' : 'Start timer')),
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
        React.createElement('button', { onClick: onContinue, style: { flex: 1, padding: 12, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Continue (−penalty)'),
        React.createElement('button', { onClick: onFinish, style: { flex: 1, padding: 12, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Finish now'))));
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
  const [stage, setStage] = React.useState((mode === 'osce' && !initialSessionId) ? 'brief' : 'chat'); // brief | chat | pf | assess
  const [pf, setPf] = React.useState({ notes: '', areas: [] });
  const isOsce = mode === 'osce';
  // V3 family cards opt into the physical-exam step even in Practice mode
  // (backend `/pf` dispatches to the V3 variant's system_findings). Legacy
  // V2 practice keeps the original anamnesis-only behaviour.
  const isV3Family = caseSummary && caseSummary.source_type === 'v3_family';
  const hasPhysicalExam = isOsce || isV3Family;
  const [secs, setSecs] = React.useState((caseSummary.estimated_minutes || 15) * 60);
  const [timerOn, setTimerOn] = React.useState(isOsce); // OSCE auto-starts the countdown
  const [timeUp, setTimeUp] = React.useState(false);
  const [overtime, setOvertime] = React.useState(false);
  // FASE 6 hardening: completed banner + duplicate-send guard (no redesign).
  const [sessionStatus, setSessionStatus] = React.useState('active');
  const sendInflightRef = React.useRef(false);
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
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), 30000);
          let res;
          try {
            res = await fetch(_qv2Base() + '/api/ai/transcribe', {
              method: 'POST',
              headers: tok ? { Authorization: 'Bearer ' + tok } : {},
              body: formData,
              signal: controller.signal,
            });
          } finally {
            clearTimeout(timeout);
          }

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
    // or start a fresh one. FASE 6: preserve exact status so a completed
    // session reopens as read-only instead of accepting new turns.
    if (initialSessionId) {
      qv2Fetch('/api/v2/sessions/' + initialSessionId + '/turns')
        .then(d => {
          const turns = (d && d.turns) || [];
          setMessages(turns.map(t => ({ role: t.role, text: t.content || t.text || '' })));
          if (!turns.length && d && d.opening_line) setMessages([{ role: 'patient', text: d.opening_line }]);
          if (d && d.status) setSessionStatus(d.status);
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

  // Shared-shell rule (Fase 1) + FASE 6: 'nearest' keeps new replies in view
  // without yanking the chat header underneath the sticky App header on load.
  // scroll-margin on the anchor handles the sticky header offset.
  React.useEffect(() => { if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [messages]);

  // Update the trailing (streaming) patient bubble in place.
  const patchPatient = (t, streaming) => setMessages(m => {
    const c = m.slice();
    for (let i = c.length - 1; i >= 0; i--) {
      if (c[i].role === 'patient') { c[i] = { role: 'patient', text: t, streaming }; break; }
    }
    return c;
  });

  async function send(textArg, source) {
      const text = (typeof textArg === 'string' ? textArg : input).trim();
      // FASE 6: harden duplicate-send (double-Enter / double-tap / mic auto-send
      // race) + completed-session reopen. V3 engine still gets plain text only.
      if (!text || busy || sendInflightRef.current || !sessionId) return;
      if (sessionStatus === 'completed') { setErr('This session is already completed — open the report instead.'); return; }
      const inputType = source === 'voice' ? 'voice' : 'text';
      sendInflightRef.current = true;
      setErr('');
      setInput(''); setBusy(true);
      setMessages(m => m.concat([{ role: 'user', text }, { role: 'patient', text: '', streaming: true }]));
      try {
        const doStream = async (retried) => {
        const tok = _qv2Token();
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 150000);
        let r;
        try {
          r = await fetch(_qv2Base() + '/api/v2/sessions/' + sessionId + '/turns/stream', {
            method: 'POST',
            headers: Object.assign({ 'Content-Type': 'application/json' }, tok ? { Authorization: 'Bearer ' + tok } : {}),
            body: JSON.stringify({ text: text, input_type: inputType }),
            signal: controller.signal,
          });
        } finally {
          clearTimeout(timeout);
        }
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
      // FASE 6: stream interrupted (timeout/abort/offline) → non-stream retry.
      // Backend dedupes the already-persisted user turn, so no duplicate pair.
      // On hard failure keep the typed/voice text in the input for retry.
      try {
        const d = await qv2Fetch('/api/v2/sessions/' + sessionId + '/turns', { method: 'POST', body: { text, input_type: inputType } });
        patchPatient((d && d.reply) || '…', false);
      } catch (e2) {
        patchPatient('(error: ' + (e2.message || e2) + ') — your message is kept above; tap Assess later or retry.', false);
        setInput(text);
        setErr(String((e2 && e2.message) || e2 || e));
      }
    }
    sendInflightRef.current = false;
    setBusy(false);
  }

  // Fase 5 §35.1 — mark the pilot session as started once it exists.
  React.useEffect(() => {
    if (typeof window === 'undefined' || !sessionId) return;
    _pilotEvent('session_started', { session_id: sessionId, stage: 'chat',
      meta: { case_id: caseSummary.id, mode: mode, language: language } });
  }, [sessionId]);

  async function score(ddx, mgmt) {
    if (!sessionId) return;
    setBusy(true);
    try { const report = await qv2Fetch('/api/v2/sessions/' + sessionId + '/score', { method: 'POST', timeout: 150000, body: { ddx, management: mgmt, mode: mode, overtime: overtime, pf_notes: pf.notes || null, pf_areas: (pf.areas && pf.areas.length) ? pf.areas : null } }); try { sessionStorage.removeItem('qora_session_meta'); } catch (e) {} onScored(report); }
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

  if (stage === 'brief') {
    return React.createElement(QV2StationBrief, { caseSummary, mode, language, onExit, onBegin: () => { setStage('chat'); } });
  }

  if (stage === 'pf') {
    return React.createElement(QV2PhysicalExam, { caseSummary, sessionId, language: language, onBack: () => setStage('chat'), onContinue: (pfData) => { setPf(pfData); setStage('assess'); } });
  }

  if (stage === 'assess') {
    return React.createElement(QV2Assess, { caseSummary, isOsce, busy, err, transcript: messages, onBack: () => setStage('chat'), onSubmit: score });
  }

  const mmss = String(Math.floor(secs / 60)).padStart(2, '0') + ':' + String(secs % 60).padStart(2, '0');

  // Shared-shell rule (Fase 1) + FASE 6 hardening: on phones the page owns the
  // scroll so the input dock + Exam/Assess CTA can never be trapped inside a
  // fixed-height inner scroller behind the bottom tab bar. Wide screens keep
  // the app-like inner scroll column. Input dock is sticky with safe-area so
  // the mobile keyboard / address-bar resize never hides it; bubbles wrap
  // long messages; anchor has scroll-margin for the sticky header offset.
  const isCompleted = sessionStatus === 'completed';
  const chatColumn = React.createElement('div', { style: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: isMobile ? 'auto' : 'calc(100dvh - 140px)', minHeight: isMobile ? 'calc(100dvh - 260px)' : undefined } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 } },
      React.createElement('button', { onClick: () => { _pilotEvent('abandoned', { session_id: sessionId, stage: stage }); onExit(); }, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '← Library'),
      React.createElement(QV2Pill, { tone: isOsce ? 'violet' : 'teal' }, isOsce ? 'OSCE' : 'Practice'),
      React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, _qv2Title(caseSummary)),
      !wide && React.createElement('button', { onClick: () => setTimerOn((v) => !v), title: 'Session timer', style: { padding: '4px 10px', borderRadius: 999, border: '1px solid var(--border)', background: timerOn ? (secs < 60 ? 'var(--red-l)' : 'var(--surface-2)') : 'var(--surface)', color: timerOn ? (secs < 60 ? 'var(--red-d)' : 'var(--text-1)') : 'var(--text-3)', fontSize: 12, fontWeight: 700, fontVariantNumeric: 'tabular-nums', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, timerOn ? ('⏱ ' + mmss) : '⏱ Timer')),
    React.createElement(QV2MediaBar, { caseId: caseSummary.id }),
    isCompleted && React.createElement('div', { role: 'status', style: { fontSize: 12.5, color: 'var(--text-2)', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 12, padding: '10px 14px', marginBottom: 8 } }, 'This session is completed — the conversation is read-only. Open the report via Assess.'),
    busy && React.createElement('div', { role: 'status', 'aria-live': 'polite', style: { fontSize: 12, color: 'var(--text-3)', marginBottom: 4 } }, 'Patient is replying…'),
    err && React.createElement('div', { role: 'alert', style: { color: 'var(--red-d)', fontSize: 12, marginBottom: 8, overflowWrap: 'break-word' } }, err),
    React.createElement('div', { 'aria-live': 'polite', style: { flex: 1, overflowY: isMobile ? 'visible' : 'auto', display: 'flex', flexDirection: 'column', gap: 10, padding: '8px 2px' } },
      messages.map((m, i) => React.createElement('div', { key: i, className: 'af', style: {
        alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: isMobile ? '86%' : '78%',
        padding: '10px 14px', borderRadius: 16, fontSize: 13.5, lineHeight: 1.5,
        overflowWrap: 'break-word', wordBreak: 'break-word',
        background: m.role === 'user' ? 'var(--primary)' : 'var(--surface)',
        color: m.role === 'user' ? '#fff' : 'var(--text-1)',
        border: m.role === 'user' ? 'none' : '1px solid var(--border)', boxShadow: 'var(--sh-xs)',
      } }, m.streaming && !m.text
        ? React.createElement('span', { className: 'qv2-typing', style: { color: 'var(--text-3)' } }, '● ● ●')
        : (m.streaming ? m.text + ' ▋' : m.text))),
      React.createElement('div', { ref: endRef, style: { scrollMarginTop: 72 } })),
    React.createElement('div', { style: { padding: '12px 0 calc(16px + env(safe-area-inset-bottom, 0px))', display: 'flex', flexDirection: 'column', gap: 10, position: isMobile ? 'sticky' : 'static', bottom: 0, background: isMobile ? 'var(--bg, transparent)' : 'transparent', zIndex: 2 } },
      hasPhysicalExam && React.createElement('div', { style: { fontSize: 11.5, color: 'var(--text-3)', textAlign: 'center' } }, '🩺 Done with your questions? Tap ' + (isMobile ? 'Exam' : 'Exam →') + ' to perform the physical examination before assessing.'),
      React.createElement('div', { style: { display: 'flex', justifyContent: 'center' } },
        React.createElement(QV2MicButton, { onTranscript: (t) => setInput(t), onAutoSend: (t) => send(t, 'voice'), disabled: busy || isCompleted, sessionLang: language, compact: isMobile })),
      React.createElement('div', { style: { display: 'flex', gap: 8 } },
        React.createElement('input', {
          value: input, onChange: e => setInput(e.target.value),
          onKeyDown: e => { if (e.key === 'Enter' && !e.repeat) send(); },
          placeholder: isCompleted ? 'Session completed — read-only' : 'Or type a question…', disabled: busy || isCompleted,
          'aria-label': 'Type your question',
          style: { flex: 1, minWidth: 0, padding: '11px 14px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13.5, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' },
        }),
        React.createElement('button', { onClick: () => send(), disabled: busy || isCompleted || !input.trim(), title: 'Send question', style: { padding: isMobile ? '0 14px' : '0 16px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 16, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: (busy || isCompleted || !input.trim()) ? 'not-allowed' : 'pointer', opacity: (busy || isCompleted || !input.trim()) ? 0.55 : 1, whiteSpace: 'nowrap' } }, '↑'),
        React.createElement('button', { onClick: () => setStage(hasPhysicalExam ? 'pf' : 'assess'), disabled: busy, style: { padding: isMobile ? '0 12px' : '0 16px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', whiteSpace: 'nowrap' } }, hasPhysicalExam ? 'Exam →' : 'Assess →'))));

  return React.createElement('div', { style: { maxWidth: 'min(' + (wide ? 1200 : 760) + 'px, calc(100% - 16px))', margin: '0 auto', padding: isMobile ? '12px 10px 8px' : '16px 16px 0', display: 'flex', gap: 20, alignItems: 'flex-start' } },
    wide && React.createElement('div', { style: { width: 240, flexShrink: 0 } },
      React.createElement(QV2TaskPanel, { mode: mode, secs: secs, timerOn: timerOn, onToggleTimer: () => setTimerOn((v) => !v) })),
    chatColumn,
    timeUp && React.createElement(QV2TimeUpModal, {
      onFinish: () => { setTimeUp(false); setStage('assess'); },
      onContinue: () => { setTimeUp(false); setOvertime(true); },
    }));
}

// ---- Result + answer-key reveal ----
function QV2ItemRow({ item, status }) {
  // Clear per-item status: hit=✓ green / partial=~ amber / miss=✕ red /
  // none (not matched) =○ grey. Makes "sudah dijawab vs belum" obvious.
  const v = status === 'hit' ? { bg: 'var(--teal-l)', c: 'var(--teal-d)', icon: '✓', label: 'Done' }
    : status === 'partial' ? { bg: 'rgba(240,180,41,0.18)', c: '#8a5d00', icon: '~', label: 'Partial' }
    : status === 'miss' ? { bg: 'rgba(239,68,68,0.12)', c: 'var(--red-d)', icon: '✕', label: 'Miss' }
    : { bg: 'var(--surface-3)', c: 'var(--text-3)', icon: '○', label: '' };
  const txt = (item && item.item) ? item.item : item;
  return React.createElement('div', { style: { display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12.5, color: 'var(--text-2)', padding: '4px 0' } },
    React.createElement('span', { style: { width: 16, height: 16, borderRadius: 999, background: v.bg, color: v.c, fontSize: 10, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 } }, v.icon),
    React.createElement('span', { style: { flex: 1, minWidth: 0, lineHeight: 1.4, color: 'var(--text-2)' } }, txt),
    item && item.critical && React.createElement('span', { title: 'Important — high-yield / must hit', style: { fontSize: 9.5, fontWeight: 800, color: '#8a5d00', background: 'rgba(240,180,41,0.20)', padding: '2px 7px', borderRadius: 999, flexShrink: 0, marginTop: 2, border: '1px solid rgba(240,180,41,0.35)' } }, '⚑ Important'),
    v.label && React.createElement('span', { style: { fontSize: 9.5, fontWeight: 700, color: v.c, background: v.bg, padding: '2px 7px', borderRadius: 999, flexShrink: 0, marginTop: 2 } }, v.label));
}

// Answer-key group card: one box per checklist group, with an answered-count
// badge in the header (e.g. "3/5") that turns green when the whole group's done.
function QV2AnswerCard({ title, badge, badgeDone, children, style, center }) {
  return React.createElement('div', { className: 'as', style: Object.assign({ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: '14px 16px', boxShadow: 'var(--sh-xs)', display: 'flex', flexDirection: 'column' }, style || {}) },
    React.createElement('div', { style: { display: 'flex', justifyContent: center ? 'center' : 'space-between', alignItems: 'center', gap: 8, marginBottom: 6, textAlign: center ? 'center' : 'left' } },
      React.createElement('span', { style: { fontSize: 11.5, fontWeight: 800, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em' } }, title),
      badge != null && React.createElement('span', { style: { fontSize: 10.5, fontWeight: 800, color: badgeDone ? 'var(--teal-d)' : 'var(--text-3)', background: badgeDone ? 'var(--teal-l)' : 'var(--surface-2)', padding: '2px 8px', borderRadius: 999, border: '1px solid ' + (badgeDone ? 'var(--teal)' : 'var(--border)') } }, badge)),
    React.createElement('div', { style: { display: 'flex', flexDirection: 'column', textAlign: center ? 'center' : 'left' } }, children));
}

// ── Rolling number (progress juice, cheap rAF; respects reduced motion) ──
function useReducedMotion() {
  var m = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  return !!(m && m.matches);
}
function QNumeric({ value, ms, style }) {
  var [n, setN] = React.useState(0);
  var reduce = useReducedMotion();
  React.useEffect(function () {
    if (reduce) { setN(value); return undefined; }
    var dur = ms || 700, from = 0, raf;
    var start = performance.now();
    function step(t) {
      var k = Math.min(1, (t - start) / dur);
      var eased = 1 - Math.pow(1 - k, 3);
      setN(Math.round(from + (value - from) * eased));
      if (k < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
    return function () { cancelAnimationFrame(raf); };
  }, [value, reduce, ms]);
  return React.createElement('span', { style: style || {} }, n);
}

function QV2Result({ report, caseSummary, onAgain, onLibrary, sessionId }) {
  const ak = report.answer_key || {};
  const dims = report.per_dimension || {};
  var _t = window.__t || function(k) { return k; };
  const gates = (report.safety_gates || []).filter(Boolean);
  const gateLabel = { missed_critical_red_flag: _t('session.safety_missed_critical_red_flag'), unsafe_management: _t('session.safety_unsafe_management'), failed_urgent_referral: _t('session.safety_failed_urgent_referral') };
  const isMobile = useIsMobile();
  // Confetti ONLY for a meaningful milestone (high score) — routine
  // completion gets a quieter visual. §10 of the playfulness doc: don't
  // confetti every case. Branded palette, respects reduced-motion.
  var reduce = useReducedMotion();
  React.useEffect(function () {
    if (typeof window.confetti !== 'function' || reduce) return;
    var score = report.overall || 0;
    if (score >= 80) {
      window.confetti({ particleCount: 90, spread: 75, startVelocity: 42, origin: { y: 0.6 }, colors: ['#5C3F96', '#9A76DB', '#C77FC0', '#C97A15'], shapes: ['circle', 'square', 'star'] });
    }
  }, [reduce]);
  // Reasoning autopsy (Qora Mentor §4.2): fetch, or generate post-score.
  const [autopsy, setAutopsy] = React.useState(null);
  React.useEffect(function () {
    if (!sessionId) return;
    var cancelled = false;
    function loadAutopsy() {
      qv2Fetch('/api/v2/mentor/sessions/' + sessionId + '/autopsy')
        .then(function (d) {
          if (cancelled) return;
          if (d && d.autopsy) { setAutopsy(d.autopsy); }
          else {
            qv2Fetch('/api/v2/mentor/sessions/' + sessionId + '/autopsy', { method: 'POST' })
              .then(function (r) { if (!cancelled && r && r.autopsy) setAutopsy(r.autopsy); })
              .catch(function () {});
          }
        })
        .catch(function () {});
    }
    loadAutopsy();
    return function () { cancelled = true; };
  }, [sessionId]);
  // Fase 5 §35.9-10 — the debrief (and its answer key) was opened.
  React.useEffect(() => {
    if (!sessionId) return;
    _pilotEvent('debrief_opened', { session_id: sessionId, stage: 'result' });
    _pilotEvent('answer_key_revealed', { session_id: sessionId, stage: 'result' });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // map item text -> status from per_item (loose lowercase contains match)
  const statusFor = (text) => {
    const t = String(text || '').toLowerCase();
    const hit = (report.per_item || []).find(p => t && (t.includes(String(p.item || '').toLowerCase()) || String(p.item || '').toLowerCase().includes(t)));
    return hit ? hit.status : null;
  };
  // Strongest / focus-next chips, from the scored dimensions (skill mastery,
  // §12). Only meaningful once 2+ dimensions have been scored.
  const dimList = Object.keys(dims).map(k => ({ label: QV2_DIM_LABEL[k] || k.replace(/_/g, ' '), pct: dims[k].max ? Math.round((dims[k].score / dims[k].max) * 100) : 0 }));
  const sortedDims = dimList.slice().sort((a, b) => b.pct - a.pct);
  const strongest = sortedDims[0];
  const weakest = sortedDims.length > 1 ? sortedDims[sortedDims.length - 1] : null;
  // Answer-key cards packed into balanced columns (proxy = item count) so both
  // sides end near-equal height: avoids the "huge empty stretch" of equal-height
  // cards AND the "uneven bottoms / background gaps" of a raw 3-col when group
  // sizes don't divide evenly into a tidy grid. Mobile renders a single column.
  const akCards = [];
  (ak.anamnesis_checklist || []).forEach(g => {
    const items = g.items || [];
    const done = items.filter(it => { const st = statusFor(it.item); return st === 'hit' || st === 'partial'; }).length;
    akCards.push({ title: g.group.replace(/_/g, ' '), badge: done + '/' + items.length, badgeDone: done === items.length && items.length > 0, items: items, weight: items.length + 1 });
  });
  if ((ak.red_flags || []).length) {
    const rf = ak.red_flags || [];
    const n = rf.filter(it => { const st = statusFor(it.item); return st === 'hit' || st === 'partial'; }).length;
    akCards.push({ title: 'Red flags to screen', badge: n + '/' + rf.length, badgeDone: n === rf.length, items: rf, weight: rf.length + 1 });
  }
  const colSum = [0, 0]; const colCards = [[], []];
  akCards.forEach(cd => { const i = colSum[0] <= colSum[1] ? 0 : 1; colCards[i].push(cd); colSum[i] += cd.weight; });
  const renderAKCard = (cd) => React.createElement(QV2AnswerCard, { key: cd.title, title: cd.title, badge: cd.badge, badgeDone: cd.badgeDone },
    cd.items.map((it, i) => React.createElement(QV2ItemRow, { key: i, item: it, status: statusFor(it.item) })));
  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(820px, calc(100% - 16px))', margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)' } }, 'Debrief'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 18 } }, caseSummary.presentation),
    // Safety gates (§9.2 Layer 3) — surfaced before anything else so a dangerous
    // mistake is never hidden inside small point deductions.
    gates.length > 0 && React.createElement('div', { className: 'as', style: { marginBottom: 16, padding: 14, borderRadius: 'var(--r-lg)', background: 'rgba(239,68,68,0.10)', border: '1px solid var(--red)', boxShadow: 'var(--sh-sm)' } },
      React.createElement('div', { style: { fontSize: 13, fontWeight: 800, color: 'var(--red-d)', marginBottom: 8 } }, _t('session.safety_gates')),
      gates.map((g, i) => React.createElement('div', { key: i, style: { display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12.5, color: 'var(--text-1)', padding: '3px 0', lineHeight: 1.45 } },
        React.createElement('span', { style: { color: 'var(--red-d)', fontWeight: 800, flexShrink: 0 } }, '✕'),
        React.createElement('span', null,
          React.createElement('b', { style: { color: 'var(--red-d)' } }, String(gateLabel[g.type] || g.type) + ' · '),
          String(g.detail || ''))))),
    // Examiner verdict first (§10.1) — the debrief leads with what a real examiner
    // would say, so the feedback is the first thing the learner reads.
    report.summary && React.createElement('div', { className: 'as d1', style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6, padding: 14, borderRadius: 'var(--r-md)', background: 'var(--primary-ll)', marginBottom: 16 } }, report.summary),
    // overall + dimensions
    React.createElement('div', { className: 'as', style: { display: 'flex', alignItems: 'center', gap: 18, padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)', marginBottom: 16 } },
      React.createElement('div', { className: 'as', style: { fontSize: 38, fontWeight: 800, color: 'var(--primary)', minWidth: 56, textAlign: 'center' } }, React.createElement(QNumeric, { value: (report.overall != null ? report.overall : 0), ms: 800 })),
      React.createElement('div', { style: { flex: 1 } },
        Object.keys(dims).map(k => {
          const d = dims[k]; const pct = d.max ? Math.round((d.score / d.max) * 100) : 0;
          return React.createElement('div', { key: k, style: { marginBottom: 6 } },
            React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--text-2)', fontWeight: 600, marginBottom: 2 } },
              React.createElement('span', null, QV2_DIM_LABEL[k] || k.replace(/_/g, ' ')),
              React.createElement('span', null, d.score + '/' + d.max)),
            React.createElement('div', { style: { height: 6, borderRadius: 999, background: 'var(--surface-3)' } },
              React.createElement('div', { style: { width: pct + '%', height: '100%', borderRadius: 999, background: 'var(--primary)' } })));
        }))),
    (strongest || weakest) && React.createElement('div', { className: 'as d1', style: { display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 16 } },
      strongest && React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 700, padding: '8px 14px', borderRadius: 999, background: 'var(--teal-l)', color: 'var(--teal-d)' } }, 'Strongest: ' + strongest.label + ' · ' + strongest.pct + '%'),
      weakest && React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 700, padding: '8px 14px', borderRadius: 999, background: 'var(--violet-l)', color: 'var(--violet)' } }, 'Focus next: ' + weakest.label)),
    // answer key
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '6px 12px', alignItems: 'center', marginBottom: 10, fontSize: 11, color: 'var(--text-3)' } },
      React.createElement('span', { style: { marginRight: 2 } }, 'Status:'),
      React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 5 } }, React.createElement('span', { style: { width: 13, height: 13, borderRadius: 999, background: 'var(--teal-l)', color: 'var(--teal-d)', fontSize: 9, fontWeight: 800, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' } }, '✓'), ' Done'),
      React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 5 } }, React.createElement('span', { style: { width: 13, height: 13, borderRadius: 999, background: 'rgba(240,180,41,0.18)', color: '#8a5d00', fontSize: 9, fontWeight: 800, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' } }, '~'), ' Partial'),
      React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 5 } }, React.createElement('span', { style: { width: 13, height: 13, borderRadius: 999, background: 'rgba(239,68,68,0.12)', color: 'var(--red-d)', fontSize: 9, fontWeight: 800, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' } }, '✕'), ' Miss'),
      React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 5 } }, React.createElement('span', { style: { width: 13, height: 13, borderRadius: 999, background: 'var(--surface-3)', color: 'var(--text-3)', fontSize: 9, fontWeight: 800, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' } }, '○'), ' Not asked'),
      React.createElement('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 5, color: '#8a5d00' } }, '⚑ Important item')),
    React.createElement('div', { style: { fontSize: 16, fontWeight: 800, color: 'var(--text-1)', margin: '0 0 12px' } }, '🗝 Model answer (what a complete workup includes)'),
    (isMobile
      ? React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 12 } }, akCards.map(renderAKCard))
      : React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12, alignItems: 'start', marginBottom: 12 } },
          colCards.map((col, ci) => React.createElement('div', { key: ci, style: { display: 'flex', flexDirection: 'column', gap: 12 } }, col.map(renderAKCard))))),
    // Bottom row: Investigations · Working diagnosis & differentials (center) · Management
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, minmax(0, 1fr))', gap: 12, alignItems: 'start', marginTop: 12 } },
      (ak.investigations && (ak.investigations.appropriate || []).length) ? React.createElement(QV2AnswerCard, { title: 'Investigations' },
        (ak.investigations.appropriate || []).map((iv, i) => React.createElement('div', { key: i, style: { fontSize: 12.5, color: 'var(--text-2)', padding: '3px 0', lineHeight: 1.4 } }, '• ' + iv.name + (iv.expected ? ' → ' + iv.expected : '')))) : null,
      React.createElement(QV2AnswerCard, { title: 'Working diagnosis & differentials', center: true,
        style: { justifyContent: 'center' } },
        React.createElement('div', { style: { fontSize: 15, color: 'var(--text-1)', fontWeight: 800, margin: '12px 0 4px' } }, (ak.expected_ddx && ak.expected_ddx.working_diagnosis) || '–'),
        React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.5 } }, ((ak.expected_ddx && ak.expected_ddx.differentials) || []).join(' · '))),
      (ak.management && ((ak.management.pharmacological || []).concat(ak.management.non_pharmacological || [], ak.management.education_safety_netting || [])).length) ? React.createElement(QV2AnswerCard, { title: 'Management' },
        (ak.management.pharmacological || []).concat(ak.management.non_pharmacological || [], ak.management.education_safety_netting || []).map((m, i) => React.createElement('div', { key: i, style: { fontSize: 12.5, color: 'var(--text-2)', padding: '3px 0', lineHeight: 1.4 } }, '• ' + m))) : null),
    // Reasoning autopsy (Qora Mentor §4.2) — rendered when available
    typeof QAutopsyCard === 'function' && autopsy && React.createElement(QAutopsyCard, { autopsy: autopsy }),
    // actions
    React.createElement('div', { style: { display: 'flex', gap: 10, marginTop: 22 } },
      React.createElement('button', { onClick: () => { _pilotEvent('retry_attempt', { session_id: sessionId }); onAgain(); }, style: { padding: '10px 18px', borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Try another case'),
      React.createElement('button', { onClick: onLibrary, style: { padding: '10px 18px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Back to library'))
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
  const dimLabel = QV2_DIM_LABEL;
  const dims = p.dimensionAverages || {};
  const specs = p.specialtyCounts || {};
  const dimKeys = Object.keys(dims);
  const specKeys = Object.keys(specs);
  const goal = p.dailyGoal || { done: 0, target: 1 };
  const goalMet = goal.done >= goal.target;
  return React.createElement('div', { className: 'au', style: { maxWidth: 820, margin: '0 auto', padding: '24px 20px' } },
    React.createElement('button', { onClick: onBack, style: { marginBottom: 14, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '← Library'),
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
        React.createElement('button', { onClick: onDone, style: { padding: '11px 16px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-3)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Skip'),
        React.createElement('button', { onClick: () => last ? onDone() : setStep(step + 1), style: { flex: 1, padding: '11px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, last ? 'Start practising' : 'Next'))));
}

// ---- Dashboard (Qora style, inspired by OphthaSim) ----
// ============================================================
// QAMood — GDV §4 "pita suasana": one family of colour, different
// time of day per screen. Vector SVG scenes from the theme mockup.
// ============================================================
function QAMoodScene({ scene }) {
  // Returns the SVG scene markup (gradient sky + light source + layered
  // silhouettes + floating dots). Six moods, one colour family.
  var scenes = {
    fajar: { w:400, h:970, children: [
      ['sky','linearGradient',[['#331F63',0],['#6A4499',0.5],['#A9739F',1]],null],
      ['sun','radial',[['#F7CE85',0.95],['#F7CE85',0]],790,288,205,'flick'],
      ['sunC','circle',790,288,52,'#FBE0AC',0.9],
      ['m1','M0 300c130-62 210 18 330-22s200-74 330-22 220 76 420 44v100H0z','#4E3080',0.55],
      ['m2','M0 334c150-52 250 22 380-14s230-56 360-18 230 52 340 26v72H0z','#361F63',0.85],
      ['m3','M0 366c170-36 280 16 430-8s270-30 650-4v46H0z','#251646',1],
      ['dots',[[150,66,2.4,0.65],[286,42,1.8,0.5],[470,86,2.2,0.45],[940,56,1.9,0.5],[620,40,1.6,0.4]]],
      ['float',[[600,196,4.2,'#F7CE85',0.7],[668,152,2.9,'#E4C6F2',0.6],[540,146,2.4,'#F7CE85',0.5]]],
    ]},
    senja: { w:330, h:970, children: [
      ['sky','linearGradient',[['#2A1852',0],['#573484',0.6],['#8B4F94',1]],null],
      ['glow','radial',[['#D48ACB',0.65],['#D48ACB',0]],660,290,400,'flick'],
      ['arch1',[[40,118,50,212],[102,152,36,178],[150,96,56,234],[218,170,32,160],[262,140,44,190]],'#1F1240',0.45],
      ['arch2',[[880,136,46,194],[938,102,40,228],[990,160,52,170]],'#1F1240',0.45],
      ['arch3',[[0,196,44,134],[316,212,36,118],[812,204,40,126],[1048,188,32,142]],'#150C2C',0.72],
      ['float',[[500,104,3.6,'#F6DCF2',0.6],[592,70,2.5,'#F6DCF2',0.45],[418,76,2.2,'#F6DCF2',0.4],[700,118,2.8,'#F6DCF2',0.4]]],
    ]},
    lentera: { w:330, h:970, children: [
      ['sky','linearGradient',[['#1F1240',0],['#472B70',0.6],['#7B4B80',1]],null],
      ['m1','M0 246c150-52 250 26 390-8s240-64 380-24 220 54 310 26v90H0z','#2C1A56',0.75],
      ['m2','M0 284c180-32 300 20 450-4s280-26 630 8v42H0z','#1D1139',1],
      ['path','M110 292C300 260 400 206 540 200s280 34 440 12',null,0.7],
      ['lamp','radial',[['#F0A63A',0.9],['#F0A63A',0]],540,200,180,'flick'],
      ['node1','circ',[110,292,7.5,'#C77FC0',null]],
      ['node2','circ',[330,238,7.5,'#C77FC0',null]],
      ['node3','circ',[540,200,11,'#F5C87A',null]],
      ['node4','circ',[740,204,6.5,'#3B2568','#9A76DB']],
      ['node5','circ',[930,212,6.5,'#3B2568','#9A76DB']],
      ['float',[[620,112,3.2,'#F0A63A',0.6],[486,86,2.5,'#F0A63A',0.45],[690,66,2.1,'#F6DCF2',0.4]]],
    ]},
    malam: { w:300, h:970, children: [
      ['sky','linearGradient',[['#120A24',0],['#2F1B56',0.6],['#553584',1]],null],
      ['dots',[[90,58,1.9,0.7],[212,36,1.4,0.5],[336,76,2.2,0.6],[472,44,1.5,0.45],[614,66,2,0.6],[762,34,1.4,0.5],[884,62,2.1,0.55],[1002,46,1.6,0.45],[152,104,1.3,0.4],[706,112,1.5,0.4],[400,120,1.2,0.35]]],
      ['m1','M0 214c150-40 250 18 390-8s240-42 380-12 230 38 310 14v92H0z','#28174C',0.85],
      ['m2','M0 254c180-28 290 14 450-6s270-20 630 8v44H0z','#1A0F32',1],
      ['path','M50 178C230 146 400 168 540 142S870 130 1030 152',null,0.5],
      ['node','circ',[540,142,6,'#C77FC0','#C77FC0'],'flick'],
    ]},
    profil: { w:290, h:970, children: [
      ['sky','linearGradient',[['#271748',0],['#74469C',1]],null],
      ['aurora1','M0 120c180-70 340 42 540 10s360-86 540-30v50c-180-50-340 32-540 54S180 152 0 190z',['#9A76DB',0,0.5,'#C77FC0',0.6,1,'#9A76DB',0],'flick'],
      ['aurora2','M0 176c200-46 360 36 560 12s340-56 520-12v28c-180-38-320 26-520 46S200 216 0 204z',['#F0A63A',0,0.5,'#F0A63A',0.4,1,'#F0A63A',0],0.8],
      ['dots',[[180,52,1.8,0.55],[640,40,1.5,0.45],[900,66,1.6,0.4]]],
      ['m1','M0 236c190-28 300 18 460 2s300-24 620 8v44H0z','#1F1338',1],
    ]},
    pagi: { w:270, h:970, children: [
      ['sky','linearGradient',[['#553783',0],['#B389C4',1]],null],
      ['glow','radial',[['#FFE9C4',0.8],['#FFE9C4',0]],850,220,190,'flick'],
      ['m1','M0 196c160-38 260 20 420-4s280-34 660 4v74H0z','#5A3C8C',0.5],
      ['m2','M0 230c180-26 300 14 470-4s300-16 610 8v36H0z','#3C2668',1],
    ]},
  };
  var s = scenes[scene] || scenes.fajar;
  // Build the layers in order, referencing gradients by id constructed after defs.
  var body = s.children.map(function (c, i) {
    var t = c[0];
    if (t === 'sky') return React.createElement('rect', { key: i, width: 970, height: s.w, fill: 'url(#s' + scene + ')' });
    if (t === 'sun' || t === 'glow' || t === 'lamp') {
      return React.createElement('circle', { key: i, cx: c[3], cy: c[4], r: c[5], fill: 'url(#r' + scene + ')', className: c[6] || null });
    }
    if (t === 'sunC') return React.createElement('circle', { key: i, cx: c[2], cy: c[3], r: c[4], fill: c[5], opacity: c[6] });
    if (t === 'm1' || t === 'm2' || t === 'm3') {
      var h = s.w;
      return React.createElement('path', { key: i, d: c[1], fill: c[2], opacity: c[3] });
    }
    if (t === 'dots') {
      return React.createElement('g', { key: i, fill: '#F1E6FF' }, c[1].map(function (d, j) { return React.createElement('circle', { key: j, cx: d[0], cy: d[1], r: d[2], opacity: d[3] }); }));
    }
    if (t === 'float') {
      return React.createElement('g', { key: i, className: 'qa-float' }, c[1].map(function (d, j) { return React.createElement('circle', { key: j, cx: d[0], cy: d[1], r: d[2], fill: d[3], opacity: d[4] }); }));
    }
    if (t === 'path') return React.createElement('path', { key: i, d: c[1], fill: 'none', stroke: '#9A76DB', strokeWidth: c[0]==='path' ? (scene==='malam'?1.8:2.6) : 2.6, strokeDasharray: scene==='malam' ? '4 8' : '7 9', opacity: c[2] });
    if (t === 'arch1' || t === 'arch2' || t === 'arch3') {
      return React.createElement('g', { key: i, opacity: c[3], fill: c[2] }, c[1].map(function (r, j) { return React.createElement('rect', { key: j, x: r[0], y: r[1], width: r[2], height: r[3], rx: 7 }); }));
    }
    if (t === 'aurora1' || t === 'aurora2') {
      var gid = scene + '_a' + (t === 'aurora1' ? '1' : '2');
      return React.createElement('path', { key: i, d: c[1], fill: 'url(#' + gid + ')', className: t === 'aurora1' ? 'qa-flick' : null, opacity: t === 'aurora1' ? undefined : c[3] });
    }
    if (t === 'node1' || t === 'node2' || t === 'node3' || t === 'node4' || t === 'node5') {
      var d = c[2];
      return React.createElement('circle', { key: i, cx: d[0], cy: d[1], r: d[2], fill: d[3], stroke: d[4] || 'none', strokeWidth: d[4] ? 2.2 : undefined, className: (scene==='malam' && d[3]==='#C77FC0') ? 'qa-flick' : null });
    }
    if (t === 'node') return React.createElement('circle', { key: i, cx: c[2][0], cy: c[2][1], r: c[2][2], fill: c[2][3], className: c[3] || 'qa-flick' });
    return null;
  });
  var defs = [];
  if (scenes[scene] && scenes[scene].children.filter(function (c) { return c[0] === 'sky' || c[0] === 'glow' || c[0] === 'lamp' || c[0] === 'sun'; }).length) {
    var skyC = s.children.find(function (c) { return c[0] === 'sky'; });
    var radC = s.children.find(function (c) { return c[0] === 'sun' || c[0] === 'glow' || c[0] === 'lamp'; });
    defs.push(React.createElement('defs', { key: 'defs' },
      skyC && React.createElement('linearGradient', { id: 's' + scene, x1: 0, y1: 0, x2: 0.3, y2: 1 }, skyC[2].map(function (st, j) { return React.createElement('stop', { key: j, offset: String(st[1]), stopColor: st[0] }); })),
      radC && React.createElement('radialGradient', { id: 'r' + scene, cx: 0.5, cy: 0.5, r: 0.5 }, radC[2].map(function (st, j) { return React.createElement('stop', { key: j, offset: String(st[1]), stopColor: st[0], stopOpacity: st[2] }); }))));
    // aurora gradients
    scenes[scene].children.filter(function (c) { return c[0].indexOf('aurora') === 0; }).forEach(function (c) {
      var gid = scene + '_a' + (c[0] === 'aurora1' ? '1' : '2');
      var arr = c[2] || [];
      defs.push(React.createElement('defs', { key: gid }, React.createElement('linearGradient', { id: gid, x1: 0, y1: 0, x2: 1, y2: c[0] === 'aurora1' ? 0.4 : 0 }, arr.map(function (st, j) { return React.createElement('stop', { key: j, offset: String(st[1]), stopColor: st[0], stopOpacity: st[2] }); }))));
    });
  }
  return React.createElement('svg', { className: 'qa-scene', style: { display: 'block', width: '100%', height: 'auto' }, viewBox: '0 0 970 ' + s.w, xmlns: 'http://www.w3.org/2000/svg', 'aria-hidden': true },
    defs, body);
}

function QAMoodBand({ scene, kicker, title, sub, children }) {
  // Standard pita suasana: sky + caption (bottom) + optional floating glass
  // panel (children). Matches GDV §4 structure on every screen.
  return React.createElement('div', { className: 'qa-band au', style: { marginBottom: 0 } },
    React.createElement(QAMoodScene, { scene: scene }),
    React.createElement('div', { style: { position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: '30px 32px 96px', color: '#fff' } },
      kicker && React.createElement('div', { style: { fontSize: 10.5, letterSpacing: '.18em', fontWeight: 700, opacity: .82, marginBottom: 7, textTransform: 'uppercase' } }, kicker),
      React.createElement('h1', { style: { fontSize: 'clamp(24px,7vw,28px)', margin: 0, fontWeight: 800, letterSpacing: '-.02em', textShadow: '0 2px 18px rgba(20,10,40,.35)' } }, title),
      sub && React.createElement('p', { style: { margin: '6px 0 0', fontSize: 14, opacity: .88, maxWidth: '44ch', textShadow: '0 1px 8px rgba(20,10,40,.4)' } }, sub),
      children));
}

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
  // Explicit XP progression (#2): X / 200 this level, plus "to next".
  const xpInLevel = (p.xp || 0) % 200;
  const toNext = 200 - xpInLevel;
  const totalSessions = p.totalSessions || 0;
  const completedCases = p.completedCases || 0;
  const dims = p.dimensionAverages || {};
  // Skill mastery (#3): surface the strongest dimension from scaled scores.
  const dimArr = Object.keys(dims).map(k => ({ label: QV2_DIM_LABEL[k] || k.replace(/_/g, ' '), pct: dims[k] || 0 }));
  const strongestDim = dimArr.length ? dimArr.slice().sort((a, b) => b.pct - a.pct)[0] : null;
  const hasDims = Object.keys(dims).length > 0;
  const specs = p.specialtyCounts || {};
  const specKeys = Object.keys(specs);
  const avgScore = hasDims ? Math.round(Object.values(dims).reduce((a, b) => a + b, 0) / Object.keys(dims).length) : 0;

  // Recent sessions helper
  const specLabel = { internal_medicine: 'Internal medicine', surgery: 'Surgery', paediatrics: 'Paediatrics', obstetrics_gynaecology: 'Obs & Gynae', psychiatry: 'Psychiatry', neurology: 'Neurology', ent: 'ENT', dermatology: 'Dermatology', ophthalmology: 'Ophthalmology', emergency: 'Emergency' };

  // Uniform panel + heading styles shared across every content section
  // (keeps the existing look — surface, border, radius — but enforces
  //  one consistent spec so cards align on a clean grid).
  const panel = { padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)' };
  const secTitle = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, gap: 10 };
  const secHead = { fontSize: 13, fontWeight: 700, color: 'var(--text-1)' };

  return React.createElement('div', { style: { maxWidth: 'min(1100px, calc(100% - 16px))', margin: '0 auto', padding: isMobile ? '20px 10px 60px' : '32px 24px 60px' } },

    // ── Hero: pita suasana "Fajar" (GDV §4) + floating glass panel ──
    React.createElement(QAMoodBand, { scene: 'fajar', kicker: 'CLINICAL INTERVIEW TRAINER', title: 'Welcome back' + (firstName ? ', ' + firstName : '') + '! 👋',
      sub: 'Practise taking a structured history across every specialty. Each virtual patient brings a new clinical challenge.' },
      // Floating glass level panel (GDV §9) — top-right, one brief piece of info
      React.createElement('div', { style: { position: 'absolute', right: 26, top: 28, width: 250, padding: '17px 19px', borderRadius: 18,
        background: 'rgba(255,255,255,0.16)', backdropFilter: 'blur(20px) saturate(150%)', WebkitBackdropFilter: 'blur(20px) saturate(150%)',
        border: '1px solid rgba(255,255,255,0.34)', boxShadow: '0 12px 30px rgba(20,10,40,.22), inset 0 1px 0 rgba(255,255,255,.4)', color: '#fff' } },
        React.createElement('div', { style: { fontSize: 10, letterSpacing: '.16em', fontWeight: 700, opacity: .78, textTransform: 'uppercase' } }, 'Your Progress'),
        React.createElement('div', { style: { fontSize: 20, fontWeight: 800, letterSpacing: '-.02em', margin: '5px 0 3px' } }, 'Lv ' + level + ' · ' + levelName),
        React.createElement('div', { style: { fontSize: 12, opacity: .82 } }, React.createElement(QNumeric, { value: xpInLevel, ms: 800 }), ' / 200 XP'),
        React.createElement('div', { style: { height: 6, borderRadius: 99, background: 'rgba(255,255,255,0.26)', overflow: 'hidden', marginTop: 11 } },
          React.createElement('div', { style: { height: '100%', borderRadius: 99, background: '#fff', width: levelProgress + '%', transition: 'width 1s var(--ease)' } })),
        React.createElement('div', { style: { fontSize: 11.5, opacity: .72, marginTop: 8 } }, toNext + ' XP to next level')),
      // CTA buttons pinned at the caption row (content preserved verbatim)
      React.createElement('div', { style: { display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 } },
        React.createElement('button', { onClick: () => onNav('cases'), style: { padding: '11px 22px', borderRadius: 12, border: 'none', background: '#fff', color: 'var(--u700)', fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', boxShadow: '0 5px 16px rgba(0,0,0,0.18)' } }, '▶ Start new case'),
        completedCases > 0 && React.createElement('button', { onClick: () => onNav('cases'), style: { padding: '11px 22px', borderRadius: 12, border: '1.5px solid rgba(255,255,255,0.42)', background: 'rgba(255,255,255,0.16)', color: '#fff', fontSize: 14, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', backdropFilter: 'blur(10px)' } }, 'Continue practising'))),

    // ── Summary stats: glass cards floating over the mood band (GDV) ──
    React.createElement('div', { className: 'au', style: { position: 'relative', zIndex: 5, marginTop: -76, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(165px, 100%), 1fr))', gap: 14, marginBottom: 24 } },
      React.createElement(QDStat, { label: 'Cases completed', value: completedCases, icon: 'cases', sub: 'across ' + specKeys.length + ' specialties' }),
      React.createElement(QDStat, { label: 'Total sessions', value: totalSessions, icon: 'streak', sub: 'practice encounters' }),
      React.createElement(QDStat, { label: 'Avg score', value: avgScore + '%', icon: 'chart', sub: hasDims ? 'across all dimensions' : 'complete a case to see' }),
      React.createElement(QDStat, { label: 'Streak', value: p.streak ? p.streak + 'd' : '0d', icon: 'flame', sub: p.streak ? 'days in a row' : 'start your streak' })),

    // ── Content: balanced two-column grid (stacks on mobile) ──
    // Fixed tracks (minmax(0, x)) instead of auto-fit so the columns stay
    // stable, cards align on shared rows, and nothing overlaps or clips.
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'minmax(0, 1.35fr) minmax(0, 1fr)', gap: 20, alignItems: 'start' } },

      // ---- Left column: Sesi terbaru + Skill mastery ----
      React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 } },
        // Recent activity
        React.createElement('div', { className: 'as', style: panel },
          React.createElement('div', { style: secTitle },
            React.createElement('span', { style: secHead }, '📋 ' + _t('dashboard.recent_sessions')),
            recent.length > 0 && React.createElement('button', { onClick: () => onNav('sessions'), style: { padding: '4px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 11, color: 'var(--primary)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', fontWeight: 600 } }, _t('dashboard.browse_cases'))),
          recent.length === 0 && React.createElement('div', { style: { padding: '28px 20px', textAlign: 'center', fontSize: 13, color: 'var(--text-3)', background: 'var(--surface)', borderRadius: 12, border: '1px dashed var(--border)' } },
            'Complete your first case to see activity here.'),
          React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 10 } },
            recent.slice(0, 5).map((s, i) => React.createElement('div', { key: s.sessionId || i, style: { display: 'flex', alignItems: 'center', gap: 14, padding: 13, borderRadius: 12, background: 'var(--surface-2)', border: '1px solid var(--border)' } },
              React.createElement('div', { style: { width: 42, height: 42, borderRadius: 12, background: 'var(--primary-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 } },
                s.specialty === 'emergency' ? '🚑' : s.specialty === 'surgery' ? '🔪' : s.specialty === 'paediatrics' ? '👶' : s.specialty === 'psychiatry' ? '🧠' : s.specialty === 'ophthalmology' ? '👁' : '🩺'),
              React.createElement('div', { style: { flex: 1, minWidth: 0 } },
                React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, s.presentation || 'Case'),
                React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, (specLabel[s.specialty] || s.specialty) + (s.score != null ? ' · Score: ' + s.score : ' · In progress'))))))),

        // Skill breakdown ("Skill mastery") — bars
        hasDims && React.createElement('div', { className: 'as', style: panel },
          React.createElement('div', { style: secTitle },
            React.createElement('span', { style: secHead }, 'Skill mastery'),
            strongestDim && React.createElement('span', { style: { fontSize: 11, fontWeight: 700, color: 'var(--teal-d)', background: 'var(--teal-l)', padding: '3px 10px', borderRadius: 999 } }, 'Strong: ' + strongestDim.label)),
          React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)', marginBottom: 14 } }, 'How your interview skills stack up across dimensions.'),
          Object.keys(dims).map(k => {
            const dimLabel = QV2_DIM_LABEL;
            const pct = dims[k];
            return React.createElement('div', { key: k, style: { marginBottom: 10 } },
              React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-2)', fontWeight: 600, marginBottom: 3 } },
                React.createElement('span', null, dimLabel[k] || k),
                React.createElement('span', null, Math.round(pct) + '%')),
              React.createElement('div', { style: { height: 6, borderRadius: 999, background: 'var(--surface-3)' } },
                React.createElement('div', { style: { width: pct + '%', height: '100%', borderRadius: 999, background: 'var(--primary)', transition: 'width 0.6s ease' } })));
          }))),

      // ---- Right column: radar + achievements + specialty coverage ----
      React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 } },
        // Skill radar ("Rincian kemampuan")
        hasDims && React.createElement('div', { className: 'as', style: panel },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10, textAlign: 'center' } }, '📊 ' + _t('dashboard.skill_breakdown')),
          React.createElement(QSkillRadar, { dims: dims, size: 200 })),

        // Achievements
        (p.badges && p.badges.some((b) => b.earned)) ? React.createElement('div', { className: 'as', style: panel },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, '🏅 Achievements'),
          React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' } },
            p.badges.filter((b) => b.earned).slice(0, 10).map((b) => React.createElement('span', { key: b.id, title: b.name, style: { fontSize: 22, padding: 6, borderRadius: 10, background: 'var(--surface-2)', border: '1px solid var(--border)' } }, b.icon)))) : null,

        // Specialty coverage
        React.createElement('div', { className: 'as', style: panel },
          React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, '🎯 Specialty coverage'),
          specKeys.length === 0 && React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)' } }, 'No specialties practised yet.'),
          React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6 } },
            specKeys.map(s => React.createElement('span', { key: s, style: { fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 999, background: 'var(--primary-l)', color: 'var(--primary)' } },
              (specLabel[s] || s) + ' · ' + specs[s])))))));

}

function QDStat({ label, value, icon, color, sub }) {
  // GDV §9 stat card: the number is always ink (ungu 900) — a different
  // colour per card makes the eye hunt a meaning that isn't there. Glass
  // surface so it floats above the mood band.
  return React.createElement('div', { className: 'as qa-glass', style: { padding: 18, borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', minHeight: 136 } },
    React.createElement(QIcon, { n: icon, s: 22, color: 'var(--u700)' }),
    React.createElement('div', { style: { fontSize: 26, fontWeight: 800, color: 'var(--u900)', lineHeight: 1.1, fontVariantNumeric: 'tabular-nums' } }, value),
    React.createElement('div', { style: { fontSize: 12.5, fontWeight: 600, color: 'var(--n500)', marginTop: 10 } }, label),
    React.createElement('div', { style: { fontSize: 10.5, color: 'var(--n500)', marginTop: 3, lineHeight: 1.4 } }, sub));
}


function QoraV2Screen() {
  const [view, setView] = React.useState('catalogue'); // catalogue | setup | session | result | progress
  const [picked, setPicked] = React.useState(null);
  const [sessionMode, setSessionMode] = React.useState('practice');
  const [sessionLanguage, setSessionLanguage] = React.useState('en');
  const [report, setReport] = React.useState(null);
  const [initialSessionId, setInitialSessionId] = React.useState(null);
  const [sessionId, setSessionId] = React.useState(null); // current session (for autopsy link)
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
      setSessionId(p1);
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
    body = React.createElement(QV2Session, { caseSummary: picked, mode: sessionMode, language: sessionLanguage, initialSessionId: initialSessionId, onSessionReady: (sid) => { setSessionId(sid); setHash('session/' + sid); }, onScored: (r) => { setReport(r); try { sessionStorage.setItem('qora_last_report', JSON.stringify({ report: r, caseId: picked.id, sessionId: sessionId })); } catch (e) {} setView('result'); setHash('result'); }, onExit: () => { try { sessionStorage.removeItem('qora_session_meta'); } catch (e) {} setView('catalogue'); setHash('cases'); } });
  } else if (view === 'result' && report && picked) {
    body = React.createElement(QV2Result, { report, caseSummary: picked, sessionId: sessionId, onAgain: () => { try { sessionStorage.removeItem('qora_last_report'); } catch (e) {} setView('catalogue'); setHash('cases'); }, onLibrary: () => { try { sessionStorage.removeItem('qora_last_report'); } catch (e) {} setView('catalogue'); setHash('cases'); } });
  } else if (view === 'progress') {
    body = React.createElement(QV2Progress, { onBack: () => { setView('catalogue'); setHash('cases'); } });
  } else {
    body = React.createElement(QV2Catalogue, { onPick: (c) => { setPicked(c); setReport(null); setInitialSessionId(null); setView('setup'); setHash('cases/' + c.id); }, onProgress: () => { setView('progress'); setHash('progress'); } });
  }
  return React.createElement(React.Fragment, null, onboard ? React.createElement(QV2Onboarding, { onDone: dismiss }) : null, body);
}

// ---- User profile (view + edit) ----
const QP_AVATARS = ['👤', '🧑‍⚕️', '👩‍⚕️', '👨‍⚕️', '🩺', '🧠', '👁️', '🫀', '🦴', '🧬', '⚕️', '🎓'];
const QP_COLORS = ['#5C3F96', '#4A3278', '#7B57C4', '#9A76DB', '#C97A15', '#B3452F', '#9B4A96', '#2E7D5B'];

function QP_Field({ label, value, set, ph }) {
  return React.createElement('label', { style: { display: 'block', marginBottom: 14 } },
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 5 } }, label),
    React.createElement('input', {
      value: value || '', onChange: (e) => set(e.target.value), placeholder: ph,
      style: { width: '100%', padding: '11px 13px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' },
    }));
}

function QoraProfile({ onNav }) {
  const [me, setMe] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  var _t = window.__t || function(k) { return k; };
  const [form, setForm] = React.useState({ full_name: '', school: '', year: '', avatar_emoji: '👤', avatar_color: '#5C3F96' });
  React.useEffect(() => {
    qv2Fetch('/api/users/me')
      .then((d) => { setMe(d); setForm({ full_name: d.full_name || '', school: d.school || '', year: d.year || '', avatar_emoji: d.avatar_emoji || '👤', avatar_color: d.avatar_color || '#5C3F96' }); })
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
  return React.createElement('div', { style: { maxWidth: 720, margin: '0 auto', padding: '28px 20px 60px' } },
    // GDV §4: pita suasana "Profile" — aurora berpita
    React.createElement(QAMoodBand, { scene: 'profil', kicker: 'PROFILE', title: _t('profile.title') }),
    React.createElement('div', { className: 'au', style: { position: 'relative', zIndex: 5, marginTop: -56 } },
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
      React.createElement('button', { onClick: save, disabled: saving, style: { padding: '11px 22px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: saving ? 0.7 : 1 } }, saving ? 'Saving\u2026' : _t('common.save')),
      React.createElement('button', { onClick: () => onNav && onNav('dashboard'), style: { padding: '11px 18px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, _t('common.back')),
      saved && React.createElement('span', { style: { fontSize: 12.5, color: 'var(--teal, var(--primary))', fontWeight: 600 } }, '\u2713 ' + _t('common.save') + 'd'))));
}

// ---- Pricing / upgrade (Midtrans Snap primary, Xendit fallback; §7.3) ----
const QORA_PLAN_FEATURES = {
  free: ['A few free cases each month', 'Preview every specialty', 'Instant scoring + answer key'],
  monthly: ['Unlimited practice (fair use)', 'Full case library, all specialties', 'OSCE mode, timer & task panel', 'Full model-answer reveal', 'Progress, streaks & badges'],
  annual: ['Everything in Monthly', 'Best value vs paying monthly', 'Priority access to new cases'],
  exam_pass: ['Unlimited practice for one month', 'Built for exam season', 'Full OSCE arc + answer keys'],
};

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


window.QoraV2Screen = QoraV2Screen;
window.QoraDashboard = QoraDashboard;
window.QoraProfile = QoraProfile;
