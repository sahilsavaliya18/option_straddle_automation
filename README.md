# NIFTY Options Strategy Lab & Automated Backtesting Platform

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![React: 19](https://img.shields.io/badge/React-19-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)
![Tests: 12 Passed](https://img.shields.io/badge/Tests-12%20Passed-brightgreen.svg)

A professional, full-stack options research and backtesting platform for **NIFTY 50 intraday strategies**. The system integrates automated daily NSE option chain acquisition, a multi-strategy backtesting engine with realistic margin and transaction cost modeling, and an interactive React-based analytics dashboard.

---

## 🌟 Key Features

- **12 Pre-Built Strategies**: Full support for single-leg, 2-leg spreads, straddles, strangles, and 4-leg condors/butterflies.
- **Realistic Cost Model (Indian Market)**: Accounts for flat brokerage (₹20/order), STT on sell side (0.05%), NSE exchange turnover fees (0.053%), 18% GST, stamp duty, SEBI fees, and slippage friction.
- **SPAN-Like Margin Modeling**: Dynamic margin calculation (~15% of underlying notional for short legs) prevents unrealistic sizing and margin over-allocation.
- **Data Quality & Execution Tracking**: Real-time monitoring of slot attempts, execution rate, and reason-coded skips (`zero_quantity`, `missing_option_data`, `no_trade_window`).
- **Interactive Web Dashboard**: React + Vite + Recharts frontend with payoff visualizers, equity curves, strategy comparative matrix, and granular trade-by-trade logs.
- **Resilient & Tested**: Full test suite verifying P&L math, cost models, and strategy signatures; React `ErrorBoundary` guards against UI crashes.
- **Automated Data Fetching**: Daily parallel downloader fetching 61 strikes of NIFTY spot + option chain in 6–12 seconds.

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

## 📁 Repository Structure

```
NEW_PROJECT/
├── STRATEGY_LAB/                 # 🚀 Web Dashboard & Multi-Strategy Engine
│   ├── backend/                  # FastAPI backend
│   │   ├── api/                  # REST endpoints (/strategies, /backtest, /data)
│   │   ├── engine/               # Python backtesting engine & execution tracker
│   │   ├── strategies/           # Strategy implementations (all 12 strategies)
│   │   │   ├── base.py           # Base strategy, P&L logic, margin & cost model
│   │   │   ├── registry.py       # Strategy registry & metadata
│   │   │   └── ...
│   │   ├── results/              # SQLite store (results.db)
│   │   ├── tests/                # Automated pytest test suite
│   │   ├── config.py             # Global defaults & cost parameters
│   │   └── main.py               # FastAPI entry point
│   ├── frontend/                 # React 19 + Vite dashboard
│   │   ├── src/
│   │   │   ├── pages/            # Dashboard, Strategies, RunBacktest, Results, Compare
│   │   │   ├── components/       # Sidebar, ErrorBoundary, Payoff charts
│   │   │   └── ...
│   └── start_dashboard.bat       # One-click launcher (backend + frontend)
│
├── DATA_FETCH/                   # 📥 Automated NSE Data Downloader
│   ├── DATA_FETCH.py             # Manual date fetcher
│   └── DATA_FETCH_AUTO.py        # Automated date & expiry fetcher
│
├── NEUTRAL_STRADDLE/             # ⚡ C++ Accelerated Engine (Standalone)
│   ├── STRATEGY_V1_AUTO.py       # Standalone automated straddle runner
│   ├── cpp_engine/               # C++ pybind11 implementation
│   └── schedule_daily.ps1        # Windows Task Scheduler orchestrator
│
├── SKILLS/                       # 🧠 Pre-mortem & Discovery Frameworks
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
Open `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Tests

Run the test suite to verify P&L calculations, cost deductions, and strategy signatures:

```powershell
python -m pytest STRATEGY_LAB/backend/tests/test_pnl_accuracy.py -v
```

All 12 test assertions check:
- Multi-leg P&L math (BUY leg decay vs SELL leg profit)
- Regulatory transaction cost deductions
- Realistic SPAN margin vs simple sizing
- Default configurations & strategy registry health

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
