# NIFTY Neutral Long Straddle Backtester

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A fully automated, C++-accelerated backtesting pipeline for the **NIFTY Neutral Long Straddle** strategy. This project seamlessly integrates daily NSE option-chain downloading with a high-performance C++ backtest engine, designed specifically to be orchestrated via Windows Task Scheduler.

---

## Overview

This project automates the entire daily workflow:

1. **Download**: Fetches NIFTY 50 spot and all CE/PE intraday strike data from the NSE API.
2. **Auto-detect**: Automatically detects the ATM strike from the 9:15 AM spot price and dynamically finds the nearest weekly expiry.
3. **Backtest**: Executes the Neutral Strategy using a heavily optimized C++ engine (via `pybind11`).
4. **Schedule**: Exposes a `.ps1` script to trivially schedule daily 18:00 runs via Windows Task Scheduler.

### Neutral Strategy Logic
The strategy executes a long straddle by buying both Call (CE) and Put (PE) options. The neutral logic calculates the fractional lots affordable for both legs based on the allocated capital per leg, and strictly uses the **minimum quantity of both legs** to ensure perfect Delta neutrality at entry:
`quantity = min(call_quantity, put_quantity)`

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  NSE Website    │───> │  DATA_FETCH_AUTO │────>│  NEUTRAL ENGINE │
│  (option-chain) │     │  • Spot CSV      │     │  (C++ & Python) │
│                 │     │  • Strike CSVs   │     │  • Neutral Qty  │
└─────────────────┘     └──────────────────┘     │  • P&L calc     │
                                                 └────────┬────────┘
                                                          │
                           ┌──────────────────────────────┘
                           ▼
                  ┌─────────────────┐
                  │  RESULT/NEUTRAL │
                  └─────────────────┘
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Note: Requires `pandas` and `curl_cffi`)*

### 2. Build the C++ Engine
The core execution logic is written in C++ for maximum speed (~10-15ms per run vs ~3-5s in Python). You must compile it first.
Requires MSVC (Visual Studio Build Tools) and C++17 support.

```bash
cd NEUTRAL_STRADDLE/cpp_engine/build
cmake .. -Dpybind11_DIR=$(python -m pybind11 --cmakedir)
cmake --build . --config Release
```
This generates the `.pyd` module inside `NEUTRAL_STRADDLE/`.

### 3. Run the Automated Pipeline
The pipeline handles fetching today's data and running the backtest immediately after.
```bash
cd NEUTRAL_STRADDLE
python DAILY_PIPELINE.py
```

### 4. Schedule Daily Runs (Windows)
Set up a "set-and-forget" automation that runs every day at 18:00 (after market hours).
```powershell
# Run as Administrator
PowerShell -ExecutionPolicy Bypass -File NEUTRAL_STRADDLE/schedule_daily.ps1
```

---

## Configuration

You can tweak the strategy parameters inside `NEUTRAL_STRADDLE/STRATEGY_V1_AUTO.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ENTRY_TIME` | 09:20 | First trade entry |
| `TRADE_INTERVAL` | 5 min | Time between entries |
| `HOLD_MINUTES` | 60 | Max hold time |
| `TAKE_PROFIT_PCT` | 3.0% | Take profit (% of capital per leg) |
| `STOP_LOSS_PCT` | 1.0% | Stop loss (% of capital per leg) |
| `NO_TRADE_WINDOWS` | 10:00-14:00, 14:30-15:30 | No-trade periods |
| `CAPITAL_PER_TRADE` | 100,000 | Capital allocated per trade |

---

## Important Notices
- **Windows-only**: PowerShell scripts, Task Scheduler, and MSVC compilation are tailored for Windows.
- **NSE Terms of Service**: Scraping NSE data may violate their ToS. `curl_cffi` is used to bypass anti-bot mechanisms, but use this project at your own risk for educational purposes.
- **Data Folder Isolation**: Downloaded market data and result CSVs are dynamically routed to `/DATA/` and `/RESULT/` in the root folder, keeping the strategy directory clean.

## License
MIT License. See `LICENSE` for details.
