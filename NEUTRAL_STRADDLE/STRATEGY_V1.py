"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          NIFTY  —  LONG STRADDLE  BACKTESTER  (MULTI-TRADE) - FIXED V1       ║  
╠══════════════════════════════════════════════════════════════════════════════╣
║  Fixed Issues:                                                               ║
║   • Trades now sorted by Entry_Time (chronological order)                    ║
║   • Trade_No renumbered in ascending order                                   ║
║   • Cumulative_PnL correctly recalculated after sorting                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
from datetime import datetime, time, timedelta
from pathlib import Path

import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG  ←  edit these values before running
# ═══════════════════════════════════════════════════════════════════════════════

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_FOLDER   = str(Path(__file__).parent.parent / "DATA" / "May_2026_DATA" / "15_05_2026")
RESULT_FOLDER = str(Path(__file__).parent.parent / "RESULT" / "NEUTRAL" / "MAY" / "V1")

# ── Expiry ─────────────────────────────────────────────────────────────────────
EXPIRY_DATE      = "19-05-2026"

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


# ═══════════════════════════════════════════════════════════════════════════════
#  Derived constants
# ═══════════════════════════════════════════════════════════════════════════════
TP_RUPEES    = CAPITAL_PER_TRADE * TAKE_PROFIT_PCT / 100
SL_RUPEES    = CAPITAL_PER_TRADE * STOP_LOSS_PCT   / 100


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def to_time(hhmm: str) -> time:
    h, m = map(int, hhmm.split(":"))
    return time(h, m)


def round_to_atm(spot: float) -> int:
    """Nearest multiple of 50."""
    return int(round(spot / 50) * 50)


def floor_qty(leg_capital: float, price: float, lot: int) -> int:
    """Units buyable — always floor to whole contracts."""
    if price <= 0:
        return 0
    return math.floor((leg_capital / price) / lot) * lot


def in_no_trade_window(t: time) -> bool:
    for s, e in NO_TRADE_WINDOWS:
        if to_time(s) <= t < to_time(e):
            return True
    return False


def build_slot_set(entry: str, interval: int, close: str) -> set:
    slots   = set()
    eh, em  = map(int, entry.split(":"))
    ch, cm  = map(int, close.split(":"))
    base    = datetime(2000, 1, 1, eh, em)
    ceiling = datetime(2000, 1, 1, ch, cm)
    t = base
    while t < ceiling:
        slots.add(t.strftime("%H:%M"))
        t += timedelta(minutes=interval)
    return slots


# ═══════════════════════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════════════════════

_strike_cache: dict = {}

def load_spot_data(folder: str):
    candidates = sorted(Path(folder).glob("NIFTY50_spot_*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No NIFTY50_spot_*.csv found in: {folder}")
    path = candidates[0]
    print(f"  Spot file  →  {path.name}")
    df         = pd.read_csv(path, encoding="utf-8-sig")
    df["_dt"]  = pd.to_datetime(df["DateTime"])
    df["_min"] = df["_dt"].dt.strftime("%H:%M")
    prices     = {}
    for _, row in df.iterrows():
        prices[row["_min"]] = float(row["Spot_Price"])
    date_str = df["_dt"].iloc[0].strftime("%d%m%Y")
    return prices, date_str


def load_strike_data(folder: str, strike: int, expiry: str) -> dict:
    key = (strike, expiry)
    if key in _strike_cache:
        return _strike_cache[key]

    filename = f"{strike}_{expiry}.csv"
    filepath = Path(folder) / filename
    if not filepath.exists():
        print(f"  ⚠  Not found: {filename}")
        _strike_cache[key] = {}
        return {}

    df       = pd.read_csv(filepath, encoding="utf-8-sig")
    call_col = f"{strike}CALL"
    put_col  = f"{strike}PUT"

    if call_col not in df.columns or put_col not in df.columns:
        print(f"  ⚠  Missing columns in {filename}")
        _strike_cache[key] = {}
        return {}

    df["_min"] = df["DateTime"].str[-5:]
    prices = {}
    for _, row in df.iterrows():
        prices[row["_min"]] = (float(row[call_col]), float(row[put_col]))

    _strike_cache[key] = prices
    print(f"  Loaded  {filename}  ({len(prices)} candles)")
    return prices


# ═══════════════════════════════════════════════════════════════════════════════
#  P&L Functions
# ═══════════════════════════════════════════════════════════════════════════════

def calc_pnl(trade, call1, put1) -> float:
    return (
        (call1 - trade["ec"]) * trade["qc"] +
        (put1  - trade["ep"]) * trade["qp"]
    )


def get_exit_prices(trade, minute_str):
    d = load_strike_data(DATA_FOLDER, trade["strike"], EXPIRY_DATE)
    c, p = d.get(minute_str, (trade["ec"], trade["ep"]))
    return c, p


def make_row(num, trade, exit_time, reason, c, p, pnl, cum) -> dict:
    return {
        "Trade_No"       : num,
        "Entry_Time"     : trade["entry_time"],
        "Exit_Time"      : exit_time,
        "Exit_Reason"    : reason,
        "ATM_at_Entry"   : trade["atm"],
        "Strike"         : trade["strike"],
        "CE_Entry"       : trade["ec"],
        "CE_Exit"        : c,
        "CE_Qty"         : trade["qc"],
        "CE_PnL"         : round((c - trade["ec"]) * trade["qc"], 2),
        "PE_Entry"       : trade["ep"],
        "PE_Exit"        : p,
        "PE_Qty"         : trade["qp"],
        "PE_PnL"         : round((p - trade["ep"]) * trade["qp"], 2),
        "Net_PnL"        : round(pnl, 2),
        "Cumulative_PnL" : round(cum, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest():
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     NIFTY LONG STRADDLE BACKTESTER (MULTI-TRADE) - FIXED V1     ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  Data folder   : {DATA_FOLDER}")
    print(f"║  Expiry        : {EXPIRY_DATE}")
    print(f"║  First slot    : {ENTRY_TIME}  │  Interval : {TRADE_INTERVAL} min  │  Hold : {HOLD_MINUTES} min")
    print(f"║  Capital       : ₹{CAPITAL_PER_TRADE:,}  (2 legs × ₹{LEG_CAPITAL:,.0f})")
    side = f"ATM−{OFFSET_FROM_SPOT}" if OFFSET_FROM_SPOT > 0 else f"ATM+{abs(OFFSET_FROM_SPOT)}"
    print(f"║  TP ₹{TP_RUPEES:,.0f}  │  SL ₹{SL_RUPEES:,.0f}  │  Strike: {side}  │  Lot {LOT_SIZE}")
    nw = ", ".join(f"{s}–{e}" for s, e in NO_TRADE_WINDOWS)
    print(f"║  No-trade windows : {nw}")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    spot_prices, backtest_date = load_spot_data(DATA_FOLDER)
    print(f"     {len(spot_prices)} minute-candles loaded.\n")

    # Build timeline
    oh, om = map(int, MARKET_OPEN.split(":"))
    ch, cm = map(int, MARKET_CLOSE.split(":"))
    open_dt  = datetime(2000, 1, 1, oh, om)
    close_dt = datetime(2000, 1, 1, ch, cm)
    timeline = []
    t = open_dt
    while t <= close_dt:
        timeline.append(t.strftime("%H:%M"))
        t += timedelta(minutes=1)

    slot_set    = build_slot_set(ENTRY_TIME, TRADE_INTERVAL, MARKET_CLOSE)
    close_time  = to_time(MARKET_CLOSE)
    entry_from  = to_time(ENTRY_TIME)

    trades      = []
    open_trades = []
    trade_num   = 0
    cum_pnl     = 0.0  # will be recalculated later

    for minute_str in timeline:
        cur_t    = to_time(minute_str)
        is_slot  = minute_str in slot_set
        is_close = cur_t >= close_time

        # Check exits for open trades
        still_open = []
        for trade in open_trades:
            c, p = get_exit_prices(trade, minute_str)
            pnl = calc_pnl(trade, c, p)

            hold_deadline = trade["hold_deadline"]
            held_long_enough = cur_t >= hold_deadline

            if is_close:
                reason = "MARKET_CLOSE"
            elif pnl >= TP_RUPEES:
                reason = "TAKE_PROFIT"
            elif pnl <= -SL_RUPEES:
                reason = "STOP_LOSS"
            elif held_long_enough:
                reason = "INTERVAL"
            else:
                reason = None

            if reason:
                row = make_row(trade["trade_num"], trade, minute_str, reason, c, p, pnl, 0)
                trades.append(row)
                sign = "+" if pnl >= 0 else ""
                print(f"  [{trade['trade_num']:>3}]  {trade['entry_time']} → {minute_str}  {reason:<14}  P&L: {sign}₹{pnl:>8,.0f}")
            else:
                still_open.append(trade)

        open_trades = still_open

        # New Trade Entry
        if not is_slot or cur_t < entry_from or is_close:
            continue
        if in_no_trade_window(cur_t):
            print(f"  {minute_str}  SLOT SKIPPED — inside no-trade window")
            continue

        spot = spot_prices.get(minute_str)
        if spot is None:
            print(f"  {minute_str}  SLOT SKIPPED — no spot data")
            continue

        atm    = round_to_atm(spot)
        strike = atm - OFFSET_FROM_SPOT

        d  = load_strike_data(DATA_FOLDER, strike, EXPIRY_DATE)
        pr = d.get(minute_str)

        if pr is None:
            print(f"  {minute_str}  SLOT SKIPPED — no option data for {strike}")
            continue

        ec, ep = pr

        qc_raw = floor_qty(LEG_CAPITAL, ec, LOT_SIZE)
        qp_raw = floor_qty(LEG_CAPITAL, ep, LOT_SIZE)
        min_qty = min(qc_raw, qp_raw)
        
        qc = min_qty
        qp = min_qty

        if qc == 0 and qp == 0:
            print(f"  {minute_str}  SLOT SKIPPED — all quantities 0")
            continue

        mh, mm        = map(int, minute_str.split(":"))
        entry_dt      = datetime(2000, 1, 1, mh, mm)
        deadline_dt   = entry_dt + timedelta(minutes=HOLD_MINUTES)
        hold_deadline = deadline_dt.time()

        trade_num += 1
        new_trade = {
            "trade_num"     : trade_num,
            "entry_time"    : minute_str,
            "hold_deadline" : hold_deadline,
            "atm"           : atm,
            "strike"        : strike,
            "ec": ec, "ep": ep,
            "qc": qc, "qp": qp,
        }
        open_trades.append(new_trade)

        print(f"\n  [{trade_num:>3}]  ENTRY  {minute_str}  Spot={spot:.1f}  ATM={atm}  Strike={strike}")
        print(f"         CE={ec:.2f} × {qc}   │   PE={ep:.2f} × {qp}")

    # Force close remaining trades
    for trade in open_trades:
        last = timeline[-1]
        c, p = get_exit_prices(trade, last)
        pnl = calc_pnl(trade, c, p)
        row = make_row(trade["trade_num"], trade, last, "MARKET_CLOSE", c, p, pnl, 0)
        trades.append(row)
        sign = "+" if pnl >= 0 else ""
        print(f"\n  [{trade['trade_num']:>3}]  {trade['entry_time']} → {last}  MARKET_CLOSE    P&L: {sign}₹{pnl:>8,.0f}")

    # ===================================================================
    # FINAL PROCESSING: SORT + RECALCULATE CUMULATIVE PnL
    # ===================================================================
    print("\n" + "─" * 60)
    print("[4]  Sorting trades by Entry Time and recalculating Cumulative PnL...")

    if not trades:
        print("  No trades were executed.")
        input("\nPress Enter to exit...")
        return

    df_out = pd.DataFrame(trades)

    # Sort by Entry_Time
    df_out['Entry_Time'] = pd.to_datetime(df_out['Entry_Time'], format='%H:%M')
    df_out = df_out.sort_values(by='Entry_Time').reset_index(drop=True)

    # Renumber Trade_No
    df_out['Trade_No'] = range(1, len(df_out) + 1)

    # Recalculate Cumulative PnL
    df_out['Cumulative_PnL'] = df_out['Net_PnL'].cumsum()

    # Format back
    df_out['Entry_Time'] = df_out['Entry_Time'].dt.strftime('%H:%M')

    # Reorder columns
    cols = ["Trade_No", "Entry_Time", "Exit_Time", "Exit_Reason", "ATM_at_Entry", 
            "Strike", "CE_Entry", "CE_Exit", "CE_Qty", "CE_PnL", 
            "PE_Entry", "PE_Exit", "PE_Qty", "PE_PnL", "Net_PnL", "Cumulative_PnL"]
    df_out = df_out[cols]

    # Save
    out_path = Path(RESULT_FOLDER) / f"result_{backtest_date}.csv"
    Path(RESULT_FOLDER).mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  ✓  Saved sorted results → {out_path}\n")

    # Summary
    total   = len(df_out)
    wins    = sum(1 for r in df_out["Net_PnL"] if r > 0)
    losses  = sum(1 for r in df_out["Net_PnL"] if r < 0)
    avg     = df_out["Net_PnL"].mean()
    final   = df_out["Cumulative_PnL"].iloc[-1]  # type: ignore

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                         SUMMARY                                 ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  Total trades      :  {total}")
    print(f"║  Profitable        :  {wins}   │   Loss : {losses}")
    print(f"║  Average P&L/trade :  ₹{avg:,.2f}")
    print(f"║  Final P&L         :  ₹{final:,.2f}")
    print("╚══════════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    run_backtest()
    input("\nPress Enter to exit...")
