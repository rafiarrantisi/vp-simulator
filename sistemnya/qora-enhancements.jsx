// ============================================================
// Qora — Phase A enhancements: skill chart, session history,
// settings panel, i18n helpers
// ------------------------------------------------------------
// Self-contained components that extend qora-v2.jsx without
// modifying the original. Additive — loaded after qora-v2.jsx
// in the bundle LOAD_ORDER.
// ============================================================

// ── i18n shortcut ──
var _t = window.__t || function (k) { return k; };

// ── SVG Radar / Spider chart for skill breakdown ──
function QSkillRadar(props) {
  var dims = props.dims || {};
  var keys = Object.keys(dims);
  var n = keys.length;
  if (n < 3) return React.createElement('div', { style: { fontSize: 12, color: 'var(--text-3)', textAlign: 'center', padding: 20 } }, 'Complete a few cases across different specialties to see your skill radar.');

  var size = props.size || 180;
  var cx = size / 2, cy = size / 2, r = size / 2 - 16;
  var slice = 2 * Math.PI / n;
  var L = { history_coverage: _t('dashboard.dim_history_coverage'), red_flags: _t('dashboard.dim_red_flags'), ice_fife: _t('dashboard.dim_ice_fife'), questioning_technique: _t('dashboard.dim_questioning_technique'), communication: _t('dashboard.dim_communication'), diagnostic_reasoning: _t('dashboard.dim_diagnostic_reasoning'), investigations: _t('dashboard.dim_investigations'), management: _t('dashboard.dim_management'), clinical_safety: _t('dashboard.dim_clinical_safety'), coverage: 'Coverage', fife: 'FIFE', redFlags: 'Red flags' };
  var rings = [0.25, 0.5, 0.75, 1.0];
  var elements = [];

  rings.forEach(function (pct) {
    var pts = [];
    for (var i = 0; i <= n; i++) {
      var angle = -Math.PI / 2 + slice * (i % n);
      pts.push((cx + r * pct * Math.cos(angle)).toFixed(1) + ',' + (cy + r * pct * Math.sin(angle)).toFixed(1));
    }
    elements.push(React.createElement('polygon', { key: 'r' + pct, points: pts.join(' '), fill: 'none', stroke: 'var(--border)', strokeWidth: 1, opacity: 0.5 }));
  });

  for (var i = 0; i < n; i++) {
    var angle = -Math.PI / 2 + slice * i;
    elements.push(React.createElement('line', { key: 'a' + i, x1: cx, y1: cy, x2: (cx + r * Math.cos(angle)), y2: (cy + r * Math.sin(angle)), stroke: 'var(--border)', strokeWidth: 1, opacity: 0.3 }));
  }

  var dataPts = [];
  for (var i = 0; i <= n; i++) {
    var angle = -Math.PI / 2 + slice * (i % n);
    var val = (dims[keys[i % n]] || 0) / 100;
    dataPts.push((cx + r * val * Math.cos(angle)).toFixed(1) + ',' + (cy + r * val * Math.sin(angle)).toFixed(1));
  }
  elements.push(React.createElement('polygon', { points: dataPts.join(' '), fill: 'var(--primary)', fillOpacity: 0.15, stroke: 'var(--primary)', strokeWidth: 2 }));

  for (var i = 0; i < n; i++) {
    var angle = -Math.PI / 2 + slice * i;
    var val = (dims[keys[i]] || 0) / 100;
    elements.push(React.createElement('circle', { key: 'd' + i, cx: cx + r * val * Math.cos(angle), cy: cy + r * val * Math.sin(angle), r: 4, fill: 'var(--primary)', stroke: '#fff', strokeWidth: 2 }));
  }

  for (var i = 0; i < n; i++) {
    var angle = -Math.PI / 2 + slice * i;
    var label = L[keys[i]] || keys[i];
    var pct = Math.round(dims[keys[i]] || 0);
    elements.push(React.createElement('text', { key: 'l' + i, x: cx + (r + 20) * Math.cos(angle), y: cy + (r + 20) * Math.sin(angle), textAnchor: 'middle', dominantBaseline: 'central', fontSize: 9, fontWeight: 600, fill: 'var(--text-1)', fontFamily: 'Poppins' }, label + ' ' + pct + '%'));
  }

  return React.createElement('svg', { width: size, height: size + 10, viewBox: '0 0 ' + size + ' ' + size, style: { display: 'block', margin: '0 auto' } }, elements);
}

// ── Session History Screen ──
function QoraSessions(props) {
  var onNav = props.onNav;
  var sessionsState = React.useState(null);
  var sessions = sessionsState[0];
  var setSessions = sessionsState[1];
  var specLabel = { internal_medicine: 'Internal Medicine', surgery: 'Surgery', paediatrics: 'Paediatrics', obstetrics_gynaecology: 'Obs & Gynae', psychiatry: 'Psychiatry', neurology: 'Neurology', ent: 'ENT', dermatology: 'Dermatology', ophthalmology: 'Ophthalmology', emergency: 'Emergency' };

  React.useEffect(function () {
    qv2Fetch('/api/v2/sessions?limit=50').then(function (d) { setSessions((d && d.sessions) || []); }).catch(function () {});
  }, []);

  function renderSession(s, i) {
    var icon = s.specialty === 'emergency' ? '\uD83D\uDE91' : s.specialty === 'surgery' ? '\uD83D\uDD2A' : s.specialty === 'paediatrics' ? '\uD83D\uDC76' : s.specialty === 'psychiatry' ? '\uD83E\uDDE0' : s.specialty === 'ophthalmology' ? '\uD83D\uDC41' : '\uD83D\uDC89';
    var specName = specLabel[s.specialty] || s.specialty;
    var hasScore = s.score != null;
    var detail = hasScore ? ' \u00B7 ' + _t('result.overall_score') + ': ' + s.score : ' \u00B7 ' + (s.status || 'In progress');
    var badge = hasScore ? s.score + '%' : '...';
    return React.createElement('div', { key: s.sessionId || i, className: 'as d' + Math.min(i, 3), style: { display: 'flex', alignItems: 'center', gap: 14, padding: 14, borderRadius: 14, background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-xs)' } },
      React.createElement('div', { style: { width: 42, height: 42, borderRadius: 12, background: 'var(--primary-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 } }, icon),
      React.createElement('div', { style: { flex: 1, minWidth: 0 } },
        React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 2 } }, s.presentation || 'Case'),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, specName + detail)),
      React.createElement('span', { style: { fontSize: 10, fontWeight: 600, padding: '4px 10px', borderRadius: 999, background: hasScore ? 'var(--teal-l)' : 'var(--surface-2)', color: hasScore ? 'var(--teal-d)' : 'var(--text-3)' } }, badge));
  }

  var content;
  if (sessions === null) {
    content = React.createElement('div', { style: { padding: 40, textAlign: 'center', color: 'var(--text-3)' } }, _t('common.loading'));
  } else if (sessions.length === 0) {
    content = React.createElement('div', { style: { padding: 40, textAlign: 'center', color: 'var(--text-3)', background: 'var(--surface)', borderRadius: 16, border: '1px dashed var(--border)' } }, _t('dashboard.no_sessions'));
  } else {
    content = React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 10 } }, sessions.map(renderSession));
  }

  return React.createElement('div', { className: 'au', style: { maxWidth: 860, margin: '0 auto', padding: '28px 20px 60px' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 } },
      React.createElement('button', { onClick: function () { onNav('dashboard'); }, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '\u2190 ' + _t('common.back')),
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)' } }, '\uD83D\uDCCB ' + _t('dashboard.recent_sessions'))),
    content);
}

// ── Settings Panel (full page) ──
function QoraSettings(props) {
  var onNav = props.onNav;
  var dataState = React.useState(null);
  var me = dataState[0];
  var setMe = dataState[1];
  var errState = React.useState('');
  var err = errState[0];
  var setErr = errState[1];
  var savingState = React.useState(false);
  var saving = savingState[0];
  var setSaving = savingState[1];
  var savedState = React.useState(false);
  var saved = savedState[0];
  var setSaved = savedState[1];
  var langState = React.useState('en');
  var lang = langState[0];
  var setLang = langState[1];

  React.useEffect(function () {
    qv2Fetch('/api/users/me').then(function (d) { setMe(d); setLang(d.preferred_language || 'en'); }).catch(function (e) { setErr(String(e.message || e)); });
  }, []);

  async function saveLang() {
    setSaving(true); setErr('');
    try {
      var d = await qv2Fetch('/api/users/me', { method: 'PATCH', body: { preferred_language: lang } });
      setMe(d); setSaved(true); setTimeout(function () { setSaved(false); }, 2000);
    } catch (e) { setErr(String(e.message || e)); }
    setSaving(false);
  }

  var LANGS = [['en', 'English'], ['id', 'Bahasa Indonesia'], ['ms', 'Bahasa Melayu'], ['tl', 'Tagalog'], ['vi', 'Ti\u1EBFng Vi\u1EC7t'], ['th', '\u0E20\u0E32\u0E29\u0E32\u0E44\u0E17\u0E22']];
  var REGION_LABEL = { indo: 'Indonesia', asean: 'ASEAN', row: 'Rest of World' };

  if (!me) return React.createElement('div', { style: { padding: 40, textAlign: 'center', color: 'var(--text-3)' } }, _t('common.loading'));

  return React.createElement('div', { className: 'au', style: { maxWidth: 640, margin: '0 auto', padding: '28px 20px 60px' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 } },
      React.createElement('button', { onClick: function () { onNav('dashboard'); }, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '\u2190 ' + _t('common.back')),
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)' } }, '\u2699\uFE0F ' + _t('profile.settings'))),
    React.createElement('div', { className: 'as', style: { padding: 24, borderRadius: 'var(--r-xl)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)' } },
      React.createElement('div', { style: { marginBottom: 20 } },
        React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 6 } }, _t('profile.language')),
        React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8 } },
          LANGS.map(function (p) {
            var code = p[0], label = p[1];
            return React.createElement('button', { key: code, onClick: function () { setLang(code); }, style: { padding: '8px 16px', borderRadius: 999, fontSize: 12.5, fontFamily: 'Poppins', cursor: 'pointer', fontWeight: lang === code ? 700 : 500, border: '1px solid ' + (lang === code ? 'var(--primary)' : 'var(--border)'), background: lang === code ? 'var(--primary-l)' : 'var(--surface)', color: lang === code ? 'var(--primary)' : 'var(--text-2)' } }, (lang === code ? '\u2713 ' : '') + label);
          }))),
      React.createElement('div', { style: { marginBottom: 20 } },
        React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 } }, _t('profile.region')),
        React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)' } }, REGION_LABEL[me.region] || me.region || 'ROW')),
      React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)', marginBottom: 16 } },
        'Email: ' + me.email + ' \u00B7 ' + _t('dashboard.sessions') + ': ' + (me.total_sessions || 0)),
      err ? React.createElement('div', { style: { fontSize: 12.5, color: 'var(--red-d)', marginBottom: 12 } }, err) : null,
      React.createElement('div', { style: { display: 'flex', gap: 10, alignItems: 'center' } },
        React.createElement('button', { onClick: saveLang, disabled: saving, style: { padding: '11px 22px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: saving ? 0.7 : 1 } }, saving ? 'Saving\u2026' : _t('common.save')),
        saved ? React.createElement('span', { style: { fontSize: 12.5, color: 'var(--teal)', fontWeight: 600 } }, '\u2713 ' + _t('profile.save') + 'd') : null)));
}
