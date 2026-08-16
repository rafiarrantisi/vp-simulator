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
  var base = { padding: '10px 18px', borderRadius: 12, border: 'none', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', transition: 'all 0.18s ease' };
  if (kind === 'primary') return Object.assign({}, base, { background: 'var(--primary)', color: '#fff' });
  if (kind === 'ghost') return Object.assign({}, base, { background: 'var(--surface)', color: 'var(--text-2)', border: '1px solid var(--border)' });
  if (kind === 'danger') return Object.assign({}, base, { background: 'var(--red-l)', color: 'var(--red-d)', border: '1px solid var(--red)' });
  return base;
};

function _mtBar(fillPct, height) {
  return React.createElement('div', { style: { height: height || 8, borderRadius: 99, background: 'var(--surface-3)', overflow: 'hidden' } },
    React.createElement('div', { style: { width: Math.max(0, Math.min(100, fillPct)) + '%', height: '100%', borderRadius: 99, background: 'var(--primary)', transition: 'width 0.5s ease' } }));
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
    React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, '🎓 ' + _mt('mentor.title')),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 16, lineHeight: 1.6 } }, _mt('mentor.subtitle')),
    React.createElement('div', Object.assign({}, _mtCard, { padding: 16 }),
      React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 } }, '💬 ' + _mt('mentor.tell_qora')),
      React.createElement('textarea', {
        value: story, onChange: function (e) { setStory(e.target.value); },
        placeholder: _mt('mentor.chat_placeholder'),
        rows: 3, maxLength: 2000,
        style: { width: '100%', boxSizing: 'border-box', resize: 'none', padding: '12px 14px', borderRadius: 16, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 14, fontFamily: 'Poppins', outline: 'none' },
      }),
      err && React.createElement('div', { style: { marginTop: 8, fontSize: 12, color: 'var(--red-d)', background: 'var(--red-l)', padding: '8px 12px', borderRadius: 10 } }, '⚠️ ' + err),
      React.createElement('div', { style: { display: 'flex', justifyContent: 'flex-end', marginTop: 10 } },
        React.createElement('button', Object.assign({ onClick: submit, disabled: busy || !story.trim() }, _mtBtn('primary'), { opacity: busy ? 0.6 : 1 }),
          busy ? '…' : _mt('mentor.send')))));
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
  var startPct = r.target > 0 ? Math.round(100 * (r.start || 0) / r.target) : 0;

  return React.createElement('div', { className: 'au', style: { maxWidth: 640, margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', Object.assign({}, _mtCard, { padding: 20 }),
      React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, '🎓 ' + _mt('mentor.your_journey')),
      React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--primary)', marginBottom: 2 } }, '📋 ' + (proposal.package_name || j.package_name || '')),
      React.createElement('div', { style: { fontSize: 12, color: 'var(--text-2)', marginBottom: 10 } },
        '⏱ ' + _mt('mentor.days').replace('{d}', proposal.duration_days || '').replace('{m}', '45-60'),
        ' · 🎯 ' + _mt('mentor.target_readiness') + ': ' + (r.target || 80) + '%'),
      React.createElement('div', { style: { marginBottom: 4, fontSize: 11, color: 'var(--text-3)' } }, _mt('mentor.readiness_start') + ': ' + (r.start || 0) + '%'),
      _mtBar(startPct, 10),
      React.createElement('div', { style: { marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 } },
        cases.map(function (c) {
          var locked = c.day > 1;
          var dayStyle = locked
            ? { background: 'var(--surface-2)', border: '1px solid var(--border)', opacity: 0.6 }
            : { background: 'var(--surface)', border: '1px solid var(--primary)', boxShadow: 'var(--sh-sm)' };
          return React.createElement('div', { key: c.day, style: Object.assign({ padding: '10px 14px', borderRadius: 'var(--r-md)' }, dayStyle) },
            React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 } },
              React.createElement('div', { style: { fontWeight: 700, fontSize: 13, color: 'var(--text-1)' } },
                'Day ' + c.day + ': ' + (c.focus_area || c.case_id)),
              React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)', whiteSpace: 'nowrap' } },
                '~' + (c.estimated_minutes || 15) + ' min')),
            React.createElement('div', { style: { marginTop: 4, fontSize: 11, color: 'var(--text-2)' } },
              '🩺 ' + c.case_id + ' · ' + (locked ? '🔒 ' + _mt('mentor.locked').replace('{d}', c.day - 1) : '✅ ' + _mt('mentor.available_now'))));
        })),
      proposal.reasoning && React.createElement('div', { style: { marginTop: 14, padding: '12px 14px', borderRadius: 'var(--r-md)', background: 'var(--violet-l)', border: '1px solid var(--violet)', fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 } },
        React.createElement('div', { style: { fontWeight: 700, color: 'var(--violet)', marginBottom: 4 } }, '💡 ' + _mt('mentor.reasoning')),
        proposal.reasoning),
      changes.length > 0 && React.createElement('div', { style: { marginTop: 10, fontSize: 11, color: 'var(--teal-d)', background: 'var(--teal-l)', padding: '8px 12px', borderRadius: 10 } },
        '🔄 ' + _mt('mentor.changes') + ': ' + changes.join(', ')),
      err && React.createElement('div', { style: { marginTop: 10, fontSize: 12, color: 'var(--red-d)', background: 'var(--red-l)', padding: '8px 12px', borderRadius: 10 } }, '⚠️ ' + err),
      React.createElement('div', { style: { marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' } },
        React.createElement('button', Object.assign({ onClick: props.onAccept }, _mtBtn('primary')), '🚀 ' + _mt('mentor.accept')),
        React.createElement('button', Object.assign({ onClick: function () { props.onCancel(); } }, _mtBtn('ghost')), _mt('mentor.cancel')))),
    React.createElement('div', Object.assign({}, _mtCard, { marginTop: 12, padding: 14 }),
      React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 } }, '✏️ ' + _mt('mentor.customize')),
      React.createElement('div', { style: { display: 'flex', gap: 8 } },
        React.createElement('input', {
          value: fb, onChange: function (e) { setFb(e.target.value); },
          placeholder: _mt('mentor.customize_feedback'),
          onKeyDown: function (e) { if (e.key === 'Enter') customize(); },
          style: { flex: 1, minWidth: 0, padding: '9px 12px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 13, fontFamily: 'Poppins', outline: 'none' },
        }),
        React.createElement('button', Object.assign({ onClick: customize, disabled: busy || !fb.trim() }, _mtBtn('ghost'), { whiteSpace: 'nowrap' }), busy ? '…' : '↻'))));
}

// ── QJourneyDashboard: active journey tracking ──────────────────────────
function QJourneyDashboard(props) {
  var j = props.journey;
  var cases = j.cases || [];
  var progress = j.progress || {};
  var r = j.readiness || {};
  var today = cases.filter(function (c) { return c.status === 'available' || c.status === 'in_progress'; })[0] || null;
  var done = progress.completed || 0;
  var total = progress.total || 0;

  function startCase(c) {
    // Navigate via hash ONLY — the App's hashchange listener maps
    // #/cases/<id> → cases screen, and QoraV2Screen reads the full hash
    // on mount (calling onNav('cases') would clobber the case id).
    try { window.location.hash = '#/cases/' + c.case_id; } catch (e) {}
  }

  return React.createElement('div', { className: 'au', style: { maxWidth: 640, margin: '0 auto', padding: '24px 16px' } },
    React.createElement('div', Object.assign({}, _mtCard, { padding: 20 }),
      React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', marginBottom: 2 } }, '🎓 ' + _mt('mentor.title')),
      React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', marginBottom: 10 } }, '📋 ' + (j.package_name || '')),
      React.createElement('div', { style: { marginBottom: 4, fontSize: 12, color: 'var(--text-2)' } },
        _mt('mentor.progress').replace('{d}', j.current_day || 1).replace('{n}', total).replace('{p}', progress.percent || 0)),
      _mtBar(progress.percent || 0, 10),
      React.createElement('div', { style: { marginTop: 14, marginBottom: 4, fontSize: 12, color: 'var(--text-2)' } },
        _mt('mentor.readiness') + ': ' + (r.current != null ? r.current : r.start || 0) + '% → ' + _mt('mentor.target_readiness') + ' ' + (r.target || 80) + '%'),
      _mtBar(r.target > 0 ? Math.round(100 * (r.current != null ? r.current : (r.start || 0)) / r.target) : 0, 10),
      today && React.createElement('div', { style: { marginTop: 16, padding: '12px 14px', borderRadius: 'var(--r-md)', border: '1px solid var(--primary)', background: 'var(--primary-l)' } },
        React.createElement('div', { style: { fontSize: 11, fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.06em' } }, '📌 ' + _mt('mentor.today')),
        React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', margin: '4px 0 2px' } },
          'Day ' + today.day + ': ' + (today.focus_area || today.case_id)),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-2)', marginBottom: 10 } }, '🩺 ' + today.case_id + ' · ~' + (today.estimated_minutes || 15) + ' min'),
        React.createElement('button', Object.assign({ onClick: function () { startCase(today); } }, _mtBtn('primary')), _mt('mentor.start_case'))),
      React.createElement('div', { style: { marginTop: 14, display: 'flex', flexDirection: 'column', gap: 6 } },
        cases.map(function (c) {
          var st = c.status;
          var icon = st === 'completed' ? '✅' : st === 'available' || st === 'in_progress' ? '▶️' : '🔒';
          var color = st === 'completed' ? 'var(--teal)' : st === 'available' || st === 'in_progress' ? 'var(--primary)' : 'var(--text-3)';
          return React.createElement('button', {
            key: c.day,
            onClick: function () { if (st === 'available' || st === 'in_progress') startCase(c); },
            style: Object.assign({ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, padding: '8px 12px', borderRadius: 'var(--r-md)', background: 'var(--surface)', border: '1px solid var(--border)', fontFamily: 'Poppins', cursor: st === 'available' || st === 'in_progress' ? 'pointer' : 'default', width: '100%', textAlign: 'left' }),
          },
            React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-1)' } }, icon + ' Day ' + c.day + ': ' + (c.focus_area || c.case_id)),
            React.createElement('div', { style: { fontSize: 11, fontWeight: 700, color: color } },
              st === 'completed' ? (c.score != null ? c.score + '%' : '✓') : st === 'available' || st === 'in_progress' ? _mt('mentor.start_case') : '🔒'));
        })),
      React.createElement('div', { style: { marginTop: 14, display: 'flex', justifyContent: 'flex-end', gap: 8 } },
        props.onReport && React.createElement('button', Object.assign({ onClick: props.onReport }, _mtBtn('ghost')), '📊 ' + _mt('mentor.view_report')),
        React.createElement('button', Object.assign({ onClick: props.onAbandon }, _mtBtn('danger')), _mt('mentor.abandon')))));
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
            fontSize: 12.5, fontWeight: tab === t[0] ? 700 : 500, fontFamily: 'Poppins',
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
        React.createElement('button', Object.assign({ onClick: function () { setView('dashboard'); } }, _mtBtn('ghost')), '← ' + _mt('mentor.back_to_journey'))),
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
