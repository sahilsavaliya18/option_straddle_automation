"""API routes for data availability and status."""

from fastapi import APIRouter

from ..data.loader import get_available_months, get_available_dates

router = APIRouter(tags=["data"])


@router.get("/data/months")
async def list_months():
    """List all available month folders in DATA/."""
    months = get_available_months()
    return {"months": months}


@router.get("/data/dates")
async def list_dates(month: str | None = None):
    """List available date folders with data status."""
    dates = get_available_dates(month)
    return {"dates": dates}


@router.get("/data/status")
async def data_status():
    """Overall data health check."""
    months = get_available_months()
    all_dates = get_available_dates()

    total_days = len(all_dates)
    days_with_spot = sum(1 for d in all_dates if d["has_spot"])
    avg_strikes = (
        sum(d["strike_count"] for d in all_dates) / total_days
        if total_days > 0 else 0
    )

    return {
        "total_months": len(months),
        "total_days": total_days,
        "days_with_spot": days_with_spot,
        "avg_strikes_per_day": round(avg_strikes, 1),
        "months": months,
    }
