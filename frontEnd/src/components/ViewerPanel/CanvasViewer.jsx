import { useRef, useEffect, useCallback } from 'react';
import { useAppContext } from '../../context/AppContext';
import './CanvasViewer.css';

export default function CanvasViewer({ activeView, opacity }) {
  const { config, appState } = useAppContext();
  const wrapRef = useRef(null);
  const origRef = useRef(null);
  const maskRef = useRef(null);
  const overRef = useRef(null);

  const fit = (img, mw, mh) => {
    const r = Math.min(mw / img.naturalWidth, mh / img.naturalHeight);
    return [Math.round(img.naturalWidth * r), Math.round(img.naturalHeight * r)];
  };

  const paintAll = useCallback(() => {
    const wrap = wrapRef.current;
    const cOrig = origRef.current;
    const cMask = maskRef.current;
    const cOver = overRef.current;
    if (!wrap || !cOrig || !cMask || !cOver || !appState.img) return;

    const [W, H] = fit(appState.img, wrap.clientWidth || 600, wrap.clientHeight || 500);

    // Paint original
    cOrig.width = W;
    cOrig.height = H;
    cOrig.getContext('2d').drawImage(appState.img, 0, 0, W, H);

    // Recolor mask + overlay if mask exists
    if (appState.hasMask && appState.maskImg) {
      const tmp = document.createElement('canvas');
      tmp.width = W;
      tmp.height = H;
      tmp.getContext('2d').drawImage(appState.maskImg, 0, 0, W, H);
      const pix = tmp.getContext('2d').getImageData(0, 0, W, H);
      const [r, g, b] = config.color.split(',').map(Number);

      // Raw mask canvas
      cMask.width = W;
      cMask.height = H;
      cMask.getContext('2d').putImageData(pix, 0, 0);

      // Colored overlay
      cOver.width = W;
      cOver.height = H;
      const vctx = cOver.getContext('2d');
      const vd = vctx.createImageData(W, H);

      for (let i = 0; i < pix.data.length; i += 4) {
        const bright = (pix.data[i] + pix.data[i + 1] + pix.data[i + 2]) / 3;
        if (bright > 128) {
          vd.data[i] = r;
          vd.data[i + 1] = g;
          vd.data[i + 2] = b;
          vd.data[i + 3] = 185;
        }
      }
      vctx.putImageData(vd, 0, 0);
    }
  }, [appState.img, appState.hasMask, appState.maskImg, config.color]);

  // Paint on state changes
  useEffect(() => {
    paintAll();
  }, [paintAll]);

  // Handle container resize
  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;
    const ro = new ResizeObserver(() => paintAll());
    ro.observe(wrap);
    return () => ro.disconnect();
  }, [paintAll]);

  // Canvas visibility
  const showOrig =
    activeView === 'orig' ||
    (activeView === 'mask' && !appState.hasMask) ||
    activeView === 'over';
  const showMask = activeView === 'mask' && appState.hasMask;
  const showOver = activeView === 'over' && appState.hasMask;
  const showLegend = (activeView === 'mask' || activeView === 'over') && appState.hasMask;

  return (
    <div className="canvas-wrap" ref={wrapRef}>
      <canvas ref={origRef} style={{ display: showOrig ? 'block' : 'none' }} />
      <canvas ref={maskRef} style={{ display: showMask ? 'block' : 'none' }} />
      <canvas
        ref={overRef}
        style={{
          display: showOver ? 'block' : 'none',
          pointerEvents: 'none',
          opacity: opacity / 100,
        }}
      />
      {showLegend && (
        <div className="legend">
          <div className="leg-item">
            <div className="leg-dot" style={{ background: `rgba(${config.color},.75)` }} />
            <span>{config.label}</span>
          </div>
        </div>
      )}
    </div>
  );
}
