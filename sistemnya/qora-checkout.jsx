// ============================================================
// Qora — Checkout page (Website Revision Notes §1.2, §5.3)
// ------------------------------------------------------------
// Single checkout flow across the whole product:
//   Landing / Billing → pilih paket → #/checkout/<plan> → payment
// Plan-aware via the hash segment (#/checkout/monthly | annual).
// The payment step executes the CURRENT gateway (Midtrans Snap
// for IDR, Xendit hosted invoice fallback) through the existing
// backend endpoints. The UI is provider-agnostic — swapping in
// Sendit Payment Gateway after approval touches _coPay() only.
// ADDITIVE: design.css tokens only. Loaded AFTER qora-v2.jsx
// (reuses QORA_PLAN_FEATURES + _loadSnap globals).
// ============================================================

var _ct = window.__t || function (k) { return k; };

// ── Payment execution (Midtrans Snap → Xendit fallback) ─────
// Structure ready for Sendit: replace the body with Sendit calls
// once approval + integration info lands.
async function _coPay(planId, setBusy, setErr) {
  setBusy(true); setErr('');
  try {
    // Primary: Midtrans Snap popup (Indonesia / IDR).
    try {
      const r = await qv2Fetch('/api/billing/midtrans/checkout/' + planId, { method: 'POST' });
      if (r && r.snap_token) {
        await _loadSnap();
        if (window.snap && window.snap.pay) {
          window.snap.pay(r.snap_token, {
            onSuccess: function () { try { window.location.hash = '#/billing-success'; } catch (e) {} },
            onPending: function () { setErr('Payment pending — complete it to activate your plan.'); setBusy(false); },
            onError: function () { setErr('Payment failed — please try again.'); setBusy(false); },
            onClose: function () { setBusy(false); },
          });
          return;
        }
        if (r.redirect_url) { window.location.href = r.redirect_url; return; }
      }
    } catch (e) {
      if (!/not configured|503/i.test(String((e && e.message) || e))) throw e;
    }
    // Fallback: Xendit hosted invoice (USD / non-IDR).
    const r2 = await qv2Fetch('/api/billing/xendit/checkout/' + planId, { method: 'POST' });
    if (r2 && r2.checkout_url) { window.location.href = r2.checkout_url; return; }
    setErr('Checkout is not available yet.');
  } catch (e) {
    setErr(/not configured|503/i.test(String(e.message || e)) ? 'Payments are not enabled yet — check back soon.' : String(e.message || e));
  }
  setBusy(false);
}

// ── Checkout screen ──────────────────────────────────────────
function QoraCheckout(props) {
  var onNav = props.onNav;
  // Plan id from the hash: #/checkout/<plan>
  var planId = 'monthly';
  try {
    var seg = (location.hash || '').replace(/^#\/?/, '').split('/');
    if (seg[0] === 'checkout' && seg[1]) planId = seg[1];
  } catch (e) {}
  var region = 'row';
  try { region = localStorage.getItem('qora_region') || 'row'; } catch (e) {}
  var isID = region === 'indo';

  var plansState = React.useState(null);
  var plansData = plansState[0];
  var setPlans = plansState[1];
  var meState = React.useState(null);
  var me = meState[0];
  var setMe = meState[1];
  var errState = React.useState('');
  var err = errState[0];
  var setErr = errState[1];
  var busyState = React.useState(false);
  var busy = busyState[0];
  var setBusy = busyState[1];
  var methodState = React.useState('');
  var method = methodState[0];
  var setMethod = methodState[1];

  React.useEffect(function () {
    qv2Fetch('/api/billing/plans').then(setPlans).catch(function (e) { setErr(String(e.message || e)); });
    qv2Fetch('/api/billing/me').then(setMe).catch(function () {});
  }, []);

  var plan = null;
  var plans = (plansData && plansData.plans) || [];
  for (var i = 0; i < plans.length; i++) { if (plans[i].id === planId) { plan = plans[i]; break; } }
  var paymentsLive = !!(plansData && plansData.provider);

  var METHODS = isID
    ? [
        { id: 'qris', icon: '\uD83D\uDCF1', label: 'QRIS — GoPay, OVO, DANA, ShopeePay' },
        { id: 'va', icon: '\uD83C\uDFE6', label: 'Virtual Account — BCA, Mandiri, BNI, BRI' },
        { id: 'alfamart', icon: '\uD83C\uDFEA', label: 'Alfamart / Indomaret' },
      ]
    : [
        { id: 'card', icon: '\uD83D\uDCB3', label: 'Credit / Debit Card — Visa, Mastercard' },
      ];

  function pay() {
    if (!planId || busy) return;
    _coPay(planId, setBusy, setErr);
  }

  function goBack() {
    if (typeof onNav === 'function') onNav('billing');
    else try { window.location.hash = '#/billing'; } catch (e) {}
  }

  // Loading / error states
  if (!plansData) {
    return React.createElement('div', { className: 'au', style: { maxWidth: 'min(860px, calc(100% - 16px))', margin: '0 auto', padding: '60px 20px', textAlign: 'center', color: 'var(--text-3)', fontSize: 13 } },
      err ? (_ct('common.error') + ': ' + err) : _ct('common.loading'));
  }

  var priceText = plan ? (plan.display_price || ('$' + plan.price)) : '';
  // Avoid a doubled period ("$14.99/mo /month") when display_price already
  // carries it (e.g. "/mo", "/yr").
  var hasPeriod = /\/\s*(mo|month|yr|year|bln|thn|bulan|tahun)/i.test(priceText);
  var intervalText = plan
    ? (plan.interval === 'year' ? (hasPeriod ? '' : (isID ? '/thn' : '/year'))
       : plan.interval === 'one_time' ? (isID ? 'sekali bayar' : 'one-off')
       : (hasPeriod ? '' : (isID ? '/bln' : '/month')))
    : '';
  var priceFull = priceText + (intervalText ? ' ' + intervalText : '');
  var sessionsText = isID ? 'Tak terbatas sesi' : 'Unlimited sessions';
  var features = QORA_PLAN_FEATURES[planId] || [];
  var featureFallback = plan && plan.features ? plan.features : [];

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(900px, calc(100% - 16px))', margin: '0 auto', padding: '28px 16px 80px' } },
    // Header
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 } },
      React.createElement('button', { onClick: goBack, style: { padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, '\u2190 ' + _ct('common.back')),
      React.createElement('div', null,
        React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.2 } }, isID ? 'Checkout' : 'Checkout'),
        React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-2)', marginTop: 2 } }, isID ? 'Langkah terakhir sebelum kamu mulai latihan tanpa batas.' : 'One step away from unlimited practice.'))),
    !paymentsLive && React.createElement('div', { style: { textAlign: 'center', fontSize: 12.5, color: 'var(--text-3)', marginBottom: 18, marginTop: 8 } },
      isID ? 'Semua fitur sedang terbuka selama Qora masih beta.' : 'Everything is currently unlocked while Qora is in beta.'),

    React.createElement('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, alignItems: 'start', marginTop: 18 } },
      // ── Left: order summary ──
      React.createElement('div', { className: 'as', style: { padding: 22, borderRadius: 'var(--r-xl)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-md)' } },
        React.createElement('div', { style: { fontSize: 11, fontWeight: 800, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 12 } }, '\uD83D\uDED2 ' + (isID ? 'Ringkasan pesanan' : 'Order summary')),
        plan
          ? React.createElement('div', null,
              React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8, marginBottom: 2 } },
                React.createElement('div', { style: { fontSize: 17, fontWeight: 800, color: 'var(--text-1)' } }, plan.label || planId),
                React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: 'var(--primary)' } }, priceFull)),
              React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', marginBottom: 14 } },
                isID ? 'Paket ' + planId + ' · ' + sessionsText : planId + ' plan · ' + sessionsText),
              React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 8, padding: '14px 0', borderTop: '1px solid var(--border)' } },
                (features.length ? features : featureFallback).map(function (f, i) {
                  return React.createElement('div', { key: i, style: { display: 'flex', alignItems: 'center', gap: 9, fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.45 } },
                    React.createElement('span', { style: { color: 'var(--primary)', fontWeight: 700, flexShrink: 0 } }, '\u2713'), f);
                })),
              React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 12, borderTop: '1px solid var(--border)' } },
                React.createElement('span', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)' } }, isID ? 'Total' : 'Total'),
                React.createElement('span', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)' } }, priceFull)))
          : React.createElement('div', { style: { fontSize: 13, color: 'var(--red-d)', padding: '10px 0' } },
              isID ? 'Paket "' + planId + '" tidak ditemukan.' : 'Plan "' + planId + '" not found.')),

      // ── Right: payment ──
      React.createElement('div', { className: 'as', style: { padding: 22, borderRadius: 'var(--r-xl)', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--sh-md)' } },
        React.createElement('div', { style: { fontSize: 11, fontWeight: 800, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 14 } }, '\uD83D\uDCB8 ' + (isID ? 'Metode pembayaran' : 'Payment method')),
        React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 } },
          METHODS.map(function (m) {
            var active = method === m.id;
            return React.createElement('button', {
              key: m.id,
              onClick: function () { setMethod(m.id); },
              style: {
                display: 'flex', alignItems: 'center', gap: 11, padding: '12px 14px', borderRadius: 14,
                border: '1.5px solid ' + (active ? 'var(--primary)' : 'var(--border)'),
                background: active ? 'var(--primary-l)' : 'var(--surface)',
                cursor: 'pointer', fontFamily: 'Plus Jakarta Sans', textAlign: 'left', width: '100%',
                transition: 'all 0.18s ease',
              },
            },
              React.createElement('span', { style: { fontSize: 20 } }, m.icon),
              React.createElement('span', { style: { flex: 1, fontSize: 13, fontWeight: active ? 700 : 500, color: 'var(--text-1)' } }, m.label),
              React.createElement('span', { style: { width: 18, height: 18, borderRadius: '50%', border: '2px solid ' + (active ? 'var(--primary)' : 'var(--border)'), display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 } },
                active && React.createElement('span', { style: { width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)' } })));
          })),
        React.createElement('button', {
          onClick: pay,
          disabled: busy || !plan || !method,
          style: {
            width: '100%', padding: '14px', borderRadius: 14, border: 'none',
            background: busy || !plan || !method ? 'var(--surface-3)' : 'var(--primary)',
            color: busy || !plan || !method ? 'var(--text-3)' : '#fff',
            fontSize: 15, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: busy || !plan || !method ? 'default' : 'pointer',
            boxShadow: busy || !plan || !method ? 'none' : 'var(--sh-md)',
            transition: 'all 0.18s ease',
          },
        },
          busy
            ? React.createElement('span', null, isID ? 'Memproses pembayaran\u2026' : 'Processing payment\u2026')
            : (isID ? 'Bayar sekarang' : 'Pay now')),
        err && React.createElement('div', { style: { marginTop: 12, fontSize: 12.5, color: 'var(--red-d)', background: 'var(--red-l)', padding: '9px 12px', borderRadius: 10, lineHeight: 1.5 } }, err),
        React.createElement('div', { style: { marginTop: 14, fontSize: 11, color: 'var(--text-3)', lineHeight: 1.6, textAlign: 'center' } },
          '\uD83D\uDD12 ' + (isID ? 'Pembayaran aman & terenkripsi. Aktivasi instan setelah pembayaran diverifikasi.' : 'Secure & encrypted checkout. Your plan activates instantly once payment is verified.')))));
}

window.QoraCheckout = QoraCheckout;

// Global hook: any screen can jump straight to the checkout page.
window.__goCheckout = function (planId) {
  try { window.location.hash = '#/checkout/' + (planId || 'monthly'); } catch (e) {}
};