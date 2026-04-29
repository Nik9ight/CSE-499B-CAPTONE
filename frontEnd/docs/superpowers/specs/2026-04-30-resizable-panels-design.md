# Resizable Panels Design

**Date:** 2026-04-30  
**Feature:** Draggable resize divider between ViewerPanel and ReportPanel

---

## Overview

The main layout is currently a fixed 50/50 CSS Grid split. This feature adds a draggable divider between the two panels so users can resize them freely, with the split position persisted to localStorage.

---

## Architecture

A custom hook `usePanelResize` encapsulates drag logic and localStorage persistence. `App.jsx` consumes it and applies the split via an inline `grid-template-columns` style. A `<div className="resize-divider">` is inserted between the two panels in the DOM.

---

## Components

### `src/hooks/usePanelResize.js`

- **Signature:** `usePanelResize(storageKey, defaultPct, minPct)`
- **Parameters:**
  - `storageKey` — localStorage key to persist the split (`"panelSplit"`)
  - `defaultPct` — initial split percentage if no saved value (`50`)
  - `minPct` — minimum percentage for either panel (`20`)
- **Returns:** `{ splitPct, dividerProps }` where `dividerProps = { onMouseDown }`
- **Behavior:**
  - Reads initial value from localStorage on mount (falls back to `defaultPct`)
  - On `mousedown`, attaches `mousemove` and `mouseup` to `window`
  - On `mousemove`, computes `newPct = (e.clientX / window.innerWidth) * 100`, clamps to `[minPct, 100 - minPct]`, updates state
  - On `mouseup`, removes listeners and writes the final value to localStorage
  - Applies `user-select: none` to `document.body` during drag, removes it on `mouseup`
  - Cleans up listeners in a `useEffect` return on unmount

### `App.jsx` changes

- Import and call `usePanelResize("panelSplit", 50, 20)`
- Apply `style={{ gridTemplateColumns: `${splitPct}fr ${100 - splitPct}fr` }}` to `.main`
- Insert `<div className="resize-divider" {...dividerProps} />` between `.viewer-panel` and `.report-panel`

### `App.css` changes

- Remove `border-right: 1px solid var(--border)` from `.viewer-panel` (divider replaces it)
- Add `.resize-divider` styles:
  - `width: 4px`
  - `cursor: col-resize`
  - `background: var(--border)`
  - `flex-shrink: 0`
  - Hover state: slightly brighter/highlighted color for discoverability

---

## Constraints

| Constraint | Value |
|---|---|
| Minimum panel width | 20% of viewport width |
| Default split | 50 / 50 |
| localStorage key | `"panelSplit"` |
| No external dependencies | Pure React hooks + DOM events |

---

## Error Handling

- If localStorage read fails (e.g., private browsing with storage blocked), fall back silently to `defaultPct`
- Clamp all computed values — no runtime errors possible from out-of-bounds percentages

---

## Testing

- Drag divider left past 20% — should stop at 20%
- Drag divider right past 80% — should stop at 80%
- Refresh page — split should restore to last saved position
- Drag and release — text selection should not occur during drag
