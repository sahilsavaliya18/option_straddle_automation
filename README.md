# NIFTY Options Strategy Lab & Automated Backtesting Platform

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![React: 19](https://img.shields.io/badge/React-19-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)
![Tests: 23 Passed](https://img.shields.io/badge/Tests-23%20Passed-brightgreen.svg)
![AI Desk: 100% Free](https://img.shields.io/badge/AI%20Trading%20Desk-Gemini%20Free%20Tier-purple.svg)

A professional, full-stack options research, backtesting, and autonomous multi-agent quantitative trading desk for **NIFTY 50 intraday strategies**. The system integrates automated daily NSE option chain acquisition, a multi-strategy backtesting engine with realistic margin and transaction cost modeling, an interactive React-based analytics dashboard, and a **100% free multi-agent trading & design engineering crew**.

---

## 🌟 Key Features

- **Autonomous AI Trading Desk (Virtual Employees)**: 5 specialized agents + Team Lead managing data audits, quantitative alpha experiments, margin/cost verification, daily executive briefings, and UI design engineering.
- **Emil Kowalski Design Engineering Standard**: UI Webmaster agent governed by 15 Emil Kowalski design engineering skills (`SKILLS/emil-kowalski/`), enforcing responsive easing curves, sub-pixel alignments, tactile press scales, and structured `| Before | After | Why |` reviews.
- **100% Free of Cost Execution**: Powered by Google Gemini Free API (1,500 req/day) with zero external vector DB or paid subscriptions, featuring deterministic offline fallback.
- **12 Pre-Built Strategies**: Full support for single-leg, 2-leg spreads, straddles, strangles, and 4-leg condors/butterflies.
- **Realistic Cost Model (Indian Market)**: Accounts for flat brokerage (₹20/order), STT on sell side (0.05%), NSE exchange turnover fees (0.053%), 18% GST, stamp duty, SEBI fees, and slippage friction.
- **SPAN-Like Margin Modeling**: Dynamic margin calculation (~15% of underlying notional for short legs) prevents unrealistic sizing and margin over-allocation.
- **Data Quality & Execution Tracking**: Real-time monitoring of slot attempts, execution rate, and reason-coded skips (`zero_quantity`, `missing_option_data`, `no_trade_window`).
- **Interactive Web Dashboard & AI Desk**: React + Vite frontend with payoff visualizers, equity curves, strategy comparative matrix, granular trade logs, and dedicated `/ai-desk` console.
- **Resilient & Tested**: 23 automated tests verifying P&L math, cost models, agent tool execution, team personas, and fallback execution.

---

## 📊 Supported Strategies

| Category | Strategy | Legs | Risk Profile | Ideal Condition |
|---|---|---|---|---|
| **Bullish** | Bull Call Spread | 2 (Buy ATM CE + Sell OTM CE) | Defined | Mild Uptrend |
| | Bull Put Spread | 2 (Sell ATM PE + Buy OTM PE) | Defined | Mild Uptrend |
| | Buy Call | 1 (Buy ATM CE) | Defined | Strong Momentum Up |
| **Bearish** | Bear Put Spread | 2 (Buy ATM PE + Sell OTM PE) | Defined | Mild Downtrend |
| | Bear Call Spread | 2 (Sell ATM CE + Buy OTM CE) | Defined | Mild Downtrend |
| | Buy Put | 1 (Buy ATM PE) | Defined | Strong Momentum Down |
| **Neutral** | Short Straddle | 2 (Sell ATM CE + Sell ATM PE) | Undefined | Low Volatility / Sideways |
| | Short Strangle | 2 (Sell OTM CE + Sell OTM PE) | Undefined | Wide Range-Bound |
| | Iron Butterfly | 4 (Short Straddle + Long OTM Wings) | Defined | High IV / Low Volatility |
| | Iron Condor | 4 (Short Strangle + Long OTM Wings) | Defined | High IV / Range-Bound |
| **Volatile** | Long Straddle | 2 (Buy ATM CE + Buy ATM PE) | Defined | High Volatility Breakout |
| | Long Strangle | 2 (Buy OTM CE + Buy OTM PE) | Defined | Large Directional Move |

---

## 🤖 Autonomous AI Trading Desk (Virtual Employees)

The platform includes a 6-persona multi-agent trading & engineering desk operating **100% free of cost** using Google Gemini Free API (with deterministic offline fallback):

| Agent Persona | Role | Core Mission & Assigned Tools |
|---|---|---|
| **Data Guard** | Senior Market Data Engineer | Verifies tick continuity, checks spot file presence, and ensures >= 20 option strikes before execution. Tool: `audit_market_data`. |
| **Quant Strategist** | Lead Quantitative Researcher | Runs comparative intraday backtests across all 12 option strategies and ranks by Net P&L. Tools: `run_backtest_tool`, `compare_all_strategies_tool`. |
| **Risk Officer** | Chief Risk & Margin Auditor | Enforces realistic SPAN margin adequacy (~15% of spot notional) and verifies profitability after full Indian regulatory costs. Tool: `audit_margin_tool`. |
| **Portfolio Analyst** | Chief Market Intelligence Reporter | Synthesizes daily performance, explains market regime (theta decay vs gamma spike), and publishes report cards to the dashboard. Tool: `publish_agent_insight_tool`. |
| **UI Webmaster** | Frontend Design Engineer & Handler | Monitors backend/DB health and reviews React components under **Emil Kowalski's Design Engineering** standards. Tools: `check_dashboard_health_tool`, `inspect_ui_design_tokens_tool`, `review_ui_animations_tool`. |
| **Team Lead** | Desk Managing Director & Orchestrator | Coordinates sequential multi-agent workflows, dispatches tasks, and answers interactive user inquiries. |

### 🎨 Emil Kowalski Design Engineering Integration
Located in `SKILLS/emil-kowalski/`, the desk includes 15 curated design engineering skills:
- **Motion Polish**: Eliminates generic `transition: all` in favor of hardware-accelerated transforms and opacity.
- **Micro-Interactions**: Enforces instant `:active` button scale feedback (`transform: scale(0.98)`).
- **Easing Curves**: Replaces sluggish `ease-in` with responsive ease-out curves (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **Structured Audits**: The UI Webmaster outputs actionable critique tables formatted as `| Before | After | Why |`.

---

## 📁 Repository Structure

```
NEW_PROJECT/
├── STRATEGY_LAB/                 # 🚀 Web Dashboard & Multi-Strategy Engine
│   ├── backend/                  # FastAPI backend
│   │   ├── agents/               # 🤖 Autonomous Multi-Agent Desk
│   │   │   ├── core.py           # Lightweight Agent, Task & Crew pattern (Zero heavy dependencies)
│   │   │   ├── team.py           # 6 Virtual employee personas & system prompts
│   │   │   ├── tools.py          # 8 Safe, typed tools (Backtest, Margin, Emil UI review, etc.)
│   │   │   └── runner.py         # Autonomous daily workflow & interactive chat runners
│   │   ├── api/                  # REST endpoints (/strategies, /backtest, /data, /agents)
│   │   ├── engine/               # Python backtesting engine & execution tracker
│   │   ├── strategies/           # Strategy implementations (all 12 strategies)
│   │   ├── results/              # SQLite store (results.db with agent_insights table)
│   │   ├── tests/                # Automated pytest test suite (23 tests)
│   │   ├── config.py             # Global defaults & cost parameters
│   │   └── main.py               # FastAPI entry point
│   ├── frontend/                 # React 19 + Vite dashboard
│   │   ├── src/
│   │   │   ├── pages/            # Dashboard, Strategies, RunBacktest, Results, Compare, AiDesk
│   │   │   ├── components/       # Sidebar, ErrorBoundary, Payoff charts
│   │   │   └── ...
│   │   └── start_dashboard.bat   # One-click launcher (backend + frontend)
│   │
├── DATA_FETCH/                   # 📥 Automated NSE Data Downloader
│   ├── DATA_FETCH.py             # Manual date fetcher
│   └── DATA_FETCH_AUTO.py        # Automated date & expiry fetcher
│
├── NEUTRAL_STRADDLE/             # ⚡ C++ Accelerated Engine (Standalone)
│   ├── STRATEGY_V1_AUTO.py       # Standalone automated straddle runner
│   ├── cpp_engine/               # C++ pybind11 implementation
│   └── schedule_daily.ps1        # Windows Task Scheduler orchestrator
│
├── SKILLS/                       # 🧠 Pre-mortem, Discovery & Emil Kowalski Design Skills
│   ├── emil-kowalski/            # 15 Emil Kowalski design engineering & animation skills
│   └── pre-build-discovery/      # Pre-build discovery & spec verification framework
├── .gitignore                    # Excludes data, results, node_modules, build artifacts
├── requirements.txt              # Backend dependencies
└── README.md                     # Documentation
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** (64-bit)
- **Node.js 18+** & npm (for the frontend dashboard)
- Windows OS (for automated Task Scheduler scripts)

### 2. Install Dependencies

**Backend:**
```bash
pip install -r requirements.txt
pip install -r STRATEGY_LAB/backend/requirements.txt
```

*(Optional for LLM reasoning)*: Set `GEMINI_API_KEY` in your environment or `.env`. If not provided, agents run fully deterministically without error.

**Frontend:**
```bash
cd STRATEGY_LAB/frontend
npm install
cd ../..
```

### 3. Launch the Web Dashboard

**One-Click Start (Windows):**
Double-click `STRATEGY_LAB/start_dashboard.bat` or run:
```powershell
& ".\STRATEGY_LAB\start_dashboard.bat"
```

**Manual Start:**
- **Backend API**:
  ```powershell
  python -m uvicorn STRATEGY_LAB.backend.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Frontend Dashboard**:
  ```powershell
  cd STRATEGY_LAB\frontend
  npm run dev
  ```
Open `http://localhost:5173` in your browser and click on **AI Desk** in the navigation sidebar.

---

## 🧪 Running Automated Tests

Run the full test suite to verify P&L calculations, cost deductions, strategy signatures, agent tools, and multi-agent workflows:

```powershell
python -m pytest STRATEGY_LAB/backend/tests/ -v
```

All **23 unit tests** verify:
- Multi-leg P&L math (BUY leg decay vs SELL leg profit)
- Regulatory transaction cost deductions (brokerage, STT, turnover, GST, stamp duty)
- Realistic SPAN margin calculation & sizing protection
- All 12 strategy registries & metadata
- Agent tools: data audit, backtest, margin check, Emil Kowalski UI review, and insight persistence
- Multi-agent team construction & deterministic daily workflow execution

---

## 💰 Transaction Cost & Margin Model

### Indian Market Regulatory Costs
Calculated per trade in `STRATEGY_LAB/backend/strategies/base.py`:
- **Brokerage**: ₹20 flat per order (2 orders per leg: Entry + Exit)
- **STT**: 0.05% charged on sell-side option premium
- **Exchange Turnover**: 0.053% of total traded premium turnover
- **GST**: 18% on (Brokerage + Exchange Charges)
- **Stamp Duty**: 0.003% on buy-side premium
- **SEBI Fee**: 0.0001% (₹10 / crore) on turnover
- **Slippage**: ₹1.0 per lot per leg friction

### Realistic Margin Model
- Short legs require ~15% of the underlying strike value per lot (approximating NSE SPAN margin), preventing over-leveraged sizing in SELL strategies.
- Defined-risk spreads (Bull/Bear spreads, Condors, Butterflies) use defined spread width minus net credit.

---

## 📥 Market Data Acquisition

To fetch intraday 1-minute spot and option strike data for today:
```powershell
python DATA_FETCH\DATA_FETCH_AUTO.py
```
This fetches 61 strikes centered at ATM from the NSE API and saves the files into `DATA/<Month>_DATA/<DD_MM_YYYY>/`.

---

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.
