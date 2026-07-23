// ============================================================
// Qora — DataStore seam (rebuilt after the OphthaSim cleanup)
// ------------------------------------------------------------
// Self-contained persistence/auth seam for the Qora frontend. The
// previous engine/data-store.js depended on OphthaSim globals
// (loadProfile / CASES from the deleted data.js); this rebuild has
// NO such dependencies — it talks to the FastAPI backend directly and
// falls back to localStorage for client-only preferences.
//
// window.ApiDataStore is what qora-landing.jsx calls for login/signup.
// The Bearer token is stored under 'ophtha_api_auth' (unchanged key so
// existing sessions and qora-v2.jsx's _qv2Token() keep working).
// ============================================================

var API_AUTH_KEY = 'ophtha_api_auth';

function _apiBase() {
  return (typeof window !== 'undefined' && window.OPHTHA_API_BASE) || '';
}

function _readApiAuth() {
  try {
    var raw = localStorage.getItem(API_AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) { return null; }
}

// ── Silent access-token refresh ──
// On a 401, exchange the refresh_token for a fresh access token and retry once.
// Concurrent callers share one in-flight refresh. If refresh also fails, the
// session is truly expired: clear it and bounce to the landing/login.
var _refreshInFlight = null;

function _qoraRefreshToken() {
  var auth = _readApiAuth();
  if (!auth || !auth.refresh_token) return Promise.resolve(null);
  if (_refreshInFlight) return _refreshInFlight;
  _refreshInFlight = (async function () {
    try {
      var res = await fetch(_apiBase() + '/api/auth/refresh', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: auth.refresh_token }),
      });
      var json = null; try { json = await res.json(); } catch (e) { json = null; }
      if (!res.ok || !json || json.success === false || !json.data || !json.data.token) {
        try { localStorage.removeItem(API_AUTH_KEY); } catch (e) {}
        if (typeof window !== 'undefined' && !window.__qoraExpiredReload) {
          window.__qoraExpiredReload = true;
          setTimeout(function () { window.location.reload(); }, 50);
        }
        return null;
      }
      try { localStorage.setItem(API_AUTH_KEY, JSON.stringify(json.data)); } catch (e) {}
      return json.data.token;
    } catch (e) {
      return null;
    } finally {
      _refreshInFlight = null;
    }
  })();
  return _refreshInFlight;
}

async function _apiFetch(path, opts, _retried) {
  opts = opts || {};
  var headers = { 'Content-Type': 'application/json' };
  var auth = _readApiAuth();
  if (auth && auth.token) headers['Authorization'] = 'Bearer ' + auth.token;
  var res = await fetch(_apiBase() + path, {
    method: opts.method || 'GET',
    headers: headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 401 && !_retried && path.indexOf('/api/auth/') !== 0) {
    var nt = await _qoraRefreshToken();
    if (nt) return _apiFetch(path, opts, true);
  }
  var json = null;
  try { json = await res.json(); } catch (e) { json = null; }
  if (!res.ok || (json && json.success === false)) {
    // Never swallow the error — let the UI surface / retry (contract §3).
    var msg = (json && (json.error || (json.detail && json.detail.message))) || ('HTTP ' + res.status);
    throw new Error(msg);
  }
  return json ? json.data : null;
}

// ── Client-only preferences (no backend endpoint) ──
var LocalPrefs = {
  loadSettings: function () {
    try {
      var s = localStorage.getItem('ophtha_settings');
      return Promise.resolve(s ? JSON.parse(s) : null);
    } catch (e) { return Promise.resolve(null); }
  },
  saveSettings: function (s) {
    try { localStorage.setItem('ophtha_settings', JSON.stringify(s)); } catch (e) {}
    return Promise.resolve();
  },
};

var ApiDataStore = {
  // — auth —
  login: async function (email, password) {
    var s = await _apiFetch('/api/auth/login', {
      method: 'POST', body: { email: email, password: password },
    });
    await ApiDataStore.saveAuth(s);
    return s;
  },
  signup: async function (payload) {
    var s = await _apiFetch('/api/auth/signup', { method: 'POST', body: payload });
    await ApiDataStore.saveAuth(s);
    return s;
  },
  googleLogin: async function (credential) {
    var s = await _apiFetch('/api/auth/google', { method: 'POST', body: { credential: credential } });
    await ApiDataStore.saveAuth(s);
    return s;
  },
  loadAuth: function () { return Promise.resolve(_readApiAuth()); },
  saveAuth: function (a) {
    try {
      if (a) localStorage.setItem(API_AUTH_KEY, JSON.stringify(a));
      else localStorage.removeItem(API_AUTH_KEY);
    } catch (e) {}
    return Promise.resolve();
  },

  // — profile (mapped to the UI's Profile shape) —
  loadProfile: async function () {
    var d = await _apiFetch('/api/users/me');
    return {
      name: d.full_name || '', email: d.email || '',
      school: d.school || '', year: d.year || '',
      avatarEmoji: d.avatar_emoji || '👤', avatarColor: d.avatar_color || '#5865F2',
      xp: d.xp || 0, streak: d.streak || 0,
      totalSessions: d.total_sessions || 0,
      role: d.role || 'student',
      _server: d,
    };
  },
  saveProfile: async function (p) {
    return _apiFetch('/api/users/me', {
      method: 'PATCH',
      body: {
        full_name: p.name, school: p.school, year: p.year,
        avatar_emoji: p.avatarEmoji, avatar_color: p.avatarColor,
      },
    });
  },

  loadSettings: LocalPrefs.loadSettings,
  saveSettings: LocalPrefs.saveSettings,

  listCases: function () { return _apiFetch('/api/v2/cases'); },
};

// Selector kept for API compatibility with legacy call-sites. The Qora flow
// calls window.ApiDataStore directly, so this always resolves to the API store.
function createDataStore() { return ApiDataStore; }

window.LocalPrefs = LocalPrefs;
window.ApiDataStore = ApiDataStore;
window.createDataStore = createDataStore;
window.DataStore = ApiDataStore;
window._qoraRefreshToken = _qoraRefreshToken;
