import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStrategies } from '../utils/api';
import { categoryBadgeClass, categoryColor } from '../utils/formatters';

const CATEGORIES = ['all', 'bullish', 'bearish', 'neutral', 'other'];

export default function Strategies() {
  const [strategies, setStrategies] = useState([]);
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStrategies()
      .then(res => { setStrategies(res.strategies || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const filtered = activeCategory === 'all'
    ? strategies
    : strategies.filter(s => s.category === activeCategory);

  if (loading) {
    return <div className="loading-state"><div className="spinner" />Loading strategies...</div>;
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Strategies</h1>
        <p className="page-subtitle">12 options strategies across 4 market outlook categories</p>
      </div>

      {/* Category Tabs */}
      <div className="tab-bar">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            className={`tab-item${activeCategory === cat ? ' active' : ''}`}
            onClick={() => setActiveCategory(cat)}
            style={activeCategory === cat && cat !== 'all' ? { borderBottomColor: categoryColor(cat) } : {}}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
            {cat !== 'all' && (
              <span style={{ marginLeft: 6, opacity: 0.5, fontSize: 'var(--text-xs)' }}>
                {strategies.filter(s => s.category === cat).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Strategy Cards */}
      <div className="grid-auto">
        {filtered.map((s, i) => (
          <div
            key={s.id}
            className={`strategy-card animate-in stagger-${(i % 4) + 1}`}
            style={{ '--card-accent-color': categoryColor(s.category) }}
            onClick={() => navigate(`/run?strategy=${s.id}`)}
          >
            <span className={`category-badge ${categoryBadgeClass(s.category)}`}>
              {s.category}
            </span>
            <div className="strat-name">{s.name}</div>
            <div className="strat-desc">{s.description}</div>

            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr',
              gap: 'var(--sp-3)', marginTop: 'var(--sp-4)',
              paddingTop: 'var(--sp-3)', borderTop: '1px solid var(--border-subtle)'
            }}>
              <div>
                <div className="strat-meta-label">Max Profit</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-profit)', marginTop: 2 }}>
                  {s.max_profit}
                </div>
              </div>
              <div>
                <div className="strat-meta-label">Max Loss</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-loss)', marginTop: 2 }}>
                  {s.max_loss}
                </div>
              </div>
              <div>
                <div className="strat-meta-label">Legs</div>
                <div className="strat-meta-value">{s.num_legs}</div>
              </div>
              <div>
                <div className="strat-meta-label">Best IV</div>
                <div className="strat-meta-value">{s.ideal_iv || '—'}</div>
              </div>
            </div>

            <button
              className="btn btn-primary btn-sm"
              style={{ width: '100%', marginTop: 'var(--sp-4)' }}
              onClick={(e) => { e.stopPropagation(); navigate(`/run?strategy=${s.id}`); }}
            >
              Run Backtest
            </button>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="empty-state">
          <h3>No strategies in this category</h3>
          <p>Try selecting a different category tab</p>
        </div>
      )}
    </div>
  );
}
