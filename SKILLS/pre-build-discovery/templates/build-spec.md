# Build Spec Template

> Fill this template during Phase 5 of Pre-Build Discovery. This becomes the
> document you hand to AI when you say "build this." Every section with a
> ❓ needs YOUR input — don't leave blanks.

---

## 1. Project Overview

**Project Name:** ❓
**One-sentence description:** ❓
**Domain:** ❓ (trading, web app, data pipeline, etc.)
**End user:** ❓ (just me / my team / public users)
**Deployment target:** ❓ (local-only / cloud later / cloud from day 1)

**Reference products** (2-3 that match the desired look/feel):
1. ❓
2. ❓
3. ❓

**Success definition:**
> "This project is successful when I can ❓ and trust the result enough to ❓."

---

## 2. Data Contract

### Input Sources

| Source | Format | Update Frequency | Sample |
|--------|--------|-----------------|--------|
| ❓ | ❓ | ❓ | ❓ |

### Data Quality Rules

| Scenario | Action |
|----------|--------|
| Missing data point | ❓ (skip+warn / skip+silent / halt / use-default) |
| Corrupt/invalid data | ❓ |
| Zero values | ❓ |
| Out-of-range values | ❓ |

### Data Volume

- Current: ❓
- In 6 months: ❓

---

## 3. Core Logic & Calculations

### Calculation 1: ❓ [Name]

**Formula:**
```
❓ (write in plain language or math)
```

**Worked example:**
```
Input:  ❓
Step 1: ❓
Step 2: ❓
Output: ❓ (this is the expected result to verify against)
```

### Calculation 2: ❓ [Name]

*(repeat for every calculation)*

---

## 4. Parameters & Defaults

| Parameter | Description | Default | Valid Range | Boundary Behavior |
|-----------|------------|---------|-------------|-------------------|
| ❓ | ❓ | ❓ | ❓ | ❓ |

---

## 5. Costs & Fees

| Cost Type | Formula / Amount | Applied When |
|-----------|-----------------|-------------|
| ❓ | ❓ | ❓ |

**Display:** ❓ (gross only / net only / both)

---

## 6. Edge Cases

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 1 | ❓ | ❓ |
| 2 | ❓ | ❓ |
| 3 | ❓ | ❓ |
| 4 | ❓ | ❓ |
| 5 | ❓ | ❓ |

---

## 7. Outputs

### Metrics / Fields

| Field | Unit | Precision | Format |
|-------|------|-----------|--------|
| ❓ | ❓ | ❓ | ❓ |

### Display Requirements

- ❓ (charts, tables, cards — be specific)

---

## 8. Acceptance Criteria

| # | Criterion | Pass/Fail |
|---|-----------|-----------|
| 1 | ❓ | |
| 2 | ❓ | |
| 3 | ❓ | |

### Verification Method

- [ ] Hand-calculated expected result exists? Which calculation?
- [ ] Existing system to compare against? Which one?
- [ ] Sanity check rules defined? (e.g., "P&L ≤ capital deployed")

---

## 9. Explicit Exclusions (NOT in scope)

1. ❓
2. ❓
3. ❓

---

## 10. User Workflow

Describe the step-by-step user journey:

1. User opens the app →
2. User sees ❓ →
3. User selects ❓ →
4. User clicks ❓ →
5. System shows ❓ →
6. User can then ❓

---

## 11. Technical Constraints

- **Language / Framework:** ❓
- **Must integrate with:** ❓
- **Must NOT touch:** ❓ (existing files/systems to keep isolated)
- **Performance requirement:** ❓

---

## Pre-Submission Checklist

Before handing this to AI, verify:

- [ ] Every ❓ is replaced with a real answer
- [ ] At least one worked calculation example with expected output
- [ ] At least one hand-calculated verification case
- [ ] Default parameters reviewed and make sense for my domain
- [ ] Costs/fees listed (even if the answer is "none for v1")
- [ ] At least 5 edge cases listed
- [ ] Success definition is concrete and measurable
- [ ] Explicit exclusions prevent scope creep
