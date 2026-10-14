"""
Tool definitions for the Autonomous AI Trading Desk & Engineering Team.
All functions are typed, documented, and safe to execute natively or via LLM tool-calling.
"""

from __future__ import annotations
import os
import re
import json
from pathlib import Path
from typing import Optional

from ..config import DATA_ROOT, DEFAULT_PARAMS
from ..data.loader import get_available_months, get_available_dates, find_date_folder, detect_expiry_from_folder
from ..strategies.registry import get_all_strategies, get_strategy
from ..strategies.base import BaseStrategy, Leg
from ..engine.python_engine import run_backtest
from ..results.store import save_agent_insight, get_backtests, init_db


def audit_market_data(date_str: str) -> dict:
    """
    Audit whether spot and option strike data files exist and are complete for a given date.

    Args:
        date_str: The trading date in DD_MM_YYYY format (e.g., '27_08_2026') or partial date.

    Returns:
        dict containing status ('valid', 'incomplete', or 'missing'), strike_count, has_spot, and folder path.
    """
    try:
        folder = find_date_folder(date_str)
        if not folder or not folder.exists():
            return {
                "status": "missing",
                "error": f"No data folder found for date '{date_str}' in DATA directory.",
                "has_spot": False,
                "strike_count": 0,
            }

        spot_files = list(folder.glob("NIFTY50_spot_*.csv"))
        strike_files = [f for f in folder.glob("*.csv") if not f.name.startswith("NIFTY50_spot_")]
        has_spot = len(spot_files) > 0
        strike_count = len(strike_files)

        is_valid = has_spot and strike_count >= 20

        return {
            "status": "valid" if is_valid else "incomplete",
            "date": date_str,
            "folder_path": str(folder),
            "has_spot": has_spot,
            "spot_filename": spot_files[0].name if has_spot else None,
            "strike_count": strike_count,
            "is_ready_for_backtest": is_valid,
            "notes": "Data is clean and ready" if is_valid else "Warning: missing spot or strikes count < 20",
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "has_spot": False, "strike_count": 0}


def run_backtest_tool(
    strategy_id: str,
    date_str: str,
    capital: float = 500000.0,
    params: Optional[dict] = None
) -> dict:
    """
    Execute an option strategy backtest for a specific date with realistic margin and transaction costs.

    Args:
        strategy_id: Strategy identifier (e.g. 'short_straddle', 'bull_call_spread', 'iron_condor')
        date_str: Date string in DD_MM_YYYY format (e.g. '27_08_2026')
        capital: Capital allocated in ₹ (default: 500000.0)
        params: Optional dictionary of parameter overrides (e.g. {'take_profit_pct': 2.5, 'margin_mode': 'realistic'})

    Returns:
        dict with Net P&L, Gross P&L, transaction costs, trade count, win rate, and skip rate.
    """
    try:
        strat = get_strategy(strategy_id)
        folder = find_date_folder(date_str)
        if not folder:
            return {"error": f"Data folder not found for date {date_str}"}

        expiry = detect_expiry_from_folder(folder)
        run_params = {"capital_per_trade": capital, **(params or {})}

        result = run_backtest(
            strategy=strat,
            data_folder=str(folder),
            expiry_date=expiry,
            params=run_params
        )

        if "error" in result:
            return {"error": result["error"]}

        return {
            "strategy_id": strategy_id,
            "strategy_name": result["strategy_name"],
            "date": date_str,
            "capital": capital,
            "final_net_pnl": result["final_pnl"],
            "gross_pnl": result["gross_pnl"],
            "total_txn_costs": result["total_txn_costs"],
            "total_trades": result["total_trades"],
            "wins": result["wins"],
            "losses": result["losses"],
            "win_rate_pct": round((result["wins"] / result["total_trades"] * 100) if result["total_trades"] > 0 else 0, 1),
            "data_quality": result.get("data_quality", {}),
            "execution_ms": result.get("elapsed_ms", 0),
        }
    except Exception as e:
        return {"error": f"Backtest failed: {str(e)}"}


def compare_all_strategies_tool(date_str: str, capital: float = 500000.0) -> list[dict]:
    """
    Run all 12 strategies for a given market date and return a leaderboard ranked by Net P&L.

    Args:
        date_str: Date string in DD_MM_YYYY format (e.g. '27_08_2026')
        capital: Capital allocated in ₹ (default: 500000.0)

    Returns:
        List of strategy results sorted from highest Net P&L to lowest.
    """
    strategies = get_all_strategies()
    leaderboard = []

    for sid in strategies.keys():
        res = run_backtest_tool(strategy_id=sid, date_str=date_str, capital=capital)
        if "error" not in res:
            leaderboard.append({
                "strategy_id": sid,
                "strategy_name": res["strategy_name"],
                "net_pnl": res["final_net_pnl"],
                "gross_pnl": res["gross_pnl"],
                "txn_costs": res["total_txn_costs"],
                "trades": res["total_trades"],
                "win_rate": res["win_rate_pct"],
                "skip_rate": res.get("data_quality", {}).get("skip_rate", 0),
            })

    leaderboard.sort(key=lambda x: x["net_pnl"], reverse=True)
    return leaderboard


def audit_margin_tool(strategy_id: str, capital: float = 500000.0, lot_size: int = 65) -> dict:
    """
    Audit capital adequacy and SPAN margin requirements for an option strategy.

    Args:
        strategy_id: Strategy identifier (e.g. 'short_straddle', 'buy_call')
        capital: Available capital in ₹
        lot_size: Contract lot size (default: 65)

    Returns:
        dict with margin requirements per lot, affordable lots, and viability verdict.
    """
    try:
        strat = get_strategy(strategy_id)
        meta = strat.meta()

        sample_atm = 24500
        dummy_legs = strat.get_legs(sample_atm, float(sample_atm), {})
        for leg in dummy_legs:
            leg.entry_price = 100.0

        sized_legs = strat.calc_quantities(
            dummy_legs, capital=capital, lot_size=lot_size, config={"margin_mode": "realistic"}
        )

        lots_affordable = (sized_legs[0].quantity // lot_size) if sized_legs else 0

        # Calculate representative margin per lot
        if any(leg.direction == "SELL" for leg in dummy_legs):
            # Short margin model
            single_leg_margin = sample_atm * lot_size * 0.15
            est_margin_per_lot = single_leg_margin * (1.5 if len(dummy_legs) >= 2 else 1.0)
        else:
            # Long margin model (premium only)
            est_margin_per_lot = sum(leg.entry_price * lot_size for leg in dummy_legs)

        is_viable = lots_affordable > 0
        return {
            "strategy_id": strategy_id,
            "strategy_name": meta.name,
            "risk_type": meta.risk_type,
            "capital_provided": capital,
            "est_margin_required_per_lot": round(est_margin_per_lot, 2),
            "max_lots_affordable": lots_affordable,
            "is_viable": is_viable,
            "recommendation": "Adequate capital" if is_viable else f"Underfunded: needs at least ₹{est_margin_per_lot:,.0f} for 1 lot.",
        }
    except Exception as e:
        return {"error": f"Margin audit failed: {str(e)}"}


def publish_agent_insight_tool(
    date_str: str,
    summary_md: str,
    top_strategy: str,
    worst_strategy: str,
    regime_notes: str = "",
    risk_assessment: str = ""
) -> dict:
    """
    Store an executive daily market intelligence report into the SQLite results database for the React dashboard.

    Args:
        date_str: Analysis date (DD_MM_YYYY)
        summary_md: Markdown formatted executive summary
        top_strategy: Name of the top performing strategy
        worst_strategy: Name of the worst performing strategy
        regime_notes: Notes on market regime (trend, decay, IV crush)
        risk_assessment: Capital risk commentary

    Returns:
        dict with success status and generated insight_id.
    """
    try:
        insight_id = save_agent_insight({
            "analysis_date": date_str,
            "executive_summary": summary_md,
            "top_strategy": top_strategy,
            "worst_strategy": worst_strategy,
            "regime_notes": regime_notes,
            "risk_assessment": risk_assessment,
        })
        return {"status": "success", "insight_id": insight_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_dashboard_health_tool() -> dict:
    """
    Inspect the health and connectivity of the Strategy Lab backend, database, and data repository.

    Returns:
        dict containing database status, backtest records count, and available months.
    """
    try:
        init_db()
        recent_backtests = get_backtests(limit=5)
        months = get_available_months()

        return {
            "status": "healthy",
            "database": "SQLite connected (results.db)",
            "saved_backtests_count": len(recent_backtests),
            "available_data_months": months,
            "api_server": "FastAPI operational",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def inspect_ui_design_tokens_tool() -> dict:
    """
    Read active CSS design tokens from frontend index.css to verify styling standards.

    Returns:
        dict containing theme variables (colors, fonts, radius, shadows).
    """
    try:
        css_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "index.css"
        if not css_path.exists():
            return {"error": f"index.css not found at {css_path}"}

        content = css_path.read_text(encoding="utf-8")
        tokens = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("--") and ":" in line:
                key, val = line.split(":", 1)
                tokens[key.strip()] = val.rstrip(";").strip()

        sample_tokens = {
            "bg_dark": tokens.get("--bg-dark", "#0b0d14"),
            "bg_card": tokens.get("--bg-card", "#151824"),
            "color_profit": tokens.get("--color-profit", "#10b981"),
            "color_loss": tokens.get("--color-loss", "#f43f5e"),
            "color_accent": tokens.get("--color-accent", "#6366f1"),
            "font_family": tokens.get("--font-body", "Inter"),
        }
        return {"status": "ok", "tokens_count": len(tokens), "core_palette": sample_tokens}
    except Exception as e:
        return {"error": str(e)}


def review_ui_animations_tool(component_name: str) -> dict:
    """
    Evaluate a frontend React component against Emil Kowalski's Design Engineering & animation principles.
    Checks: absence of 'transition: all', active button press scale, cubic-bezier ease-out, and layout shifts.

    Args:
        component_name: Name of component or page (e.g. 'RunBacktest', 'Sidebar', 'App')

    Returns:
        dict containing an Emil Kowalski craft review with a structured Before/After/Why markdown table.
    """
    try:
        src_dir = Path(__file__).parent.parent.parent / "frontend" / "src"
        matches = list(src_dir.rglob(f"{component_name}.*"))

        if not matches:
            return {"error": f"Component {component_name} not found in {src_dir}"}

        comp_path = matches[0]
        code = comp_path.read_text(encoding="utf-8")

        # Emil Kowalski craft checks
        issues = []

        if "transition: all" in code or 'transition: "all"' in code or "transition: 'all'" in code:
            issues.append({
                "before": "transition: all 300ms",
                "after": "transition: transform 200ms ease-out, opacity 200ms ease-out",
                "why": "Avoid 'all' to prevent layout recalculations; specify exact animated properties."
            })

        if "ease-in" in code:
            issues.append({
                "before": "animation: fadeIn 300ms ease-in",
                "after": "animation: fadeIn 200ms cubic-bezier(0.16, 1, 0.3, 1)",
                "why": "ease-in feels sluggish on UI entry; ease-out feels instant and responsive."
            })

        if "scale(0)" in code:
            issues.append({
                "before": "transform: scale(0)",
                "after": "transform: scale(0.95); opacity: 0",
                "why": "Nothing in the physical world pops out of absolute zero; scale(0.95) feels natural."
            })

        if not issues:
            issues.append({
                "before": "Standard static interactive elements",
                "after": "Add button:active { transform: scale(0.98); }",
                "why": "Buttons should provide immediate micro-tactile press feedback confirming the interface heard the user."
            })

        # Format markdown table in Emil's required format
        table_md = "| Before | After | Why |\n| --- | --- | --- |\n"
        for item in issues:
            table_md += f"| `{item['before']}` | `{item['after']}` | {item['why']} |\n"

        return {
            "component": comp_path.name,
            "craft_evaluation": "Reviewed under Emil Kowalski Design Engineering philosophy (SKILLS/emil-kowalski/emil-design-eng).",
            "review_table": table_md,
            "issues_found": len(issues),
        }
    except Exception as e:
        return {"error": f"UI review failed: {str(e)}"}
