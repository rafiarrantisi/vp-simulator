// ============================================================
// Qora — critical-screen error boundary (Phase 12 hardening)
// ------------------------------------------------------------
// Replaces silent blank screens with a GDV-consistent recovery state:
// calm solid card, one primary retry, one quiet back navigation.
// Reports to /api/ops/client-errors (fire-and-forget, bounded) so a
// chat/judge/Mentor failure is traceable via request correlation.
// Self-contained: React only (no dependency on other screens).
// Loaded AFTER qora-v2.jsx in bundle LOAD_ORDER.
// ============================================================

class QoraErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
    this._retry = this._retry.bind(this);
  }
  static getDerivedStateFromError(error) {
    return { error: error || new Error('unknown render error') };
  }
  componentDidCatch(error, info) {
    try {
      var msg = String((error && error.message) || error || 'render error').slice(0, 1000);
      var stack = '';
      try { stack = String((info && info.componentStack) || '').slice(0, 4000); } catch (e) {}
      var url = '';
      try { url = String(window.location.hash || '').slice(0, 500); } catch (e) {}
      if (typeof qv2Fetch === 'function') {
        qv2Fetch('/api/ops/client-errors', {
          method: 'POST', timeout: 8000,
          body: { screen: String(this.props.screen || 'unknown').slice(0, 80), message: msg, url: url, stack: stack },
        }).catch(function () {});
      }
    } catch (e) { /* reporting must never break rendering */ }
  }
  _retry() {
    this.setState({ error: null });
    try { if (typeof this.props.onRetry === 'function') this.props.onRetry(); } catch (e) {}
  }
  render() {
    if (!this.state.error) return this.props.children;
    var _t = (typeof window !== 'undefined' && window.__t) || function (k) { return k; };
    var goBack = this.props.onBack;
    return React.createElement('div', { style: { maxWidth: 560, margin: '0 auto', padding: '48px 20px', textAlign: 'center' }, role: 'alert' },
      React.createElement('div', { style: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', boxShadow: 'var(--sh-sm)', padding: 28 } },
        React.createElement('div', { style: { width: 52, height: 52, borderRadius: '50%', background: 'var(--primary-l)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' } },
          React.createElement('svg', { width: 26, height: 26, viewBox: '0 0 24 24', fill: 'none', stroke: 'var(--primary)', strokeWidth: 1.75, strokeLinecap: 'round', 'aria-hidden': true },
            React.createElement('path', { d: 'M12 5a7 7 0 1 1 0 14 7 7 0 0 1 0-14zM12 8.5V12M12 15h.01' }))),
        React.createElement('div', { style: { fontSize: 17, fontWeight: 800, color: 'var(--text-1)', marginBottom: 6 } }, _t('error.boundary_title')),
        React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 18 } }, _t('error.boundary_body')),
        React.createElement('div', { style: { display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' } },
          React.createElement('button', { onClick: this._retry, style: { padding: '11px 22px', minHeight: 44, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13.5, fontWeight: 700, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, _t('error.retry')),
          goBack && React.createElement('button', { onClick: goBack, style: { padding: '11px 22px', minHeight: 44, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)', fontSize: 13.5, fontWeight: 600, fontFamily: 'Plus Jakarta Sans', cursor: 'pointer' } }, _t('error.back')))));
  }
}

window.QoraErrorBoundary = QoraErrorBoundary;
