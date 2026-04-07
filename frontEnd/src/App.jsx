import { useState } from 'react';
import { useAppContext } from './context/AppContext';
import { useReport } from './hooks/useReport';
import Header from './components/Header';
import ConfigDrawer from './components/ConfigDrawer';
import ViewerPanel from './components/ViewerPanel/ViewerPanel';
import ReportPanel from './components/ReportPanel/ReportPanel';
import './components/App.css';

export default function App() {
  const { appState, config } = useAppContext();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [status, setStatus] = useState({ type: '', message: 'Ready \u2014 open CONFIG to set up' });
  const { generateReport, isLoading: reportLoading, report, error: reportError } = useReport();

  const getReportImageBase64 = () => {
    if (!appState.dataUrl) return null;

    if (!appState.hasMask || !appState.rawMask || !appState.img) {
      return appState.dataUrl.split(',')[1];
    }

    try {
      const img = appState.img;
      const width = img.naturalWidth || img.width;
      const height = img.naturalHeight || img.height;
      if (!width || !height) return appState.dataUrl.split(',')[1];

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return appState.dataUrl.split(',')[1];

      ctx.drawImage(img, 0, 0, width, height);

      const base = ctx.getImageData(0, 0, width, height);
      const basePx = base.data;
      const mask = appState.rawMask;
      const maskPx = mask.data;

      const rgb = (config.color || '59,130,246').split(',').map((v) => Number(v.trim()));
      const [or, og, ob] = [rgb[0] || 59, rgb[1] || 130, rgb[2] || 246];
      const alpha = 0.45;

      // Blend overlay color where mask is active.
      for (let y = 0; y < height; y++) {
        const my = Math.min(mask.height - 1, Math.floor((y / height) * mask.height));
        for (let x = 0; x < width; x++) {
          const mx = Math.min(mask.width - 1, Math.floor((x / width) * mask.width));
          const mIdx = (my * mask.width + mx) * 4;
          if (maskPx[mIdx] > 127) {
            const i = (y * width + x) * 4;
            basePx[i] = Math.round(basePx[i] * (1 - alpha) + or * alpha);
            basePx[i + 1] = Math.round(basePx[i + 1] * (1 - alpha) + og * alpha);
            basePx[i + 2] = Math.round(basePx[i + 2] * (1 - alpha) + ob * alpha);
          }
        }
      }

      ctx.putImageData(base, 0, 0);
      return canvas.toDataURL('image/png').split(',')[1];
    } catch (_) {
      return appState.dataUrl.split(',')[1];
    }
  };

  const handleGenerateReport = () => {
    const imageBase64 = getReportImageBase64();
    if (!imageBase64) return;
    generateReport(imageBase64, setStatus);
  };

  return (
    <div className="app">
      <Header onToggleDrawer={() => setDrawerOpen(prev => !prev)} />
      <ConfigDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />

      <div className="main">
        <div className="viewer-panel">
          <ViewerPanel setStatus={setStatus} onGenerateReport={handleGenerateReport} />
        </div>
        <div className="report-panel">
          <ReportPanel
            report={report}
            reportLoading={reportLoading}
            reportError={reportError}
            status={status}
          />
        </div>
      </div>
    </div>
  );
}
