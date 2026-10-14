"""
Generalized Python backtest engine.

Supports any strategy (1-leg, 2-leg, 4-leg) through the BaseStrategy interface.
Mirrors the simulation loop from the existing C++ engine but with pluggable strategy logic.
"""

from __future__ import annotations
import time as _time
from pathlib import Path

from ..strategies.base import BaseStrategy, Leg, TradeEntry
from ..data.loader import (
    load_spot_data, load_strike_data, get_backtest_date,
    detect_expiry_from_folder, round_to_atm, clear_strike_cache,
)
from ..config import MARKET_OPEN, MARKET_CLOSE


def _to_minutes(hhmm: str) -> int:
    """Convert 'HH:MM' to total minutes from midnight."""
    h, m = int(hhmm[:2]), int(hhmm[3:5])
    return h * 60 + m


def _from_minutes(total: int) -> str:
    """Convert total minutes from midnight to 'HH:MM'."""
    return f"{total // 60:02d}:{total % 60:02d}"


def _build_timeline(open_str: str, close_str: str) -> list[str]:
    """Build minute-by-minute timeline from market open to close."""
    start = _to_minutes(open_str)
    end = _to_minutes(close_str)
    return [_from_minutes(m) for m in range(start, end + 1)]


def _build_slot_set(entry_time: str, interval: int, close_str: str) -> set[str]:
    """Build set of valid entry slot times."""
    start = _to_minutes(entry_time)
    end = _to_minutes(close_str)
    return {_from_minutes(m) for m in range(start, end, interval)}


def _in_no_trade_window(hhmm: str, windows: list[tuple[str, str]]) -> bool:
    """Check if time is inside a no-trade window."""
    t = _to_minutes(hhmm)
    for start, end in windows:
        if _to_minutes(start) <= t < _to_minutes(end):
            return True
    return False


def run_backtest(
    strategy: BaseStrategy,
    data_folder: str,
    expiry_date: str | None = None,
    params: dict | None = None,
) -> dict:
    """
    Run a backtest for a given strategy on a single day's data.

    Args:
        strategy: an instance of BaseStrategy
        data_folder: path to the day's data folder
        expiry_date: expiry in DD-MM-YYYY format (auto-detected if None)
        params: override strategy parameters

    Returns:
        dict with keys: trades, logs, backtest_date, summary stats
    """
    start_wall = _time.perf_counter()
    clear_strike_cache()

    meta = strategy.meta()

    # ── Merge params ────────────────────────────────────────────────────────
    from ..config import DEFAULT_PARAMS
    config = {**DEFAULT_PARAMS}
    if meta.default_params:
        config.update(meta.default_params)
    if params:
        config.update(params)

    # Derive TP/SL in rupees
    capital = config["capital_per_trade"]
    config["tp_rupees"] = capital * config["take_profit_pct"] / 100
    config["sl_rupees"] = capital * config["stop_loss_pct"] / 100
    config["leg_capital"] = capital / 2

    # ── Load data ───────────────────────────────────────────────────────────
    data_path = Path(data_folder)
    if not data_path.exists():
        return {"error": f"Data folder not found: {data_folder}"}

    spot_prices = load_spot_data(data_path)
    if not spot_prices:
        return {"error": "No spot data loaded"}

    backtest_date = get_backtest_date(data_path)

    if expiry_date is None:
        expiry_date = detect_expiry_from_folder(data_path)
        if expiry_date is None:
            return {"error": "Could not auto-detect expiry date"}

    # ── Build timeline and slots ────────────────────────────────────────────
    timeline = _build_timeline(MARKET_OPEN, MARKET_CLOSE)
    slot_set = _build_slot_set(
        config["entry_time"], config["trade_interval"], MARKET_CLOSE
    )
    entry_from = _to_minutes(config["entry_time"])
    close_min = _to_minutes(MARKET_CLOSE)

    no_trade_windows = config.get("no_trade_windows", [])

    # ── Simulation ──────────────────────────────────────────────────────────
    open_trades: list[TradeEntry] = []
    closed_trades: list[TradeEntry] = []
    logs: list[dict] = []
    trade_num = 0

    # T2 fix: Data quality tracking
    slots_attempted = 0
    slots_executed = 0
    skip_reasons: dict[str, int] = {}  # reason → count

    def _track_skip(reason: str):
        nonlocal slots_attempted
        slots_attempted += 1
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

    for minute_str in timeline:
        cur_min = _to_minutes(minute_str)
        is_slot = minute_str in slot_set
        is_close = cur_min >= close_min

        # ── Check exits on open trades ──────────────────────────────────
        still_open: list[TradeEntry] = []

        for trade in open_trades:
            # Gather current prices for all legs
            current_prices: dict[tuple[int, str], float] = {}
            for leg in trade.legs:
                strike_data = load_strike_data(
                    data_folder, leg.strike, expiry_date
                )
                if minute_str in strike_data:
                    ce_price, pe_price = strike_data[minute_str]
                    current_prices[(leg.strike, "CE")] = ce_price
                    current_prices[(leg.strike, "PE")] = pe_price

            # Update leg prices
            for leg in trade.legs:
                key = (leg.strike, leg.option_type)
                if key in current_prices:
                    leg.current_price = current_prices[key]

            # Check exit conditions
            reason = ""
            if is_close:
                reason = "MARKET_CLOSE"
            else:
                # Strategy-specific exit check
                custom_reason = strategy.check_exit(trade, current_prices, config)
                if custom_reason:
                    reason = custom_reason
                elif cur_min >= trade.hold_deadline_min:
                    reason = "INTERVAL"

            if reason:
                trade.exit_time = minute_str
                trade.exit_reason = reason
                closed_trades.append(trade)

                pnl = trade.net_pnl
                sign = "+" if pnl >= 0 else ""
                logs.append({
                    "message": (
                        f"[{trade.trade_no:3d}]  {trade.entry_time} -> "
                        f"{minute_str}  {reason:<14s}  P&L: {sign}Rs{pnl:,.0f}"
                    ),
                    "is_entry": False,
                })
            else:
                still_open.append(trade)

        open_trades = still_open

        # ── New trade entry ─────────────────────────────────────────────
        if not is_slot or cur_min < entry_from or is_close:
            continue

        if _in_no_trade_window(minute_str, no_trade_windows):
            _track_skip("no_trade_window")
            logs.append({
                "message": f"{minute_str}  SLOT SKIPPED -- inside no-trade window",
                "is_entry": False,
            })
            continue

        if minute_str not in spot_prices:
            _track_skip("no_spot_data")
            logs.append({
                "message": f"{minute_str}  SLOT SKIPPED -- no spot data",
                "is_entry": False,
            })
            continue

        spot = spot_prices[minute_str]
        atm = round_to_atm(spot)

        # Get legs from strategy
        legs = strategy.get_legs(atm, spot, config)
        if not legs:
            _track_skip("strategy_no_legs")
            logs.append({
                "message": f"{minute_str}  SLOT SKIPPED -- strategy returned no legs",
                "is_entry": False,
            })
            continue

        # Fill entry prices from data
        all_prices_found = True
        for leg in legs:
            strike_data = load_strike_data(data_folder, leg.strike, expiry_date)
            if minute_str not in strike_data:
                all_prices_found = False
                break
            ce_price, pe_price = strike_data[minute_str]
            leg.entry_price = ce_price if leg.option_type == "CE" else pe_price
            leg.current_price = leg.entry_price

        if not all_prices_found:
            _track_skip("missing_option_data")
            logs.append({
                "message": f"{minute_str}  SLOT SKIPPED -- missing option data",
                "is_entry": False,
            })
            continue

        # Calculate quantities (pass config for margin model awareness)
        legs = strategy.calc_quantities(
            legs, config["capital_per_trade"], config["lot_size"], config
        )
        if not legs or all(leg.quantity == 0 for leg in legs):
            _track_skip("zero_quantity")
            logs.append({
                "message": f"{minute_str}  SLOT SKIPPED -- all quantities 0 (insufficient capital/margin)",
                "is_entry": False,
            })
            continue

        # Track successful entry
        slots_attempted += 1
        slots_executed += 1

        # Create trade
        trade_num += 1
        hold_deadline = cur_min + config["hold_minutes"]

        trade = TradeEntry(
            trade_no=trade_num,
            entry_time=minute_str,
            legs=legs,
            atm_at_entry=atm,
            hold_deadline_min=hold_deadline,
        )
        open_trades.append(trade)

        # Log entry
        leg_details = "  |  ".join(
            f"{l.option_type}({l.direction[0]})@{l.strike}={l.entry_price:.2f}x{l.quantity}"
            for l in legs
        )
        logs.append({
            "message": (
                f"[{trade_num:3d}]  ENTRY  {minute_str}  "
                f"Spot={spot:.1f}  ATM={atm}  {leg_details}"
            ),
            "is_entry": True,
        })

    # ── Force close remaining trades at market close ────────────────────
    last_min = timeline[-1] if timeline else MARKET_CLOSE
    for trade in open_trades:
        for leg in trade.legs:
            strike_data = load_strike_data(data_folder, leg.strike, expiry_date)
            if last_min in strike_data:
                ce_price, pe_price = strike_data[last_min]
                leg.current_price = (
                    ce_price if leg.option_type == "CE" else pe_price
                )

        trade.exit_time = last_min
        trade.exit_reason = "MARKET_CLOSE"
        closed_trades.append(trade)

        pnl = trade.net_pnl
        sign = "+" if pnl >= 0 else ""
        logs.append({
            "message": (
                f"[{trade.trade_no:3d}]  {trade.entry_time} -> "
                f"{last_min}  MARKET_CLOSE    P&L: {sign}Rs{pnl:,.0f}"
            ),
            "is_entry": False,
        })

    # ── Post-process ────────────────────────────────────────────────────
    # Sort by entry time
    closed_trades.sort(key=lambda t: t.entry_time)

    # Calculate transaction costs for each trade (E1 fix)
    for trade in closed_trades:
        trade.txn_costs = strategy.calc_txn_costs(trade, config)

    # Build output
    cum_gross_pnl = 0.0
    cum_net_pnl = 0.0
    trade_rows = []
    for i, trade in enumerate(closed_trades):
        trade.trade_no = i + 1
        gross = round(trade.gross_pnl, 2)
        net = round(trade.net_pnl, 2)
        txn = round(trade.txn_costs, 2)
        cum_gross_pnl += gross
        cum_net_pnl += net

        row = {
            "Trade_No": trade.trade_no,
            "Entry_Time": trade.entry_time,
            "Exit_Time": trade.exit_time,
            "Exit_Reason": trade.exit_reason,
            "ATM_at_Entry": trade.atm_at_entry,
            "Gross_PnL": gross,
            "Txn_Costs": txn,
            "Net_PnL": net,
            "Cumulative_PnL": round(cum_net_pnl, 2),
            "Cumulative_Gross": round(cum_gross_pnl, 2),
            "Legs": [],
        }

        for leg in trade.legs:
            row["Legs"].append({
                "strike": leg.strike,
                "type": leg.option_type,
                "direction": leg.direction,
                "entry_price": round(leg.entry_price, 2),
                "exit_price": round(leg.current_price, 2),
                "quantity": leg.quantity,
                "pnl": round(leg.pnl, 2),
            })

        # Backward-compatible columns for 2-leg straddle/strangle
        if len(trade.legs) >= 2:
            ce_legs = [l for l in trade.legs if l.option_type == "CE"]
            pe_legs = [l for l in trade.legs if l.option_type == "PE"]
            if ce_legs:
                row["Strike"] = ce_legs[0].strike
                row["CE_Entry"] = ce_legs[0].entry_price
                row["CE_Exit"] = round(ce_legs[0].current_price, 2)
                row["CE_Qty"] = ce_legs[0].quantity
                row["CE_PnL"] = round(ce_legs[0].pnl, 2)
            if pe_legs:
                row["PE_Entry"] = pe_legs[0].entry_price
                row["PE_Exit"] = round(pe_legs[0].current_price, 2)
                row["PE_Qty"] = pe_legs[0].quantity
                row["PE_PnL"] = round(pe_legs[0].pnl, 2)
        elif len(trade.legs) == 1:
            leg = trade.legs[0]
            row["Strike"] = leg.strike
            col = "CE" if leg.option_type == "CE" else "PE"
            row[f"{col}_Entry"] = leg.entry_price
            row[f"{col}_Exit"] = round(leg.current_price, 2)
            row[f"{col}_Qty"] = leg.quantity
            row[f"{col}_PnL"] = round(leg.pnl, 2)

        trade_rows.append(row)

    # Summary
    total = len(trade_rows)
    wins = sum(1 for t in trade_rows if t["Net_PnL"] > 0)
    losses = sum(1 for t in trade_rows if t["Net_PnL"] < 0)
    avg_pnl = cum_net_pnl / total if total > 0 else 0.0
    total_txn_costs = sum(t["Txn_Costs"] for t in trade_rows)

    # T2 fix: Data quality metrics
    skip_rate = round(
        ((slots_attempted - slots_executed) / slots_attempted * 100)
        if slots_attempted > 0 else 0, 1
    )

    elapsed = _time.perf_counter() - start_wall

    return {
        "strategy_id": meta.id,
        "strategy_name": meta.name,
        "backtest_date": backtest_date,
        "expiry_date": expiry_date,
        "data_folder": str(data_folder),
        "params": config,
        "trades": trade_rows,
        "logs": logs,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "avg_pnl": round(avg_pnl, 2),
        "final_pnl": round(cum_net_pnl, 2),
        "gross_pnl": round(cum_gross_pnl, 2),
        "total_txn_costs": round(total_txn_costs, 2),
        "elapsed_ms": round(elapsed * 1000, 1),
        # T2 fix: Data quality section
        "data_quality": {
            "slots_attempted": slots_attempted,
            "slots_executed": slots_executed,
            "skip_rate": skip_rate,
            "skip_reasons": skip_reasons,
        },
    }
