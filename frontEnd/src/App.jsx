import { useState } from 'react';
import { useAppContext } from './context/AppContext';
import { useReport } from './hooks/useReport';
import Header from './components/Header';
import ConfigDrawer from './components/ConfigDrawer';
import ViewerPanel from './components/ViewerPanel/ViewerPanel';
import ReportPanel from './components/ReportPanel/ReportPanel';
import './components/App.css';

export default function App() {
  const { appState } = useAppContext();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [status, setStatus] = useState({ type: '', message: 'Ready \u2014 open CONFIG to set up' });
  const { generateReport, isLoading: reportLoading, report, error: reportError } = useReport();

  const handleGenerateReport = () => {
    if (!appState.dataUrl) return;
    generateReport(appState.dataUrl.split(',')[1], setStatus);
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
