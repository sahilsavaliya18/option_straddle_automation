---
name: pre-build-discovery
description: >
  Structured requirements discovery skill that forces critical thinking BEFORE
  code is written. Prevents the #1 cause of project failure with AI: building
  the wrong thing correctly. Guides users through domain assumptions, accuracy
  requirements, data contracts, edge cases, and success criteria — producing a
  Build Spec that the AI uses as its source of truth throughout implementation.
license: MIT
metadata:
  version: 1.0.0
  author: sahil (created via Antigravity)
  category: project-management
  domain: pre-implementation
  updated: 2026-09-11
  origin: lessons-learned from NIFTY Strategy Lab pre-mortem analysis
  tech-stack: requirements-engineering, domain-driven-design, specification-by-example
---

# Pre-Build Discovery: Think Before You Build

## Why This Skill Exists

> **The most expensive bugs are the ones nobody thought to prevent.**

When you go to an AI and say *"build me an options backtesting dashboard"*, the AI will
build something that compiles, runs, and looks good — but it will fill in every unspoken
detail with **reasonable-sounding defaults that may be financially wrong, logically
incomplete, or silently misleading.**

This happened in the NIFTY Strategy Lab project:

| What went wrong | Root cause |
|----------------|------------|
| Short strategy P&L signs might be inverted | Nobody defined how SELL legs should calculate profit |
| Margin model uses `2 × premium` (unrealistic) | Nobody specified what margin model to use |
| Default config blocks 87% of the trading day | Nobody reviewed what default parameters actually mean |
| No transaction costs in results | Nobody listed what costs exist in real trading |
| Engine silently skips missing data | Nobody defined what "valid backtest" means |

**Every one of these was caused by the same thing: the builder (AI) filled in a gap
that the requester (you) didn't know existed.**

This skill exists to **surface those gaps before building starts.**

---

## When to Use This Skill

- **Before** asking AI to build any project larger than a single script
- **Before** any project involving money, calculations, or data accuracy
- **Before** any project where "wrong output" looks the same as "right output"
- **When** you have a vague idea ("I want a dashboard") but not a precise spec
- **When** rebuilding/expanding an existing system (like adding 12 strategies to an existing straddle engine)

## When NOT to Use

- Quick scripts, one-off utilities, or throwaway prototypes you'll delete
- Projects where you already have a detailed spec from a domain expert
- Bug fixes or small feature additions to well-understood systems

---

## The Process: 5 Phases

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Phase 1    │ →  │  Phase 2    │ →  │  Phase 3    │ →  │  Phase 4    │ →  │  Phase 5    │
│  DOMAIN     │    │  INPUTS &   │    │  LOGIC &    │    │  OUTPUTS &  │    │  BUILD      │
│  MAPPING    │    │  DATA       │    │  RULES      │    │  VALIDATION │    │  SPEC       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
  "What world       "What goes in      "What happens     "What comes out     "The contract
   am I in?"         and how?"          inside?"          and how do I        with AI"
                                                          know it's right?"
```

### Phase 1: Domain Mapping (10-15 min)

**Goal:** Establish what world this project lives in, so the AI doesn't make wrong
domain assumptions.

Answer these questions **in writing** before talking to AI:

1. **What domain is this?** (trading, healthcare, education, etc.)
2. **Who is the end user?** (you personally, a team, public users?)
3. **What does "wrong" look like?** Describe a specific scenario where the
   system gives incorrect output and what the consequence is.
4. **What existing tools/systems does this replace or extend?**
5. **What domain knowledge does the builder NEED to know?**
   List things that are obvious to you but wouldn't be obvious to a general
   programmer. Examples:
   - "NIFTY options have a lot size of 65, not 1"
   - "SELL options have margin requirements, not just premium"
   - "NSE data has gaps — not every minute has a price tick"

> **Load `references/domain-questions.md`** for domain-specific question banks
> (trading/finance, web apps, data pipelines, etc.)

### Phase 2: Inputs & Data (10-15 min)

**Goal:** Define exactly what data goes into the system and its quality
characteristics.

1. **What are the input data sources?** List every file, API, database, or
   user input.
2. **What does the data look like?** Show an actual sample — 5 rows of a CSV,
   a JSON response, a screenshot. Don't describe it; show it.
3. **What are the known data quality issues?**
   - Missing values? How often?
   - Incorrect values? How would you detect them?
   - Timezone issues?
   - Format inconsistencies?
4. **What should happen when data is missing or corrupt?**
   - Skip silently? (dangerous)
   - Log and continue? (better)
   - Halt and alert? (safest)
   - Which one, and why?
5. **What volume of data are we talking about?**
   - 10 files or 10,000?
   - 1 MB or 10 GB?
   - This determines architecture choices the AI will make.

### Phase 3: Logic & Rules (15-20 min)

**Goal:** Define the core calculations and business rules so the AI doesn't
invent them.

This is where most projects fail. **You must write down the rules, not just
think about them.**

1. **List every calculation the system performs.**
   For each one:
   - Write the formula in plain language or math
   - Give a worked example with real numbers
   - State the expected output for the example

   Example (from trading):
   ```
   P&L for a BUY leg:
     Formula: (exit_price - entry_price) × quantity
     Example: Buy CE at 150, exit at 180, qty 65
     Expected: (180 - 150) × 65 = +₹1,950

   P&L for a SELL leg:
     Formula: (entry_price - exit_price) × quantity
     Example: Sell CE at 150, exit at 180, qty 65
     Expected: (150 - 180) × 65 = -₹1,950
   ```

2. **What are the configurable parameters?**
   For each parameter:
   - What is it?
   - What is the sensible default?
   - What is the valid range?
   - What happens at the boundaries?

3. **What costs/fees/taxes exist?**
   In finance: brokerage, STT, GST, stamp duty, slippage
   In SaaS: API rate limits, storage costs, bandwidth
   In data: cleaning overhead, refresh frequency

4. **What are the edge cases?**
   List at least 5 scenarios where the "normal" path doesn't apply:
   - What if the market closes early?
   - What if a strike has zero premium?
   - What if two trades have the exact same timestamp?
   - What if capital is less than the cost of 1 lot?

5. **What should the system NOT do?**
   Explicit exclusions prevent scope creep:
   - "Do NOT place real trades"
   - "Do NOT calculate Greeks"
   - "Do NOT support multi-day positions"

### Phase 4: Outputs & Validation (10-15 min)

**Goal:** Define what "correct" looks like so you can verify the build.

1. **What does the output look like?**
   - List every field/column/metric the system should produce
   - For each metric: what unit? what precision? what format?

2. **How will you verify the output is correct?**
   This is the most important question. You need at least ONE of:
   - A hand-calculated expected result you can compare against
   - An existing system whose output you can match
   - A sanity check rule ("P&L should never exceed capital deployed")

3. **What are the acceptance criteria?**
   Write concrete pass/fail statements:
   - "Long Straddle results must match existing C++ engine within ₹10"
   - "Dashboard must load all 12 strategies in under 2 seconds"
   - "No backtest should report 0 trades without a warning"

4. **What does failure look like?**
   - Silent wrong numbers (worst — you act on bad data)
   - Crash / error message (better — you know something is wrong)
   - Missing data shown as zero (dangerous — looks like a valid result)

### Phase 5: Build Spec (10 min)

**Goal:** Compile everything into a single document that becomes the AI's
source of truth.

> **Use `templates/build-spec.md`** — fill in the template from your Phase 1-4
> answers. This becomes the artifact you give to the AI when you say "build this."

The Build Spec should be:
- **Specific enough** that two different AI sessions would build roughly the
  same thing
- **Concise enough** that an AI can read it in one context window
- **Testable** — every major claim has a verification method

---

## References

Load the reference that matches your situation:

- **[references/domain-questions.md](references/domain-questions.md)** — domain-specific
  question banks for trading/finance, web applications, data pipelines, and ML projects.
  Read when doing Phase 1-3 for a specific domain.

- **[references/common-gaps.md](references/common-gaps.md)** — the 20 most common
  specification gaps that cause project failures, with examples from real projects.
  Read when reviewing your Build Spec before starting implementation.

- **[templates/build-spec.md](templates/build-spec.md)** — the Build Spec template.
  Fill this in during Phase 5. This is the document you hand to AI.

- **[examples/strategy-lab-retrospective.md](examples/strategy-lab-retrospective.md)** —
  a worked example showing how this skill would have prevented the Strategy Lab
  pre-mortem issues, with before/after requirement statements.

---

## Integration Points

| Integration | Direction | Description |
|------------|-----------|-------------|
| `pre-mortem/` | Feeds into | Build Spec becomes the input for pre-mortem risk analysis |
| `webdesignskill.md` | Receives from | Frontend design skill informs UI/UX section of Build Spec |
| Implementation Plan | Feeds into | Build Spec replaces vague user requests as the planning input |
| Post-build testing | Feeds into | Acceptance criteria from Phase 4 become test cases |

---

## Scope & Limitations

**In Scope:** Requirements elicitation for software projects; domain assumption
surfacing; data contract definition; calculation specification; acceptance
criteria; producing a Build Spec artifact.

**Out of Scope:** Architecture design (that's the AI's job once it has the spec);
ongoing project management; risk analysis (use `pre-mortem/` after the Build Spec);
user research with actual end users.

**Important Caveats:**
- This skill works best when YOU are the domain expert and the AI is the builder.
  If you don't know the domain (e.g., asking AI to build something in a field
  you're learning), the gaps won't surface because you don't know what you
  don't know. In that case: research the domain first, then use this skill.
- Spending 45-60 minutes on discovery saves 5-10 hours of rework. But spending
  3 hours on discovery for a 1-hour project is waste. Scale the effort to the
  project size.
- The Build Spec is a living document. Update it when you learn something new
  during implementation. Don't treat it as frozen.
