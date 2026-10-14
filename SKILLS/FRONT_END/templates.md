# Standard Template Library

Use this file to construct the template showcase (Phase 3 of the workflow).
Adapt all four for the specific project — these are starting points, not finals.
Always modify color palette, typography choices, and content structure for the actual brief.

---

## OPTION A: Terminal Dark (Developer / Data Pipeline Tool)

**Aesthetic:** Near-black background with monospace data typography. Sidebar navigation with
icon + label pairs. Content area is a dense grid: stat row at top, main table below.
Accent color used sparingly — only for primary action and active states.
Feels like a developer-grade internal tool, not a consumer product.

**Best for:** Trading dashboards, backtesting results, data pipeline monitors, log viewers,
anything where the user is technical and the data is the product.

**Stack:** React + CSS Modules | or HTML + Vanilla for simpler tools

```
┌──────────────────────────────────────────────────────────┐
│  ● LOGO / TOOL NAME          [Status: Connected] [User] │
├────────────┬─────────────────────────────────────────────┤
│            │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  ▸ Overview│  │ Stat 1   │ │ Stat 2   │ │ Stat 3   │   │
│  ▸ Analysis│  │  42,310  │ │  ₹8.2L   │ │  -1.4%   │   │
│  ▸ History │  └──────────┘ └──────────┘ └──────────┘   │
│  ▸ Export  │                                             │
│            │  [Search ___________] [Filter ▾] [Export]  │
│  ─────     │  ┌─────────────────────────────────────┐  │
│  ▸ Settings│  │ Col A    Col B    Col C    Status   │  │
│            │  ├─────────────────────────────────────┤  │
│            │  │ data     data     data    ● Active  │  │
│            │  │ data     data     data    ● Pending │  │
│            │  │ data     data     data    ✕ Failed  │  │
│            │  └─────────────────────────────────────┘  │
│            │  Showing 1–25 of 847     [< Prev] [Next >] │
└────────────┴─────────────────────────────────────────────┘
```

**Palette suggestion:** `--color-bg: #0C0E12`, `--color-surface: #14171D`,
`--color-border: #1E2229`, `--color-accent: #00BFA5` (or amber `#F59E0B`)

---

## OPTION B: Finance Professional (Internal / Client-Facing B2B Tool)

**Aesthetic:** Off-white base with charcoal text. Clean top navigation, no sidebar.
Content in clearly sectioned cards. Single cool accent (slate-blue or teal).
Structured, trustworthy — looks like it was built by a finance team, not marketed to consumers.

**Best for:** Tax computation tools, GST processors, invoice generators, client portals,
anything where the output is a document or a compliance result.

**Stack:** HTML + Vanilla JS | or React for multi-step workflows

```
┌──────────────────────────────────────────────────────────┐
│  TOOL NAME     Overview | Reports | Upload | Settings    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Upload GSTR-2B / Statement                        │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │   ↑  Drag & drop file here, or click         │  │  │
│  │  │      Accepted: .json  .xlsx  .csv            │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │  Summary            │  │  Recent Uploads          │   │
│  │  Matched: 142        │  │  filename.json  ✓ Done  │   │
│  │  Mismatched: 7       │  │  file2.json     ● Proc  │   │
│  │  Pending: 3          │  │  file3.json     ✕ Err   │   │
│  │  [View Details →]    │  │                         │   │
│  └─────────────────────┘  └─────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Palette suggestion:** `--color-bg: #F7F8FA`, `--color-surface: #FFFFFF`,
`--color-border: #E2E5EA`, `--color-text: #1A1D23`, `--color-accent: #2563EB`

---

## OPTION C: Analyst Workspace (Multi-Panel Analytics Dashboard)

**Aesthetic:** Medium-dark background with panel-based layout. Resizable or tabbed sub-sections.
Compact typography, tight line-height — maximum data density. Chart above, table below.
Top bar is minimal — just branding + key controls.

**Best for:** Backtesting results, options chain analysis, P&L monitors, multi-strategy comparison,
any tool where the user needs to see chart + data + controls simultaneously.

**Stack:** React + CSS Modules (tabs, panels need state)

```
┌──────────────────────────────────────────────────────────┐
│  ▲ TOOL   [Strategy: Iron Condor ▾] [Period: 1Y ▾] [Run]│
├────────────────────────────┬─────────────────────────────┤
│  EQUITY CURVE              │  STATS                      │
│  ┌────────────────────────┐│  Total Return    +28.4%     │
│  │                  /\   ││  Max Drawdown    -6.2%      │
│  │               /\/  \  ││  Sharpe Ratio    1.84       │
│  │          ___/        \_││  Win Rate        63.1%      │
│  │   ______/             ││  ─────────────────────      │
│  └────────────────────────┘│  Trades: 247  Avg: +1.2%   │
│  [1D][1W][1M][3M][1Y][All] │  [Download Report]         │
├────────────────────────────┴─────────────────────────────┤
│  TRADE LOG           [Filter: All ▾]  [Search ______]    │
│  Date       Strike    Type    P&L       Status            │
│  14 Jun     19500CE   Short   +2,340    ● Closed          │
│  12 Jun     19600PE   Long    -890      ● Closed          │
│  10 Jun     19400CE   Short   +1,120    ● Closed          │
│                          [Load More]                      │
└──────────────────────────────────────────────────────────┘
```

**Palette suggestion:** `--color-bg: #191C22`, `--color-surface: #1F2330`,
`--color-border: #2A2F3E`, `--color-accent: #3B82F6`, chart line: `--color-success`

---

## OPTION D: Minimal Utility (Internal Tool / Converter / Processor)

**Aesthetic:** Pure white, maximum content width, zero decoration. Top bar with logo + minimal nav.
Content is the tool — no chrome, no cards, no sidebar. Think: a well-designed CLI translated to web.
Typography does the heavy lifting. Monospace for data output, sans-serif for UI.

**Best for:** File converters, batch processors, computation tools, admin panels, anything where
the user is experienced and wants zero friction between action and result.

**Stack:** HTML + Vanilla JS (fastest, no build, trivial to embed)

```
┌──────────────────────────────────────────────────────────┐
│  TOOL NAME                              [Docs] [Settings]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Input                                                   │
│  ─────────────────────────────────────────────────────   │
│  [________________________] ← file path or upload        │
│                                                          │
│  Options                                                 │
│  ─────────────────────────────────────────────────────   │
│  ○ Format A   ● Format B   ○ Format C                   │
│  [Option toggle] [Config value ___]                      │
│                                                          │
│  [  Run Process  ]                                       │
│                                                          │
│  Output                                                  │
│  ─────────────────────────────────────────────────────   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  > Processing complete                             │  │
│  │  > 847 records processed                          │  │
│  │  > 7 mismatches flagged                           │  │
│  │  [Download output.xlsx]                           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Palette suggestion:** `--color-bg: #FFFFFF`, `--color-surface: #F9FAFB`,
`--color-border: #D1D5DB`, `--color-text: #111827`, `--color-accent: #111827` (near-black accent)
