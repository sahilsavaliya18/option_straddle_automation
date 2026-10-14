# Error Pattern Implementations

Copy-paste ready. Adapt to project's CSS variable names.

---

## 1. ApiError Class (always include this)

```javascript
class ApiError extends Error {
    constructor(message, statusCode = 0, details = {}) {
        super(message);
        this.name = "ApiError";
        this.statusCode = statusCode;
        this.details = details;
    }
    get isNetworkError()   { return this.statusCode === 0; }
    get isClientError()    { return this.statusCode >= 400 && this.statusCode < 500; }
    get isServerError()    { return this.statusCode >= 500; }
    get isUnauthorized()   { return this.statusCode === 401; }
    get isForbidden()      { return this.statusCode === 403; }
    get isNotFound()       { return this.statusCode === 404; }
}
```

---

## 2. Safe Fetch Wrapper (Vanilla JS)

```javascript
async function safeFetch(endpoint, options = {}) {
    try {
        const res = await fetch(endpoint, {
            headers: { "Content-Type": "application/json" },
            ...options
        });
        const json = await res.json().catch(() => ({}));

        if (res.status === 0)    throw new ApiError("Cannot reach server. Is it running?", 0);
        if (res.status === 401)  throw new ApiError("Session expired. Please refresh.", 401);
        if (res.status === 403)  throw new ApiError("You don't have permission for this.", 403);
        if (res.status === 404)  throw new ApiError("Resource not found.", 404);
        if (res.status >= 500)   throw new ApiError("Server error. Check backend logs.", res.status);
        if (res.status >= 400)   throw new ApiError(json.message || "Invalid request.", res.status, json);
        if (json.status === "error") throw new ApiError(json.message, res.status, json);

        return json.data ?? json;
    } catch (e) {
        if (e instanceof ApiError) throw e;
        if (e.name === "AbortError") throw new ApiError("Request timed out.", 0);
        throw new ApiError("Connection failed. Check your network.", 0);
    }
}
```

---

## 3. Async State Pattern (Vanilla JS)

```javascript
// Call this before every async operation
function setLoading(containerEl, message = "Loading...") {
    containerEl.innerHTML = `
        <div class="state-loading">
            <div class="spinner"></div>
            <span>${message}</span>
        </div>`;
}

function setError(containerEl, error, onRetry = null) {
    const isNetwork = error instanceof ApiError && error.isNetworkError;
    containerEl.innerHTML = `
        <div class="state-error">
            <span class="state-error__icon">✕</span>
            <p class="state-error__message">${error.message}</p>
            ${isNetwork ? '<p class="state-error__hint">Make sure the server is running on port 5000</p>' : ''}
            ${onRetry ? `<button class="btn btn-sm" id="retry-btn">Retry</button>` : ''}
        </div>`;
    if (onRetry) containerEl.querySelector("#retry-btn").onclick = onRetry;
}

function setEmpty(containerEl, message, actionLabel = null, onAction = null) {
    containerEl.innerHTML = `
        <div class="state-empty">
            <p>${message}</p>
            ${actionLabel ? `<button class="btn btn-sm" id="action-btn">${actionLabel}</button>` : ''}
        </div>`;
    if (actionLabel && onAction) containerEl.querySelector("#action-btn").onclick = onAction;
}

// Usage pattern:
async function loadData() {
    setLoading(tableContainer, "Fetching records...");
    try {
        const data = await safeFetch(`${API_BASE}/api/records`);
        if (!data.length) {
            setEmpty(tableContainer, "No records found.", "Upload a file", openUpload);
            return;
        }
        renderTable(tableContainer, data);
    } catch (e) {
        console.error("[loadData]", e);
        setError(tableContainer, e, loadData);  // pass loadData as retry handler
    }
}
```

---

## 4. Toast Notification System (Vanilla JS)

```javascript
// Add once to index.html: <div id="toast-container" aria-live="polite"></div>

const toaster = (() => {
    const container = document.getElementById("toast-container");
    return {
        show(message, type = "info", duration = 4000) {
            const toast = document.createElement("div");
            toast.className = `toast toast--${type}`;
            toast.textContent = message;
            container.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add("toast--visible"));
            setTimeout(() => {
                toast.classList.remove("toast--visible");
                toast.addEventListener("transitionend", () => toast.remove());
            }, duration);
        },
        success: (msg) => toaster.show(msg, "success"),
        error:   (msg) => toaster.show(msg, "error", 6000),
        warning: (msg) => toaster.show(msg, "warning"),
        info:    (msg) => toaster.show(msg, "info"),
    };
})();

// Usage
toaster.success("File processed successfully");
toaster.error("Failed to connect to server");
```

```css
#toast-container {
    position: fixed;
    bottom: var(--space-6);
    right: var(--space-6);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

.toast {
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    opacity: 0;
    transform: translateY(8px);
    transition: opacity var(--ease-normal), transform var(--ease-normal);
    max-width: 320px;
}

.toast--visible   { opacity: 1; transform: translateY(0); }
.toast--success   { background: var(--color-success-dim); color: var(--color-success); border: 1px solid var(--color-success); }
.toast--error     { background: var(--color-danger-dim);  color: var(--color-danger);  border: 1px solid var(--color-danger); }
.toast--warning   { background: var(--color-warning-dim); color: var(--color-warning); border: 1px solid var(--color-warning); }
.toast--info      { background: var(--color-info-dim);    color: var(--color-info);    border: 1px solid var(--color-info); }
```

---

## 5. Form Error Handling (Vanilla JS)

```javascript
// Show inline field error
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    field.classList.add("input--error");
    let errorEl = field.parentElement.querySelector(".field-error");
    if (!errorEl) {
        errorEl = document.createElement("span");
        errorEl.className = "field-error";
        field.parentElement.appendChild(errorEl);
    }
    errorEl.textContent = message;
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    field.classList.remove("input--error");
    const errorEl = field.parentElement.querySelector(".field-error");
    if (errorEl) errorEl.remove();
}

// Prevent double-submit
function setFormSubmitting(form, isSubmitting) {
    const btn = form.querySelector('[type="submit"]');
    btn.disabled = isSubmitting;
    btn.textContent = isSubmitting ? "Processing..." : btn.dataset.originalText;
    if (!btn.dataset.originalText) btn.dataset.originalText = btn.textContent;
}
```

---

## 6. React ErrorBoundary Component

```jsx
class ErrorBoundary extends React.Component {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        console.error("[ErrorBoundary]", error, info);
    }

    render() {
        if (!this.state.hasError) return this.props.children;
        return (
            <div className="error-boundary">
                <h3>Something went wrong</h3>
                <p className="error-boundary__message">
                    {this.state.error?.message ?? "Unexpected error"}
                </p>
                <button
                    className="btn"
                    onClick={() => this.setState({ hasError: false, error: null })}
                >
                    Try again
                </button>
            </div>
        );
    }
}

// Wrap top-level:
// <ErrorBoundary><App /></ErrorBoundary>
```

---

## 7. Loading Spinner (CSS)

```css
.spinner {
    width: 20px;
    height: 20px;
    border: 2px solid var(--color-border);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation: spin 600ms linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* State containers */
.state-loading,
.state-error,
.state-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--space-3);
    padding: var(--space-12) var(--space-6);
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
    text-align: center;
}

.state-error { color: var(--color-danger); }
.state-error__icon { font-size: 24px; }
.state-error__hint { font-size: var(--font-size-xs); color: var(--color-text-faint); }
```

---

## 8. Skeleton Loader (for table rows)

```css
.skeleton {
    background: linear-gradient(
        90deg,
        var(--color-surface) 25%,
        var(--color-surface-alt) 50%,
        var(--color-surface) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: var(--radius-sm);
    height: 14px;
}

@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
```
