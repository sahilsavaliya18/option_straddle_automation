import { useState, useEffect } from 'react';
import { fetchResults, fetchResultDetail } from '../utils/api';
import { formatRupees, pnlClass } from '../utils/formatters';

export default function Results() {
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchResults()
      .then(res => { setResults(res.results || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const viewDetail = async (id) => {
    setDetailLoading(true);
    try {
      const detail = await fetchResultDetail(id);
      setSelectedResult(detail);
    } catch { /* ignore */ }
    setDetailLoading(false);
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner" />Loading results...</div>;
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Results History</h1>
        <p className="page-subtitle">{results.length} backtests saved</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedResult ? '1fr 1fr' : '1fr', gap: 'var(--sp-6)' }}>
        {/* Results List */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">All Backtests</span>
          </div>
          <div className="card-body" style={{ padding: 0, overflow: 'auto', maxHeight: 600 }}>
            {results.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Date</th>
                    <th>Trades</th>
                    <th>W/L</th>
                    <th style={{ textAlign: 'right' }}>P&L</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {results.map(r => (
                    <tr key={r.id}
                      style={{ cursor: 'pointer', background: selectedResult?.id === r.id ? 'var(--bg-hover)' : undefined }}
                      onClick={() => viewDetail(r.id)}
                    >
                      <td style={{ fontFamily: 'var(--font-body)', color: 'var(--text-primary)' }}>
                        {r.strategy_name}
                      </td>
                      <td>{r.backtest_date}</td>
                      <td>{r.total_trades}</td>
                      <td>
                        <span className="text-profit">{r.wins}</span>
                        {' / '}
                        <span className="text-loss">{r.losses}</span>
                      </td>
                      <td className={`${pnlClass(r.final_pnl)}`} style={{ textAlign: 'right' }}>
                        {formatRupees(r.final_pnl)}
                      </td>
                      <td>
                        <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); viewDetail(r.id); }}>
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <h3>No results yet</h3>
                <p>Run backtests from the Run Backtest page</p>
              </div>
            )}
          </div>
        </div>

        {/* Detail Panel */}
        {selectedResult && (
          <div className="card animate-in">
            <div className="card-header">
              <span className="card-title">{selectedResult.strategy_name}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelectedResult(null)}>Close</button>
            </div>
            <div className="card-body">
              {detailLoading ? (
                <div className="loading-state"><div className="spinner" /></div>
              ) : (
                <>
                  <div className="grid-3 mb-4">
                    <div>
                      <div className="metric-label">Date</div>
                      <div className="mono" style={{ fontSize: 'var(--text-md)' }}>{selectedResult.backtest_date}</div>
                    </div>
                    <div>
                      <div className="metric-label">Final P&L</div>
                      <div className={`mono ${pnlClass(selectedResult.final_pnl)}`}
                        style={{ fontSize: 'var(--text-md)', fontWeight: 600 }}>
                        {formatRupees(selectedResult.final_pnl)}
                      </div>
                    </div>
                    <div>
                      <div className="metric-label">Win Rate</div>
                      <div className="mono" style={{ fontSize: 'var(--text-md)' }}>
                        {selectedResult.total_trades > 0
                          ? ((selectedResult.wins / selectedResult.total_trades) * 100).toFixed(1)
                          : 0}%
                      </div>
                    </div>
                  </div>

                  <div style={{ overflow: 'auto', maxHeight: 400 }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Entry</th>
                          <th>Exit</th>
                          <th>Reason</th>
                          <th style={{ textAlign: 'right' }}>P&L</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(selectedResult.trades || []).map(t => (
                          <tr key={t.trade_no}>
                            <td>{t.trade_no}</td>
                            <td>{t.entry_time}</td>
                            <td>{t.exit_time}</td>
                            <td>{t.exit_reason}</td>
                            <td className={pnlClass(t.net_pnl)} style={{ textAlign: 'right' }}>
                              {formatRupees(t.net_pnl)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
