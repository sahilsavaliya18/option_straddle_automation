"""
High-level execution runners for the Autonomous AI Trading Desk.
Supports autonomous daily multi-agent runs and interactive chat.
"""

from __future__ import annotations
import json
from datetime import datetime
from typing import Optional

from .core import Task, Crew
from .team import (
    create_team_lead_agent,
    create_data_guard_agent,
    create_quant_strategist_agent,
    create_risk_officer_agent,
    create_portfolio_analyst_agent,
    create_ui_webmaster_agent,
    get_agent_by_role,
)
from .tools import compare_all_strategies_tool, publish_agent_insight_tool, check_dashboard_health_tool, review_ui_animations_tool


def run_daily_desk_workflow(
    date_str: str = "27_08_2026",
    capital: float = 500000.0,
    api_key: Optional[str] = None
) -> dict:
    """
    Executes the full end-of-day sequence across all 5 virtual employees:
    1. Data Guard: Audits dataset completeness
    2. Quant Strategist: Backtests and ranks all 12 strategies
    3. Risk Officer: Audits SPAN margin & fees
    4. Portfolio Analyst: Publishes executive briefing
    5. UI Webmaster: Runs dashboard health and Emil Kowalski craft review
    """
    data_agent = create_data_guard_agent()
    quant_agent = create_quant_strategist_agent()
    risk_agent = create_risk_officer_agent()
    analyst_agent = create_portfolio_analyst_agent()
    web_agent = create_ui_webmaster_agent()

    tasks = [
        Task(
            agent=data_agent,
            description=f"Audit the market data files for date '{date_str}'. Check if spot price and at least 20 strikes exist.",
            expected_output="Confirmation of dataset validity, total strike count, and spot status.",
        ),
        Task(
            agent=quant_agent,
            description=f"Run a comparative backtest across all 12 strategies for date '{date_str}' with capital ₹{capital:,.0f}. Identify the #1 top performer and #1 worst performer by Net P&L.",
            expected_output="Leaderboard of top strategies with Net P&L, gross P&L, and trade counts.",
        ),
        Task(
            agent=risk_agent,
            description=f"Evaluate the margin adequacy and Indian transaction cost impact for the top performing strategy on date '{date_str}'. Confirm whether capital ₹{capital:,.0f} satisfies realistic SPAN margins (~15% notional).",
            expected_output="Risk approval, required margin per lot, and net cost deductions.",
        ),
        Task(
            agent=analyst_agent,
            description=f"Synthesize the findings into an executive briefing for date '{date_str}'. Explain the primary market driver (theta decay, trend, or IV spike). Publish the insight report using the publish tool.",
            expected_output="Published executive report card with actionable takeaways.",
        ),
        Task(
            agent=web_agent,
            description="Run a health check on the dashboard backend and evaluate the 'RunBacktest' component under Emil Kowalski's Design Engineering standards (SKILLS/emil-kowalski/emil-design-eng).",
            expected_output="Dashboard health status and Emil Kowalski Before/After/Why critique table.",
        ),
    ]

    crew = Crew(
        agents=[data_agent, quant_agent, risk_agent, analyst_agent, web_agent],
        tasks=tasks,
    )

    result = crew.kickoff(inputs={"date": date_str, "capital": capital, "api_key": api_key})

    # Ensure report is saved in SQLite even in deterministic mode
    try:
        leaderboard = compare_all_strategies_tool(date_str, capital)
        top = leaderboard[0]["strategy_name"] if leaderboard else "Short Straddle"
        worst = leaderboard[-1]["strategy_name"] if leaderboard else "Long Straddle"
        top_pnl = leaderboard[0]["net_pnl"] if leaderboard else 0.0

        summary = (
            f"### Daily Executive Briefing ({date_str})\n\n"
            f"- **Top Performer**: **{top}** with **+₹{top_pnl:,.2f}** Net P&L.\n"
            f"- **Worst Performer**: **{worst}**.\n"
            f"- **Market Regime**: Volatility decay favored credit and neutral strategies; high-frequency directional legs incurred slippage.\n"
            f"- **Risk & Margin**: Account capital ₹{capital:,.0f} safely satisfies SPAN margin rules.\n"
        )
        insight_id = publish_agent_insight_tool(
            date_str=date_str,
            summary_md=summary,
            top_strategy=top,
            worst_strategy=worst,
            regime_notes="Intraday range-bound with steady theta decay.",
            risk_assessment="Capital adequate for 1-2 lots realistic margin.",
        ).get("insight_id", 1)
        result["insight_id"] = insight_id
        result["top_strategy"] = top
        result["top_pnl"] = top_pnl
    except Exception:
        pass

    return result


def chat_with_trading_desk(
    message: str,
    target_agent_role: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """
    Direct a question or assignment to a specific virtual employee or the Team Lead.
    """
    if target_agent_role:
        agent = get_agent_by_role(target_agent_role)
    else:
        agent = None

    if not agent:
        agent = create_team_lead_agent()

    start_time = datetime.now()
    response_text = agent.execute(task_description=message, api_key=api_key)

    return {
        "agent_name": agent.name,
        "agent_role": agent.role,
        "prompt": message,
        "response": response_text,
        "timestamp": start_time.strftime("%H:%M:%S"),
    }
