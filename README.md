# NIFTY Neutral Long Straddle Backtester

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A fully automated, C++-accelerated backtesting pipeline for the **NIFTY Neutral Long Straddle** strategy. This project seamlessly integrates daily NSE option-chain downloading with a high-performance C++ backtest engine, designed to be orchestrated via Windows Task Scheduler.

---

## Overview

This project automates the entire daily workflow:

1. **Download**: Fetches NIFTY 50 spot and all CE/PE intraday strike data in parallel from the NSE API (61 strikes, ~6–12 seconds).
2. **Auto-detect**: Automatically detects the ATM strike from the 9:15 AM spot price and dynamically finds the nearest weekly expiry via the NSE API.
3. **Backtest**: Executes the Neutral Strategy using a heavily optimized C++ engine (via `pybind11`) — runs in ~10–20ms per day.
4. **Log & Save**: Results are saved as CSV files in `RESULT/NEUTRAL/<MONTH>/V1/` and a running `auto_run.log` is maintained.
5. **Schedule**: Exposes a `.ps1` script to trivially schedule daily 18:00 runs via Windows Task Scheduler.

### Neutral Strategy Logic

The strategy executes a long straddle by buying both a Call (CE) and a Put (PE) option at the same ATM strike. The neutral logic ensures **perfect Delta neutrality at entry** by using the minimum of the two legs:

```
quantity = min(floor(leg_capital / call_price / lot_size), floor(leg_capital / put_price / lot_size))
qc = quantity × lot_size
qp = quantity × lot_size
```

A new trade can be entered every 5 minutes from 09:20, subject to configurable no-trade windows. Each trade exits on Take Profit, Stop Loss, Hold Time expiry, or Market Close — whichever comes first.

---

## Project Structure

```
NEW_PROJECT/
├── NEUTRAL_STRADDLE/          # ← This strategy (public)
│   ├── STRATEGY_V1.py         # Manual backtest (interactive, set date/expiry by hand)
│   ├── STRATEGY_V1_AUTO.py    # Automated backtest (auto-detects date, expiry, paths)
│   ├── DAILY_PIPELINE.py      # Orchestrator: fetch → backtest → log
│   ├── schedule_daily.ps1     # Windows Task Scheduler setup script
│   └── cpp_engine/            # C++ source (pybind11)
│       ├── backtest_engine.cpp
│       ├── csv_loader.cpp
│       ├── bindings.cpp
│       └── CMakeLists.txt
│
├── DATA_FETCH/                # Shared data downloader (used by both strategies)
│   ├── DATA_FETCH.py          # Manual fetch (set date by hand)
│   └── DATA_FETCH_AUTO.py     # Automated fetch (auto-detects today's date)
│
├── DATA/                      # Downloaded market data (gitignored)
│   └── May_2026_DATA/
│       └── DD_MM_YYYY/
│           ├── NIFTY50_spot_DD_MM_YYYY.csv
│           └── <STRIKE>_DD-MM-YYYY.csv
│
├── RESULT/                    # Backtest output CSVs (gitignored)
│   └── NEUTRAL/
│       └── MAY/
│           └── V1/
│               └── result_DDMMYYYY.csv
│
├── build_engines.bat          # One-click build script for C++ engines
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Quick Start

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```
*Requires `pandas` and `curl_cffi`*

### 2. Build the C++ Engine

The core simulation engine is written in C++ for maximum speed. Requires **MSVC** (Visual Studio Build Tools 2019+) and **CMake 3.14+**.

**Recommended: use the included batch script (builds all engines at once):**
```powershell
# Run from the NEW_PROJECT root folder
& ".\build_engines.bat"
```

**Or build manually:**
```powershell
cd NEUTRAL_STRADDLE\cpp_engine
mkdir build
cd build
cmake .. "-Dpybind11_DIR=$(python -m pybind11 --cmakedir)"
cmake --build . --config Release
```

> **Note:** The double-quotes around `-Dpybind11_DIR=...` are required in PowerShell to prevent argument splitting. The `.pyd` file will be placed directly in the `NEUTRAL_STRADDLE/` folder.

### 3. Run the Full Automated Pipeline
```powershell
# From the NEW_PROJECT root folder
python NEUTRAL_STRADDLE\DAILY_PIPELINE.py
```

This will:
- Auto-detect today's date and build the correct data folder path
- Fetch 61 option strikes + spot price from NSE (parallel, ~6–12s)
- Validate the nearest Tuesday expiry via NSE API
- Run the C++ backtest engine (~10–20ms)
- Save results to `RESULT/NEUTRAL/<MONTH>/V1/result_DDMMYYYY.csv`

### 4. Schedule Daily Runs (Windows Task Scheduler)
```powershell
# Run as Administrator once
PowerShell -ExecutionPolicy Bypass -File NEUTRAL_STRADDLE\schedule_daily.ps1
```
This creates a Task Scheduler job that runs the pipeline automatically every trading day at 18:00.

---

## Configuration

Tweak strategy parameters in `NEUTRAL_STRADDLE/STRATEGY_V1_AUTO.py`:

| Parameter | Default | Description |
|---|---|---|
| `ENTRY_TIME` | `09:20` | First trade entry slot |
| `TRADE_INTERVAL` | `5` min | Minutes between entry slots |
| `HOLD_MINUTES` | `60` | Max hold time per trade |
| `TAKE_PROFIT_PCT` | `3.0%` | Take profit as % of total capital |
| `STOP_LOSS_PCT` | `1.0%` | Stop loss as % of total capital |
| `CAPITAL_PER_TRADE` | `1,00,000` | Capital allocated per trade (2 legs) |
| `LOT_SIZE` | `65` | NIFTY lot size |
| `OFFSET_FROM_SPOT` | `0` | Strike offset from ATM (0 = ATM) |
| `NO_TRADE_WINDOWS` | `10:00–14:00, 14:30–15:30` | No-trade periods |
| `STRIKES_ABOVE/BELOW_ATM` | `30` | Strikes downloaded each side of ATM |

---

## Output Format

Each result CSV contains one row per executed trade:

| Column | Description |
|---|---|
| `Trade_No` | Sequential trade number |
| `Entry_Time` | HH:MM when trade was entered |
| `Exit_Time` | HH:MM when trade was closed |
| `Exit_Reason` | `TAKE_PROFIT` / `STOP_LOSS` / `INTERVAL` / `MARKET_CLOSE` |
| `ATM_at_Entry` | ATM strike at entry |
| `Strike` | Actual strike traded |
| `CE_Entry` / `CE_Exit` | Call option entry/exit price |
| `CE_Qty` | Call option quantity |
| `CE_PnL` | Call leg P&L |
| `PE_Entry` / `PE_Exit` | Put option entry/exit price |
| `PE_Qty` | Put option quantity |
| `PE_PnL` | Put leg P&L |
| `Net_PnL` | Combined P&L for the trade |
| `Cumulative_PnL` | Running total P&L |

---

## Important Notices

- **Windows-only**: PowerShell scripts, Task Scheduler, and MSVC compilation are tailored for Windows.
- **NSE Terms of Service**: This project fetches data from NSE's public option-chain API. Use it for educational and personal research purposes only.
- **Data Isolation**: Market data (`/DATA/`) and results (`/RESULT/`) are excluded from version control via `.gitignore`. Only the strategy source code is tracked.
- **Rebuild required**: If you update `CMakeLists.txt` or the `.cpp` files, re-run `build_engines.bat` to recompile.

---

## License

MIT License. See [`LICENSE`](LICENSE) for details.
