# Resizable Panels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a draggable divider between ViewerPanel and ReportPanel that persists the split to localStorage.

**Architecture:** A `usePanelResize` hook handles drag events and localStorage I/O. App.jsx inserts a `<div className="resize-divider">` between the two panels and applies the computed split as an inline `grid-template-columns` style (3-column grid: `Xfr 4px Yfr`). App.css is updated to remove the old fixed split and add divider styles.

**Tech Stack:** React 19, Vite, plain CSS custom properties

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/hooks/usePanelResize.js` | Drag logic, clamping, localStorage read/write |
| Modify | `src/App.jsx` | Import hook, add divider element, apply inline grid style |
| Modify | `src/components/App.css` | Remove fixed `grid-template-columns`, add `.resize-divider` styles |

---

### Task 1: Create `usePanelResize` hook

**Files:**
- Create: `src/hooks/usePanelResize.js`

- [ ] **Step 1: Create the file with the full hook implementation**

`src/hooks/usePanelResize.js`:

```js
import { useState, useRef, useCallback } from 'react';

export function usePanelResize(storageKey, defaultPct = 50, minPct = 20) {
  const [splitPct, setSplitPct] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) {
        const n = Number(saved);
        if (n >= minPct && n <= 100 - minPct) return n;
      }
    } catch {}
    return defaultPct;
  });

  const splitPctRef = useRef(splitPct);

  const onMouseDown = useCallback((e) => {
    e.preventDefault();
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev) => {
      const newPct = (ev.clientX / window.innerWidth) * 100;
      const clamped = Math.min(Math.max(newPct, minPct), 100 - minPct);
      splitPctRef.current = clamped;
      setSplitPct(clamped);
    };

    const onMouseUp = () => {
      document.body.style.userSelect = '';
      try {
        localStorage.setItem(storageKey, String(splitPctRef.current));
      } catch {}
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [storageKey, minPct]);

  return { splitPct, dividerProps: { onMouseDown } };
}
```

- [ ] **Step 2: Commit**

```bash
git add src/hooks/usePanelResize.js
git commit -m "feat: add usePanelResize hook"
```

---

### Task 2: Update `App.css`

**Files:**
- Modify: `src/components/App.css`

- [ ] **Step 1: Replace the `.main` and `.viewer-panel` blocks and add `.resize-divider`**

Replace the entire contents of `src/components/App.css` with:

```css
.app {
  display: grid;
  grid-template-rows: 56px 1fr;
  height: 100vh;
  background: var(--bg);
}

.main {
  display: grid;
  overflow: hidden;
  height: calc(100vh - 56px);
}

.viewer-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.report-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.resize-divider {
  width: 4px;
  cursor: col-resize;
  background: var(--border);
  flex-shrink: 0;
  transition: background 0.15s;
}

.resize-divider:hover,
.resize-divider:active {
  background: var(--accent, #6b7280);
}

/* cfg-strip styles moved to ReportPanel/ConfigStrip.css */
```

Note: `grid-template-columns` is removed from `.main` here — it will be set via inline style in App.jsx.
The `border-right` on `.viewer-panel` is removed because the `.resize-divider` replaces it.

- [ ] **Step 2: Commit**

```bash
git add src/components/App.css
git commit -m "feat: add resize-divider styles, remove fixed grid split"
```

---

### Task 3: Wire up `App.jsx`

**Files:**
- Modify: `src/App.jsx`

- [ ] **Step 1: Import `usePanelResize` at the top of `App.jsx`**

Add to the existing imports block (after line 8, before `import './components/App.css'`):

```js
import { usePanelResize } from './hooks/usePanelResize';
```

- [ ] **Step 2: Call the hook inside the `App` component**

Add this line inside the `App` function body, after the existing hook calls (after line 17):

```js
const { splitPct, dividerProps } = usePanelResize('panelSplit', 50, 20);
```

- [ ] **Step 3: Update the `.main` JSX to apply the dynamic grid and insert the divider**

Replace this block in the return statement:

```jsx
      <div className="main">
        <div className="viewer-panel">
          <ViewerPanel setStatus={setStatus} onGenerateReport={handleGenerateReport} />
        </div>
        <div className="report-panel">
          <ReportPanel
            report={report}
            reportLoading={reportLoading && shouldShowReport}
            reportError={reportError}
            status={status}
          />
        </div>
      </div>
```

With:

```jsx
      <div
        className="main"
        style={{ gridTemplateColumns: `${splitPct}fr 4px ${100 - splitPct}fr` }}
      >
        <div className="viewer-panel">
          <ViewerPanel setStatus={setStatus} onGenerateReport={handleGenerateReport} />
        </div>
        <div className="resize-divider" {...dividerProps} />
        <div className="report-panel">
          <ReportPanel
            report={report}
            reportLoading={reportLoading && shouldShowReport}
            reportError={reportError}
            status={status}
          />
        </div>
      </div>
```

- [ ] **Step 4: Start the dev server and manually verify**

```bash
npm run dev
```

Open the app in a browser and verify:

1. The page loads with a 50/50 split (or previously saved split)
2. Hovering over the divider shows `col-resize` cursor and a slightly highlighted divider
3. Dragging left stops at ~20% width for the left panel
4. Dragging right stops at ~20% width for the right panel
5. During drag, no text is selected anywhere on the page
6. After releasing, refresh the page — the split should restore to where you left it
7. Open DevTools → Application → Local Storage → confirm `panelSplit` key is present

- [ ] **Step 5: Commit**

```bash
git add src/App.jsx
git commit -m "feat: wire up resizable panel divider in App"
```
