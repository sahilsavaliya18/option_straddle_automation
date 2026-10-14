"""
FastAPI router for the Autonomous AI Trading Desk & Engineering Team.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..agents.team import get_trading_desk_team, get_agent_by_role
from ..agents.runner import run_daily_desk_workflow, chat_with_trading_desk
from ..agents.tools import review_ui_animations_tool, check_dashboard_health_tool
from ..results.store import get_agent_insights, get_latest_agent_insight

router = APIRouter(prefix="/agents", tags=["agents"])


class ChatRequest(BaseModel):
    message: str
    target_agent: Optional[str] = None
    api_key: Optional[str] = None


class DailyRunRequest(BaseModel):
    date: str = "27_08_2026"
    capital: float = 500000.0
    api_key: Optional[str] = None


class UiReviewRequest(BaseModel):
    component_name: str = "RunBacktest"


@router.get("/team")
async def get_team():
    """List all virtual employees on the trading & engineering desk."""
    team = get_trading_desk_team()
    result = []
    for agent in team:
        result.append({
            "name": agent.name,
            "role": agent.role,
            "goal": agent.goal,
            "backstory": agent.backstory,
            "tools": [t.__name__ for t in agent.tools],
        })
    return {"team": result}


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat with a specific virtual employee or the Team Lead."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    res = chat_with_trading_desk(
        message=req.message,
        target_agent_role=req.target_agent,
        api_key=req.api_key
    )
    return res


@router.post("/daily-run")
async def daily_run_endpoint(req: DailyRunRequest):
    """Trigger the multi-agent sequence across all 5 virtual employees."""
    res = run_daily_desk_workflow(
        date_str=req.date,
        capital=req.capital,
        api_key=req.api_key
    )
    return res


@router.get("/insights")
async def get_insights(limit: int = 20):
    """Get published agent executive briefings from SQLite."""
    insights = get_agent_insights(limit=limit)
    latest = get_latest_agent_insight()
    return {"insights": insights, "latest": latest}


@router.post("/review-ui")
async def review_ui_endpoint(req: UiReviewRequest):
    """Run an Emil Kowalski Design Engineering review on a frontend component."""
    res = review_ui_animations_tool(req.component_name)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/health")
async def health_endpoint():
    """Run full dashboard and database diagnostics."""
    return check_dashboard_health_tool()
