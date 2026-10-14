# Design Token Templates

Paste the relevant block into `tokens.css` or the `:root {}` of `main.css`.
Then reference variables everywhere. Never hardcode values outside `:root {}`.

---

## Dark Theme (Data / Analytics / Trading Tools)

```css
:root {
  /* ── Backgrounds ── */
  --color-bg:           #0C0E12;   /* main page */
  --color-surface:      #14171D;   /* cards, panels */
  --color-surface-alt:  #1A1D26;   /* elevated surfaces */
  --color-border:       #1E2229;   /* dividers */
  --color-border-focus: #3B82F6;   /* focused input ring */

  /* ── Text ── */
  --color-text:         #E8EAED;   /* primary */
  --color-text-muted:   #6B7280;   /* labels, metadata */
  --color-text-faint:   #374151;   /* placeholder, disabled */

  /* ── Accent ── one color, used sparingly */
  --color-accent:       #00BFA5;   /* or #F59E0B or #3B82F6 */
  --color-accent-dim:   rgba(0,191,165,0.12);

  /* ── Semantic ── */
  --color-success:      #10B981;
  --color-success-dim:  rgba(16,185,129,0.12);
  --color-warning:      #F59E0B;
  --color-warning-dim:  rgba(245,158,11,0.12);
  --color-danger:       #EF4444;
  --color-danger-dim:   rgba(239,68,68,0.12);
  --color-info:         #3B82F6;
  --color-info-dim:     rgba(59,130,246,0.12);

  /* ── Typography ── */
  --font-display:       'Inter', 'DM Sans', system-ui, sans-serif;
  --font-mono:          'JetBrains Mono', 'Fira Code', monospace;
  --font-size-xs:       11px;
  --font-size-sm:       12px;
  --font-size-md:       14px;
  --font-size-lg:       16px;
  --font-size-xl:       20px;
  --font-size-2xl:      26px;
  --font-size-3xl:      34px;
  --line-height-tight:  1.25;
  --line-height-normal: 1.5;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semi:   600;
  --font-weight-bold:   700;

  /* ── Spacing ── */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* ── Surfaces ── */
  --radius-sm:   3px;
  --radius-md:   6px;
  --radius-lg:   10px;
  --shadow-sm:   0 1px 2px rgba(0,0,0,0.4);
  --shadow-md:   0 2px 8px rgba(0,0,0,0.5);
  --shadow-lg:   0 8px 24px rgba(0,0,0,0.6);

  /* ── Transitions ── */
  --ease-fast:   150ms ease;
  --ease-normal: 250ms ease;
  --ease-slow:   400ms ease;

  /* ── Layout ── */
  --sidebar-width: 220px;
  --topbar-height: 52px;
  --content-max:   1200px;
}
```

---

## Light / Professional Theme (Tax, Compliance, Document Tools)

```css
:root {
  /* ── Backgrounds ── */
  --color-bg:           #F7F8FA;
  --color-surface:      #FFFFFF;
  --color-surface-alt:  #F0F2F5;
  --color-border:       #E2E5EA;
  --color-border-focus: #2563EB;

  /* ── Text ── */
  --color-text:         #111827;
  --color-text-muted:   #6B7280;
  --color-text-faint:   #9CA3AF;

  /* ── Accent ── */
  --color-accent:       #2563EB;   /* or #0F766E teal */
  --color-accent-dim:   rgba(37,99,235,0.08);

  /* ── Semantic ── */
  --color-success:      #059669;
  --color-success-dim:  rgba(5,150,105,0.10);
  --color-warning:      #D97706;
  --color-warning-dim:  rgba(217,119,6,0.10);
  --color-danger:       #DC2626;
  --color-danger-dim:   rgba(220,38,38,0.10);
  --color-info:         #2563EB;
  --color-info-dim:     rgba(37,99,235,0.08);

  /* ── Typography ── same scale, different personality ── */
  --font-display:       'Inter', 'IBM Plex Sans', system-ui, sans-serif;
  --font-mono:          'IBM Plex Mono', 'JetBrains Mono', monospace;

  /* … same spacing, radius, shadow, transition tokens … */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --shadow-sm:   0 1px 3px rgba(0,0,0,0.08);
  --shadow-md:   0 2px 8px rgba(0,0,0,0.10);
  --shadow-lg:   0 4px 20px rgba(0,0,0,0.12);
}
```

---

## Font Loading

```html
<!-- For Inter (most professional sans) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<!-- Alternative: DM Sans (slightly more characterful) -->
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap" rel="stylesheet">
```

---

## Quick Palette Ideas (Project-Specific Starting Points)

| Project Type | bg | surface | accent |
|---|---|---|---|
| Options trading | #0A0D13 | #111520 | #F59E0B (amber) |
| GST/Tax tool | #F8F9FB | #FFFFFF | #2563EB (blue) |
| Bank statement | #F5F7FA | #FFFFFF | #0F766E (teal) |
| Backtesting | #151820 | #1C1F2E | #3B82F6 (blue) |
| ITR/Compliance | #FAFAFA | #FFFFFF | #7C3AED (violet) |
| P&L dashboard | #0E1117 | #161B25 | #10B981 (green) |
