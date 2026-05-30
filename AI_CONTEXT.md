# Project Context: NIFTY Long Straddle Backtester Automation

This file serves as a comprehensive context guide for AI assistants working on this repository. It provides the necessary architectural, structural, and technical details to understand and modify the codebase without needing repeated context from the user.

## 1. Project Overview & Architecture

**Goal:** Automate the daily backtesting of a NIFTY Long Straddle options strategy. The system fetches daily option chain data from the National Stock Exchange (NSE) of India, determines the At-The-Money (ATM) strike, backtests the strategy using a high-performance C++ engine, and logs the results.

**Architecture Flow:**
1. **Trigger:** Windows Task Scheduler runs `schedule_daily.ps1` daily (e.g., at 4:30 PM).
2. **Orchestrator:** `DAILY_PIPELINE.py` is invoked. It handles market holiday checks and network connectivity.
3. **Data Fetching:** `DATA_FETCH_AUTO.py` is called. It impersonates a browser using `curl_cffi` to download the NIFTY spot CSV and all related Call (CE) and Put (PE) strike CSVs. It automatically identifies the 9:15 AM spot price to calculate the ATM strike.
4. **Backtesting:** `STRATEGY_V3_AUTO.py` is called, passing the downloaded data folder. It invokes the C++ backtest engine (`backtest_engine.cp313-win_amd64.pyd`), which computes trades, take profits (TP), stop losses (SL), and P&L.
5. **Output:** Results are saved to a CSV in the `RESULT/` directory, and summary logs are written to `auto_run.log`.

## 2. Directory & File Structure

### Root Directory: `d:\OneDrive\Desktop\pinecode rsi\PYTHON AUTOMATE\NSE DATA automation\NEW_PROJECT`

- **`DAILY_PIPELINE.py`**: The main orchestrator script. Run this to execute the full end-to-end automated pipeline.
- **`schedule_daily.ps1`**: PowerShell script to register the pipeline in Windows Task Scheduler.
- **`auto_run.log`**: Standard log file where `DAILY_PIPELINE.py` writes its daily execution status, errors, and P&L summaries.
- **`README.md`**: High-level project documentation.
- **`PATHS_REFERENCE.txt`**: Original absolute paths for reference, showing how paths were configured before the project was made portable.

### `/DATA_FETCH` (Data Scraping)
- **`DATA_FETCH.py`**: Manual script to download option chain data (prompts user for inputs).
- **`DATA_FETCH_AUTO.py`**: Fully automated scraper. Bypasses NSE bot detection, finds ATM strike from spot prices, and downloads required CSVs.

### `/STRATEGY` (Backtesting Logic)
- **`STRATEGY_V1.py` & `STRATEGY_V2.py`**: Older, pure Python implementations of the backtester. Takes 3-5 seconds per run.
- **`STRATEGY_V3.py`**: Manual execution wrapper for the C++ engine.
- **`STRATEGY_V3_AUTO.py`**: Automated execution wrapper for the C++ engine (called by the pipeline). Contains the Python logic that bridges to the C++ bindings.
- **`/cpp_engine/`**: Contains the raw C++ source files (`backtest_engine.h/cpp`, `csv_loader.cpp`, `bindings.cpp`) and the `CMakeLists.txt` for building the `pybind11` `.pyd` module.
- **`backtest_engine.cp313-win_amd64.pyd`**: The compiled C++ engine for Python 3.13 (Windows). 

### Data Folders
- **`May_2026_DATA/`**: Data storage. Organized by date (e.g., `15_05_2026/`). The fetcher puts downloaded spot and strike CSV files here.
- **`RESULT/`**: Output directory. Final backtest trade logs and metrics are written here as CSVs.

## 3. Key Technical Details & Configurations

### Strategy Configuration (in `STRATEGY_V3_AUTO.py` / `STRATEGY_V3.py`)
- **ENTRY_TIME**: 09:20 (first trade)
- **TRADE_INTERVAL**: 5 min
- **HOLD_MINUTES**: 60 (max hold time)
- **TP (Take Profit)**: 3% (of capital per leg)
- **SL (Stop Loss)**: 1% (of capital per leg)
- **NO_TRADE_WINDOWS**: 10:00-14:00, 14:30-15:30
- **LOT_SIZE**: 65 (NIFTY standard)
- **CAPITAL_PER_TRADE**: 100,000

### Strategy Lot Sizing Paradigms (Neutral vs Directional)
- **Neutral Straddle (`STRATEGY_V1.py`)**: Strict neutrality. It calculates the raw fractional lots affordable for both Call and Put legs independently, takes the `min()` of the two, and assigns this minimum to **both** legs. This ensures perfectly equal quantity weighting.
- **Directional Straddle (`STRATEGY_V2.py`, `STRATEGY_V3.py`)**: Fractional remainder allocation. It calculates the raw fractional lots, floors both, but then compares the exact fractions. It awards `+1` extra lot to whichever leg had a higher fractional remainder (i.e., the cheaper premium).

### Dependencies
- The project relies on `curl_cffi` for web scraping to impersonate browsers and avoid NSE API blocks.
- `pybind11` is required to build and bridge the C++ backtester.

## 4. Important Considerations for AI & Developers

1. **Windows Dependency**: The project relies heavily on Windows features (Task Scheduler, MSVC compiler for `.pyd`, PowerShell notifications). Path handling uses `\` (or `Path` from `pathlib`).
2. **C++ Engine Compilation**: If you change any logic in `/STRATEGY/cpp_engine/`, it MUST be recompiled using CMake. 
   ```bash
   cd STRATEGY/cpp_engine/build
   cmake .. -Dpybind11_DIR=$(python -m pybind11 --cmakedir)
   cmake --build . --config Release
   ```
3. **Market Holidays**: The pipeline checks `MARKET_HOLIDAYS` defined in `DAILY_PIPELINE.py`. If modifying the script for a new year, this set must be updated with NSE market holidays.
4. **Network Resilience**: The pipeline implements a network retry mechanism to wait for an internet connection before fetching data.
5. **Absolute vs Relative Paths**: Historically, absolute paths were used (as seen in `PATHS_REFERENCE.txt`). Current scripts rely heavily on relative paths using `pathlib.Path` resolved from the script location. Always use `pathlib` for file I/O to maintain portability.
