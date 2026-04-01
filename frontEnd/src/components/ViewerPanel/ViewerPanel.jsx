import { useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import { useSegmentation } from '../../hooks/useSegmentation';
import UploadZone from './UploadZone';
import CanvasViewer from './CanvasViewer';
import './ViewerPanel.css';

const VIEWS = [
  { id: 'orig', label: 'Original' },
  { id: 'mask', label: 'Mask' },
  { id: 'over', label: 'Overlay' },
];

export default function ViewerPanel({ setStatus, onGenerateReport }) {
  const { appState, resetAppState } = useAppContext();
  const { runSegmentation, isLoading } = useSegmentation();
  const [activeView, setActiveView] = useState('orig');
  const [opacity, setOpacity] = useState(60);

  const hasImage = !!appState.img;

  const handleViewChange = (view) => {
    setActiveView(view);
    if ((view === 'mask' || view === 'over') && !appState.hasMask) {
      setStatus({ type: 'ok', message: 'Run segmentation first' });
    }
  };

  const handleReset = () => {
    resetAppState();
    setActiveView('orig');
    setOpacity(60);
    setStatus({ type: '', message: 'Ready \u2014 upload a medical image to begin' });
  };

  const handleRunSeg = async () => {
    const success = await runSegmentation(setStatus);
    if (success) setActiveView('mask');
  };

  const showOpacity = activeView === 'over' && appState.hasMask;

  return (
    <>
      <div className="panel-header">
        <div className="panel-title">Image Viewer</div>
        <div className="vtabs">
          {VIEWS.map((v) => (
            <button
              key={v.id}
              className={`vtab${activeView === v.id ? ' active' : ''}`}
              onClick={() => handleViewChange(v.id)}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div className="viewer-body">
        {hasImage ? (
          <CanvasViewer activeView={activeView} opacity={opacity} />
        ) : (
          <UploadZone setStatus={setStatus} />
        )}
      </div>

      <div className={`ov-controls${showOpacity ? ' vis' : ''}`}>
        <label>MASK OPACITY</label>
        <input
          type="range"
          min="0"
          max="100"
          value={opacity}
          onChange={(e) => setOpacity(Number(e.target.value))}
        />
        <label>{opacity}%</label>
      </div>

      <div className="viewer-actions">
        <button className="btn btn-g" disabled={!hasImage} onClick={handleReset}>
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Reset
        </button>
        <button className="btn btn-s" disabled={!hasImage || isLoading} onClick={handleRunSeg}>
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 1-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
          Run Segmentation
        </button>
        <button className="btn btn-p" disabled={!hasImage} onClick={onGenerateReport}>
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
          </svg>
          Generate Report
        </button>
      </div>
    </>
  );
}
