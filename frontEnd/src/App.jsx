import { useState } from 'react';
import { useAppContext } from './context/AppContext';
import Header from './components/Header';
import ConfigDrawer from './components/ConfigDrawer';
import ViewerPanel from './components/ViewerPanel/ViewerPanel';
import ReportPanel from './components/ReportPanel';
import StatusBar from './components/StatusBar';
import './components/App.css';

export default function App() {
  const { config } = useAppContext();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [status, setStatus] = useState({ type: '', message: 'Ready \u2014 open CONFIG to set up' });

  const activeType = config.types?.find(t => t.id === config.activeType);

  const handleGenerateReport = () => {
    // Placeholder — will be implemented in ReportPanel prompt
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
          <div className="cfg-strip">
            SEG API&nbsp;
            <span>{activeType?.endpoint ? activeType.endpoint.replace(/^https?:\/\//, '') : '[ not configured ]'}</span>
            &nbsp;&middot;&nbsp;TYPE&nbsp;
            <span>{activeType?.label || '[ not configured ]'}</span>
            &nbsp;&middot;&nbsp;MODEL&nbsp;
            <span>{config.model ? config.model.replace('google/', '') : '[ not configured ]'}</span>
            {config.modality && (
              <>
                &nbsp;&middot;&nbsp;MODALITY&nbsp;
                <span>{config.modality}</span>
              </>
            )}
          </div>

          <ReportPanel />
          <StatusBar type={status.type} message={status.message} showHint={false} />
        </div>
      </div>
    </div>
  );
}
