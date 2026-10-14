"""API routes for results — listing, detail, deletion."""

from fastapi import APIRouter, HTTPException

from ..results.store import (
    get_backtests, get_backtest_detail, get_strategy_summary, delete_backtest,
)

router = APIRouter(tags=["results"])


@router.get("/results")
async def list_results(strategy_id: str | None = None, limit: int = 100):
    """List backtest results, optionally filtered by strategy."""
    results = get_backtests(strategy_id=strategy_id, limit=limit)
    return {"results": results}


@router.get("/results/{backtest_id}")
async def get_result_detail(backtest_id: int):
    """Get full detail for a single backtest including all trades."""
    detail = get_backtest_detail(backtest_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return detail


@router.get("/analytics/summary/{strategy_id}")
async def get_analytics_summary(strategy_id: str):
    """Get aggregate statistics for a strategy across all backtested dates."""
    summary = get_strategy_summary(strategy_id)
    return {"strategy_id": strategy_id, "summary": summary}


@router.delete("/results/{backtest_id}")
async def delete_result(backtest_id: int):
    """Delete a backtest result."""
    if delete_backtest(backtest_id):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Backtest not found")
