# Strategy Lab Retrospective: What the Build Spec Would Have Caught

> This document maps every Tiger and Elephant from the Strategy Lab pre-mortem
> to the specific Phase / Question in the Pre-Build Discovery process that would
> have surfaced it. It shows "before" (what was said) vs "after" (what should
> have been said).

---

## T1: P&L Calculation Accuracy (Sign Convention for SELL Legs)

### What happened
The AI implemented `Leg.pnl` as `multiplier = 1 if BUY else -1` and
`(current_price - entry_price) * multiplier * quantity`. Some strategy
`check_exit` methods also compute P&L independently. Nobody verified
these agree. For SELL legs, a price increase = loss, but if the sign is
wrong, a loss shows as profit.

### What Phase would have caught it
**Phase 3: Logic & Rules → "List every calculation"**

### Before (what Sahil said)
> "I want to implement 12 strategies with a backtesting dashboard."

### After (what the Build Spec should have said)
```
Calculation: P&L per leg

BUY leg formula:
  pnl = (exit_price - entry_price) × quantity
  Example: Buy CE at ₹150, exit at ₹180, qty 65
  Expected: (180 - 150) × 65 = +₹1,950 (profit)

SELL leg formula:
  pnl = (entry_price - exit_price) × quantity
  Example: Sell CE at ₹150, exit at ₹180, qty 65
  Expected: (150 - 180) × 65 = -₹1,950 (loss, because we sold and price went up)

Verification:
  Run Long Straddle (BUY CE + BUY PE) on date 30_05_2026 with
  capital=100000, lot_size=65, hold=60min.
  Compare output trade-by-trade against existing NEUTRAL_STRADDLE
  C++ engine output. Must match within ₹10 per trade.
```

### Time to write: 3 minutes
### Time it would have saved: 2+ hours of debugging and uncertainty

---

## T3: Margin Model (Short Strategy Sizing)

### What happened
The AI used `max_premium * 2 * lot_size` as margin per lot. Real SPAN
margin for NIFTY options is ₹1.5-2.5 lakh per lot. The AI had no way
to know this — it's domain-specific knowledge that only a trader would have.

### What Phase would have caught it
**Phase 3: Logic & Rules → Domain Questions → "Position Sizing & Margin"**

### Before (what Sahil said)
> "Go with your recommendation" (for strategy parameters)

### After (what the Build Spec should have said)
```
Margin model for SELL positions:
  For v1, use simplified margin: margin_per_lot = strike_price × lot_size × 0.15
  This approximates ~15% of notional value as margin.

  Example: Sell NIFTY 24500 CE, lot_size = 65
  Margin per lot = 24500 × 65 × 0.15 = ₹238,875

  With ₹100,000 capital: can sell 0 lots (insufficient margin)
  → This means short strategies need more capital.
  → Default capital for short strategies should be ₹500,000

  For v2 (if needed): integrate actual broker margin API.

  Display: Show "margin required" alongside "capital per trade" in the UI
  so users understand why short strategies have fewer lots.
```

### Time to write: 5 minutes
### Time it would have saved: 1 hour of investigation + fixing

---

## T4: Default No-Trade Windows

### What happened
The AI set `no_trade_windows = [("10:00", "14:00"), ("14:30", "15:30")]`
as the default, blocking 87% of the trading day. This was a "reasonable"
default that the AI picked because the original straddle project had
restricted entry windows.

### What Phase would have caught it
**Phase 3: Logic & Rules → "What are the configurable parameters? → Default?"**
Also: **Common Gaps #3: Undefined Default Parameters**

### Before (what Sahil said)
> "Daily basis only" (referring to backtesting scope)

### After (what the Build Spec should have said)
```
No-trade windows:
  Default: NONE (empty list — allow trading at any time during market hours)
  Configurable: Yes, user can add restricted windows via UI
  Format: list of (start_time, end_time) tuples, inclusive-exclusive

  Valid range: any time between 09:15 and 15:30
  What happens if window covers entire day: 0 trades, show warning
```

### Time to write: 1 minute
### Time it would have saved: 30 min of debugging "why are there only 3 trades?"

---

## E1: No Transaction Cost Model

### What happened
All 12 strategies calculate raw P&L without brokerage, STT, GST, slippage,
or any real-world cost. Results are systematically overstated.

### What Phase would have caught it
**Phase 3: Logic & Rules → Domain Questions → "Costs That Eat Into P&L"**
Also: **Common Gaps #4: No Cost Model**

### Before (what Sahil said)
> (Nothing — costs were never mentioned)

### After (what the Build Spec should have said)
```
Transaction costs (per trade, per leg):
  Brokerage: ₹20 per order (flat, for discount broker like Zerodha)
  STT: 0.05% on sell side premium (options)
  Exchange charges: 0.053% (NSE)
  GST: 18% on (brokerage + exchange charges)
  Stamp duty: 0.003% on buy side
  SEBI charges: 0.0001%
  Slippage estimate: ₹1 per lot per leg

  For v1: Use simplified model: ₹40 flat per trade (covers brokerage + taxes)
  Display: Show both "Gross P&L" and "Net P&L (after costs)"
  Warning: Add note "Excludes slippage and market impact"
```

### Time to write: 3 minutes (if you know the costs; 15 min to research if you don't)
### Time it would have saved: 1 hour + prevented misleading results

---

## T2: Engine Silently Skips Missing Data

### What happened
`load_strike_data()` returns `{}` for missing files. The engine logs
"SLOT SKIPPED" but doesn't surface how many slots were skipped. A
4-leg strategy could skip 80% of slots and still produce a "valid"
backtest with 3 trades.

### What Phase would have caught it
**Phase 2: Inputs & Data → "What should happen when data is missing?"**
Also: **Common Gaps #2: No Definition of "Valid Input"** and
**Common Gaps #5: Unspecified Error Handling**

### Before (what Sahil said)
> (Nothing — data quality handling was never discussed)

### After (what the Build Spec should have said)
```
Missing data handling:
  If spot price missing for a time slot: skip that slot, log warning
  If ONE leg's strike data is missing: skip that slot, log warning
  If ALL leg data is missing: skip that slot, log warning

  Data quality reporting:
    Every backtest result must include:
    - total_slots_attempted: how many time slots were checked for entry
    - slots_executed: how many trades were actually taken
    - skip_rate: (attempted - executed) / attempted × 100%

  Quality threshold:
    If skip_rate > 30%: show ⚠️ warning in UI
    If skip_rate > 70%: show ❌ error — "Insufficient data for reliable results"
    If skip_rate = 100%: show error — "No valid data found"
```

### Time to write: 3 minutes
### Time it would have saved: 1 hour + prevented misleading results

---

## Summary: Total Discovery Time vs Total Rework Avoided

| Issue | Discovery Time | Rework Avoided |
|-------|---------------|----------------|
| T1: P&L sign convention | 3 min | 2+ hours |
| T3: Margin model | 5 min | 1 hour |
| T4: No-trade windows | 1 min | 30 min |
| E1: Transaction costs | 3 min | 1 hour |
| T2: Data quality | 3 min | 1 hour |
| **Total** | **15 minutes** | **5.5+ hours** |

> **15 minutes of thinking before building would have prevented 5.5+ hours of
> post-build debugging, rework, and risk.**

And those 5.5 hours are just the direct fix time. The real cost is **trust** —
without catching these issues, you'd be making trading decisions based on
systematically wrong P&L numbers.

---

## The Meta-Lesson

The pre-mortem skill is for *after* you have a plan — stress-testing it.
This pre-build discovery skill is for *before* you have a plan — making sure
the plan addresses the right things.

**The workflow is:**

```
1. Pre-Build Discovery (this skill)  →  Build Spec
2. Give Build Spec to AI             →  Implementation Plan
3. Pre-Mortem on the plan            →  Risk Register
4. Fix Launch-Blockers               →  Build
5. Verify against Acceptance Criteria
```

Without step 1, step 3 catches the issues — but by then, the code is already
written and needs to be reworked. With step 1, the issues never enter the code
in the first place.
