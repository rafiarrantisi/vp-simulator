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
  // Room for axis labels + "%" text around the polygon (they were clipping at
  // the svg edge before — "text cut off top/bottom/left/right" on the dashboard).
  var pad = 44;
  var cx = size / 2 + pad, cy = size / 2 + pad, r = size / 2 - 26;
  var slice = 2 * Math.PI / n;
  var L = { history_coverage: _t('dashboard.dim_history_coverage'), red_flags: _t('dashboard.dim_red_flags'), ice_fife: _t('dashboard.dim_ice_fife'), questioning_technique: _t('dashboard.dim_questioning_technique'), communication: _t('dashboard.dim_communication'), physical_exam: 'Physical Exam', diagnostic_reasoning: _t('dashboard.dim_diagnostic_reasoning'), investigations: _t('dashboard.dim_investigations'), management: _t('dashboard.dim_management'), clinical_safety: _t('dashboard.dim_clinical_safety'), coverage: 'Coverage', fife: 'FIFE', redFlags: 'Red flags' };
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
    elements.push(React.createElement('text', { key: 'l' + i, x: cx + (r + 22) * Math.cos(angle), y: cy + (r + 22) * Math.sin(angle), textAnchor: 'middle', dominantBaseline: 'central', fontSize: 9.5, fontWeight: 600, fill: 'var(--text-1)', fontFamily: 'Poppins' }, label + ' ' + pct + '%'));
  }

  return React.createElement('svg', { width: size + pad * 2, height: size + pad * 2 + 4, viewBox: '0 0 ' + (size + pad * 2) + ' ' + (size + pad * 2), style: { display: 'block', margin: '0 auto', maxWidth: '100%' } }, elements);
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

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(860px, calc(100% - 16px))', margin: '0 auto', padding: '28px 20px 60px' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 } },
      React.createElement('button', { onClick: function () { onNav('dashboard'); }, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '\u2190 ' + _t('common.back')),
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)' } }, '\uD83D\uDCCB ' + _t('dashboard.recent_sessions'))),
    content);
}

// ── Billing / Payment History Page ──
function QoraBilling(props) {
  var onNav = props.onNav;
  var _t = window.__t || function (k) { return k; };
  var dataState = React.useState(null);
  var data = dataState[0];
  var setData = dataState[1];
  var errState = React.useState('');
  var err = errState[0];
  var setErr = errState[1];
  var busyState = React.useState('');
  var busy = busyState[0];
  var setBusy = busyState[1];
  var region = 'row';
  try { region = (localStorage.getItem('qora_region') || 'row'); } catch (e) {}
  var REGION_LABEL = { indo: 'Indonesia', asean: 'ASEAN', row: 'Rest of World' };
  var PRICE_LABEL = {
    indo: { monthly: 'Rp119.000/bln', annual: 'Rp999.000/thn' },
    asean: { monthly: '$9.99/mo', annual: '$84/yr' },
    row: { monthly: '$14.99/mo', annual: '$119/yr' },
  };

  React.useEffect(function () {
    qv2Fetch('/api/billing/history').then(setData).catch(function (e) { setErr(String(e.message || e)); });
  }, []);

  async function upgrade(planId) {
    setBusy(planId); setErr('');
    try {
      var r = await qv2Fetch('/api/billing/xendit/checkout/' + planId, { method: 'POST' });
      if (r && r.checkout_url) { window.location.href = r.checkout_url; return; }
      setErr('Checkout is not available yet.');
    } catch (e) {
      setErr(/not configured|503/i.test(String(e.message || e)) ? 'Payments are not enabled yet — check back soon.' : String(e.message || e));
    }
    setBusy('');
  }

  if (err && !data) return React.createElement('div', { style: { padding: 40, color: 'var(--text-2)', textAlign: 'center' } }, _t('common.error') + ': ' + err);
  if (!data) return React.createElement('div', { style: { padding: 40, color: 'var(--text-3)', textAlign: 'center' } }, _t('common.loading'));

  var isPaid = data.unlimited === undefined ? (data.plan && data.plan !== 'free') : data.unlimited;
  var prices = PRICE_LABEL[region] || PRICE_LABEL.row;
  var usage = data.usage || {};
  var usedSessions = usage.sessions || 0;
  var limit = data.free_session_limit || 3;
  var pct = Math.min(Math.round(usedSessions / limit * 100), 100);

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(760px, calc(100% - 16px))', margin: '0 auto', padding: '28px 20px 60px' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 } },
      React.createElement('button', { onClick: function () { onNav('dashboard'); }, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, '\u2190 ' + _t('common.back')),
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)' } }, '\uD83D\uDCB3 ' + (window.__t ? window.__t('profile.billing', {}) || 'Billing & plan' : 'Billing & plan'))),
    // Current plan card
    React.createElement('div', { className: 'as', style: { padding: 24, borderRadius: 'var(--r-xl)', background: isPaid ? 'var(--primary)' : 'var(--surface)', border: isPaid ? 'none' : '1px solid var(--border)', boxShadow: 'var(--sh-md)', color: isPaid ? '#fff' : 'var(--text-1)', marginBottom: 20 } },
      React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 } },
        React.createElement('div', null,
          React.createElement('div', { style: { fontSize: 12, fontWeight: 600, opacity: 0.75, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 } }, _t('profile.plan', {}) || 'Current plan'),
          React.createElement('div', { style: { fontSize: 22, fontWeight: 800, textTransform: 'capitalize' } }, data.plan || 'free')),
        React.createElement('span', { style: { fontSize: 11, fontWeight: 700, padding: '4px 12px', borderRadius: 999, background: isPaid ? 'rgba(255,255,255,0.2)' : 'var(--surface-2)', color: isPaid ? '#fff' : 'var(--text-2)' } }, isPaid ? '\u2713 Active' : 'Free')),
      isPaid
        ? React.createElement('div', { style: { fontSize: 13, opacity: 0.85 } },
            data.current_period_end ? ('Renews: ' + String(data.current_period_end).slice(0, 10)) : 'Unlimited sessions active')
        : React.createElement('div', null,
            React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 8 } }, usedSessions + ' of ' + limit + ' free sessions used this period'),
            React.createElement('div', { style: { height: 8, borderRadius: 999, background: 'var(--surface-3)', marginBottom: 16 } },
              React.createElement('div', { style: { width: pct + '%', height: '100%', borderRadius: 999, background: pct >= 80 ? 'var(--red)' : 'var(--primary)', transition: 'width 0.6s ease' } })),
            React.createElement('button', { onClick: function () { upgrade('monthly'); }, disabled: !!busy, style: { width: '100%', padding: 13, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: busy ? 0.7 : 1 } },
              busy === 'monthly' ? 'Redirecting\u2026' : ('Upgrade to ' + (prices.monthly || '$14.99/mo')))),
      err && React.createElement('div', { style: { fontSize: 12.5, color: isPaid ? 'rgba(255,255,255,0.9)' : 'var(--red-d)', marginTop: 10 } }, err)),
    // Plan options
    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 20 } },
      React.createElement('button', { onClick: function () { upgrade('monthly'); }, disabled: !!busy, style: { textAlign: 'left', padding: 18, borderRadius: 'var(--r-lg)', border: '1px solid var(--border)', background: 'var(--surface)', cursor: 'pointer', fontFamily: 'Poppins' } },
        React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 } }, 'Monthly'),
        React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--primary)', marginBottom: 2 } }, prices.monthly || '$14.99/mo'),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, 'Cancel anytime')),
      React.createElement('button', { onClick: function () { upgrade('annual'); }, disabled: !!busy, style: { textAlign: 'left', padding: 18, borderRadius: 'var(--r-lg)', border: '2px solid var(--primary)', background: 'var(--primary-l)', cursor: 'pointer', fontFamily: 'Poppins', position: 'relative' } },
        React.createElement('span', { style: { position: 'absolute', top: -10, right: 12, background: 'var(--amber)', color: '#fff', fontSize: 9, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', padding: '2px 10px', borderRadius: 999 } }, 'Best value'),
        React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 } }, 'Annual'),
        React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--primary)', marginBottom: 2 } }, prices.annual || '$119/yr'),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, 'Save ~34%'))),
    // Recent sessions
    React.createElement('div', { className: 'as', style: { padding: 18, borderRadius: 'var(--r-lg)', background: 'var(--surface)', border: '1px solid var(--border)' } },
      React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 12 } }, '\uD83D\uDCCB ' + (_t('dashboard.recent_sessions'))),
      (!data.history || !data.history.length) && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', padding: '12px 0', textAlign: 'center' } }, _t('dashboard.no_sessions')),
      (data.history || []).slice(0, 6).map(function (s, i) {
        return React.createElement('div', { key: s.id || i, style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderTop: '1px solid var(--border)' } },
          React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)' } }, s.caseId || 'Case'),
          React.createElement('span', { style: { fontSize: 12, fontWeight: 700, color: s.totalScore != null ? 'var(--teal-d)' : 'var(--text-3)' } }, s.totalScore != null ? s.totalScore + '%' : (s.status || '—')));
      })));
}

// ── Billing Success / Failed redirect pages ──
function QoraBillingResult(props) {
  var okResult = !!props.ok;
  var onNav = props.onNav;
  var _t = window.__t || function (k) { return k; };
  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(480px, calc(100% - 16px))', margin: '0 auto', padding: '60px 20px', textAlign: 'center' } },
    React.createElement('div', { style: { fontSize: 56, marginBottom: 16 } }, okResult ? '\uD83C\uDF89' : '\uD83D\uDEA8'),
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 8 } },
      okResult ? (window.__t ? window.__t('billing.success', {}) || 'Payment successful!' : 'Payment successful!') : (window.__t ? window.__t('billing.failed', {}) || 'Payment not completed' : 'Payment not completed')),
    React.createElement('div', { style: { fontSize: 13.5, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 28 } },
      okResult
        ? 'Your plan has been activated. You can now practise without limits.'
        : 'No charge was made. You can retry, or contact support if you think this is a mistake.'),
    React.createElement('div', { style: { display: 'flex', gap: 10, justifyContent: 'center' } },
      React.createElement('button', { onClick: function () { onNav('dashboard'); }, style: { padding: '11px 22px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, _t('common.back') + ' \u2192 Dashboard'),
      !okResult && React.createElement('button', { onClick: function () { onNav('billing'); }, style: { padding: '11px 18px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Retry payment')));
}


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

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(640px, calc(100% - 16px))', margin: '0 auto', padding: '28px 20px 60px' } },
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
