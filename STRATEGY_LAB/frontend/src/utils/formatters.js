/**
 * Format a number as Indian Rupees.
 */
export function formatRupees(value, decimals = 0) {
  if (value == null || isNaN(value)) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}₹${Math.abs(value).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

/**
 * Format a number as percentage.
 */
export function formatPct(value, decimals = 1) {
  if (value == null || isNaN(value)) return '—';
  return `${value.toFixed(decimals)}%`;
}

/**
 * Return CSS class for P&L coloring.
 */
export function pnlClass(value) {
  if (value > 0) return 'text-profit';
  if (value < 0) return 'text-loss';
  return 'text-muted';
}

/**
 * Category to badge CSS class.
 */
export function categoryBadgeClass(category) {
  const map = {
    bullish: 'badge-bullish',
    bearish: 'badge-bearish',
    neutral: 'badge-neutral',
    other: 'badge-other',
  };
  return map[category] || 'badge-other';
}

/**
 * Category accent color for charts.
 */
export function categoryColor(category) {
  const map = {
    bullish: '#10b981',
    bearish: '#f43f5e',
    neutral: '#6366f1',
    other: '#f59e0b',
  };
  return map[category] || '#6366f1';
}
