import { useState, useEffect } from 'react';
import { fetchStrategies, fetchDataDates, fetchDataMonths, runBacktest } from '../utils/api';
import { formatRupees, pnlClass, categoryColor } from '../utils/formatters';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';

export default function Compare() {
  const [strategies, setStrategies] = useState([]);
  const [months, setMonths] = useState([]);
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);

  const [strategyA, setStrategyA] = useState('');
  const [strategyB, setStrategyB] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetchStrategies().catch(() => ({ strategies: [] })),
      fetchDataMonths().catch(() => ({ months: [] })),
    ]).then(([stratRes, monthRes]) => {
      setStrategies(stratRes.strategies || []);
      const m = monthRes.months || [];
      setMonths(m);
      if (m.length > 0) setSelectedMonth(m[m.length - 1]);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedMonth) return;
    fetchDataDates(selectedMonth)
      .then(res => {
        const d = (res.dates || []).filter(x => x.has_spot);
        setDates(d);
        if (d.length > 0) setSelectedDate(d[d.length - 1].path);
      })
      .catch(() => setDates([]));
  }, [selectedMonth]);

  const handleCompare = async () => {
    if (!strategyA || !strategyB || !selectedDate) return;
    setComparing(true);
    setError(null);
    setResults(null);

    try {
      const [resA, resB] = await Promise.all([
        runBacktest({ strategy_id: strategyA, data_folder: selectedDate }),
        runBacktest({ strategy_id: strategyB, data_folder: selectedDate }),
      ]);
      setResults({ a: resA, b: resB });
    } catch (err) {
      setError(err.message);
    } finally {
      setComparing(false);
    }
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner" />Loading...</div>;
  }

  // Build comparison chart data
  let comparisonData = [];
  if (results) {
    const metrics = [
      { label: 'Final P&L', a: results.a.final_pnl, b: results.b.final_pnl },
      { label: 'Avg P&L/Trade', a: results.a.avg_pnl, b: results.b.avg_pnl },
      { label: 'Total Trades', a: results.a.total_trades, b: results.b.total_trades },
      { label: 'Wins', a: results.a.wins, b: results.b.wins },
      { label: 'Losses', a: results.a.losses, b: results.b.losses },
    ];
    comparisonData = metrics;
  }

  const stratAName = strategies.find(s => s.id === strategyA)?.name || 'Strategy A';
  const stratBName = strategies.find(s => s.id === strategyB)?.name || 'Strategy B';

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Compare Strategies</h1>
        <p className="page-subtitle">Run two strategies side-by-side on the same date</p>
      </div>

      {/* Selector Row */}
      <div className="card mb-4">
        <div className="card-body" style={{ display: 'flex', gap: 'var(--sp-4)', alignItems: 'end', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
            <label className="form-label">Strategy A</label>
            <select value={strategyA} onChange={e => setStrategyA(e.target.value)}>
              <option value="">— Select —</option>
              {strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>

          <div style={{ fontSize: 'var(--text-lg)', color: 'var(--text-tertiary)', paddingBottom: 'var(--sp-2)' }}>vs</div>

          <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
            <label className="form-label">Strategy B</label>
            <select value={strategyB} onChange={e => setStrategyB(e.target.value)}>
              <option value="">— Select —</option>
              {strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>

          <div className="form-group" style={{ minWidth: 160 }}>
            <label className="form-label">Month</label>
            <select value={selectedMonth} onChange={e => setSelectedMonth(e.target.value)}>
              {months.map(m => <option key={m} value={m}>{m.replace('_DATA', '').replace('_', ' ')}</option>)}
            </select>
          </div>

          <div className="form-group" style={{ minWidth: 160 }}>
            <label className="form-label">Date</label>
            <select value={selectedDate} onChange={e => setSelectedDate(e.target.value)}>
              {dates.map(d => <option key={d.path} value={d.path}>{d.date}</option>)}
            </select>
          </div>

          <button
            className="btn btn-primary"
            disabled={!strategyA || !strategyB || !selectedDate || comparing}
            onClick={handleCompare}
            style={{ height: 38 }}
          >
            {comparing ? 'Comparing...' : 'Compare'}
          </button>
        </div>
      </div>

      {error && (
        <div className="card mb-4" style={{ borderColor: 'var(--color-loss-border)' }}>
          <div className="card-body" style={{ color: 'var(--color-loss)' }}>{error}</div>
        </div>
      )}

      {results && (
        <div className="animate-in">
          {/* Side-by-side metrics */}
          <div className="grid-2 mb-4">
            {[
              { data: results.a, name: stratAName, color: '#6366f1' },
              { data: results.b, name: stratBName, color: '#f59e0b' },
            ].map(({ data, name, color }) => (
              <div className="card" key={name} style={{ borderTopColor: color, borderTopWidth: 2 }}>
                <div className="card-header">
                  <span className="card-title" style={{ color }}>{name}</span>
                </div>
                <div className="card-body">
                  <div className="grid-2" style={{ gap: 'var(--sp-4)' }}>
                    <div>
                      <div className="metric-label">Final P&L</div>
                      <div className={`mono font-semibold ${pnlClass(data.final_pnl)}`}
                        style={{ fontSize: 'var(--text-xl)' }}>
                        {formatRupees(data.final_pnl)}
                      </div>
                    </div>
                    <div>
                      <div className="metric-label">Win Rate</div>
                      <div className="mono font-semibold" style={{ fontSize: 'var(--text-xl)' }}>
                        {data.total_trades > 0
                          ? ((data.wins / data.total_trades) * 100).toFixed(1)
                          : 0}%
                      </div>
                    </div>
                    <div>
                      <div className="metric-label">Total Trades</div>
                      <div className="mono">{data.total_trades}</div>
                    </div>
                    <div>
                      <div className="metric-label">Avg P&L</div>
                      <div className={`mono ${pnlClass(data.avg_pnl)}`}>{formatRupees(data.avg_pnl)}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Comparison Bar Chart */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Metric Comparison</span>
            </div>
            <div className="card-body">
              <div className="chart-container-lg">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData} layout="vertical">
                    <CartesianGrid stroke="#1e2230" strokeDasharray="3 3" />
                    <XAxis type="number"
                      tick={{ fill: '#5c6078', fontSize: 11 }}
                      axisLine={{ stroke: '#1e2230' }}
                      tickLine={false}
                    />
                    <YAxis type="category" dataKey="label" width={120}
                      tick={{ fill: '#8b8fa5', fontSize: 12 }}
                      axisLine={{ stroke: '#1e2230' }}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#1c1f2a', border: '1px solid #272b3a',
                        borderRadius: 8, fontSize: 12, color: '#e8eaf0'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="a" name={stratAName} fill="#6366f1" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="b" name={stratBName} fill="#f59e0b" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {!results && !comparing && (
        <div className="card">
          <div className="card-body">
            <div className="empty-state">
              <h3>Select two strategies to compare</h3>
              <p>They will be run on the same trading date for a fair comparison</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
