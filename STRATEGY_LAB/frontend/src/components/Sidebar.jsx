import { NavLink } from 'react-router-dom';

const navItems = [
  {
    section: 'Overview',
    items: [
      { to: '/', label: 'Dashboard', icon: '◫' },
      { to: '/strategies', label: 'Strategies', icon: '◇' },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { to: '/ai-desk', label: 'AI Trading Desk', icon: '✦' },
    ],
  },
  {
    section: 'Analysis',
    items: [
      { to: '/run', label: 'Run Backtest', icon: '▷' },
      { to: '/results', label: 'Results', icon: '☰' },
      { to: '/compare', label: 'Compare', icon: '⊞' },
    ],
  },
  {
    section: 'System',
    items: [
      { to: '/data-status', label: 'Data Status', icon: '◉' },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-dot" />
        <h1>Strategy Lab</h1>
      </div>

      {navItems.map((section) => (
        <nav className="sidebar-section" key={section.section}>
          <div className="sidebar-section-title">{section.section}</div>
          {section.items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `nav-link${isActive ? ' active' : ''}`
              }
            >
              <span className="nav-icon" style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', textAlign: 'center' }}>
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      ))}

      <div style={{ flex: 1 }} />

      <div className="sidebar-section" style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: 'var(--sp-4)' }}>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', padding: '0 var(--sp-3)' }}>
          NIFTY Strategy Lab v1.0
        </div>
      </div>
    </aside>
  );
}
