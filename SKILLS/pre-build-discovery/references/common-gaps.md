# 20 Most Common Specification Gaps

> These are the gaps that appear in 80% of projects where the requester says
> "build me X" without a detailed spec. Each gap shows what gets assumed,
> why it causes problems, and a one-line check to catch it.

---

## Gap 1: Missing Precision Requirements

**What gets assumed:** AI picks whatever precision seems reasonable — floating
point for money, rounded integers for quantities, truncated timestamps.

**Why it causes problems:** Financial calculations with floating point accumulate
rounding errors. 1000 trades × ₹0.01 rounding error = ₹10 per day.

**One-line check:** "For every number the system produces, I've specified:
unit, precision, rounding rule."

---

## Gap 2: No Definition of "Valid Input"

**What gets assumed:** All input data is clean, complete, and correctly formatted.

**Why it causes problems:** Real data has gaps, nulls, wrong types, out-of-range
values. System either crashes or silently uses bad data.

**One-line check:** "I've defined what happens for: missing data, null values,
zero values, negative values, out-of-range values."

---

## Gap 3: Undefined Default Parameters

**What gets assumed:** AI picks "reasonable" defaults based on general knowledge,
not domain expertise.

**Why it causes problems:** A "reasonable" stop loss in general = 5%. A
reasonable stop loss for a short straddle on NIFTY = maybe 1.5%. Wrong
defaults lead to wrong results that look correct.

**One-line check:** "I've reviewed every default parameter and verified it
makes sense for MY specific use case."

---

## Gap 4: No Cost Model

**What gets assumed:** Transactions are free. There are no taxes, fees,
commissions, or overhead costs.

**Why it causes problems:** A strategy that shows +₹5,000/day profit becomes
-₹500/day loss when you add brokerage + STT + GST + slippage.

**One-line check:** "I've listed every cost that exists in the real-world
version of what I'm simulating."

---

## Gap 5: Unspecified Error Handling

**What gets assumed:** Errors are caught generically or ignored.

**Why it causes problems:** The difference between "skip this trade" and
"crash the whole backtest" is the difference between useful results and
no results. But the difference between "skip silently" and "skip with warning"
is the difference between trustworthy results and misleading results.

**One-line check:** "For each thing that can go wrong, I've specified: crash,
skip+warn, skip+silent, or use-default."

---

## Gap 6: No Verification Strategy

**What gets assumed:** If it runs without errors, it's correct.

**Why it causes problems:** A backtest can run perfectly and produce completely
wrong P&L numbers because the sign convention is inverted. Running without
crashing ≠ correct.

**One-line check:** "I have at least one hand-calculated expected result I can
compare the system's output against."

---

## Gap 7: Vague Scope ("Make it Professional")

**What gets assumed:** AI interprets "professional" based on its training data,
which may not match your vision.

**Why it causes problems:** You get a generic-looking dashboard when you
wanted Bloomberg Terminal aesthetics. Or you get an over-engineered enterprise
app when you wanted a personal tool.

**One-line check:** "I can name 2-3 specific existing products/tools that
match the look and feel I want."

---

## Gap 8: Missing State Machine

**What gets assumed:** Every operation is independent.

**Why it causes problems:** A trade has states: PENDING → ENTERED → HOLDING →
EXITED. If the system doesn't track state, it might try to exit a trade that
was never entered, or enter the same trade twice.

**One-line check:** "I've listed every 'state' an entity can be in and what
transitions are allowed."

---

## Gap 9: No Concurrency Model

**What gets assumed:** One thing happens at a time.

**Why it causes problems:** In a backtest, can two trades be open simultaneously?
If yes, do they share capital? If capital is shared and both hit stop loss
at the same time, is there enough capital for both?

**One-line check:** "I've specified whether things can happen in parallel and
what resources they share."

---

## Gap 10: Undefined Time Zone

**What gets assumed:** Everything is local time, or UTC, or... something.

**Why it causes problems:** NSE is IST. Your server might be UTC. Your data
timestamps might be ambiguous. A 5.5-hour offset means your "09:15 entry"
actually happens at "03:45 UTC."

**One-line check:** "I've specified which timezone every timestamp is in."

---

## Gap 11: No Data Contract

**What gets assumed:** Data format won't change.

**Why it causes problems:** NSE changes their API response format. Your
CSV column names change. The date format switches from DD-MM-YYYY to
YYYY-MM-DD. System breaks silently.

**One-line check:** "I've documented the exact format of every data source
with field names, types, and examples."

---

## Gap 12: Missing Scaling Requirements

**What gets assumed:** Current scale is permanent.

**Why it causes problems:** 50 data files works fine with CSV loading.
5,000 files takes 20 minutes. The architecture choice made at 50 files
becomes a bottleneck at 5,000.

**One-line check:** "I've stated how much data will exist in 6 months
and whether current approach handles it."

---

## Gap 13: No Deployment Target

**What gets assumed:** Local development setup is the deployment target.

**Why it causes problems:** SQLite works locally, breaks with multiple
users in cloud. Hardcoded file paths break on Linux. API on localhost
doesn't work when frontend and backend are on different servers.

**One-line check:** "I've stated where this will run: local-only,
local→cloud-later, or cloud-from-day-1."

---

## Gap 14: Undefined User Workflow

**What gets assumed:** Users will figure out the correct order of operations.

**Why it causes problems:** User runs a backtest before selecting a strategy.
User changes parameters after starting a run. User refreshes the page mid-run.
Each of these needs a defined behavior.

**One-line check:** "I can describe the step-by-step workflow a user follows
from opening the app to getting a result."

---

## Gap 15: No Boundary Conditions

**What gets assumed:** All inputs are within normal ranges.

**Why it causes problems:** Capital = 0. Lot size = 0. Stop loss = 100%.
Hold time = 0 minutes. Every parameter has a boundary where the logic
breaks differently.

**One-line check:** "For every parameter, I've tested: what happens at 0,
what happens at the maximum, what happens with negative values."

---

## Gap 16: Missing Audit Trail

**What gets assumed:** You only need the current state.

**Why it causes problems:** "Why did trade #47 exit at STOP_LOSS?" Without
logs of the price at each check, you can't debug. Without parameter history,
you can't reproduce old results.

**One-line check:** "If something goes wrong, can I trace exactly what
happened and why?"

---

## Gap 17: No Idempotency Specification

**What gets assumed:** Every operation is run exactly once.

**Why it causes problems:** User clicks "Run Backtest" twice. Does it run
twice? Does the second run overwrite the first? Does it deduplicate?

**One-line check:** "I've specified what happens if the same operation is
triggered twice."

---

## Gap 18: Unspecified Comparison Semantics

**What gets assumed:** Comparison is straightforward.

**Why it causes problems:** "Compare two strategies" — on the same date?
With the same capital? Same parameters? If parameters differ, is the
comparison meaningful?

**One-line check:** "When comparing things, I've specified what is held
constant and what varies."

---

## Gap 19: Missing Data Freshness Requirements

**What gets assumed:** Data is always current.

**Why it causes problems:** Using yesterday's options data to make today's
trading decision. Cache serves stale results. Last week's backtest is
presented as current.

**One-line check:** "I've specified how old data can be before it's
considered stale."

---

## Gap 20: No Success Definition

**What gets assumed:** "It works" means success.

**Why it causes problems:** The system "works" — it runs, shows numbers,
doesn't crash. But is it useful? Does it answer the question you actually
had? Would you trust it enough to trade with real money?

**One-line check:** "I can complete this sentence: 'This project is
successful when I can _______ and trust the result enough to _______.'"

---

## Quick Reference Checklist

Before handing your spec to AI, verify:

| # | Gap | Covered? |
|---|-----|----------|
| 1 | Precision & rounding for every number | |
| 2 | Valid input definition + handling of invalid | |
| 3 | Every default parameter reviewed | |
| 4 | All real-world costs listed | |
| 5 | Error handling specified per failure mode | |
| 6 | At least one verification case written | |
| 7 | 2-3 reference products named for look/feel | |
| 8 | Entity states and transitions defined | |
| 9 | Concurrency / shared resources specified | |
| 10 | Timezones stated for all timestamps | |
| 11 | Data format documented with examples | |
| 12 | 6-month scale stated | |
| 13 | Deployment target specified | |
| 14 | User workflow described step-by-step | |
| 15 | Boundary conditions tested (0, max, negative) | |
| 16 | Audit trail / debuggability considered | |
| 17 | Double-execution behavior defined | |
| 18 | Comparison semantics specified | |
| 19 | Data freshness requirements stated | |
| 20 | Success defined in concrete terms | |
