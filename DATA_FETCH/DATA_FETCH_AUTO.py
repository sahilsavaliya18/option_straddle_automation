"""
NSE Off-Market Data Fetcher  —  AUTO MODE
==========================================
• Auto-detects ATM strike from NIFTY 50 open price at 09:15
• Auto-detects nearest weekly expiry from NSE option-chain API
• No manual input required — fully scheduled-task compatible
• All other logic identical to DATA_FETCH.py
"""

# ── Imports ───────────────────────────────────────────────────────────────────
from curl_cffi import requests as cffi_requests
import csv, os, time, threading, queue, json, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from io import StringIO

import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

ROOT_FOLDER       = str(Path(__file__).parent.parent)

STRIKES_ABOVE_ATM = 30
STRIKES_BELOW_ATM = 30
STRIKE_GAP        = 50

PARALLEL_WORKERS  = 10
MAX_RETRIES       = 3
RETRY_DELAY       = 1.5

# ── Log file for scheduled runs ──────────────────────────────────────────────
LOG_FILE = Path(ROOT_FOLDER) / "auto_run.log"

# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL   = "https://www.nseindia.com"
TODAY_STR  = datetime.now().strftime("%d_%m_%Y")
MONTH_STR  = datetime.now().strftime("%B_%Y") + "_DATA"

_print_lock = threading.Lock()

def tprint(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)
        # Also write to log file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            print(*args, **kwargs, file=f)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO-DETECT: ATM Strike from 9:15 AM Open Price
# ═══════════════════════════════════════════════════════════════════════════════

def auto_detect_atm(session) -> int:
    """
    Fetches NIFTY 50 spot data and finds the price at 09:15.
    Rounds to nearest 50 to get ATM strike.
    Falls back to the last available price if 09:15 is not found.
    """
    url = (f"{BASE_URL}/api/NextApi/apiClient"
           f"?functionName=getGraphChart&&type=NIFTY%2050&flag=1D")
    headers = {
        "Referer":        f"{BASE_URL}/",
        "Accept":         "application/json, text/plain, */*",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r    = session.get(url, headers=headers, timeout=15)
            data = r.json()
            raw  = (data.get("data", {}).get("grapthData") or
                    data.get("data", {}).get("graphData") or [])

            if not raw:
                raise ValueError("Empty spot data in response")

            # Build a dict: HH:MM → price
            prices_by_minute = {}
            for point in raw:
                if len(point) >= 2 and point[1] is not None and point[1] != 0:
                    dt = datetime.fromtimestamp(int(point[0]) / 1000, tz=timezone.utc).replace(tzinfo=None)
                    # Convert UTC to IST (+5:30)
                    dt_ist = dt + timedelta(hours=5, minutes=30)
                    key = dt_ist.strftime("%H:%M")
                    prices_by_minute[key] = point[1]

            # Try 09:15 first
            spot_915 = prices_by_minute.get("09:15")

            # If 09:15 not found, try closest minute after 09:00
            if spot_915 is None:
                for minute in range(0, 60):
                    key = f"09:{minute:02d}"
                    if key in prices_by_minute:
                        spot_915 = prices_by_minute[key]
                        tprint(f"  ATM using {key} spot price (09:15 not found)")
                        break

            # Last resort: use the last available price
            if spot_915 is None:
                # Get the last point
                last_point = raw[-1]
                spot_915 = last_point[1]
                tprint(f"  WARNING: Using last available spot price: {spot_915}")

            atm = int(round(spot_915 / 50) * 50)
            tprint(f"  Auto-detected ATM = {atm}  (spot at 09:15 = {spot_915:.2f})")
            return atm

        except Exception as e:
            if attempt < MAX_RETRIES:
                tprint(f"  ATM detect attempt {attempt} failed ({e}) — retrying...")
                time.sleep(RETRY_DELAY)
            else:
                tprint(f"  FATAL: Cannot detect ATM after {MAX_RETRIES} attempts: {e}")
                raise RuntimeError(f"Cannot auto-detect ATM: {e}")

    raise RuntimeError("Failed to detect ATM (loop exhausted or MAX_RETRIES < 1)")

# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO-DETECT: Nearest Weekly Expiry from NSE Option-Chain API
# ═══════════════════════════════════════════════════════════════════════════════

def auto_detect_expiry(session) -> str:
    """
    Returns the nearest weekly expiry date in DD-MM-YYYY format.

    Strategy:
    1. Calculate next Tuesday (NIFTY weekly expiry day)
    2. Call the NSE option-chain-v3 API with that expiry to VALIDATE it exists
    3. If the API returns data, the expiry is confirmed
    4. If the API fails (holiday on Tuesday), try the following Tuesday
    5. Returns DD-MM-YYYY format for use in data fetching

    NSE API confirmed from DevTools:
      GET /api/option-chain-v3?type=Indices&symbol=NIFTY&expiry=DD-Mon-YYYY
      Response: records.data[].expiryDate = "DD-MM-YYYY"
    """
    today = datetime.now().date()

    # Try up to 2 upcoming Tuesdays (in case Tuesday is a holiday)
    for week_offset in range(2):
        days_ahead = 1 - today.weekday()  # Tuesday = weekday 1
        if days_ahead < 0:
            days_ahead += 7
        tuesday = today + timedelta(days=days_ahead + (7 * week_offset))

        # API expects: DD-Mon-YYYY (e.g., 19-May-2026)
        expiry_api_fmt = tuesday.strftime("%d-%b-%Y")
        # Internal format: DD-MM-YYYY (e.g., 19-05-2026)
        expiry_ddmmyyyy = tuesday.strftime("%d-%m-%Y")

        # Validate by calling the API
        url = f"{BASE_URL}/api/option-chain-v3?type=Indices&symbol=NIFTY&expiry={expiry_api_fmt}"
        headers = {
            "Referer":        f"{BASE_URL}/option-chain",
            "Accept":         "application/json, text/plain, */*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        try:
            r    = session.get(url, headers=headers, timeout=15)
            data = r.json()

            # Check if we got valid data (records.data should be non-empty)
            records_data = data.get("records", {}).get("data", [])
            if records_data and len(records_data) > 0:
                tprint(f"  Auto-detected expiry = {expiry_ddmmyyyy}  "
                       f"(validated via API, {len(records_data)} strikes)")
                return expiry_ddmmyyyy
            else:
                tprint(f"  Tuesday {expiry_ddmmyyyy} returned empty data (holiday?). Trying next week.")

        except Exception as e:
            tprint(f"  Expiry API call failed ({e}). Trying next Tuesday.")
            time.sleep(RETRY_DELAY)

    # Final fallback: just use the next Tuesday calculation without API validation
    tprint("  WARNING: API validation failed. Using calculated next Tuesday.")
    return _next_tuesday()


def _next_tuesday() -> str:
    """Calculate the nearest Tuesday (including today) in DD-MM-YYYY format."""
    today = datetime.now().date()
    # Tuesday = weekday 1
    days_ahead = 1 - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    tuesday = today + timedelta(days=days_ahead)
    return tuesday.strftime("%d-%m-%Y")


# ═══════════════════════════════════════════════════════════════════════════════
#  Session pool (same as DATA_FETCH.py)
# ═══════════════════════════════════════════════════════════════════════════════

def _warm_single_session(index: int):
    session = cffi_requests.Session(impersonate="chrome120")
    try:
        session.get(BASE_URL, timeout=15)
        time.sleep(1)
        session.get(f"{BASE_URL}/option-chain", timeout=15)
        time.sleep(1)
        tprint(f"  Session {index} ready")
        return session
    except Exception as e:
        tprint(f"  Session {index} failed: {e}")
        return None


def build_session_pool(count: int):
    tprint(f"[Step 1] Warming {count} sessions in parallel...")
    pool = queue.Queue()
    with ThreadPoolExecutor(max_workers=count) as ex:
        futures = {ex.submit(_warm_single_session, i + 1): i for i in range(count)}
        for fut in as_completed(futures):
            s = fut.result()
            if s:
                pool.put(s)
    if pool.empty():
        tprint("  No sessions could be created. Check your internet connection.")
        return None
    tprint(f"  {pool.qsize()} / {count} sessions ready\n")
    return pool


# ═══════════════════════════════════════════════════════════════════════════════
#  Folder setup
# ═══════════════════════════════════════════════════════════════════════════════

def build_folders():
    clean_folder = Path(ROOT_FOLDER) / "DATA" / MONTH_STR / TODAY_STR
    clean_folder.mkdir(parents=True, exist_ok=True)
    tprint(f"  Folder ready: {clean_folder}\n")
    return clean_folder


# ═══════════════════════════════════════════════════════════════════════════════
#  Epoch → IST string
# ═══════════════════════════════════════════════════════════════════════════════

def epoch_to_ist(epoch_ms: int) -> str:
    dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════════════════════
#  Fetch + clean (same logic as DATA_FETCH.py)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_side_with_retry(session, expiry_ddmmyyyy: str,
                          strike: int, opt_type: str) -> dict:
    identifier = f"OPTIDXNIFTY{expiry_ddmmyyyy}{opt_type}{strike:.2f}"
    url        = f"{BASE_URL}/api/chart-databyindex?index={identifier}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r    = session.get(url, timeout=15)
            data = r.json()
            raw  = data.get("grapthData") or data.get("graphData") or []
            result = {}
            for point in raw:
                if len(point) >= 2 and point[1] is not None and point[1] != 0:
                    result[int(point[0])] = point[1]
            return result
        except Exception as e:
            if attempt < MAX_RETRIES:
                tprint(f"    {opt_type} {strike} attempt {attempt} failed "
                       f"({e}) - retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                tprint(f"    X {opt_type} {strike} failed after "
                       f"{MAX_RETRIES} attempts: {e}")
    return {}


def fetch_strike(session, expiry: str, strike: int):
    ce_result = {}
    pe_result = {}
    def _fetch_ce():
        nonlocal ce_result
        ce_result = fetch_side_with_retry(session, expiry, strike, "CE")
    def _fetch_pe():
        nonlocal pe_result
        pe_result = fetch_side_with_retry(session, expiry, strike, "PE")
    t_ce = threading.Thread(target=_fetch_ce)
    t_pe = threading.Thread(target=_fetch_pe)
    t_ce.start(); t_pe.start()
    t_ce.join();  t_pe.join()
    return ce_result, pe_result


def fetch_nifty_spot_csv(session, clean_folder: Path):
    url = (f"{BASE_URL}/api/NextApi/apiClient"
           f"?functionName=getGraphChart&&type=NIFTY%2050&flag=1D")
    headers = {
        "Referer":        f"{BASE_URL}/",
        "Accept":         "application/json, text/plain, */*",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r    = session.get(url, headers=headers, timeout=15)
            data = r.json()
            raw  = (data.get("data", {}).get("grapthData") or
                    data.get("data", {}).get("graphData") or [])
            if not raw:
                raise ValueError("Empty data in response")
            csv_path = clean_folder / f"NIFTY50_spot_{TODAY_STR}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["DateTime", "Spot_Price", "Change", "Change_Pct"])
                for point in raw:
                    if len(point) >= 2 and point[1] is not None and point[1] != 0:
                        writer.writerow([
                            epoch_to_ist(int(point[0])),
                            point[1],
                            point[3] if len(point) > 3 else "",
                            point[4] if len(point) > 4 else "",
                        ])
            tprint(f"  Nifty spot saved -> {csv_path.name}  ({len(raw)} points)")
            return
        except Exception as e:
            if attempt < MAX_RETRIES:
                tprint(f"  Nifty spot attempt {attempt} failed ({e}) - retrying...")
                time.sleep(RETRY_DELAY)
            else:
                tprint(f"  X Nifty spot failed after {MAX_RETRIES} attempts: {e}")


def clean_and_save(strike: int, ce_data: dict, pe_data: dict,
                   expiry: str, clean_folder: Path) -> int:
    all_ts = sorted(set(ce_data.keys()) | set(pe_data.keys()))
    if not all_ts:
        return 0
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["DateTime", "CE_LTP", "PE_LTP"])
    for ts in all_ts:
        writer.writerow([epoch_to_ist(ts), ce_data.get(ts, ""), pe_data.get(ts, "")])
    buffer.seek(0)
    df = pd.read_csv(buffer)
    df["DateTime"] = pd.to_datetime(df["DateTime"], format="%Y-%m-%d %H:%M:%S").dt.strftime("%d-%m-%Y %H:%M")
    df = df.ffill().bfill()
    df.rename(columns={"CE_LTP": f"{strike}CALL", "PE_LTP": f"{strike}PUT"}, inplace=True)
    clean_path = clean_folder / f"{strike}_{expiry}.csv"
    df.to_csv(clean_path, index=False, encoding="utf-8-sig")
    return len(df)


def download_strike(args):
    session_pool, expiry, strike, clean_folder, index, total = args
    session = session_pool.get()
    try:
        ce_data, pe_data = fetch_strike(session, expiry, strike)
        if not ce_data and not pe_data:
            tprint(f"  [{index:>3}/{total}]  {strike}  SKIPPED  (no data)")
            return strike, "skipped"
        rows = clean_and_save(strike, ce_data, pe_data, expiry, clean_folder)
        if rows:
            tprint(f"  [{index:>3}/{total}]  {strike}  OK  "
                   f"CE={len(ce_data)} pts  PE={len(pe_data)} pts  -> {rows} rows")
            return strike, "success"
        else:
            tprint(f"  [{index:>3}/{total}]  {strike}  FAILED  (could not write)")
            return strike, "failed"
    finally:
        session_pool.put(session)
        time.sleep(0.2)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO-DETECT ATM FROM SPOT CSV (fallback for off-market hours)
# ═══════════════════════════════════════════════════════════════════════════════

def auto_detect_atm_from_csv(clean_folder: Path) -> int:
    """
    After spot CSV is downloaded, read it and find the 09:15 price.
    This is the most reliable method since the CSV contains the actual data.
    """
    candidates = sorted(Path(clean_folder).glob("NIFTY50_spot_*.csv"))
    if not candidates:
        raise FileNotFoundError("No NIFTY50_spot_*.csv found")

    df = pd.read_csv(candidates[0], encoding="utf-8-sig")
    df["_dt"] = pd.to_datetime(df["DateTime"])
    df["_min"] = df["_dt"].dt.strftime("%H:%M")

    # Try 09:15 first
    row_915 = df[df["_min"] == "09:15"]
    if not row_915.empty:
        spot = float(row_915.iloc[0]["Spot_Price"])
    else:
        # Try 09:16, 09:17, etc.
        for minute in range(16, 31):
            key = f"09:{minute:02d}"
            row = df[df["_min"] == key]
            if not row.empty:
                spot = float(row.iloc[0]["Spot_Price"])
                tprint(f"  ATM from spot CSV at {key}: {spot:.2f}")
                break
        else:
            # Last resort: first row after 09:00
            after_9 = df[df["_dt"].dt.hour >= 9]
            if not after_9.empty:
                spot = float(after_9.iloc[0]["Spot_Price"])
            else:
                spot = float(df.iloc[0]["Spot_Price"])

    atm = int(round(spot / 50) * 50)
    tprint(f"  Auto-detected ATM from CSV = {atm}  (spot at 09:15 = {spot:.2f})")
    return atm


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN  —  AUTO MODE
# ═══════════════════════════════════════════════════════════════════════════════

def main(auto_mode: bool = True):
    """
    auto_mode=True  : No user input, auto-detect ATM + expiry
    auto_mode=False : Falls back to manual input (like original)
    """
    tprint("=" * 60)
    tprint("  NSE Off-Market Data Fetcher  [AUTO MODE]")
    tprint(f"  Date        : {TODAY_STR}")
    tprint(f"  Month       : {MONTH_STR}")
    tprint(f"  Root folder : {ROOT_FOLDER}")
    tprint("=" * 60 + "\n")


    # ── Step 1: Build session pool ─────────────────────────────────────────
    session_pool = build_session_pool(PARALLEL_WORKERS)
    if not session_pool:
        return False

    # ── Step 2: Auto-detect OR manual input ────────────────────────────────
    if auto_mode:
        tprint("[Step 2] Auto-detecting ATM and Expiry...")

        # Get one session for API calls
        detect_session = session_pool.get()

        # Detect expiry first (doesn't need spot data)
        expiry = auto_detect_expiry(detect_session)
        tprint(f"  Expiry: {expiry}")

        # Create folders
        clean_folder = build_folders()

        # Fetch Nifty spot CSV first, then detect ATM from it
        tprint("[Step 3] Fetching Nifty 50 spot price CSV...")
        fetch_nifty_spot_csv(detect_session, clean_folder)
        session_pool.put(detect_session)

        # Detect ATM from the downloaded spot CSV (most reliable)
        tprint("[Step 4] Detecting ATM from spot data...")
        try:
            atm = auto_detect_atm_from_csv(clean_folder)
        except Exception as e:
            tprint(f"  CSV-based ATM detect failed ({e}). Trying API method...")
            detect_session = session_pool.get()
            atm = auto_detect_atm(detect_session)
            session_pool.put(detect_session)

        tprint(f"  ATM = {atm}   Expiry = {expiry}\n")
    else:
        # Manual mode (original behavior)
        atm, expiry = _manual_input()
        clean_folder = build_folders()

        tprint("[Step 3] Fetching Nifty 50 spot price CSV...")
        spot_session = session_pool.get()
        fetch_nifty_spot_csv(spot_session, clean_folder)
        session_pool.put(spot_session)

    # ── Step 5: Build strike list ──────────────────────────────────────────
    strike_prices = [
        atm + i * STRIKE_GAP
        for i in range(-STRIKES_BELOW_ATM, STRIKES_ABOVE_ATM + 1)
    ]
    total = len(strike_prices)

    tprint(f"\n[Step 5] Downloading {total} strikes in parallel "
           f"({strike_prices[0]} -> {strike_prices[-1]})")
    tprint(f"  Workers : {PARALLEL_WORKERS}")
    tprint(f"  Retries : {MAX_RETRIES} per request\n")

    args_list = [
        (session_pool, expiry, strike, clean_folder, i, total)
        for i, strike in enumerate(strike_prices, 1)
    ]

    # ── Step 6: Download + clean all strikes ───────────────────────────────
    success = skipped = failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {executor.submit(download_strike, args): args[2]
                   for args in args_list}
        for fut in as_completed(futures):
            _, status = fut.result()
            if status == "success":    success += 1
            elif status == "skipped": skipped += 1
            else:                     failed  += 1

    elapsed = time.time() - start_time

    tprint("")
    tprint("=" * 60)
    tprint(f"  Data fetch complete!")
    tprint(f"  OK {success}   SKIPPED {skipped}   FAILED {failed}")
    tprint(f"  Time taken : {elapsed:.1f}s")
    tprint(f"  Data       -> {clean_folder}")
    tprint("=" * 60)

    # Return results for pipeline use
    return {
        "success": True,
        "atm": atm,
        "expiry": expiry,
        "clean_folder": str(clean_folder),
        "total_strikes": total,
        "success_count": success,
        "skipped_count": skipped,
        "failed_count": failed,
    }


def _manual_input():
    """Original manual input (for non-auto mode)."""
    tprint("\n" + "=" * 60)
    tprint("  MANUAL INPUT  (enter ATM strike and expiry date)")
    tprint("=" * 60)
    while True:
        try:
            atm = int(input("\n  Enter ATM strike (e.g. 23200): ").strip())
            break
        except ValueError:
            tprint("  Please enter a whole number.")
    while True:
        expiry = input("  Enter expiry date DD-MM-YYYY (e.g. 10-04-2026): ").strip()
        try:
            datetime.strptime(expiry, "%d-%m-%Y")
            break
        except ValueError:
            tprint("  Use format DD-MM-YYYY")
    tprint(f"\n  ATM = {atm}   Expiry = {expiry}\n")
    return atm, expiry


if __name__ == "__main__":
    import sys
    # Run with --manual for interactive mode, otherwise auto
    auto = "--manual" not in sys.argv
    result = main(auto_mode=auto)
    if not auto:
        input("\nPress Enter to exit...")