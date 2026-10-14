import { useState, useEffect } from 'react';
import { fetchDataStatus, fetchDataDates, fetchDataMonths } from '../utils/api';

export default function DataStatus() {
  const [status, setStatus] = useState(null);
  const [months, setMonths] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState('');
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchDataStatus().catch(() => null),
      fetchDataMonths().catch(() => ({ months: [] })),
    ]).then(([statusRes, monthRes]) => {
      setStatus(statusRes);
      const m = monthRes.months || [];
      setMonths(m);
      if (m.length > 0) setSelectedMonth(m[m.length - 1]);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedMonth) return;
    fetchDataDates(selectedMonth)
      .then(res => setDates(res.dates || []))
      .catch(() => setDates([]));
  }, [selectedMonth]);

  if (loading) {
    return <div className="loading-state"><div className="spinner" />Loading data status...</div>;
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1 className="page-title">Data Status</h1>
        <p className="page-subtitle">Overview of available market data in the DATA/ folder</p>
      </div>

      {/* Overview Cards */}
      <div className="grid-4 mb-4">
        <div className="metric-card animate-in stagger-1">
          <div className="metric-label">Total Months</div>
          <div className="metric-value">{status?.total_months || 0}</div>
        </div>
        <div className="metric-card animate-in stagger-2">
          <div className="metric-label">Trading Days</div>
          <div className="metric-value">{status?.total_days || 0}</div>
        </div>
        <div className="metric-card animate-in stagger-3">
          <div className="metric-label">Days with Spot</div>
          <div className="metric-value">{status?.days_with_spot || 0}</div>
        </div>
        <div className="metric-card animate-in stagger-4">
          <div className="metric-label">Avg Strikes/Day</div>
          <div className="metric-value">{status?.avg_strikes_per_day || 0}</div>
        </div>
      </div>

      {/* Month selector */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Data Calendar</span>
          <select value={selectedMonth} onChange={e => setSelectedMonth(e.target.value)}
            style={{ minWidth: 200 }}>
            {months.map(m => (
              <option key={m} value={m}>{m.replace('_DATA', '').replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <div className="card-body" style={{ padding: 0, overflow: 'auto' }}>
          {dates.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Spot Data</th>
                  <th>Strikes</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {dates.map(d => (
                  <tr key={d.date}>
                    <td style={{ fontFamily: 'var(--font-body)' }}>{d.date}</td>
                    <td>
                      <span className={`status-dot ${d.has_spot ? 'green' : 'red'}`} />
                      {' '}
                      {d.has_spot ? 'Available' : 'Missing'}
                    </td>
                    <td className="mono">{d.strike_count}</td>
                    <td>
                      {d.has_spot && d.strike_count > 50 ? (
                        <span style={{
                          padding: '1px 8px', borderRadius: 4, fontSize: 'var(--text-xs)',
                          background: 'var(--color-profit-bg)', color: 'var(--color-profit)',
                          border: '1px solid var(--color-profit-border)',
                        }}>Ready</span>
                      ) : d.has_spot ? (
                        <span style={{
                          padding: '1px 8px', borderRadius: 4, fontSize: 'var(--text-xs)',
                          background: 'var(--color-warn-bg)', color: 'var(--color-warn)',
                        }}>Partial</span>
                      ) : (
                        <span style={{
                          padding: '1px 8px', borderRadius: 4, fontSize: 'var(--text-xs)',
                          background: 'var(--color-loss-bg)', color: 'var(--color-loss)',
                        }}>Missing</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No data found for this month</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
