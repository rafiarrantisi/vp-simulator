// ============================================================
// Qora — English landing + auth (pivot-v4 Phase 5, Stage 2)
// ------------------------------------------------------------
// Primary entry for the multi-specialty English prototype. Self-contained:
// landing -> auth (via window.ApiDataStore.login/signup) -> reload (the App
// re-inits authed and defaults to the Qora catalogue). ADDITIVE: design.css
// tokens only (CSS hash index-Bj97HpXF.css preserved). Legacy eye app stays
// reachable via the "Classic" link. Social login = deferred plug (disabled).
// ============================================================

/* ── Section wrapper ── */
function QLSection(props) {
  return React.createElement('section', { id: props.id, style: {
    padding: '60px 24px',
    background: props.dark ? 'var(--surface-2)' : 'transparent',
    borderBottom: props.dark ? 'none' : '1px solid var(--border)',
  } },
    React.createElement('div', { style: { maxWidth: 'min(920px, calc(100% - 32px))', margin: '0 auto' } },
      props.title && React.createElement('h2', { className: 'au', style: {
        fontSize: 'clamp(22px, 3.5vw, 34px)', fontWeight: 800,
        color: 'var(--text-1)', textAlign: 'center', marginBottom: 8,
        letterSpacing: '-0.01em', lineHeight: 1.2,
      } }, props.title),
      props.subtitle && React.createElement('p', { className: 'au d1', style: {
        fontSize: 14.5, color: 'var(--text-2)', textAlign: 'center',
        maxWidth: 'min(580px, calc(100% - 24px))', margin: '0 auto 40px', lineHeight: 1.7,
      } }, props.subtitle),
      props.children));
}

function QLFeature({ icon, title, body, accent }) {
  return React.createElement('div', { className: 'as', style: {
    padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderTop: accent ? '3px solid var(--primary)' : '1px solid var(--border)',
    boxShadow: 'var(--sh-sm)',
  } },
    React.createElement('div', { style: { fontSize: 26, marginBottom: 10 } }, icon),
    React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', marginBottom: 6 } }, title),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 } }, body));
}

/* ── Stats / Social proof ── */
function QLStats() {
  var items = [
    { icon: '📚', num: '92', label: 'Practice cases' },
    { icon: '🏥', num: '10', label: 'Specialties' },
    { icon: '🎓', num: '2', label: 'Stages: pre-clinical & Koas' },
    { icon: '🧭', num: '2', label: 'Training modes' },
  ];
  return React.createElement('div', { className: 'au', style: {
    display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap',
    margin: '40px auto 0', maxWidth: 'min(780px, 100%)',
  } },
    items.map(function(item, i) {
      return React.createElement('div', { key: item.label, style: {
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '12px 20px', borderRadius: 'var(--r-md)',
        background: 'var(--surface)', border: '1px solid var(--border)',
        boxShadow: 'var(--sh-xs)',
      } },
        React.createElement('span', { style: { fontSize: 20 } }, item.icon),
        React.createElement('div', null,
          React.createElement('div', { style: { fontSize: 18, fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.2 } }, item.num),
          React.createElement('div', { style: { fontSize: 10.5, color: 'var(--text-3)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' } }, item.label)));
    }));
}

/* ── Target Audience ── */
function QLAudience() {
  var groups = [
    { icon: '🎓', title: 'Pre-clinical', body: 'Build history-taking reflexes before you step onto the ward.' },
    { icon: '📋', title: 'Clinical (Koas)', body: 'Sharpen differentials and workup plans against realistic presentations.' },
  ];
  return React.createElement('div', { style: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 12,
  } },
    groups.map(function(g, i) {
      return React.createElement('div', { key: g.title, className: 'as d' + i, style: {
        padding: 20, borderRadius: 'var(--r-lg)',
        background: 'var(--surface)', border: '1px solid var(--border)',
        boxShadow: 'var(--sh-sm)', textAlign: 'center',
      } },
        React.createElement('div', { style: { fontSize: 28, marginBottom: 8 } }, g.icon),
        React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 } }, g.title),
        React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.5 } }, g.body));
    }));
}

/* ── How It Works ── */
function QLHowItWorks() {
  var steps = [
    { icon: '🩺', step: '1', title: 'Conduct the interview', body: 'Ask targeted questions in free text. The AI patient answers only what you ask — just like a real lay patient.' },
    { icon: '📋', step: '2', title: 'List your differentials', body: 'Draft your differential diagnosis, order workup, and propose a management plan before seeing the answer key.' },
    { icon: '📊', step: '3', title: 'Get scored & revealed', body: 'Receive per-item hit/miss scoring, red-flag review, and a full model-answer checklist with management guidelines.' },
    { icon: '🧭', step: '4', title: 'Follow your mentor plan', body: 'Your AI mentor turns every result into a daily mission, targeted coaching, and a readiness report that tells you when you are exam-ready.' },
  ];
  return React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 16 } },
    steps.map(function(s, i) {
      return React.createElement('div', { key: s.title, className: 'as d' + i, style: {
        display: 'flex', gap: 16, alignItems: 'flex-start',
        padding: 20, borderRadius: 'var(--r-lg)',
        background: 'var(--surface)', border: '1px solid var(--border)',
        boxShadow: 'var(--sh-sm)',
      } },
        React.createElement('div', { style: {
          width: 44, height: 44, borderRadius: 'var(--r-md)',
          background: 'var(--primary-l)', color: 'var(--primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, fontWeight: 800, flexShrink: 0,
        } }, s.icon || s.step),
        React.createElement('div', { style: { flex: 1 } },
          React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 } },
            React.createElement('span', { style: {
              fontSize: 11, fontWeight: 800, color: 'var(--primary)',
              background: 'var(--primary-l)', padding: '2px 8px',
              borderRadius: 999, lineHeight: '18px',
            } }, 'Step ' + s.step),
            React.createElement('span', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)' } }, s.title)),
          React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 } }, s.body)));
    }));
}

/* ── Specialties Grid ── */
function QLSpecialties() {
  var list = [
    'Internal Medicine', 'Surgery', 'Paediatrics', 'Obstetrics & Gynaecology',
    'Psychiatry', 'Emergency Medicine', 'Neurology', 'Dermatology',
    'ENT', 'Ophthalmology',
  ];
  return React.createElement('div', { style: {
    display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 10,
  } },
    list.map(function(s, i) {
      return React.createElement('div', { key: s, className: 'as d' + Math.min(i, 5), style: {
        padding: '10px 18px', borderRadius: 'var(--r-full)',
        background: 'var(--surface)', border: '1px solid var(--border)',
        fontSize: 13, fontWeight: 600, color: 'var(--text-1)',
        boxShadow: 'var(--sh-xs)',
      } }, s);
    }));
}

/* ── Region detection ── */
function _detectRegion() {
  // Cached?
  try {
    var cached = localStorage.getItem('qora_region');
    if (cached) return cached;
  } catch (e) {}
  // Try timezone → country → region
  var tz = '';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) {}
  var indoTZ = /^Asia\/(Jakarta|Pontianak|Makassar|Jayapura)$/;
  var aseanTZ = /^Asia\/(Bangkok|Singapore|Kuala_Lumpur|Ho_Chi_Minh|Manila|Phnom_Penh|Vientiane|Yangon)$/;
  if (indoTZ.test(tz)) return 'indo';
  if (aseanTZ.test(tz)) return 'asean';
  // Fallback: navigator.language
  var lang = (navigator.language || 'en-US').toLowerCase();
  if (lang === 'id' || lang === 'id-id') return 'indo';
  // Default: ROW
  return 'row';
}

/* ── Pricing ── */
function QLPricing(props) {
  var region = (props && props.region) || 'row';
  var onFree = props.onFree;
  var onPaid = props.onPaid;
  var prices, accentIdx;
  if (region === 'indo') {
    prices = [
      { id: 'free', name: 'Free Trial', price: 'Rp0', period: '', sessions: '5', features: ['5 sesi gratis tiap 30 hari', 'Hingga 3 kasus berbeda', 'Skoring + kunci jawaban'], cta: 'Coba gratis', accent: false },
      { id: 'monthly', name: 'Bulanan', price: 'Rp119.000', period: '/bln', sessions: 'Tak terbatas', features: ['Praktik tak terbatas', 'Semua spesialisasi & level', 'Skoring + kunci jawaban', 'Misi harian mentor', 'Laporan kesiapan ujian'], cta: 'Langganan', accent: true },
      { id: 'annual', name: 'Tahunan', price: 'Rp999.000', period: '/thn', sessions: 'Tak terbatas', features: ['Praktik tak terbatas', 'Semua spesialisasi & level', 'Skoring + kunci jawaban', 'Misi harian mentor', 'Laporan kesiapan ujian', 'Hemat 30%'], cta: 'Langganan', accent: false },
    ];
    accentIdx = 1;
  } else if (region === 'asean') {
    prices = [
      { id: 'free', name: 'Free Trial', price: '$0', period: '', sessions: 5, features: ['5 free sessions / 30 days', 'Up to 3 cases', 'Full scoring & reveal'], cta: 'Try free', accent: false },
      { id: 'monthly', name: 'Monthly', price: '$9.99', period: '/mo', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Daily mentor missions', 'Exam-readiness report'], cta: 'Subscribe', accent: true },
      { id: 'annual', name: 'Annual', price: '$84', period: '/yr', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Daily mentor missions', 'Exam-readiness report', 'Best value — save 30%'], cta: 'Subscribe', accent: false },
    ];
    accentIdx = 1;
  } else {
    prices = [
      { id: 'free', name: 'Free Trial', price: '$0', period: '', sessions: 5, features: ['5 free sessions / 30 days', 'Up to 3 cases', 'Full scoring & reveal'], cta: 'Try free', accent: false },
      { id: 'monthly', name: 'Monthly', price: '$14.99', period: '/mo', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Daily mentor missions', 'Exam-readiness report'], cta: 'Subscribe', accent: true },
      { id: 'annual', name: 'Annual', price: '$119', period: '/yr', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Daily mentor missions', 'Exam-readiness report', 'Best value — save 34%'], cta: 'Subscribe', accent: false },
    ];
    accentIdx = 1;
  }
  return React.createElement('div', { style: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 16, alignItems: 'start',
  } },
    prices.map(function(p, i) {
      var isAccent = p.accent;
      return React.createElement('div', { key: p.name, className: 'as d' + i, style: {
        padding: 24, borderRadius: 'var(--r-xl)',
        background: isAccent ? 'var(--primary)' : 'var(--surface)',
        border: isAccent ? 'none' : '1px solid var(--border)',
        boxShadow: isAccent ? 'var(--sh-lg)' : 'var(--sh-sm)',
        color: isAccent ? '#fff' : 'var(--text-1)',
        position: 'relative',
      } },
        isAccent && React.createElement('div', { style: {
          position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
          background: 'var(--amber)', color: '#fff', fontSize: 10,
          fontWeight: 800, letterSpacing: '0.05em', textTransform: 'uppercase',
          padding: '3px 14px', borderRadius: 999,
        } }, 'Most popular'),
        React.createElement('div', { style: { fontSize: 14, fontWeight: 700, marginBottom: 4, color: isAccent ? 'rgba(255,255,255,0.8)' : 'var(--text-2)' } }, p.name),
        React.createElement('div', { style: { marginBottom: 16 } },
          React.createElement('span', { style: { fontSize: 28, fontWeight: 800 } }, p.price),
          React.createElement('span', { style: { fontSize: 13, fontWeight: 500, opacity: 0.7 } }, p.period)),
        React.createElement('div', { style: { fontSize: 12, color: isAccent ? 'rgba(255,255,255,0.75)' : 'var(--text-3)', marginBottom: 16 } }, '' + p.sessions + (region === 'indo' ? ' sesi' : ' sessions')),
        React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 } },
          p.features.map(function(f) {
            return React.createElement('div', { key: f, style: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: isAccent ? 'rgba(255,255,255,0.85)' : 'var(--text-2)' } },
              React.createElement('span', { style: { color: isAccent ? '#fff' : 'var(--primary)', fontWeight: 700 } }, '✓'),
              f);
          })),
        React.createElement('button', {
          onClick: function () {
            if (p.id === 'free') { if (typeof onFree === 'function') onFree(); }
            else if (typeof onPaid === 'function') onPaid(p.id);
          },
          style: {
            width: '100%', padding: 12, borderRadius: 12, border: 'none',
            background: isAccent ? '#fff' : 'var(--primary)',
            color: isAccent ? 'var(--primary)' : '#fff',
            fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans',
            cursor: 'pointer', textAlign: 'center',
            boxShadow: isAccent ? '0 4px 14px rgba(92,63,150,0.24)' : 'none',
            transition: 'transform 0.15s ease, box-shadow 0.15s ease',
          },
        }, p.cta));
    }));
}

/* ── Testimonials (carousel) ── */
function QLTestimonial() {
  var quotes = [
    { text: 'Pasien AI-nya nggak gampang bocor — harus benar-benar gali anamnesisnya. Buat latihan OSCE ini ngebantu banget.', name: 'Nadia Prameswari', meta: 'FK Universitas Indonesia · Koas' },
    { text: 'Skor per-item-nya jelas, jadi tahu persis bagian mana yang ke-skip. Model answer-nya juga lengkap.', name: 'Rizky Ramadhan', meta: 'FK Universitas Gadjah Mada · Pre-klinik' },
    { text: 'Misi harian dari mentor bikin latihan jadi terarah, nggak asal buka kasus. Readiness report-nya memotivasi.', name: 'Sinta Maharani', meta: 'FK Universitas Airlangga · Koas' },
  ];
  var idxState = React.useState(0);
  var idx = idxState[0];
  var setIdx = idxState[1];
  var q = quotes[idx % quotes.length];
  var dot = function(i) {
    return React.createElement('button', {
      key: i, onClick: function() { setIdx(i); }, 'aria-label': 'Show testimonial ' + (i + 1),
      style: { width: i === idx ? 22 : 8, height: 8, borderRadius: 999, border: 'none', cursor: 'pointer', background: i === idx ? 'var(--primary)' : 'var(--border)', transition: 'all 0.2s ease', padding: 0 },
    });
  };
  var arrow = function(dir, label) {
    return React.createElement('button', {
      onClick: function() { setIdx((idx + dir + quotes.length) % quotes.length); }, 'aria-label': label,
      style: { width: 34, height: 34, borderRadius: '50%', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 15, fontWeight: 700, cursor: 'pointer', flexShrink: 0 },
    }, dir < 0 ? '‹' : '›');
  };
  return React.createElement('div', { className: 'au', style: {
    maxWidth: 'min(620px, calc(100% - 32px))', margin: '0 auto',
    padding: 28, borderRadius: 'var(--r-xl)',
    background: 'var(--surface)', border: '1px solid var(--border)',
    boxShadow: 'var(--sh-md)', textAlign: 'center',
  } },
    React.createElement('div', { style: { fontSize: 32, marginBottom: 12, opacity: 0.3 } }, '❝'),
    React.createElement('div', { key: idx, style: { fontSize: 15, color: 'var(--text-1)', lineHeight: 1.7, fontStyle: 'italic', marginBottom: 16, minHeight: 78 } }, q.text),
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 18 } },
      React.createElement('div', { style: {
        width: 32, height: 32, borderRadius: '50%',
        background: 'var(--primary-l)', color: 'var(--primary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 14, fontWeight: 700,
      } }, q.name.charAt(0)),
      React.createElement('div', { style: { textAlign: 'left' } },
        React.createElement('div', { style: { fontSize: 12.5, fontWeight: 700, color: 'var(--text-1)' } }, q.name),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, q.meta))),
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14 } },
      arrow(-1, 'Previous testimonial'),
      React.createElement('div', { style: { display: 'flex', gap: 6 } }, quotes.map(function(_, i) { return dot(i); })),
      arrow(1, 'Next testimonial')));
}

/* ── FAQ (accordion) ── */
function QLFAQ() {
  var items = [
    { q: 'What is Qora?', a: 'Qora is an AI-powered clinical interview trainer for medical students. You interview a virtual patient, list your differentials, and get transparent per-item scoring plus a full model-answer reveal.' },
    { q: 'Who is this for?', a: 'Pre-clinical students building history-taking skills and clinical students (koas) preparing for OSCEs — in Indonesian or English.' },
    { q: 'How does scoring work?', a: 'Every case carries a structured checklist. The system evaluates your questions (did you cover the key items?), your differentials (red flags, appropriate breadth), and your management plan — then shows you exactly what you missed. Scores are graded conservatively, never inflated.' },
    { q: 'How many cases are available?', a: '92 practice cases across 10 specialties (internal medicine, surgery, paediatrics, OB-GYN, psychiatry, emergency, neurology, dermatology, ENT, and ophthalmology), with new cases added regularly.' },
    { q: 'What does the AI mentor do?', a: 'Your mentor turns every result into a plan: a daily mission with the right case, targeted coaching on your weak spots, and a readiness report that tells you when you are exam-ready.' },
    { q: 'What do I get for free?', a: '5 free practice sessions every 30 days, across up to 3 different cases — including full scoring and the model-answer reveal. Subscribe for unlimited practice, all cases, mentor journeys, and readiness tracking.' },
    { q: 'Can I use this on mobile?', a: 'Yes — Qora works on desktop, tablet, and phone. The interface adapts to your screen size.' },
    { q: 'Is this a replacement for clinical training?', a: 'No. Qora is a study aid and practice tool. It complements — never replaces — real clinical exposure and supervision.' },
  ];
  // One flat state array to comply with React hooks rules
  var openState = React.useState(function() {
    var arr = new Array(items.length);
    arr[0] = true; // first item open by default
    return arr;
  });
  var openArr = openState[0];
  var setOpenArr = openState[1];
  var toggle = function(i) {
    var next = openArr.slice();
    next[i] = !next[i];
    setOpenArr(next);
  };
  return React.createElement('div', { style: { maxWidth: 'min(640px, calc(100% - 32px))', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 8 } },
    items.map(function(item, i) {
      var isOpen = openArr[i] || false;
      return React.createElement('div', { key: item.q, className: 'as d' + Math.min(i, 3), style: {
        borderRadius: 'var(--r-md)',
        border: '1px solid var(--border)',
        background: 'var(--surface)',
        overflow: 'hidden',
      } },
        React.createElement('div', {
          onClick: function() { toggle(i); },
          style: {
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '14px 18px', cursor: 'pointer', userSelect: 'none',
          },
        },
          React.createElement('span', { style: { fontSize: 13.5, fontWeight: 600, color: 'var(--text-1)' } }, item.q),
          React.createElement('span', { style: { fontSize: 14, color: 'var(--text-3)', transition: 'transform 0.2s ease', transform: isOpen ? 'rotate(180deg)' : 'none' } }, '\u25BE')),
        isOpen && React.createElement('div', { style: {
          padding: '0 18px 14px', fontSize: 13, color: 'var(--text-2)',
          lineHeight: 1.65, borderTop: '1px solid var(--border)',
          margin: '0 18px', paddingTop: 12, marginTop: 0, paddingLeft: 0, paddingRight: 0,
        } }, item.a));
    }));
}

/* ── Footer ── */
function QLFooter() {
  return React.createElement('footer', { style: {
    borderTop: '1px solid var(--border)', background: 'var(--surface)',
    padding: '32px 24px',
  } },
    React.createElement('div', { style: { maxWidth: 'min(920px, calc(100% - 32px))', margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 16 } },
      React.createElement('div', null,
        React.createElement('div', { style: { fontSize: 14, fontWeight: 800, color: 'var(--text-1)' } }, 'Qora'),
        React.createElement('div', { style: { fontSize: 10.5, color: 'var(--text-3)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: 2 } }, 'Clinical Interview Trainer')),
      React.createElement('div', { style: { textAlign: 'right', fontSize: 12, color: 'var(--text-3)', lineHeight: 1.7 } },
        React.createElement('div', null, 'PT Qora Cendekia Medika'),
        React.createElement('div', null, 'info@qora.app · +62 821-2493-3053'),
        React.createElement('div', { style: { marginTop: 4, fontSize: 10.5, color: 'var(--text-3)', opacity: 0.7 } }, '© 2026 Qora. All rights reserved. A study aid, not a medical device.'))));
}

// Load Google Identity Services once (external script).
function _loadGis() {
  return new Promise(function (resolve, reject) {
    if (window.google && window.google.accounts && window.google.accounts.id) return resolve();
    var existing = document.getElementById('gis-script');
    if (existing) {
      var iv = setInterval(function () {
        if (window.google && window.google.accounts && window.google.accounts.id) { clearInterval(iv); resolve(); }
      }, 100);
      setTimeout(function () { clearInterval(iv); reject(new Error('GIS load timeout')); }, 8000);
      return;
    }
    var sc = document.createElement('script');
    sc.src = 'https://accounts.google.com/gsi/client';
    sc.async = true; sc.defer = true; sc.id = 'gis-script';
    sc.onload = function () { resolve(); };
    sc.onerror = function () { reject(new Error('Failed to load Google script')); };
    document.head.appendChild(sc);
  });
}

// Renders the official Google button when VITE_GOOGLE_CLIENT_ID is configured;
// otherwise a disabled placeholder (feature stays off until the owner sets it up).
function QLGoogleButton({ onCredential }) {
  const ref = React.useRef(null);
  const clientId = (typeof window !== 'undefined' && window.QORA_GOOGLE_CLIENT_ID) || '';
  React.useEffect(function () {
    if (!clientId) return undefined;
    let alive = true;
    _loadGis().then(function () {
      if (!alive || !window.google || !window.google.accounts) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: function (resp) { if (resp && resp.credential) onCredential(resp.credential); },
      });
      if (ref.current) {
        window.google.accounts.id.renderButton(ref.current, { theme: 'outline', size: 'large', width: 320, text: 'continue_with', shape: 'pill' });
      }
    }).catch(function () {});
    return function () { alive = false; };
  }, [clientId]);
  if (!clientId) {
    return React.createElement('button', { disabled: true, title: 'Set VITE_GOOGLE_CLIENT_ID to enable', style: { width: '100%', marginTop: 10, padding: '11px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-3)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'not-allowed' } }, 'Continue with Google · coming soon');
  }
  return React.createElement('div', { style: { marginTop: 12, display: 'flex', justifyContent: 'center' } }, React.createElement('div', { ref: ref }));
}

function QLAuth({ mode, setMode, onLogin }) {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [name, setName] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const isSignup = mode === 'signup';

  async function submit() {
    if (busy) return;
    setBusy(true); setErr('');
    try {
      if (!window.ApiDataStore) throw new Error('Backend not configured (set VITE_API_BASE).');
      const s = isSignup
        ? await window.ApiDataStore.signup({ email, password, full_name: name, region: _detectRegion() })
        : await window.ApiDataStore.login(email, password);
      // ApiDataStore already saves to 'ophtha_api_auth'
      try { localStorage.setItem('ophtha_auth', JSON.stringify(s)); } catch (e) {}
      if (onLogin) onLogin(s);
    } catch (e) {
      const m = String((e && e.message) || e);
      setErr(/40[13]|invalid|password|terdaftar|exist/i.test(m)
        ? (isSignup ? 'Could not sign up — that email may already be registered.' : 'Login failed — check your email and password.')
        : m);
      setBusy(false);
    }
  }

  const field = (label, value, set, type, ph) => React.createElement('label', { style: { display: 'block', marginBottom: 12 } },
    React.createElement('div', { style: { fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 5 } }, label),
    React.createElement('input', {
      type: type || 'text', value, onChange: e => set(e.target.value),
      onKeyDown: e => { if (e.key === 'Enter') submit(); }, placeholder: ph, autoComplete: type === 'password' ? 'current-password' : 'on',
      style: { width: '100%', padding: '11px 13px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Plus Jakarta Sans', color: 'var(--text-1)' },
    }));

  return React.createElement('div', { className: 'as', style: { maxWidth: 'min(400px, calc(100% - 32px))', margin: '40px auto', padding: 28, borderRadius: 'var(--r-xl)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-lg)' } },
    React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, isSignup ? 'Create your account' : 'Welcome back'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 20 } }, isSignup ? 'Start practising clinical interviews in minutes.' : 'Log in to continue your practice.'),
    isSignup && field('Full name', name, setName, 'text', 'Your name'),
    field('Email', email, setEmail, 'email', 'you@example.com'),
    field('Password', password, setPassword, 'password', '••••••••'),
    err && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--red-d)', marginBottom: 12 } }, err),
    React.createElement('button', { onClick: submit, disabled: busy, style: { width: '100%', padding: '12px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', opacity: busy ? 0.7 : 1 } }, busy ? 'Please wait\u2026' : (isSignup ? 'Create account' : 'Log in')),
    React.createElement(QLGoogleButton, { onCredential: async function (cred) {
      if (busy) return;
      setBusy(true); setErr('');
      try {
        const sess = await window.ApiDataStore.googleLogin(cred);
        try { localStorage.setItem('ophtha_auth', JSON.stringify(sess)); } catch (e) {}
        if (onLogin) onLogin(sess);
      } catch (e) { setErr('Google sign-in failed \u2014 ' + ((e && e.message) || e)); setBusy(false); }
    } }),
    React.createElement('div', { style: { textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--text-2)' } },
      isSignup ? 'Already have an account? ' : "Don't have an account? ",
      React.createElement('button', { onClick: () => { setErr(''); setMode(isSignup ? 'login' : 'signup'); }, style: { border: 'none', background: 'none', color: 'var(--primary)', fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', fontSize: 13 } }, isSignup ? 'Log in' : 'Sign up')));
}

function QoraLanding({ onLogin, onSubscribe }) {
  const [view, setView] = React.useState('landing'); // landing | auth
  const [mode, setMode] = React.useState('login');
  const [region, setRegion] = React.useState('');
  React.useEffect(function () {
    var r = _detectRegion();
    setRegion(r);
    if (typeof window.__setLocale === 'function') window.__setLocale(r);
  }, []);
  const go = (m) => { setMode(m); setView('auth'); };
  // Pricing CTA → checkout. Logged-out visitors pick the plan now; after
  // login/signup the App's handleLogin resumes the checkout flow.
  const pickPlan = (id) => {
    if (typeof onSubscribe === 'function') onSubscribe(id);
    try { localStorage.setItem('qora_pending_checkout', id); } catch (e) {}
    go('signup');
  };

  const header = React.createElement('header', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', maxWidth: 'min(1080px, calc(100% - 32px))', margin: '0 auto' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'baseline', gap: 8 } },
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', letterSpacing: '-0.02em' } }, 'Qora'),
      React.createElement('div', { style: { fontSize: 9, color: 'var(--text-3)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' } }, 'Clinical interview trainer')),
    React.createElement('div', { style: { display: 'flex', gap: 8 } },
      React.createElement('button', { onClick: () => go('login'), style: { padding: '7px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Log in'),
      React.createElement('button', { onClick: () => go('signup'), style: { padding: '7px 16px', borderRadius: 10, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Get started')));

  if (view === 'auth') {
    return React.createElement('div', { style: { minHeight: '100vh' } }, header,
      React.createElement(QLAuth, { mode, setMode, onLogin }));
  }

  return React.createElement('div', { style: { minHeight: '100vh', position: 'relative', overflow: 'hidden' } },
    // Subtle decorative background (revision §1.3) — kept light & clean.
    React.createElement('div', { style: { position: 'absolute', inset: 0, zIndex: -1, overflow: 'hidden', pointerEvents: 'none' } },
      React.createElement('div', { style: { position: 'absolute', width: 520, height: 520, borderRadius: '50%', top: -180, right: -140, background: 'radial-gradient(circle, rgba(92,63,150,0.12) 0%, rgba(92,63,150,0) 70%)' } }),
      React.createElement('div', { style: { position: 'absolute', width: 420, height: 420, borderRadius: '50%', top: '30%', left: -150, background: 'radial-gradient(circle, rgba(155,74,150,0.10) 0%, rgba(155,74,150,0) 70%)' } }),
      React.createElement('div', { style: { position: 'absolute', width: 260, height: 260, borderRadius: '50%', top: '62%', right: -80, border: '1.5px solid rgba(92,63,150,0.10)' } })),
    header,
    // ── Hero ──
    React.createElement('section', { style: { padding: '60px 24px 20px' } },
      React.createElement('div', { style: { maxWidth: 'min(900px, 100%)', margin: '0 auto', textAlign: 'center' } },
        React.createElement('div', { className: 'au', style: { display: 'inline-block', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--primary)', background: 'var(--primary-l)', padding: '5px 12px', borderRadius: 999, marginBottom: 20 } }, 'Beta \u00b7 for medical students'),
        React.createElement('h1', { className: 'au', style: { fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.1, letterSpacing: '-0.02em', marginBottom: 18 } },
          'Practise the patient interview, ',
          React.createElement('span', { style: { color: 'var(--primary)' } }, 'across every specialty.')),
        React.createElement('p', { className: 'au d1', style: { fontSize: 16, color: 'var(--text-2)', lineHeight: 1.7, maxWidth: 'min(620px, 100%)', margin: '0 auto 28px' } },
          'Interview an AI patient who answers only what you ask \u2014 then get instant, transparent scoring and a full model-answer reveal, guided by your personal AI mentor.'),
        React.createElement('div', { className: 'au d2', style: { display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 12, flexWrap: 'wrap' } },
          React.createElement('button', { onClick: () => go('signup'), style: { padding: '13px 26px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer', boxShadow: 'var(--sh-md)' } }, 'Start practising free'),
          React.createElement('button', { onClick: () => go('login'), style: { padding: '13px 22px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 15, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'I have an account')),
        // Stats
        React.createElement(QLStats, null))),

    // ── For whom ──
    React.createElement(QLSection, { title: 'Built for your stage of training', subtitle: 'From pre-clinical foundations to koas OSCE preparation \u2014 Qora adapts to where you are.' },
      React.createElement(QLAudience, null)),

    // ── How it works ──
    React.createElement(QLSection, { id: 'how-it-works', title: 'How it works', subtitle: 'Four steps from patient encounter to exam readiness.', dark: true },
      React.createElement(QLHowItWorks, null)),

    // ── Specialties ──
    React.createElement(QLSection, { id: 'specialties', title: '92 cases across 10 specialties', subtitle: 'Internal medicine, surgery, paediatrics, OB-GYN, psychiatry, emergency, neurology, dermatology, ENT, and ophthalmology \u2014 with more added regularly.' },
      React.createElement(QLSpecialties, null)),

    // ── Features ──
    React.createElement(QLSection, { id: 'features', title: 'Why Qora is different', subtitle: 'Built like a real examination — not a chatbot quiz.', dark: true },
      React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, textAlign: 'left' } },
        React.createElement(QLFeature, { icon: '\uD83D\uDDE3\uFE0F', title: 'Patients that make you ask', body: 'Like a real lay patient, they answer only what you ask and never volunteer the full story. You learn to elicit \u2014 not just receive.', accent: true }),
        React.createElement(QLFeature, { icon: '\uD83C\uDFAF', title: 'Transparent, calibrated scoring', body: 'Per-item hit/miss against a structured checklist, red-flag screening, and reasoning \u2014 graded conservatively, never inflated.', accent: true }),
        React.createElement(QLFeature, { icon: '\uD83D\uDDDD\uFE0F', title: 'Full answer-key reveal', body: 'After every case, see exactly what a complete workup should have covered \u2014 the checklist, red flags, differentials and management.', accent: true }),
        React.createElement(QLFeature, { icon: '🧭', title: 'A mentor, not just a score', body: 'Daily missions, targeted coaching on your weak spots, and a readiness report \u2014 your practice compounds into exam readiness.', accent: true }))),

    // ── Pricing ──
    React.createElement(QLSection, { id: 'pricing', title: 'Simple, transparent pricing', subtitle: 'Start free, then subscribe when you’re ready to practise without limits.' },
      React.createElement(QLPricing, { region: region, onFree: function () { go('signup'); }, onPaid: pickPlan })),

    // ── Outcomes: feedback, modes, progress ──
    React.createElement(QLSection, { title: 'Turn practice into progress', subtitle: 'Every session feeds the same progress engine behind your dashboard and your mentor plan.' },
      React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, textAlign: 'left' } },
        React.createElement(QLFeature, { icon: '📝', title: 'Detailed feedback after every case', body: 'Per-item hit/miss, red-flag screening, differentials and management reviewed against a structured checklist — then the full model answer is revealed.' }),
        React.createElement(QLFeature, { icon: '🧭', title: 'Two training modes', body: 'Anamnesis practice for focused history-taking with an optional timer, or the full OSCE exam — history, physical exam, investigations, differentials and management under countdown.' }),
        React.createElement(QLFeature, { icon: '📈', title: 'Progress you can measure', body: 'XP, levels, streaks, per-specialty coverage, a skill radar across 8 core dimensions, and a readiness report that tells you when you are exam-ready.' }))),

    // ── Testimonials ──
    React.createElement(QLSection, { title: 'What early users say', subtitle: 'Medical students across Indonesia practise with Qora every week.', dark: true },
      React.createElement(QLTestimonial, null)),

    // ── FAQ ──
    React.createElement(QLSection, { id: 'faq', title: 'Frequently asked questions' },
      React.createElement(QLFAQ, null)),

    // ── Closing CTA ──
    React.createElement('section', { style: { padding: '70px 24px' } },
      React.createElement('div', { className: 'au', style: {
        maxWidth: 'min(720px, calc(100% - 32px))', margin: '0 auto', textAlign: 'center',
        padding: '48px 32px', borderRadius: 'var(--r-xl)',
        background: 'var(--primary)', color: '#fff', boxShadow: 'var(--sh-lg)',
      } },
        React.createElement('div', { style: { fontSize: 'clamp(22px, 3.5vw, 30px)', fontWeight: 800, marginBottom: 10, letterSpacing: '-0.01em' } }, 'Your first patient is waiting.'),
        React.createElement('div', { style: { fontSize: 14, opacity: 0.85, marginBottom: 24, lineHeight: 1.6 } }, '5 free sessions. No credit card. Two minutes to your first interview.'),
        React.createElement('button', { onClick: () => go('signup'), style: { padding: '13px 30px', borderRadius: 12, border: 'none', background: '#fff', color: 'var(--primary)', fontSize: 15, fontWeight: 800, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, 'Start practising free'))),

    // ── Footer ──
    React.createElement(QLFooter, null));
}

window.QoraLanding = QoraLanding;
