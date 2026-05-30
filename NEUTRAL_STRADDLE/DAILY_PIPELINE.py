"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  NIFTY LONG STRADDLE — DAILY PIPELINE (NEUTRAL STRADDLE)                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Orchestrates the daily run:                                                 ║
║   1. Fetches NSE option chain data via DATA_FETCH_AUTO.py                    ║
║   2. Runs the Neutral Strategy via STRATEGY_V1_AUTO.py                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────
# Pathing is relative to this file's location
PROJECT_ROOT      = Path(__file__).parent.parent
DATA_FETCH_SCRIPT = PROJECT_ROOT / "DATA_FETCH" / "DATA_FETCH_AUTO.py"
STRATEGY_SCRIPT   = Path(__file__).parent / "STRATEGY_V1_AUTO.py"
LOG_FILE          = PROJECT_ROOT / "auto_run.log"

def log_msg(msg: str):
    """Print to console and append to the main auto_run.log"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            print(msg, file=f)
    except Exception as e:
        print(f"Failed to write to log: {e}")

def run_script(script_path: Path, args: list = None) -> bool:
    """Run a python script and stream its output to console/log."""
    if not script_path.exists():
        log_msg(f"❌ ERROR: Script not found -> {script_path}")
        return False
        
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
        
    log_msg(f"\n▶ Running: {script_path.name}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8"
        )
        
        # Stream output line by line
        for line in process.stdout:
            # Clean up newlines for printing
            clean_line = line.rstrip()
            print(clean_line)
            # Also write to log
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                print(clean_line, file=f)
                
        process.wait()
        
        if process.returncode == 0:
            log_msg(f"✅ Success: {script_path.name} finished successfully.")
            return True
        else:
            log_msg(f"❌ ERROR: {script_path.name} failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        log_msg(f"❌ EXCEPTION running {script_path.name}: {e}")
        return False

def main():
    now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_msg("\n" + "="*70)
    log_msg(f"🚀 STARTING DAILY PIPELINE (NEUTRAL STRADDLE) | {now_str}")
    log_msg("="*70)
    
    # STEP 1: Fetch Data
    log_msg("\n[STEP 1] Starting Data Fetch (Auto Mode)...")
    fetch_success = run_script(DATA_FETCH_SCRIPT)
    
    if not fetch_success:
        log_msg("\n⛔ Pipeline STOPPED: Data fetch failed.")
        return
        
    # STEP 2: Run Strategy
    log_msg("\n[STEP 2] Starting Backtest/Strategy Run (Auto Mode)...")
    # We pass no arguments so STRATEGY_V1_AUTO.py uses auto-detected paths
    strategy_success = run_script(STRATEGY_SCRIPT)
    
    if not strategy_success:
        log_msg("\n⛔ Pipeline WARNING: Strategy run encountered errors.")
    
    log_msg("\n" + "="*70)
    log_msg(f"🏁 PIPELINE FINISHED | {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    log_msg("="*70 + "\n")

if __name__ == "__main__":
    main()
