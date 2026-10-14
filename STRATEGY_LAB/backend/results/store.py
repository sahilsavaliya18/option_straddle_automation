"""
SQLite result storage for backtests.
Stores backtest summaries + individual trades for fast retrieval and comparison.
"""

from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import DB_PATH


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS backtests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id     TEXT    NOT NULL,
            strategy_name   TEXT    NOT NULL,
            backtest_date   TEXT    NOT NULL,
            expiry_date     TEXT,
            data_folder     TEXT,
            params_json     TEXT,
            total_trades    INTEGER DEFAULT 0,
            wins            INTEGER DEFAULT 0,
            losses          INTEGER DEFAULT 0,
            avg_pnl         REAL    DEFAULT 0.0,
            final_pnl       REAL    DEFAULT 0.0,
            elapsed_ms      REAL    DEFAULT 0.0,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),

            UNIQUE(strategy_id, backtest_date, params_json)
        );

        CREATE TABLE IF NOT EXISTS trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            backtest_id     INTEGER NOT NULL REFERENCES backtests(id) ON DELETE CASCADE,
            trade_no        INTEGER NOT NULL,
            entry_time      TEXT,
            exit_time       TEXT,
            exit_reason     TEXT,
            atm_at_entry    INTEGER,
            strike          INTEGER,
            net_pnl         REAL DEFAULT 0.0,
            cumulative_pnl  REAL DEFAULT 0.0,
            legs_json       TEXT,
            -- Backward-compatible columns
            ce_entry        REAL,
            ce_exit         REAL,
            ce_qty          INTEGER,
            ce_pnl          REAL,
            pe_entry        REAL,
            pe_exit         REAL,
            pe_qty          INTEGER,
            pe_pnl          REAL
        );

        CREATE INDEX IF NOT EXISTS idx_backtests_strategy
            ON backtests(strategy_id);
        CREATE INDEX IF NOT EXISTS idx_backtests_date
            ON backtests(backtest_date);
        CREATE INDEX IF NOT EXISTS idx_trades_backtest
            ON trades(backtest_id);

        CREATE TABLE IF NOT EXISTS agent_insights (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date     TEXT    NOT NULL,
            executive_summary TEXT    NOT NULL,
            top_strategy      TEXT    NOT NULL,
            worst_strategy    TEXT    NOT NULL,
            regime_notes      TEXT,
            risk_assessment   TEXT,
            ui_review         TEXT,
            raw_chat_json     TEXT,
            created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_agent_insights_date
            ON agent_insights(analysis_date);
    """)
    conn.commit()
    conn.close()


def save_backtest(result: dict) -> int:
    """
    Save a backtest result to the database.
    Returns the backtest ID.
    """
    init_db()
    conn = _get_conn()

    # Serialize params (excluding non-serializable items)
    params = result.get("params", {})
    clean_params = {
        k: v for k, v in params.items()
        if isinstance(v, (str, int, float, bool, list))
    }
    params_json = json.dumps(clean_params, sort_keys=True)

    # Check if this exact backtest already exists
    existing = conn.execute(
        "SELECT id FROM backtests WHERE strategy_id=? AND backtest_date=? AND params_json=?",
        (result["strategy_id"], result["backtest_date"], params_json),
    ).fetchone()

    if existing:
        # Delete old data and re-insert
        conn.execute("DELETE FROM backtests WHERE id=?", (existing["id"],))
        conn.commit()

    cursor = conn.execute(
        """INSERT INTO backtests
           (strategy_id, strategy_name, backtest_date, expiry_date,
            data_folder, params_json, total_trades, wins, losses,
            avg_pnl, final_pnl, elapsed_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result["strategy_id"],
            result["strategy_name"],
            result["backtest_date"],
            result.get("expiry_date", ""),
            result.get("data_folder", ""),
            params_json,
            result["total_trades"],
            result["wins"],
            result["losses"],
            result["avg_pnl"],
            result["final_pnl"],
            result.get("elapsed_ms", 0),
        ),
    )
    backtest_id = cursor.lastrowid

    # Insert trades
    for trade in result.get("trades", []):
        conn.execute(
            """INSERT INTO trades
               (backtest_id, trade_no, entry_time, exit_time, exit_reason,
                atm_at_entry, strike, net_pnl, cumulative_pnl, legs_json,
                ce_entry, ce_exit, ce_qty, ce_pnl,
                pe_entry, pe_exit, pe_qty, pe_pnl)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                backtest_id,
                trade["Trade_No"],
                trade["Entry_Time"],
                trade["Exit_Time"],
                trade["Exit_Reason"],
                trade["ATM_at_Entry"],
                trade.get("Strike"),
                trade["Net_PnL"],
                trade["Cumulative_PnL"],
                json.dumps(trade.get("Legs", [])),
                trade.get("CE_Entry"),
                trade.get("CE_Exit"),
                trade.get("CE_Qty"),
                trade.get("CE_PnL"),
                trade.get("PE_Entry"),
                trade.get("PE_Exit"),
                trade.get("PE_Qty"),
                trade.get("PE_PnL"),
            ),
        )

    conn.commit()
    conn.close()
    return int(backtest_id) if backtest_id is not None else 0


def get_backtests(
    strategy_id: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Get backtest summaries."""
    init_db()
    conn = _get_conn()

    query = "SELECT * FROM backtests"
    params_list: list = []

    if strategy_id:
        query += " WHERE strategy_id = ?"
        params_list.append(strategy_id)

    query += " ORDER BY created_at DESC LIMIT ?"
    params_list.append(limit)

    rows = conn.execute(query, params_list).fetchall()
    conn.close()

    return [dict(r) for r in rows]


def get_backtest_detail(backtest_id: int) -> dict | None:
    """Get a single backtest with all its trades."""
    init_db()
    conn = _get_conn()

    bt = conn.execute(
        "SELECT * FROM backtests WHERE id = ?", (backtest_id,)
    ).fetchone()

    if not bt:
        conn.close()
        return None

    trades = conn.execute(
        "SELECT * FROM trades WHERE backtest_id = ? ORDER BY trade_no",
        (backtest_id,),
    ).fetchall()

    conn.close()

    result = dict(bt)
    result["params"] = json.loads(result.pop("params_json", "{}"))
    result["trades"] = []

    for t in trades:
        trade_dict = dict(t)
        trade_dict["Legs"] = json.loads(trade_dict.pop("legs_json", "[]"))
        result["trades"].append(trade_dict)

    return result


def get_strategy_summary(strategy_id: str) -> dict:
    """Get aggregate stats for a strategy across all backtested dates."""
    init_db()
    conn = _get_conn()

    row = conn.execute(
        """SELECT
            COUNT(*) as total_days,
            SUM(total_trades) as total_trades,
            SUM(wins) as total_wins,
            SUM(losses) as total_losses,
            AVG(final_pnl) as avg_daily_pnl,
            SUM(final_pnl) as cumulative_pnl,
            MIN(final_pnl) as worst_day,
            MAX(final_pnl) as best_day,
            AVG(elapsed_ms) as avg_elapsed_ms
        FROM backtests WHERE strategy_id = ?""",
        (strategy_id,),
    ).fetchone()

    conn.close()
    return dict(row) if row else {}


def delete_backtest(backtest_id: int) -> bool:
    """Delete a backtest and its trades."""
    init_db()
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM backtests WHERE id = ?", (backtest_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def save_agent_insight(insight: dict) -> int:
    """Save an AI agent executive briefing/insight to SQLite."""
    init_db()
    conn = _get_conn()
    cursor = conn.execute(
        """INSERT INTO agent_insights
           (analysis_date, executive_summary, top_strategy, worst_strategy,
            regime_notes, risk_assessment, ui_review, raw_chat_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            insight.get("analysis_date", datetime.now().strftime("%d_%m_%Y")),
            insight.get("executive_summary", ""),
            insight.get("top_strategy", ""),
            insight.get("worst_strategy", ""),
            insight.get("regime_notes", ""),
            insight.get("risk_assessment", ""),
            insight.get("ui_review", ""),
            json.dumps(insight.get("raw_chat", {})) if isinstance(insight.get("raw_chat"), (dict, list)) else str(insight.get("raw_chat", "")),
        ),
    )
    conn.commit()
    insight_id = cursor.lastrowid
    conn.close()
    return int(insight_id) if insight_id is not None else 0


def get_agent_insights(limit: int = 30) -> list[dict]:
    """Retrieve historical agent briefings."""
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM agent_insights ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_agent_insight() -> dict | None:
    """Get the most recent agent briefing."""
    insights = get_agent_insights(limit=1)
    return insights[0] if insights else None

