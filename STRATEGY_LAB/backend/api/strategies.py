"""API routes for strategies — listing, metadata, running backtests."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..strategies.registry import get_all_strategies, get_strategy
from ..engine.python_engine import run_backtest
from ..results.store import save_backtest
from ..data.loader import get_available_dates, detect_expiry_from_folder
from ..config import DEFAULT_PARAMS

router = APIRouter(tags=["strategies"])


class BacktestRequest(BaseModel):
    strategy_id: str
    data_folder: str
    expiry_date: Optional[str] = None
    # Override params
    entry_time: Optional[str] = None
    trade_interval: Optional[int] = None
    hold_minutes: Optional[int] = None
    capital_per_trade: Optional[float] = None
    take_profit_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    lot_size: Optional[int] = None
    offset_from_spot: Optional[int] = None
    spread_width: Optional[int] = None
    margin_mode: Optional[str] = None
    txn_enabled: Optional[bool] = None


@router.get("/strategies")
async def list_strategies():
    """List all available strategies with their metadata."""
    strategies = get_all_strategies()
    result = []

    for sid, strat in strategies.items():
        meta = strat.meta()
        result.append({
            "id": meta.id,
            "name": meta.name,
            "category": meta.category,
            "num_legs": meta.num_legs,
            "description": meta.description,
            "risk_type": meta.risk_type,
            "max_profit": meta.max_profit,
            "max_loss": meta.max_loss,
            "ideal_iv": meta.ideal_iv,
            "ideal_trend": meta.ideal_trend,
            "default_params": {**DEFAULT_PARAMS, **meta.default_params},
        })

    return {"strategies": result}


@router.get("/strategies/{strategy_id}")
async def get_strategy_detail(strategy_id: str):
    """Get detailed info for a single strategy."""
    try:
        strat = get_strategy(strategy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    meta = strat.meta()
    merged_params = {**DEFAULT_PARAMS, **meta.default_params}

    # Generate payoff data
    payoff = strat.get_payoff_data(atm=24500, config=merged_params)

    return {
        "id": meta.id,
        "name": meta.name,
        "category": meta.category,
        "num_legs": meta.num_legs,
        "description": meta.description,
        "risk_type": meta.risk_type,
        "max_profit": meta.max_profit,
        "max_loss": meta.max_loss,
        "ideal_iv": meta.ideal_iv,
        "ideal_trend": meta.ideal_trend,
        "default_params": merged_params,
        "payoff_data": payoff,
    }


@router.post("/backtest/run")
async def run_backtest_endpoint(req: BacktestRequest):
    """Run a backtest for a strategy on a given date's data."""
    try:
        strat = get_strategy(req.strategy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Build params from request
    params = {}
    for field_name in [
        "entry_time", "trade_interval", "hold_minutes",
        "capital_per_trade", "take_profit_pct", "stop_loss_pct",
        "lot_size", "offset_from_spot", "spread_width",
        "margin_mode", "txn_enabled",
    ]:
        val = getattr(req, field_name, None)
        if val is not None:
            params[field_name] = val

    # Auto-detect expiry if not provided
    expiry = req.expiry_date
    if not expiry:
        expiry = detect_expiry_from_folder(req.data_folder)

    result = run_backtest(
        strategy=strat,
        data_folder=req.data_folder,
        expiry_date=expiry,
        params=params if params else None,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Save to database
    backtest_id = save_backtest(result)
    result["backtest_id"] = backtest_id

    return result
