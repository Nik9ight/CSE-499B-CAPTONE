import { useState, useEffect } from 'react';
import { useAppContext } from './context/AppContext';
import { useReport } from './hooks/useReport';
import Header from './components/Header';
import ConfigDrawer from './components/ConfigDrawer';
import ViewerPanel from './components/ViewerPanel/ViewerPanel';
import ReportPanel from './components/ReportPanel/ReportPanel';
import LandingPage from './components/LandingPage/LandingPage';
import './components/App.css';

export default function App() {
  const [showApp, setShowApp] = useState(false);
  const { appState, config, setAppState } = useAppContext();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [status, setStatus] = useState({ type: '', message: 'Ready \u2014 open CONFIG to set up' });
  const { fetchReport, generateReport, clearReport, isLoading: reportLoading, report, error: reportError, prefetchedReport } = useReport();
  const [shouldShowReport, setShouldShowReport] = useState(false);

  useEffect(() => {
    if (!showApp) {
      document.body.style.overflow = 'auto';
      document.documentElement.style.overflow = 'auto';
    } else {
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    }
  }, [showApp]);

  // Prefetch report as soon as image is loaded or modality changes
  useEffect(() => {
    if (appState.dataUrl) {
      clearReport();
      const imageBase64 = appState.dataUrl.split(',')[1];
      fetchReport(imageBase64);
      setShouldShowReport(false);
    }
  }, [appState.dataUrl, config.activeType, fetchReport, clearReport]);

  // If user clicked "Generate Report" while it was still loading, show it once ready
  useEffect(() => {
    if (shouldShowReport && prefetchedReport) {
      generateReport(setStatus);
      setShouldShowReport(false);
    }
  }, [shouldShowReport, prefetchedReport, generateReport]);

  const loadPresetImage = (imageUrl, fileName) => {
    const img = new Image();
    img.onload = () => {
      // Create a dummy file object for compatibility
      const file = { name: fileName, size: 0, type: 'image/png' };
      
      // We can use the imageUrl as dataUrl if it's already a base64 or a local path that doesn't violate CORS
      // For local assets in Vite, they are served as paths.
      // To get a dataUrl (which the app seems to expect for some things), we might need to canvas-to-dataurl.
      
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      const dataUrl = canvas.toDataURL('image/png');
      
      setAppState((prev) => ({ 
        ...prev, 
        file, 
        dataUrl, 
        img,
        hasMask: false,
        rawMask: null,
        maskImg: null,
        sentences: [],
        activeSentId: null
      }));
      
      setStatus({
        type: 'ok',
        message: `Loaded Preset: ${fileName} (${img.naturalWidth}\u00d7${img.naturalHeight}px)`,
      });
      setShowApp(true);
    };
    img.src = imageUrl;
  };

  if (!showApp) {
    return <LandingPage onGetStarted={() => setShowApp(true)} onSelectPreset={loadPresetImage} />;
  }

  const handleGenerateReport = () => {
    const res = generateReport(setStatus);
    if (res === 'loading') {
      setShouldShowReport(true);
    }
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
            reportLoading={reportLoading && shouldShowReport}
            reportError={reportError}
            status={status}
          />
        </div>
      </div>
    </div>
  );
}
