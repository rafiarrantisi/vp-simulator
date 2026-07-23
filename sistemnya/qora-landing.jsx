// ============================================================
// Qora — English landing + auth (pivot-v4 Phase 5, Stage 2)
// ------------------------------------------------------------
// Primary entry for the multi-specialty English prototype. Self-contained:
// landing -> auth (via window.ApiDataStore.login/signup) -> reload (the App
// re-inits authed and defaults to the Qora catalogue). ADDITIVE: design.css
// tokens only (CSS hash index-Bj97HpXF.css preserved). Legacy eye app stays
// reachable via the "Classic" link. Social login = deferred plug (disabled).
// ============================================================

function QLFeature({ icon, title, body }) {
  return React.createElement('div', { className: 'as', style: {
    padding: 20, borderRadius: 'var(--r-lg)', background: 'var(--surface)',
    border: '1px solid var(--border)', boxShadow: 'var(--sh-sm)',
  } },
    React.createElement('div', { style: { fontSize: 26, marginBottom: 10 } }, icon),
    React.createElement('div', { style: { fontSize: 15, fontWeight: 700, color: 'var(--text-1)', marginBottom: 6 } }, title),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 } }, body));
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
        ? await window.ApiDataStore.signup({ email, password, full_name: name })
        : await window.ApiDataStore.login(email, password);
      // ApiDataStore sudah save ke 'ophtha_api_auth'
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
    React.createElement('button', { onClick: submit, disabled: busy, style: { width: '100%', padding: '12px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: busy ? 0.7 : 1 } }, busy ? 'Please wait…' : (isSignup ? 'Create account' : 'Log in')),
    React.createElement(QLGoogleButton, { onCredential: async function (cred) {
      if (busy) return;
      setBusy(true); setErr('');
      try {
        const sess = await window.ApiDataStore.googleLogin(cred);
        try { localStorage.setItem('ophtha_auth', JSON.stringify(sess)); } catch (e) {}
        if (onLogin) onLogin(sess);
      } catch (e) { setErr('Google sign-in failed — ' + ((e && e.message) || e)); setBusy(false); }
    } }),
    React.createElement('div', { style: { textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--text-2)' } },
      isSignup ? 'Already have an account? ' : "Don't have an account? ",
      React.createElement('button', { onClick: () => { setErr(''); setMode(isSignup ? 'login' : 'signup'); }, style: { border: 'none', background: 'none', color: 'var(--primary)', fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', fontSize: 13 } }, isSignup ? 'Log in' : 'Sign up')));
}

function QoraLanding({ onLogin }) {
  const [view, setView] = React.useState('landing'); // landing | auth
  const [mode, setMode] = React.useState('login');
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
    React.createElement('main', { style: { maxWidth: 900, margin: '0 auto', padding: '40px 24px 60px', textAlign: 'center' } },
      React.createElement('div', { className: 'au', style: { display: 'inline-block', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--primary)', background: 'var(--primary-l)', padding: '5px 12px', borderRadius: 999, marginBottom: 20 } }, 'Beta · for medical students & IMG exam candidates'),
      React.createElement('h1', { className: 'au', style: { fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.1, letterSpacing: '-0.02em', marginBottom: 18 } },
        'Practise the patient interview, ',
        React.createElement('span', { style: { color: 'var(--primary)' } }, 'across every specialty.')),
      React.createElement('p', { className: 'au', style: { fontSize: 16, color: 'var(--text-2)', lineHeight: 1.7, maxWidth: 620, margin: '0 auto 28px' } },
        'Interview an AI patient who answers only what you ask — then get instant, transparent scoring against a hidden checklist and a full model-answer reveal. From internal medicine to emergency.'),
      React.createElement('div', { className: 'au', style: { display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 48 } },
        React.createElement('button', { onClick: () => go('signup'), style: { padding: '13px 26px', borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', boxShadow: 'var(--sh-md)' } }, 'Start practising free'),
        React.createElement('button', { onClick: () => go('login'), style: { padding: '13px 22px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-1)', fontSize: 15, fontWeight: 600, fontFamily: 'Poppins', cursor: 'pointer' } }, 'I have an account')),
      React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, textAlign: 'left' } },
        React.createElement(QLFeature, { icon: '🗣️', title: 'Patients that make you ask', body: "Like a real lay patient, they answer only what you ask and never volunteer the full story. You learn to elicit — not just receive." }),
        React.createElement(QLFeature, { icon: '🎯', title: 'Transparent, calibrated scoring', body: 'Per-item hit/miss against a hidden checklist, red-flag screening, and reasoning — graded conservatively, never inflated.' }),
        React.createElement(QLFeature, { icon: '🗝️', title: 'Full answer-key reveal', body: 'After every case, see exactly what a complete workup should have covered — the checklist, red flags, differentials and management.' })),
      React.createElement('div', { style: { marginTop: 40, fontSize: 12, color: 'var(--text-3)' } },
        'A study aid, not a medical device. ')));
}

window.QoraLanding = QoraLanding;
