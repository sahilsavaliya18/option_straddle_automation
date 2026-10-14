"""
Unit test suite for the autonomous multi-agent quantitative trading & engineering desk.
Tests:
- Agent tool execution and deterministic safety.
- Database persistence for agent insights.
- Team persona definitions and tool registries.
- Emil Kowalski UI animation review tool compliance.
- End-to-end desk workflow execution in fallback/deterministic mode.
"""

import pytest
from STRATEGY_LAB.backend.agents.tools import (
    audit_market_data,
    run_backtest_tool,
    compare_all_strategies_tool,
    audit_margin_tool,
    publish_agent_insight_tool,
    check_dashboard_health_tool,
    inspect_ui_design_tokens_tool,
    review_ui_animations_tool,
)
from STRATEGY_LAB.backend.agents.team import get_trading_desk_team, get_agent_by_role
from STRATEGY_LAB.backend.agents.runner import run_daily_desk_workflow
from STRATEGY_LAB.backend.results.store import get_agent_insights


class TestAgentTools:
    def test_audit_market_data_valid_date(self):
        """Data Guard tool: verify market data audit on an existing sample date."""
        res = audit_market_data("27_08_2026")
        assert res["status"] in ("valid", "incomplete")
        assert res["date"] == "27_08_2026"
        assert res["has_spot"] is True
        assert res["strike_count"] > 0
        assert "is_ready_for_backtest" in res

    def test_audit_market_data_missing_date(self):
        """Data Guard tool: verify proper handling when date does not exist."""
        res = audit_market_data("01_01_1990")
        assert res["status"] == "missing"
        assert res["has_spot"] is False
        assert "error" in res

    def test_audit_margin_tool(self):
        """Risk Officer tool: verify realistic margin calculation and viability verdict."""
        straddle_margin = audit_margin_tool("short_straddle")
        condor_margin = audit_margin_tool("iron_condor")

        assert straddle_margin["est_margin_required_per_lot"] > 0
        assert straddle_margin["is_viable"] is True
        assert condor_margin["is_viable"] is True
        assert "recommendation" in straddle_margin

    def test_dashboard_health_tool(self):
        """Webmaster tool: verify system health and table status."""
        health = check_dashboard_health_tool()
        assert health["status"] == "healthy"
        assert "SQLite" in health["database"]
        assert "available_data_months" in health
        assert health["api_server"] == "FastAPI operational"

    def test_inspect_ui_design_tokens(self):
        """Webmaster tool: inspect CSS variables and color system."""
        tokens = inspect_ui_design_tokens_tool()
        assert tokens["status"] == "ok"
        assert tokens["tokens_count"] > 0
        assert "core_palette" in tokens
        assert "color_profit" in tokens["core_palette"]

    def test_review_ui_animations_emil_standards(self):
        """Webmaster tool: review component under Emil Kowalski craft rules."""
        review = review_ui_animations_tool("Sidebar")
        assert "Sidebar" in review["component"]
        assert "Emil Kowalski" in review["craft_evaluation"]
        assert "| Before | After | Why |" in review["review_table"]
        assert review["issues_found"] > 0

    def test_publish_agent_insight_tool(self):
        """Portfolio Analyst tool: persist insight to SQLite database."""
        result = publish_agent_insight_tool(
            date_str="27_08_2026",
            summary_md="### Daily Desk Briefing\nTheta decay delivered consistent alpha.",
            top_strategy="Short Straddle",
            worst_strategy="Long Straddle",
            regime_notes="Intraday consolidation, low gamma risk.",
            risk_assessment="Adequate capital for 1-2 lots realistic margin.",
        )
        assert result["status"] == "success"
        assert result["insight_id"] > 0

        # Verify retrieval from store
        insights = get_agent_insights(limit=5)
        assert len(insights) > 0
        latest = insights[0]
        assert latest["top_strategy"] == "Short Straddle"
        assert latest["analysis_date"] == "27_08_2026"

    def test_run_backtest_tool(self):
        """Quant Strategist tool: run backtest safely with typed output."""
        res = run_backtest_tool(strategy_id="short_straddle", date_str="27_08_2026")
        assert res["date"] == "27_08_2026"
        assert res["strategy_id"] == "short_straddle"
        assert "final_net_pnl" in res
        assert "gross_pnl" in res
        assert "total_txn_costs" in res

    def test_compare_all_strategies_tool(self):
        """Quant Strategist tool: rank all 12 strategies for the day."""
        board = compare_all_strategies_tool(date_str="27_08_2026", capital=500000.0)
        assert isinstance(board, list)
        assert len(board) == 12
        # Check sort order: descending net P&L
        for i in range(len(board) - 1):
            assert board[i]["net_pnl"] >= board[i + 1]["net_pnl"]


class TestTeamConstruction:
    def test_build_team_personas(self):
        """Verify all 6 personas have valid configurations, backstories, and tools."""
        team = get_trading_desk_team()
        assert len(team) == 6

        roles = [agent.role for agent in team]
        assert any("Market Data" in r for r in roles)
        assert any("Quantitative" in r for r in roles)
        assert any("Risk" in r for r in roles)
        assert any("Portfolio" in r for r in roles)
        assert any("Frontend" in r or "UI" in r for r in roles)
        assert any("Managing Director" in r or "Orchestrator" in r for r in roles)

        # Verify UI Webmaster has Emil Kowalski tools
        webmaster = get_agent_by_role("ui_webmaster")
        assert webmaster is not None
        tool_names = [fn.__name__ for fn in webmaster.tools]
        assert "review_ui_animations_tool" in tool_names
        assert "inspect_ui_design_tokens_tool" in tool_names
        assert "check_dashboard_health_tool" in tool_names


class TestDeskWorkflow:
    def test_run_daily_desk_workflow(self):
        """Verify full multi-agent desk runs deterministically and completes all 5 tasks."""
        result = run_daily_desk_workflow(date_str="27_08_2026")

        assert result["status"] == "completed"
        assert len(result["task_results"]) == 5
        assert "top_strategy" in result
        assert "insight_id" in result

        agent_names = [t["agent_name"] for t in result["task_results"]]
        assert "Data Guard" in agent_names
        assert "Quant Strategist" in agent_names
        assert "Risk Officer" in agent_names
        assert "Portfolio Analyst" in agent_names
        assert "UI Webmaster" in agent_names
