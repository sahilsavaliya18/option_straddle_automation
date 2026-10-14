"""
Global configuration & path resolution for STRATEGY_LAB.
All paths are resolved relative to the project root (NEW_PROJECT/).
"""

from pathlib import Path

# ── Path Resolution ──────────────────────────────────────────────────────────
STRATEGY_LAB_ROOT = Path(__file__).parent.parent          # STRATEGY_LAB/
PROJECT_ROOT      = STRATEGY_LAB_ROOT.parent              # NEW_PROJECT/
DATA_ROOT         = PROJECT_ROOT / "DATA"
RESULT_ROOT       = STRATEGY_LAB_ROOT / "results_data"    # Separate from existing RESULT/
DB_PATH           = STRATEGY_LAB_ROOT / "results.db"

# ── Market Defaults ──────────────────────────────────────────────────────────
MARKET_OPEN       = "09:15"
MARKET_CLOSE      = "15:30"
LOT_SIZE          = 65
STRIKE_GAP        = 50

# ── Default Strategy Parameters ─────────────────────────────────────────────
DEFAULT_PARAMS = {
    "entry_time":        "09:20",
    "trade_interval":    5,        # minutes between entry slots
    "hold_minutes":      60,
    "capital_per_trade": 100_000,
    "take_profit_pct":   3.0,
    "stop_loss_pct":     1.0,
    "lot_size":          LOT_SIZE,
    "offset_from_spot":  0,        # 0 = ATM
    "spread_width":      100,      # points between legs for spreads
    "no_trade_windows":  [],       # Empty = allow all market hours (was blocking 87% of day)
    # ── Margin Model (T3 fix) ────────────────────────────────────────────────
    "margin_mode":       "realistic",  # "simple" = 2x premium, "realistic" = % of notional
    # ── Transaction Costs (E1 fix) ───────────────────────────────────────────
    "txn_cost_per_order":    20,   # ₹20 flat brokerage per order (Zerodha-like)
    "txn_stt_sell_pct":      0.05, # STT on sell-side option premium (%)
    "txn_exchange_pct":      0.053,# NSE exchange charges (%)
    "txn_gst_pct":           18.0, # GST on brokerage + exchange (%)
    "txn_stamp_buy_pct":     0.003,# Stamp duty on buy-side (%)
    "txn_sebi_pct":          0.0001,# SEBI charges (%)
    "txn_slippage_per_lot":  1.0,  # ₹ slippage per lot per leg
    "txn_enabled":           True, # Show net P&L alongside gross
}

# ── API Config ───────────────────────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
