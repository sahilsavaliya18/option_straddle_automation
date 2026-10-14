import React from 'react';

/**
 * T6: ErrorBoundary to catch rendering crashes in components
 * and display a user-friendly recovery UI instead of a blank white screen.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: 'var(--sp-8, 32px)',
          maxWidth: '720px',
          margin: '60px auto',
          background: 'var(--card-bg, #161b22)',
          border: '1px solid var(--border-color, #30363d)',
          borderRadius: '12px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          color: 'var(--text-primary, #f0f6fc)',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.2)',
              color: '#ef4444',
              fontSize: '20px',
              fontWeight: 'bold',
            }}>!</span>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>Something went wrong</h2>
          </div>

          <p style={{ color: 'var(--text-secondary, #8b949e)', lineHeight: 1.5, marginBottom: '20px' }}>
            An unexpected error occurred while rendering this view. Your backtest data and settings are safe.
          </p>

          {this.state.error && (
            <div style={{
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              padding: '12px 16px',
              fontSize: '0.85rem',
              color: '#f87171',
              fontFamily: 'monospace',
              overflowX: 'auto',
              marginBottom: '24px',
            }}>
              {this.state.error.toString()}
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={this.handleReset}
              style={{
                background: '#238636',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 16px',
                cursor: 'pointer',
                fontWeight: 500,
                fontSize: '0.9rem',
              }}
            >
              Return to Dashboard
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: 'rgba(255,255,255,0.1)',
                color: '#fff',
                border: '1px solid var(--border-color, #30363d)',
                borderRadius: '6px',
                padding: '8px 16px',
                cursor: 'pointer',
                fontWeight: 500,
                fontSize: '0.9rem',
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
