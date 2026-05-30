"""
NSE Off-Market Data Fetcher
============================
• Always uses manual input for ATM strike and expiry date
  (works regardless of whether the market is open or closed)
• Downloads CE/PE intraday data for all strikes in parallel
• Cleans data in memory (no raw file written to disk)
• Saves cleaned CSVs → Root_Folder/Month_YYYY_DATA/DD_MM_YYYY/

Cleaning applied to each file:
  - Seconds stripped from DateTime  (HH:MM:SS  →  HH:MM)
  - Blank/missing rows filled       (forward-fill then back-fill)
  - Columns renamed                 (CE_LTP → {strike}CALL,
                                     PE_LTP → {strike}PUT)
"""

# ── Imports ───────────────────────────────────────────────────────────────────
from curl_cffi import requests as cffi_requests
import csv, os, time, threading, queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from io import StringIO

import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG  ← edit these values before running
# ═══════════════════════════════════════════════════════════════════════════════

ROOT_FOLDER       = str(Path(__file__).parent.parent)

STRIKES_ABOVE_ATM = 30
STRIKES_BELOW_ATM = 30          # keep equal to STRIKES_ABOVE_ATM
STRIKE_GAP        = 50

PARALLEL_WORKERS  = 10          # concurrent download sessions
MAX_RETRIES       = 3           # retries per CE/PE request
RETRY_DELAY       = 1.5         # seconds between retries

# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL   = "https://www.nseindia.com"
TODAY_STR  = datetime.now().strftime("%d_%m_%Y")          # e.g. 05_04_2026
MONTH_STR  = datetime.now().strftime("%B_%Y") + "_DATA"   # e.g. April_2026_DATA

_print_lock = threading.Lock()

def tprint(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)


# ── Folder setup ──────────────────────────────────────────────────────────────

def build_folders():
    clean_folder = Path(ROOT_FOLDER) / "DATA" / MONTH_STR / TODAY_STR
    clean_folder.mkdir(parents=True, exist_ok=True)
    print(f"  Folder ready:")
    print(f"    data → {clean_folder}\n")
    return clean_folder


# ── Manual input ──────────────────────────────────────────────────────────────

def manual_input():
    print("\n" + "=" * 60)
    print("  MANUAL INPUT  (enter ATM strike and expiry date)")
    print("=" * 60)
    while True:
        try:
            atm = int(input("\n  Enter ATM strike (e.g. 23200): ").strip())
            break
        except ValueError:
            print("  Please enter a whole number.")
    while True:
        expiry = input("  Enter expiry date DD-MM-YYYY (e.g. 10-04-2026): ").strip()
        try:
            datetime.strptime(expiry, "%d-%m-%Y")
            break
        except ValueError:
            print("  Use format DD-MM-YYYY")
    print(f"\n  ✓ ATM = {atm}   Expiry = {expiry}\n")
    return atm, expiry


# ── Session pool ──────────────────────────────────────────────────────────────

def _warm_single_session(index: int):
    session = cffi_requests.Session(impersonate="chrome120")
    try:
        session.get(BASE_URL, timeout=15)
        time.sleep(1)
        session.get(f"{BASE_URL}/option-chain", timeout=15)
        time.sleep(1)
        tprint(f"  ✓ Session {index} ready")
        return session
    except Exception as e:
        tprint(f"  ✗ Session {index} failed: {e}")
        return None


def build_session_pool(count: int):
    print(f"[Step 1] Warming {count} sessions in parallel...")
    pool = queue.Queue()
    with ThreadPoolExecutor(max_workers=count) as ex:
        futures = {ex.submit(_warm_single_session, i + 1): i for i in range(count)}
        for fut in as_completed(futures):
            s = fut.result()
            if s:
                pool.put(s)
    if pool.empty():
        print("  ✗ No sessions could be created. Check your internet connection.")
        return None
    print(f"  ✓ {pool.qsize()} / {count} sessions ready\n")
    return pool


# ── Epoch → IST string ────────────────────────────────────────────────────────

def epoch_to_ist(epoch_ms: int) -> str:
    dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ── Fetch one side (CE or PE) with retry ──────────────────────────────────────

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
                tprint(f"    ⚠ {opt_type} {strike} attempt {attempt} failed "
                       f"({e}) — retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                tprint(f"    ✗ {opt_type} {strike} failed after "
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


# ── Nifty spot CSV ────────────────────────────────────────────────────────────

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
            tprint(f"  ✓ Nifty spot saved → {csv_path.name}  ({len(raw)} points)")
            return
        except Exception as e:
            if attempt < MAX_RETRIES:
                tprint(f"  ⚠ Nifty spot attempt {attempt} failed ({e}) "
                       f"— retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                tprint(f"  ✗ Nifty spot failed after {MAX_RETRIES} attempts: {e}")


# ── Clean and save CSV (in memory) ───────────────────────────────────────────

def clean_and_save(strike: int, ce_data: dict, pe_data: dict,
                   expiry: str, clean_folder: Path) -> int:
    """
    Builds a DataFrame directly from fetched dicts (no raw file needed), then:
      1. Strips seconds from DateTime  (HH:MM:SS → HH:MM)
      2. Fills blank rows              (forward-fill then back-fill)
      3. Renames columns               (CE_LTP → {strike}CALL,
                                        PE_LTP → {strike}PUT)
    Saves result to cleaned_data/ folder.
    Returns number of rows saved (0 on failure).
    """
    all_ts = sorted(set(ce_data.keys()) | set(pe_data.keys()))
    if not all_ts:
        return 0

    # Build in-memory CSV string and read into DataFrame
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["DateTime", "CE_LTP", "PE_LTP"])
    for ts in all_ts:
        writer.writerow([
            epoch_to_ist(ts),
            ce_data.get(ts, ""),
            pe_data.get(ts, ""),
        ])
    buffer.seek(0)
    df = pd.read_csv(buffer)

    # 1. Strip seconds
    df["DateTime"] = pd.to_datetime(
        df["DateTime"], format="%Y-%m-%d %H:%M:%S"
    ).dt.strftime("%d-%m-%Y %H:%M")

    # 2. Fill blanks
    df = df.ffill().bfill()

    # 3. Rename columns
    df.rename(columns={
        "CE_LTP": f"{strike}CALL",
        "PE_LTP": f"{strike}PUT",
    }, inplace=True)

    clean_path = clean_folder / f"{strike}_{expiry}.csv"
    df.to_csv(clean_path, index=False, encoding="utf-8-sig")
    return len(df)


# ── Worker: download one strike ───────────────────────────────────────────────

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
                   f"CE={len(ce_data)} pts  PE={len(pe_data)} pts  "
                   f"→  {rows} rows saved")
            return strike, "success"
        else:
            tprint(f"  [{index:>3}/{total}]  {strike}  FAILED  (could not write)")
            return strike, "failed"
    finally:
        session_pool.put(session)
        time.sleep(0.2)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  NSE Off-Market Data Fetcher")
    print(f"  Date        : {TODAY_STR}")
    print(f"  Month       : {MONTH_STR}")
    print(f"  Root folder : {ROOT_FOLDER}")
    print("=" * 60 + "\n")

    # ── Step 1: Build session pool ─────────────────────────────────────────────
    session_pool = build_session_pool(PARALLEL_WORKERS)
    if not session_pool:
        input("\nPress Enter to exit...")
        return

    # ── Step 2: Manual input ───────────────────────────────────────────────────
    atm, expiry = manual_input()

    # ── Step 3: Create folder ──────────────────────────────────────────────────
    clean_folder = build_folders()

    # ── Step 4: Fetch Nifty spot CSV ───────────────────────────────────────────
    print("[Step 4] Fetching Nifty 50 spot price CSV...")
    spot_session = session_pool.get()
    fetch_nifty_spot_csv(spot_session, clean_folder)
    session_pool.put(spot_session)

    # ── Step 5: Build strike list ──────────────────────────────────────────────
    strike_prices = [
        atm + i * STRIKE_GAP
        for i in range(-STRIKES_BELOW_ATM, STRIKES_ABOVE_ATM + 1)
    ]
    total = len(strike_prices)

    print(f"\n[Step 5] Downloading {total} strikes in parallel "
          f"({strike_prices[0]} → {strike_prices[-1]})")
    print(f"  Workers : {PARALLEL_WORKERS}")
    print(f"  Retries : {MAX_RETRIES} per request\n")

    args_list = [
        (session_pool, expiry, strike, clean_folder, i, total)
        for i, strike in enumerate(strike_prices, 1)
    ]

    # ── Step 6: Download + clean all strikes ───────────────────────────────────
    success = skipped = failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {executor.submit(download_strike, args): args[2]
                   for args in args_list}
        for fut in as_completed(futures):
            _, status = fut.result()
            if status == "success":  success += 1
            elif status == "skipped": skipped += 1
            else:                     failed  += 1

    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print(f"  All done!")
    print(f"  ✓ {success} saved   ~ {skipped} skipped   ✗ {failed} failed")
    print(f"  Time taken   : {elapsed:.1f}s")
    print(f"  data         → {clean_folder}")
    print("=" * 60)

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()

