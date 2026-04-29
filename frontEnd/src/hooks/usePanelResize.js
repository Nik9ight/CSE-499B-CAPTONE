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
