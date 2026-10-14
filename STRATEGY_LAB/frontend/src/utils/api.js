const API_BASE = 'http://localhost:8000/api';

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Strategies ──────────────────────────────────────────────────────────────

export const fetchStrategies = () => apiFetch('/strategies');

export const fetchStrategy = (id) => apiFetch(`/strategies/${id}`);

// ── Backtests ───────────────────────────────────────────────────────────────

export const runBacktest = (body) =>
  apiFetch('/backtest/run', {
    method: 'POST',
    body: JSON.stringify(body),
  });

// ── Results ─────────────────────────────────────────────────────────────────

export const fetchResults = (strategyId) => {
  const qs = strategyId ? `?strategy_id=${strategyId}` : '';
  return apiFetch(`/results${qs}`);
};

export const fetchResultDetail = (id) => apiFetch(`/results/${id}`);

export const deleteResult = (id) =>
  apiFetch(`/results/${id}`, { method: 'DELETE' });

// ── Analytics ───────────────────────────────────────────────────────────────

export const fetchAnalyticsSummary = (strategyId) =>
  apiFetch(`/analytics/summary/${strategyId}`);

// ── Data ────────────────────────────────────────────────────────────────────

export const fetchDataMonths = () => apiFetch('/data/months');

export const fetchDataDates = (month) => {
  const qs = month ? `?month=${month}` : '';
  return apiFetch(`/data/dates${qs}`);
};

export const fetchDataStatus = () => apiFetch('/data/status');

export const healthCheck = () => apiFetch('/health');
