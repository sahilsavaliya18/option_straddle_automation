"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NIFTY LONG STRADDLE BACKTESTER (C++ ENGINE V1) — AUTO MODE                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Fully automated: auto-detects today's data folder, expiry, and result       ║
║  paths. Designed for Windows Task Scheduler — no manual input needed.        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import time as _time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Import C++ engine
try:
    import backtest_engine as _engine  # type: ignore
except ImportError:
    print("ERROR: 'backtest_engine' module not found.")
    print("Please build it first:")
    print("  cd cpp_engine\\build")
    print("  cmake .. -Dpybind11_DIR=$(python -m pybind11 --cmakedir)")
    print("  cmake --build . --config Release")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG — Fixed values (these don't change daily)
# ═══════════════════════════════════════════════════════════════════════════════

# Root is one level up
PROJECT_ROOT     = Path(__file__).parent.parent

# ── Timings ────────────────────────────────────────────────────────────────────
MARKET_OPEN      = "09:15"
MARKET_CLOSE     = "15:30"
ENTRY_TIME       = "09:20"

TRADE_INTERVAL   = 5
HOLD_MINUTES     = 60

NO_TRADE_WINDOWS = [("10:00", "14:00"), ("14:30", "15:30")]

# ── Contract & capital ─────────────────────────────────────────────────────────
LOT_SIZE             = 65
CAPITAL_PER_TRADE    = 100000
LEG_CAPITAL          = CAPITAL_PER_TRADE / 2

# ── Offsets & exits ────────────────────────────────────────────────────────────
OFFSET_FROM_SPOT     = +0
TAKE_PROFIT_PCT      = 3.0
STOP_LOSS_PCT        = 1.0

# ── Derived ────────────────────────────────────────────────────────────────────
TP_RUPEES    = CAPITAL_PER_TRADE * TAKE_PROFIT_PCT / 100
SL_RUPEES    = CAPITAL_PER_TRADE * STOP_LOSS_PCT   / 100

# ── Log file for scheduled runs ────────────────────────────────────────────────
LOG_FILE = Path(__file__).parent / "auto_run.log"


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO-GENERATE TODAY'S PATHS + EXPIRY
# ═══════════════════════════════════════════════════════════════════════════════

def get_today_config():
    """
    Auto-generates all date-dependent values:
    - DATA_FOLDER   : Root/DATA/Month_YYYY_DATA/DD_MM_YYYY/
    - RESULT_FOLDER : Root/RESULT/MONTH/V1/
    - EXPIRY_DATE   : Auto-detected from NSE option-chain API or next Tuesday
    """
    today = datetime.now()

    # ── Data folder ────────────────────────────────────────────────────────
    month_str = today.strftime("%B_%Y") + "_DATA"        # May_2026_DATA
    day_str   = today.strftime("%d_%m_%Y")               # 15_05_2026
    data_folder = str(PROJECT_ROOT / "DATA" / month_str / day_str)

    # ── Result folder ──────────────────────────────────────────────────────
    month_abbr = today.strftime("%B").upper()             # MAY
    result_folder = str(PROJECT_ROOT / "RESULT" / "NEUTRAL" / month_abbr / "V1")

    # ── Expiry date ────────────────────────────────────────────────────────
    # Try to detect from NSE API, fall back to next Tuesday
    expiry_date = _detect_expiry()

    return {
        "data_folder"   : data_folder,
        "result_folder" : result_folder,
        "expiry_date"   : expiry_date,
    }


def _detect_expiry() -> str:
    today = datetime.now().date()

    try:
        from curl_cffi import requests as cffi_requests
        BASE_URL = "https://www.nseindia.com"

        session = cffi_requests.Session(impersonate="chrome120")
        # Warm session
        try:
            session.get(BASE_URL, timeout=15)
            _time.sleep(1)
            session.get(f"{BASE_URL}/option-chain", timeout=15)
            _time.sleep(1)
        except Exception:
            pass

        # Try up to 2 upcoming Tuesdays
        for week_offset in range(2):
            days_ahead = 1 - today.weekday()  # Tuesday = weekday 1
            if days_ahead < 0:
                days_ahead += 7
            tuesday = today + timedelta(days=days_ahead + (7 * week_offset))

            expiry_api_fmt = tuesday.strftime("%d-%b-%Y")
            expiry_ddmmyyyy = tuesday.strftime("%d-%m-%Y")

            url = f"{BASE_URL}/api/option-chain-v3?type=Indices&symbol=NIFTY&expiry={expiry_api_fmt}"
            headers = {
                "Referer":        f"{BASE_URL}/option-chain",
                "Accept":         "application/json, text/plain, */*",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }

            try:
                r = session.get(url, headers=headers, timeout=15)
                data = r.json()

                records_data = data.get("records", {}).get("data", [])
                if records_data and len(records_data) > 0:
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        print(f"  [V1 AUTO] Expiry validated via API: {expiry_ddmmyyyy} ({len(records_data)} strikes)", file=f)
                    return expiry_ddmmyyyy
                else:
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        print(f"  [V1 AUTO] Tuesday {expiry_ddmmyyyy} empty (holiday?). Trying next week.", file=f)

            except Exception as e:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    print(f"  [V1 AUTO] Expiry API failed ({e}). Trying next Tuesday.", file=f)
                _time.sleep(1)

    except Exception as e:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            print(f"  [V1 AUTO] Expiry detection failed ({e}), using next Tuesday", file=f)

    return _next_tuesday()


def _next_tuesday() -> str:
    today = datetime.now().date()
    days_ahead = 1 - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    tuesday = today + timedelta(days=days_ahead)
    return tuesday.strftime("%d-%m-%Y")


# ═══════════════════════════════════════════════════════════════════════════════
#  Build config dict for C++ engine
# ═══════════════════════════════════════════════════════════════════════════════

def build_config_dict(data_folder: str, expiry_date: str, result_folder: str):
    return {
        "data_folder"       : data_folder,
        "expiry_date"       : expiry_date,
        "market_open"       : MARKET_OPEN,
        "market_close"      : MARKET_CLOSE,
        "entry_time"        : ENTRY_TIME,
        "trade_interval"    : TRADE_INTERVAL,
        "hold_minutes"      : HOLD_MINUTES,
        "lot_size"          : LOT_SIZE,
        "capital_per_trade" : CAPITAL_PER_TRADE,
        "leg_capital"       : LEG_CAPITAL,
        "offset_from_spot"  : OFFSET_FROM_SPOT,
        "take_profit_pct"   : TAKE_PROFIT_PCT,
        "stop_loss_pct"     : STOP_LOSS_PCT,
        "tp_rupees"         : TP_RUPEES,
        "sl_rupees"         : SL_RUPEES,
        "no_trade_windows"  : NO_TRADE_WINDOWS,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest(data_folder: str | None = None, expiry_date: str | None = None,
                 result_folder: str | None = None):
    if data_folder is None or expiry_date is None or result_folder is None:
        today_cfg = get_today_config()
        data_folder   = data_folder   or today_cfg["data_folder"]
        expiry_date   = expiry_date   or today_cfg["expiry_date"]
        result_folder = result_folder or today_cfg["result_folder"]

    if not Path(data_folder).exists():
        msg = f"ERROR: Data folder does not exist: {data_folder}"
        print(msg)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            print(msg, file=f)
        return None

    print()
    print(" +----------------------------------------------------------+")
    print(" |  NIFTY LONG STRADDLE BACKTESTER (C++ ENGINE V1) - AUTO   |")
    print(" +----------------------------------------------------------+")
    print(f"  Data folder   : {data_folder}")
    print(f"  Expiry        : {expiry_date}")
    print(f"  Result folder : {result_folder}")
    print(f"  Entry         : {ENTRY_TIME}  |  Interval : {TRADE_INTERVAL} min  |  Hold : {HOLD_MINUTES} min")
    print(f"  Capital       : Rs{CAPITAL_PER_TRADE:,}  (2 legs x Rs{LEG_CAPITAL:,.0f})")
    side = f"ATM-{OFFSET_FROM_SPOT}" if OFFSET_FROM_SPOT > 0 else f"ATM+{abs(OFFSET_FROM_SPOT)}"
    print(f"  TP Rs{TP_RUPEES:,.0f}  |  SL Rs{SL_RUPEES:,.0f}  |  Strike: {side}  |  Lot {LOT_SIZE}")
    print()

    config = build_config_dict(data_folder, expiry_date, result_folder)

    print("  [C++ Engine] Running backtest...")
    py_start = _time.perf_counter()
    result = _engine.run_backtest(config)
    py_elapsed = _time.perf_counter() - py_start
    print(f"  [Python] Total wall time: {py_elapsed:.3f}s\n")

    for log_entry in result["logs"]:
        msg = log_entry["message"]
        if log_entry["is_entry"]:
            print(f"\n  {msg}")
        else:
            print(f"  {msg}")

    trades = result["trades"]

    if not trades:
        print("  No trades were executed.")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            print("  No trades executed.", file=f)
        return None

    df_out = pd.DataFrame(trades)
    cols = ["Trade_No", "Entry_Time", "Exit_Time", "Exit_Reason", "ATM_at_Entry",
            "Strike", "CE_Entry", "CE_Exit", "CE_Qty", "CE_PnL",
            "PE_Entry", "PE_Exit", "PE_Qty", "PE_PnL", "Net_PnL", "Cumulative_PnL"]
    df_out = df_out[cols]

    backtest_date = result["backtest_date"]
    out_path = Path(result_folder) / f"result_{backtest_date}.csv"
    Path(result_folder).mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n  Saved results -> {out_path}\n")

    total  = result["total_trades"]
    wins   = result["wins"]
    losses = result["losses"]
    avg    = result["avg_pnl"]
    final  = result["final_pnl"]

    summary = (
        f"\n  SUMMARY\n"
        f"  Total trades      :  {total}\n"
        f"  Profitable        :  {wins}   |   Loss : {losses}\n"
        f"  Average P&L/trade :  Rs{avg:,.2f}\n"
        f"  Final P&L         :  Rs{final:,.2f}\n"
    )
    print(summary)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        print(summary, file=f)

    return {
        "backtest_date": backtest_date,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "avg_pnl": avg,
        "final_pnl": final,
        "output_csv": str(out_path),
    }

if __name__ == "__main__":
    args = sys.argv[1:]
    df = args[0] if len(args) > 0 else None
    exp = args[1] if len(args) > 1 else None
    rf = args[2] if len(args) > 2 else None

    result = run_backtest(data_folder=df, expiry_date=exp, result_folder=rf)
