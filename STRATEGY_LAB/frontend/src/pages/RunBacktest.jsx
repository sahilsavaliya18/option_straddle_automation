import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchStrategies, fetchDataDates, fetchDataMonths, runBacktest } from '../utils/api';
import { formatRupees, pnlClass, categoryBadgeClass, categoryColor } from '../utils/formatters';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line
} from 'recharts';

export default function RunBacktest() {
  const [searchParams] = useSearchParams();
  const preselected = searchParams.get('strategy') || '';

  const [strategies, setStrategies] = useState([]);
  const [months, setMonths] = useState([]);
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Form state
  const [selectedStrategy, setSelectedStrategy] = useState(preselected);
  const [selectedMonth, setSelectedMonth] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [params, setParams] = useState({
    entry_time: '09:20',
    trade_interval: 5,
    hold_minutes: 60,
    capital_per_trade: 100000,
    take_profit_pct: 3.0,
    stop_loss_pct: 1.0,
    lot_size: 65,
    spread_width: 100,
    margin_mode: 'realistic',
    txn_enabled: true,
  });

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

  // Update strategy defaults when selection changes
  useEffect(() => {
    const strat = strategies.find(s => s.id === selectedStrategy);
    if (strat?.default_params) {
      setParams(prev => ({
        ...prev,
        take_profit_pct: strat.default_params.take_profit_pct ?? prev.take_profit_pct,
        stop_loss_pct: strat.default_params.stop_loss_pct ?? prev.stop_loss_pct,
        spread_width: strat.default_params.spread_width ?? prev.spread_width,
        capital_per_trade: strat.default_params.capital_per_trade ?? prev.capital_per_trade,
      }));
    }
  }, [selectedStrategy, strategies]);

  // Load dates when month changes
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

  const handleRun = async () => {
    if (!selectedStrategy || !selectedDate) return;
    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const res = await runBacktest({
        strategy_id: selectedStrategy,
        data_folder: selectedDate,
        ...params,
      });
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const updateParam = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const currentStrat = strategies.find(s => s.id === selectedStrategy);

  if (loading) {
    return <div className="loading-state"><div className="spinner" />Loading...</div>;
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Run Backtest</h1>
        <p className="page-subtitle">Select a strategy, date, and parameters to run</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 'var(--sp-6)', alignItems: 'start' }}>
        {/* Config Panel */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Configuration</span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>

            {/* Strategy Selector */}
            <div className="form-group">
              <label className="form-label">Strategy</label>
              <select value={selectedStrategy} onChange={e => setSelectedStrategy(e.target.value)}>
                <option value="">— Select Strategy —</option>
                {strategies.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.category})</option>
                ))}
              </select>
            </div>

            {currentStrat && (
              <div style={{
                padding: 'var(--sp-3)', background: 'var(--bg-raised)',
                borderRadius: 'var(--radius-md)', fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)', lineHeight: 1.6,
              }}>
                <span className={`category-badge ${categoryBadgeClass(currentStrat.category)}`}
                  style={{ marginBottom: 'var(--sp-2)', display: 'inline-flex' }}>
                  {currentStrat.category}
                </span>
                <div style={{ marginTop: 'var(--sp-2)' }}>{currentStrat.description}</div>
              </div>
            )}

            {/* Date Selection */}
            <div className="form-group">
              <label className="form-label">Month</label>
              <select value={selectedMonth} onChange={e => setSelectedMonth(e.target.value)}>
                {months.map(m => <option key={m} value={m}>{m.replace('_DATA', '').replace('_', ' ')}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Trading Date ({dates.length} available)</label>
              <select value={selectedDate} onChange={e => setSelectedDate(e.target.value)}>
                {dates.map(d => (
                  <option key={d.path} value={d.path}>
                    {d.date} ({d.strike_count} strikes)
                  </option>
                ))}
              </select>
            </div>

            {/* Parameters */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: 'var(--sp-4)' }}>
              <div className="form-label" style={{ marginBottom: 'var(--sp-3)' }}>Parameters</div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-3)' }}>
                <div className="form-group">
                  <label className="form-label">Capital (₹)</label>
                  <input type="number" value={params.capital_per_trade}
                    onChange={e => updateParam('capital_per_trade', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Lot Size</label>
                  <input type="number" value={params.lot_size}
                    onChange={e => updateParam('lot_size', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">TP %</label>
                  <input type="number" step="0.5" value={params.take_profit_pct}
                    onChange={e => updateParam('take_profit_pct', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">SL %</label>
                  <input type="number" step="0.5" value={params.stop_loss_pct}
                    onChange={e => updateParam('stop_loss_pct', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Hold (min)</label>
                  <input type="number" value={params.hold_minutes}
                    onChange={e => updateParam('hold_minutes', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Spread Width</label>
                  <input type="number" step="50" value={params.spread_width}
                    onChange={e => updateParam('spread_width', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Entry Time</label>
                  <input type="text" value={params.entry_time}
                    onChange={e => updateParam('entry_time', e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Interval (min)</label>
                  <input type="number" value={params.trade_interval}
                    onChange={e => updateParam('trade_interval', +e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Margin Model</label>
                  <select value={params.margin_mode}
                    onChange={e => updateParam('margin_mode', e.target.value)}>
                    <option value="realistic">Realistic (SPAN ~15%)</option>
                    <option value="simple">Simple (2x Prem)</option>
                  </select>
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', paddingTop: '24px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" checked={params.txn_enabled}
                      onChange={e => updateParam('txn_enabled', e.target.checked)} />
                    Include Txn Costs
                  </label>
                </div>
              </div>
            </div>

            <button
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 'var(--sp-2)' }}
              disabled={!selectedStrategy || !selectedDate || running}
              onClick={handleRun}
            >
              {running ? (
                <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Running...</>
              ) : (
                'Run Backtest'
              )}
            </button>

            {error && (
              <div style={{
                padding: 'var(--sp-3)', background: 'var(--color-loss-bg)',
                border: '1px solid var(--color-loss-border)', borderRadius: 'var(--radius-md)',
                color: 'var(--color-loss)', fontSize: 'var(--text-sm)',
              }}>
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Results Panel */}
        <div>
          {result ? (
            <div className="animate-in">
              {/* Summary Cards */}
              <div className="grid-4 mb-4">
                <div className="metric-card">
                  <div className="metric-label">Final Net P&L</div>
                  <div className={`metric-value ${result.final_pnl >= 0 ? 'profit' : 'loss'}`}>
                    {formatRupees(result.final_pnl)}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Gross P&L</div>
                  <div className={`metric-value ${(result.gross_pnl ?? result.final_pnl) >= 0 ? 'profit' : 'loss'}`}>
                    {formatRupees(result.gross_pnl ?? result.final_pnl)}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Txn Charges</div>
                  <div className="metric-value loss">
                    {result.total_txn_costs > 0 ? `-${formatRupees(result.total_txn_costs)}` : '₹0'}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Win Rate</div>
                  <div className="metric-value">
                    {result.total_trades > 0
                      ? ((result.wins / result.total_trades) * 100).toFixed(1)
                      : 0}%
                  </div>
                </div>
              </div>

              {/* Data Quality Banner (T2) */}
              {result.data_quality && (
                <div style={{
                  padding: 'var(--sp-3) var(--sp-4)',
                  background: 'var(--bg-raised)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--sp-4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)',
                }}>
                  <div style={{ display: 'flex', gap: 'var(--sp-4)', alignItems: 'center' }}>
                    <span>⚡ <strong>Execution:</strong> {result.data_quality.slots_executed} / {result.data_quality.slots_attempted} slots</span>
                    <span>Skip Rate: <strong>{result.data_quality.skip_rate}%</strong></span>
                  </div>
                  {result.data_quality.skip_reasons && Object.keys(result.data_quality.skip_reasons).length > 0 && (
                    <span className="mono" style={{ color: 'var(--text-tertiary)' }}>
                      Skips: {Object.entries(result.data_quality.skip_reasons).map(([k, v]) => `${k}: ${v}`).join(', ')}
                    </span>
                  )}
                </div>
              )}

              {/* P&L Chart */}
              <div className="card mb-4">
                <div className="card-header">
                  <span className="card-title">Trade-wise Cumulative P&L</span>
                  <span className="mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                    {result.elapsed_ms}ms
                  </span>
                </div>
                <div className="card-body">
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={result.trades}>
                        <CartesianGrid stroke="#1e2230" strokeDasharray="3 3" />
                        <XAxis
                          dataKey="Entry_Time"
                          tick={{ fill: '#5c6078', fontSize: 11 }}
                          axisLine={{ stroke: '#1e2230' }}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fill: '#5c6078', fontSize: 11 }}
                          axisLine={{ stroke: '#1e2230' }}
                          tickLine={false}
                          tickFormatter={v => `₹${v}`}
                        />
                        <Tooltip
                          contentStyle={{
                            background: '#1c1f2a', border: '1px solid #272b3a',
                            borderRadius: 8, fontSize: 12, color: '#e8eaf0'
                          }}
                          formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, 'P&L']}
                        />
                        <Bar dataKey="Net_PnL" radius={[3, 3, 0, 0]}>
                          {result.trades.map((t, i) => (
                            <Cell
                              key={i}
                              fill={t.Net_PnL >= 0 ? '#10b981' : '#f43f5e'}
                              fillOpacity={0.8}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Trade Table */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Trade Details</span>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>
                    {result.trades.length} trades
                  </span>
                </div>
                <div className="card-body" style={{ padding: 0, overflow: 'auto', maxHeight: 400 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>Reason</th>
                        <th>ATM</th>
                        <th style={{ textAlign: 'right' }}>Gross P&L</th>
                        <th style={{ textAlign: 'right' }}>Txn Cost</th>
                        <th style={{ textAlign: 'right' }}>Net P&L</th>
                        <th style={{ textAlign: 'right' }}>Cumulative</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map((t) => (
                        <tr key={t.Trade_No}>
                          <td>{t.Trade_No}</td>
                          <td>{t.Entry_Time}</td>
                          <td>{t.Exit_Time}</td>
                          <td>
                            <span style={{
                              padding: '1px 6px', borderRadius: 4,
                              fontSize: 'var(--text-xs)', fontWeight: 500,
                              background: t.Exit_Reason === 'TAKE_PROFIT' ? 'var(--color-profit-bg)'
                                : t.Exit_Reason === 'STOP_LOSS' ? 'var(--color-loss-bg)'
                                : 'var(--bg-hover)',
                              color: t.Exit_Reason === 'TAKE_PROFIT' ? 'var(--color-profit)'
                                : t.Exit_Reason === 'STOP_LOSS' ? 'var(--color-loss)'
                                : 'var(--text-secondary)',
                            }}>
                              {t.Exit_Reason}
                            </span>
                          </td>
                          <td className="mono">{t.ATM_at_Entry}</td>
                          <td className={`mono ${pnlClass(t.Gross_PnL ?? t.Net_PnL)}`} style={{ textAlign: 'right' }}>
                            {formatRupees(t.Gross_PnL ?? t.Net_PnL)}
                          </td>
                          <td className="mono text-loss" style={{ textAlign: 'right' }}>
                            {t.Txn_Costs > 0 ? `-${formatRupees(t.Txn_Costs)}` : '₹0'}
                          </td>
                          <td className={`mono ${pnlClass(t.Net_PnL)}`} style={{ textAlign: 'right' }}>
                            {formatRupees(t.Net_PnL)}
                          </td>
                          <td className={`mono ${pnlClass(t.Cumulative_PnL)}`} style={{ textAlign: 'right' }}>
                            {formatRupees(t.Cumulative_PnL)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="card-body">
                <div className="empty-state" style={{ padding: 'var(--sp-12) var(--sp-6)' }}>
                  <h3>Configure and run a backtest</h3>
                  <p style={{ maxWidth: 360 }}>
                    Select a strategy and trading date from the panel on the left,
                    adjust parameters, and click "Run Backtest" to see results.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


