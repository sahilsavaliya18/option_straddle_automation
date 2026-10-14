import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStrategies, fetchResults, fetchDataStatus } from '../utils/api';
import { formatRupees, pnlClass, categoryBadgeClass, categoryColor } from '../utils/formatters';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

export default function Dashboard() {
  const [strategies, setStrategies] = useState([]);
  const [results, setResults] = useState([]);
  const [dataStatus, setDataStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      fetchStrategies().catch(() => ({ strategies: [] })),
      fetchResults().catch(() => ({ results: [] })),
      fetchDataStatus().catch(() => null),
    ]).then(([stratRes, resRes, dataRes]) => {
      setStrategies(stratRes.strategies || []);
      setResults(resRes.results || []);
      setDataStatus(dataRes);
      setLoading(false);
    }).catch(err => {
      setError(err.message);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        Loading dashboard...
      </div>
    );
  }

  // Aggregate metrics
  const totalBacktests = results.length;
  const totalPnL = results.reduce((sum, r) => sum + (r.final_pnl || 0), 0);
  const totalWins = results.reduce((sum, r) => sum + (r.wins || 0), 0);
  const totalLosses = results.reduce((sum, r) => sum + (r.losses || 0), 0);
  const winRate = totalWins + totalLosses > 0
    ? ((totalWins / (totalWins + totalLosses)) * 100).toFixed(1)
    : '—';

  // Equity curve data
  const equityCurve = [];
  let cumPnl = 0;
  const sortedResults = [...results].sort((a, b) =>
    (a.backtest_date || '').localeCompare(b.backtest_date || '')
  );
  for (const r of sortedResults) {
    cumPnl += r.final_pnl || 0;
    equityCurve.push({
      date: r.backtest_date || '',
      pnl: Math.round(cumPnl),
      strategy: r.strategy_name,
    });
  }

  // Strategy performance summary
  const stratPerfMap = {};
  for (const r of results) {
    if (!stratPerfMap[r.strategy_id]) {
      stratPerfMap[r.strategy_id] = { name: r.strategy_name, totalPnl: 0, count: 0 };
    }
    stratPerfMap[r.strategy_id].totalPnl += r.final_pnl || 0;
    stratPerfMap[r.strategy_id].count += 1;
  }

  // Win/loss pie data
  const pieData = [
    { name: 'Wins', value: totalWins, color: '#10b981' },
    { name: 'Losses', value: totalLosses, color: '#f43f5e' },
  ];

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          {strategies.length} strategies available
          {dataStatus && ` · ${dataStatus.total_days} trading days of data`}
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid-4 mb-4">
        <div className="metric-card animate-in stagger-1">
          <div className="metric-label">Total P&L</div>
          <div className={`metric-value ${totalPnL >= 0 ? 'profit' : 'loss'}`}>
            {formatRupees(totalPnL)}
          </div>
          <div className="metric-sub">{totalBacktests} backtests run</div>
        </div>

        <div className="metric-card animate-in stagger-2">
          <div className="metric-label">Win Rate</div>
          <div className="metric-value">{winRate}%</div>
          <div className="metric-sub">{totalWins}W / {totalLosses}L</div>
        </div>

        <div className="metric-card animate-in stagger-3">
          <div className="metric-label">Strategies</div>
          <div className="metric-value">{strategies.length}</div>
          <div className="metric-sub">across 4 categories</div>
        </div>

        <div className="metric-card animate-in stagger-4">
          <div className="metric-label">Data Days</div>
          <div className="metric-value">{dataStatus?.total_days || 0}</div>
          <div className="metric-sub">{dataStatus?.total_months || 0} months</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-2 mb-4">
        {/* Equity Curve */}
        <div className="card animate-in stagger-2">
          <div className="card-header">
            <span className="card-title">Cumulative P&L</span>
          </div>
          <div className="card-body">
            {equityCurve.length > 0 ? (
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={equityCurve}>
                    <defs>
                      <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#1e2230" strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#5c6078', fontSize: 11 }}
                      axisLine={{ stroke: '#1e2230' }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: '#5c6078', fontSize: 11 }}
                      axisLine={{ stroke: '#1e2230' }}
                      tickLine={false}
                      tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#1c1f2a', border: '1px solid #272b3a',
                        borderRadius: 8, fontSize: 12, color: '#e8eaf0'
                      }}
                      formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, 'P&L']}
                    />
                    <Area
                      type="monotone"
                      dataKey="pnl"
                      stroke="#6366f1"
                      fill="url(#pnlGrad)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">
                <p>Run some backtests to see the equity curve</p>
              </div>
            )}
          </div>
        </div>

        {/* Win/Loss Pie */}
        <div className="card animate-in stagger-3">
          <div className="card-header">
            <span className="card-title">Win / Loss Distribution</span>
          </div>
          <div className="card-body">
            {totalWins + totalLosses > 0 ? (
              <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={4}
                      dataKey="value"
                      stroke="none"
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#1c1f2a', border: '1px solid #272b3a',
                        borderRadius: 8, fontSize: 12, color: '#e8eaf0'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state">
                <p>No trade data yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Strategy Grid */}
      <div className="card animate-in stagger-4">
        <div className="card-header">
          <span className="card-title">Available Strategies</span>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/strategies')}>
            View All
          </button>
        </div>
        <div className="card-body">
          <div className="grid-auto">
            {strategies.map((s) => (
              <div
                key={s.id}
                className="strategy-card"
                style={{ '--card-accent-color': categoryColor(s.category) }}
                onClick={() => navigate(`/run?strategy=${s.id}`)}
              >
                <span className={`category-badge ${categoryBadgeClass(s.category)}`}>
                  {s.category}
                </span>
                <div className="strat-name">{s.name}</div>
                <div className="strat-desc">{s.description}</div>
                <div className="strat-meta">
                  <div className="strat-meta-item">
                    <span className="strat-meta-label">Legs</span>
                    <span className="strat-meta-value">{s.num_legs}</span>
                  </div>
                  <div className="strat-meta-item">
                    <span className="strat-meta-label">Risk</span>
                    <span className="strat-meta-value">{s.risk_type}</span>
                  </div>
                  <div className="strat-meta-item">
                    <span className="strat-meta-label">TP/SL</span>
                    <span className="strat-meta-value">
                      {s.default_params?.take_profit_pct}% / {s.default_params?.stop_loss_pct}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {strategies.length === 0 && (
            <div className="empty-state">
              <h3>Backend not connected</h3>
              <p>Start the FastAPI server to see strategies</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
