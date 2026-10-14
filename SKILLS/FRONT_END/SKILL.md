---
name: sahil-frontend
description: |
  Use this skill for ANY frontend or UI development task for Sahil's projects. Mandatory triggers:
  "build a frontend", "create a UI", "make a dashboard", "design an interface", "frontend for this",
  "create a web interface", "make it visual", or any request where a visual interface is the output.
  This skill governs the complete frontend workflow: mandatory template discovery → scoping → build →
  integration. Use it even if the user seems to just want "a quick UI" — the discovery protocol applies always.
  Covers Sahil's standards: professional/fintech aesthetics (never AI-generic), template-first approach,
  Python/Flask/FastAPI/Java/C++ backend integration patterns, and non-negotiable error handling.
---

# Sahil Frontend Development Skill

## Who This Is For

Sahil is a CA and financial tools developer (GST, ITR, options trading, backtesting). His frontends serve
practitioners and analysts — tools that handle real data, need to be trusted, and are used by people who
can tell the difference between a polished product and an AI-generated mockup.

The standard: Would a senior developer at Zerodha, Groww, or a serious B2B fintech be proud of this?

---

## MANDATORY WORKFLOW — Follow This Order Every Time

### Phase 1 → Understand the Project (Never Skip)

Extract or ask:
1. **What does this tool do?** (one sentence — nail this first)
2. **Who uses it?** Developer, CA client, internal team, customer?
3. **What is the primary action?** Upload data? View analytics? Configure? Submit forms?
4. **Data flow?** File upload → process → result? API polling? Real-time stream? Static display?
5. **Backend language?** Python (Flask/FastAPI) | Java (Spring) | C++ | None

### Phase 2 → Scope the Features (Ask + Suggest Together)

Do NOT just ask — also propose based on project context. Format:

```
Based on this being a [tool type], I'd suggest:
  • [Page/view 1] — [one-line description]
  • [Page/view 2] — [one-line description]
  • [Page/view 3] — [one-line description]

What else do you want? Anything to remove?
```

Always ask:
- Auth needed? Login screen, or internal tool with no auth?
- Real-time updates? Polling / WebSocket / one-shot request?
- Export capability? CSV / Excel / PDF download?
- Mobile responsiveness needed? Or desktop-first tool?

### Phase 3 → Template Showcase (Mandatory Before Building)

**Present 3–4 distinct template options as ASCII wireframes + aesthetic brief. Build nothing until Sahil picks one.**

Options must differ in layout structure, not just color. See `references/templates.md` for the standard template library. Each option format:

```
OPTION [A/B/C/D]: [Name]
Aesthetic: [2–3 sentence visual identity description]
Best for: [content type / user type this suits]
Stack: [HTML+Vanilla | React+CSS Modules | React+Tailwind minimal]

┌─────────────────────────────────────────────────┐
│  [ASCII wireframe — show layout, not content]   │
└─────────────────────────────────────────────────┘
```

### Phase 4 → Build

Only after Sahil confirms template choice. Follow the architecture rules in this skill exactly.

---

## Aesthetic Rules — Non-Negotiable

**What professional looks like:**
- Information-dense, not marketing-page sparse. Real tools have data, labels, structure.
- Typography is the primary differentiator. Weights, sizes, spacing — not icons or illustrations.
- Dark or dark-tinted for data/analytics tools. Light/clean for document/report tools.
- Subtle micro-interactions on actions (button states, hover on rows). Not page transitions.
- Grid/table-dominant for data tools. Cards only when content is truly card-shaped.

**What to avoid (marks as AI-generated):**
- Blob shapes, abstract illustrations, hero images with random gradients
- Default Tailwind palette (#6366f1 purple, #10b981 green out-of-the-box, mint, coral)
- Emojis as UI elements
- Oversized rounded borders (`border-radius > 12px` on main containers)
- Centered everything layout (marketing page pattern, not app pattern)
- Same font weight across heading hierarchy
- Skeleton-heavy, sparsely populated layouts that "feel" like an onboarding screen

---

## Technology Selection

| Project Type | Stack | Reason |
|---|---|---|
| Data-heavy dashboard | React + CSS Modules | State for filters/tabs, no Tailwind pollution |
| Single-purpose tool | HTML + Vanilla JS | Zero build step, trivial Python/Java embed |
| Flask/FastAPI embedded | Jinja2 + HTMX | Server renders, minimal JS, no build |
| Complex multi-page app | React + custom CSS | Full SPA with real routing |
| Quick iteration needed | React + minimal Tailwind | Fast layout, customize aggressively |

**Always avoid:** Next.js (overkill), Bootstrap (too recognizable), MUI/AntD (alien aesthetics), heavy animation libraries unless specifically requested.

---

## Architecture — Built for Future Change

Every frontend must survive these changes without a rewrite:
- Swapping backend (Flask → FastAPI → Spring)
- Adding a new page or tab
- Changing data format (JSON → different JSON schema)
- Adding auth after the fact
- Adding dark/light toggle

### File Structure (React)
```
/src
  /components     ← Reusable UI (Table, Card, Modal, Button, Badge)
  /pages          ← Top-level views (each is one file)
  /hooks          ← useApi, useError, useWebSocket, usePagination
  /services       ← api.js — ALL fetch calls here only
  /utils          ← formatCurrency, formatDate, parseGSTR, validators
  /constants      ← API_BASE, ROUTES, FEATURE_FLAGS, STATUS_CODES
  /styles         ← tokens.css (CSS vars), global.css, components.css
```

### File Structure (HTML/Vanilla)
```
/
  index.html
  /css
    tokens.css      ← ALL CSS variables — colors, spacing, type
    main.css        ← global + layout
    components.css  ← reusable element styles
  /js
    config.js       ← API_BASE_URL, feature flags
    api.js          ← all fetch calls (single source)
    ui.js           ← DOM helpers, state renderers
    app.js          ← entry point, event wiring
```

### Extensibility Rules
1. **CSS variables for all visual values.** Never hardcode a color, spacing, or font size outside `:root {}`
2. **API_BASE in one constant only.** `config.js` or `constants/index.js` — never scattered
3. **Components receive data as props.** No component fetches its own data
4. **FEATURE_FLAGS object** — `const FEATURES = { auth: false, darkMode: true, export: false }` — toggleable without hunting code
5. **Service layer is the only API caller** — swap backend = change `api.js` only

Read `references/design-tokens.md` for the standard CSS variable template.

---

## Backend Integration Patterns

### Python — Flask
```python
from flask_cors import CORS
CORS(app, origins=["http://localhost:3000", "http://localhost:5500"])

def api_success(data, message="OK"):
    return jsonify({"status": "success", "data": data, "message": message})

def api_error(message, code=400):
    return jsonify({"status": "error", "data": None, "message": message}), code
```

### Python — FastAPI
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ApiResponse(BaseModel):
    status: str
    data: Any
    message: str
```

### Java — Spring Boot
```java
@CrossOrigin(origins = "http://localhost:3000")
@RestController

// Consistent response wrapper
ResponseEntity.ok(Map.of("status", "success", "data", result, "message", "OK"))
```

### C++ (Crow / Pistache)
```cpp
CROW_ROUTE(app, "/api/data").methods("GET"_method)([]{
    crow::json::wvalue res;
    res["status"] = "success";
    res["data"] = computeResult();
    return crow::response{res};
});
```

### Frontend API Service (Backend-Agnostic)
```javascript
// services/api.js — single source of truth
const API_BASE = config.API_BASE_URL;  // never hardcoded here

export async function apiCall(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: { "Content-Type": "application/json" },
        ...options
    });
    const json = await res.json();
    if (!res.ok || json.status === "error")
        throw new ApiError(json.message, res.status);
    return json.data;
}

// File upload with progress
export async function uploadFile(endpoint, file, onProgress) {
    const fd = new FormData();
    fd.append("file", file);
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.upload.onprogress = e => onProgress(Math.round(e.loaded / e.total * 100));
        xhr.onload = () => {
            const json = JSON.parse(xhr.responseText);
            json.status === "success" ? resolve(json.data) : reject(new ApiError(json.message));
        };
        xhr.onerror = () => reject(new ApiError("Network error — is the server running?", 0));
        xhr.open("POST", `${API_BASE}${endpoint}`);
        xhr.send(fd);
    });
}
```

---

## Error Handling — Non-Negotiable, Always Include

Every async operation must show all three states in the UI: **loading → success OR error**.
A blank screen is never acceptable. Every state renders something.

### ApiError class
```javascript
class ApiError extends Error {
    constructor(message, statusCode, details = {}) {
        super(message);
        this.name = "ApiError";
        this.statusCode = statusCode;
        this.details = details;
    }
}
```

### The Five Failure Modes — Handle All

1. **Network failure** → server not running, CORS, timeout. Message: "Could not connect. Is the server running?"
2. **Server error (5xx)** → backend crash. Message: "Server error — try again or check logs."
3. **Validation error (4xx)** → bad input. Show field-level if possible. Show what was wrong, how to fix it.
4. **Empty result** → 200 OK but no data. Show empty state with a helpful action, not a blank screen.
5. **Frontend crash** → use React ErrorBoundary or try/catch in vanilla. Show error + reload button.

### UI State Rules
- **Toasts** → transient success/failure (auto-dismiss 4s). `showToast(msg, type)` utility.
- **Inline** → field validation. Never in a separate modal.
- **Banner** → page-level degradation (stale data, partial load).
- **Blocking modal** → only for unrecoverable errors needing user decision.
- **Console** → always `console.error("[component]", error)` with context. Never swallow silently.

### Forms
- Validate on blur (field leave), not submit-only
- Disable submit during in-flight request (prevent double-submit)
- Re-enable with error message on failure
- Never reset the form on error — user should be able to fix and retry

Read `references/error-patterns.md` for copy-paste error component implementations.

---

## Sahil's Common Project Patterns

**GST / Tax Data Tool**
Must-haves: sticky-header sortable table, filter bar (search + dropdowns), row-level status badges,
pagination or virtual scroll, export button (CSV/Excel). Optional: row expansion for detail view.

**File Upload + Processing Tool (GSTR-2B, Bank Statements)**
Must-haves: drag-and-drop zone + click-to-browse, file type validation pre-upload, progress bar,
processing status with spinner/estimated time, summary stats above detail table. Never auto-submit.

**Analytics / Backtesting Dashboard**
Must-haves: time range selector, summary stat cards (P&L, returns, drawdown), chart with hover tooltip,
table below chart for trade log. Optional: chart type toggle, PNG download.

**Form-Based Computation Tool**
Must-haves: multi-step or sectioned single-page form, real-time calculated preview as fields change,
blur validation, review summary before final submission, success state with result/download.

---

## Design Token Template

Every project starts with its own `:root {}` block. Read `references/design-tokens.md` for the full
template. Core structure:

```css
:root {
  --color-bg:         /* main background */;
  --color-surface:    /* cards, panels */;
  --color-border:     /* subtle dividers */;
  --color-text:       /* primary text */;
  --color-text-muted: /* labels, metadata */;
  --color-accent:     /* one main accent — earn it */;
  --color-danger:     #EF4444;
  --color-warning:    #F59E0B;
  --color-success:    #10B981;
  --font-display:     /* chosen for the project */;
  --font-mono:        /* for data, code, numbers */;
  /* full spacing + radius scale */
}
```

Never set any color or spacing value outside `:root {}`.

---

## Quality Gate — Run Before Delivery

**Functional**
- [ ] All API calls go through `/services/api.js` only
- [ ] Every async op shows loading, success, and error states
- [ ] No hardcoded URLs or API keys in component code
- [ ] Forms cannot double-submit
- [ ] Empty states render something helpful

**Visual**
- [ ] Does not resemble any default Tailwind / Bootstrap template
- [ ] Colors + spacing come from CSS variables only
- [ ] Clear typographic hierarchy — not all same weight/size
- [ ] No blobs, random gradients, or emojis as UI elements
- [ ] Whitespace is intentional — dense where data lives, breathable at decision points

**Extensibility**
- [ ] Adding a new page = one new file, no existing file changes
- [ ] Swapping backend URL = change one constant
- [ ] Adding dark mode = swap CSS variable values only
- [ ] Adding auth = wrap routes, no per-component changes

---

## Delivery Checklist

Always include with the delivered frontend:
1. **What was built** — one paragraph, key decisions explained
2. **How to start** — exact command + port (`python app.py` → `http://localhost:5000`)
3. **How to extend** — where to add a new page, how to add a new API endpoint
4. **Known limitations** — be honest about what was descoped

If a backend already exists, ask for the endpoint contract (routes + request/response shape)
before building the frontend. Never assume the API shape.

---

## Reference Files

- `references/templates.md` — Standard template library with full ASCII wireframes + aesthetic briefs
- `references/design-tokens.md` — CSS variable template with dark/light palettes
- `references/error-patterns.md` — Copy-paste error component implementations (React + Vanilla)
