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
    React.createElement('div', { style: { maxWidth: 920, margin: '0 auto' } },
      props.title && React.createElement('h2', { className: 'au', style: {
        fontSize: 'clamp(22px, 3.5vw, 34px)', fontWeight: 800,
        color: 'var(--text-1)', textAlign: 'center', marginBottom: 8,
        letterSpacing: '-0.01em', lineHeight: 1.2,
      } }, props.title),
      props.subtitle && React.createElement('p', { className: 'au d1', style: {
        fontSize: 14.5, color: 'var(--text-2)', textAlign: 'center',
        maxWidth: 580, margin: '0 auto 40px', lineHeight: 1.7,
      } }, props.subtitle),
      props.children));
}

function QLFeature({ icon, title, body }) {
  return React.createElement('div', { className: 'as', style: {
    padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)',
    border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)',
  } },
    React.createElement('div', { style: { fontSize: 26, marginBottom: 10 } }, icon),
    React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', marginBottom: 6 } }, title),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 } }, body));
}

/* ── Stats / Social proof ── */
function QLStats() {
  var items = [
    { icon: '📚', num: '82+', label: 'Cases' },
    { icon: '🏥', num: '10', label: 'Specialties' },
    { icon: '🎯', num: '3', label: 'Difficulty Levels' },
    { icon: '🌍', num: '1,200+', label: 'Users' },
  ];
  return React.createElement('div', { className: 'au', style: {
    display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap',
    margin: '40px auto 0', maxWidth: 780,
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
    { icon: '🌍', title: 'IMG Candidates', body: 'Pass OSCE-style stations with structured, repeatable practice.' },
    { icon: '🩺', title: 'Residents (PPDS)', body: 'Test your diagnostic reasoning across unfamiliar specialties.' },
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
    'Internal Medicine', 'Surgery', 'Pediatrics', 'Obstetrics & Gynaecology',
    'Psychiatry', 'Emergency Medicine', 'Neurology', 'Orthopedics',
    'Ophthalmology', 'Family Medicine',
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
  var prices, accentIdx;
  if (region === 'indo') {
    prices = [
      { name: 'Free Trial', price: 'Rp0', period: '', sessions: '3', features: ['3 sesi gratis', 'Semua spesialisasi', 'Skoring + kunci jawaban'], cta: 'Coba gratis', accent: false },
      { name: 'Bulanan', price: 'Rp119.000', period: '/bln', sessions: 'Tak terbatas', features: ['Praktik tak terbatas', 'Semua spesialisasi & level', 'Skoring + kunci jawaban', 'Pantau progres'], cta: 'Langganan', accent: true },
      { name: 'Tahunan', price: 'Rp999.000', period: '/thn', sessions: 'Tak terbatas', features: ['Praktik tak terbatas', 'Semua spesialisasi & level', 'Skoring + kunci jawaban', 'Pantau progres', 'Hemat 30%'], cta: 'Langganan', accent: false },
    ];
    accentIdx = 1;
  } else if (region === 'asean') {
    prices = [
      { name: 'Free Trial', price: '$0', period: '', sessions: 3, features: ['3 free sessions', 'All specialties', 'Full scoring & reveal'], cta: 'Try free', accent: false },
      { name: 'Monthly', price: '$9.99', period: '/mo', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Progress tracking'], cta: 'Subscribe', accent: true },
      { name: 'Annual', price: '$84', period: '/yr', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Progress tracking', 'Best value — save 30%'], cta: 'Subscribe', accent: false },
    ];
    accentIdx = 1;
  } else {
    prices = [
      { name: 'Free Trial', price: '$0', period: '', sessions: 3, features: ['3 free sessions', 'All specialties', 'Full scoring & reveal'], cta: 'Try free', accent: false },
      { name: 'Monthly', price: '$14.99', period: '/mo', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Progress tracking'], cta: 'Subscribe', accent: true },
      { name: 'Annual', price: '$119', period: '/yr', sessions: 'Unlimited', features: ['Unlimited practice', 'All specialties & levels', 'Full scoring & reveal', 'Progress tracking', 'Best value — save 34%'], cta: 'Subscribe', accent: false },
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
        React.createElement('div', { style: {
          width: '100%', padding: 12, borderRadius: 12, border: 'none',
          background: isAccent ? '#fff' : 'var(--primary)',
          color: isAccent ? 'var(--primary)' : '#fff',
          fontSize: 13, fontWeight: 700, fontFamily: 'Poppins',
          cursor: 'pointer', textAlign: 'center',
        } }, p.cta));
    }));
}

/* ── Testimonial ── */
function QLTestimonial() {
  return React.createElement('div', { className: 'au', style: {
    maxWidth: 620, margin: '0 auto',
    padding: 28, borderRadius: 'var(--r-xl)',
    background: 'var(--surface)', border: '1px solid var(--border)',
    boxShadow: 'var(--sh-md)', textAlign: 'center',
  } },
    React.createElement('div', { style: { fontSize: 32, marginBottom: 12, opacity: 0.3 } }, '❝'),
    React.createElement('div', { style: { fontSize: 15, color: 'var(--text-1)', lineHeight: 1.7, fontStyle: 'italic', marginBottom: 16 } },
      'The AI patient never volunteers the full story — you really have to earn the diagnosis. That changed how I prepare for OSCEs.'),
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 } },
      React.createElement('div', { style: {
        width: 32, height: 32, borderRadius: '50%',
        background: 'var(--primary-l)', color: 'var(--primary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 14, fontWeight: 700,
      } }, 'M'),
      React.createElement('div', { style: { textAlign: 'left' } },
        React.createElement('div', { style: { fontSize: 12.5, fontWeight: 700, color: 'var(--text-1)' } }, 'Medical Student'),
        React.createElement('div', { style: { fontSize: 11, color: 'var(--text-3)' } }, 'Universitas Indonesia'))));
}

/* ── FAQ (accordion) ── */
function QLFAQ() {
  var items = [
    { q: 'What is Qora?', a: 'Qora is an AI-powered clinical interview trainer. You interview virtual patients, list your differentials, and get scored against a hidden checklist \u2014 designed for medical students, IMG candidates, and residents.' },
    { q: 'Who is this for?', a: 'Pre-clinical students building history-taking skills, clinical students (koas) preparing for OSCEs, IMG candidates facing licensing exams, and residents brushing up on specialties outside their core focus.' },
    { q: 'How does scoring work?', a: 'Every case has a hidden checklist. The system evaluates your questions (did you cover the key items?), your differentials (red flags, appropriate breadth), and your management plan \u2014 then shows you exactly what you missed.' },
    { q: 'How many cases are available?', a: 'Currently 82+ cases across 10 specialties at 3 difficulty levels (pre-clinical, clinical, advanced). New cases are added regularly.' },
    { q: 'Can I use this on mobile?', a: 'Yes \u2014 Qora works on desktop, tablet, and phone. The interface adapts to your screen size.' },
    { q: 'Is this a replacement for clinical training?', a: 'No. Qora is a study aid and practice tool. It complements \u2014 never replaces \u2014 real clinical exposure and supervision.' },
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
  return React.createElement('div', { style: { maxWidth: 640, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 8 } },
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
    React.createElement('div', { style: { maxWidth: 920, margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 16 } },
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
    return React.createElement('button', { disabled: true, title: 'Set VITE_GOOGLE_CLIENT_ID to enable', style: { width: '100%', marginTop: 10, padding: '11px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-3)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'not-allowed' } }, 'Continue with Google · coming soon');
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
      style: { width: '100%', padding: '11px 13px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 14, fontFamily: 'Poppins', color: 'var(--text-1)' },
    }));

  return React.createElement('div', { className: 'as', style: { maxWidth: 400, margin: '40px auto', padding: 28, borderRadius: 'var(--r-xl)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-lg)' } },
    React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, isSignup ? 'Create your account' : 'Welcome back'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 20 } }, isSignup ? 'Start practising clinical interviews in minutes.' : 'Log in to continue your practice.'),
    isSignup && field('Full name', name, setName, 'text', 'Your name'),
    field('Email', email, setEmail, 'email', 'you@example.com'),
    field('Password', password, setPassword, 'password', '••••••••'),
    err && React.createElement('div', { style: { fontSize: 12.5, color: 'var(--red-d)', marginBottom: 12 } }, err),
    React.createElement('button', { onClick: submit, disabled: busy, style: { width: '100%', padding: '12px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: busy ? 0.7 : 1 } }, busy ? 'Please wait\u2026' : (isSignup ? 'Create account' : 'Log in')),
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
      React.createElement('button', { onClick: () => { setErr(''); setMode(isSignup ? 'login' : 'signup'); }, style: { border: 'none', background: 'none', color: 'var(--primary)', fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', fontSize: 13 } }, isSignup ? 'Log in' : 'Sign up')));
}

function QoraLanding({ onLogin }) {
  const [view, setView] = React.useState('landing'); // landing | auth
  const [mode, setMode] = React.useState('login');
  const [region, setRegion] = React.useState('');
  React.useEffect(function () {
    setRegion(_detectRegion());
  }, []);
  const go = (m) => { setMode(m); setView('auth'); };

  const header = React.createElement('header', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', maxWidth: 1080, margin: '0 auto' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'baseline', gap: 8 } },
      React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', letterSpacing: '-0.02em' } }, 'Qora'),
      React.createElement('div', { style: { fontSize: 9, color: 'var(--text-3)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' } }, 'Clinical interview trainer')),
    React.createElement('div', { style: { display: 'flex', gap: 8 } },
      React.createElement('button', { onClick: () => go('login'), style: { padding: '7px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Log in'),
      React.createElement('button', { onClick: () => go('signup'), style: { padding: '7px 16px', borderRadius: 10, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer' } }, 'Get started')));

  if (view === 'auth') {
    return React.createElement('div', { style: { minHeight: '100vh' } }, header,
      React.createElement(QLAuth, { mode, setMode, onLogin }));
  }

  return React.createElement('div', { style: { minHeight: '100vh' } }, header,
    // ── Hero ──
    React.createElement('section', { style: { padding: '60px 24px 20px' } },
      React.createElement('div', { style: { maxWidth: 900, margin: '0 auto', textAlign: 'center' } },
        React.createElement('div', { className: 'au', style: { display: 'inline-block', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--primary)', background: 'var(--primary-l)', padding: '5px 12px', borderRadius: 999, marginBottom: 20 } }, 'Beta \u00b7 for medical students & IMG exam candidates'),
        React.createElement('h1', { className: 'au', style: { fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.1, letterSpacing: '-0.02em', marginBottom: 18 } },
          'Practise the patient interview, ',
          React.createElement('span', { style: { color: 'var(--primary)' } }, 'across every specialty.')),
        React.createElement('p', { className: 'au d1', style: { fontSize: 16, color: 'var(--text-2)', lineHeight: 1.7, maxWidth: 620, margin: '0 auto 28px' } },
          'Interview an AI patient who answers only what you ask \u2014 then get instant, transparent scoring against a hidden checklist and a full model-answer reveal. From internal medicine to emergency.'),
        React.createElement('div', { className: 'au d2', style: { display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 12 } },
          React.createElement('button', { onClick: () => go('signup'), style: { padding: '13px 26px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', boxShadow: 'var(--sh-md)' } }, 'Start practising free'),
          React.createElement('button', { onClick: () => go('login'), style: { padding: '13px 22px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 15, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'I have an account')),
        // Stats
        React.createElement(QLStats, null))),

    // ── For whom ──
    React.createElement(QLSection, { title: 'Built for every stage of training', subtitle: 'From pre-clinical foundations to residency-level diagnostic reasoning \u2014 Qora adapts to where you are.' },
      React.createElement(QLAudience, null)),

    // ── How it works ──
    React.createElement(QLSection, { id: 'how-it-works', title: 'How it works', subtitle: 'Three steps from patient encounter to clinical mastery.', dark: true },
      React.createElement(QLHowItWorks, null)),

    // ── Specialties ──
    React.createElement(QLSection, { id: 'specialties', title: '82+ cases across 10 specialties', subtitle: 'Internal medicine, surgery, paediatrics, OB-GYN, psychiatry, emergency, neurology, orthopaedics, ophthalmology, and family medicine \u2014 with more added regularly.' },
      React.createElement(QLSpecialties, null)),

    // ── Features ──
    React.createElement(QLSection, { id: 'features', title: 'Why Qora is different', dark: true },
      React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, textAlign: 'left' } },
        React.createElement(QLFeature, { icon: '\uD83D\uDDE3\uFE0F', title: 'Patients that make you ask', body: 'Like a real lay patient, they answer only what you ask and never volunteer the full story. You learn to elicit \u2014 not just receive.' }),
        React.createElement(QLFeature, { icon: '\uD83C\uDFAF', title: 'Transparent, calibrated scoring', body: 'Per-item hit/miss against a hidden checklist, red-flag screening, and reasoning \u2014 graded conservatively, never inflated.' }),
        React.createElement(QLFeature, { icon: '\uD83D\uDDDD\uFE0F', title: 'Full answer-key reveal', body: 'After every case, see exactly what a complete workup should have covered \u2014 the checklist, red flags, differentials and management.' }))),

    // ── Pricing ──
    React.createElement(QLSection, { id: 'pricing', title: 'Simple, transparent pricing', subtitle: 'Start free, then subscribe when you\\u2019re ready to practise without limits.' },
      React.createElement(QLPricing, { region: region })),

    // ── Testimonial ──
    React.createElement(QLSection, { dark: true, subtitle: 'What early users say' },
      React.createElement(QLTestimonial, null)),

    // ── FAQ ──
    React.createElement(QLSection, { id: 'faq', title: 'Frequently asked questions' },
      React.createElement(QLFAQ, null)),

    // ── Footer ──
    React.createElement(QLFooter, null));
}

window.QoraLanding = QoraLanding;
