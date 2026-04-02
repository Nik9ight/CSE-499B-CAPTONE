import { useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import { useExplanation } from '../../hooks/useExplanation';
import ConfigStrip from './ConfigStrip';
import ReportBody from './ReportBody';
import ExplainPanel from './ExplainPanel';
import StatusBar from '../StatusBar';
import './ReportPanel.css';

export default function ReportPanel({ report, reportLoading, reportError, status }) {
  const { appState, setAppState } = useAppContext();
  const {
    getExplanation,
    isLoading: explainLoading,
    explanation,
    error: explainError,
    clearExplanation,
  } = useExplanation();

  // Clear explanation when active sentence is deselected externally (e.g. reset)
  useEffect(() => {
    if (!appState.activeSentId) clearExplanation();
  }, [appState.activeSentId, clearExplanation]);

  const handleSentenceClick = (sentId, sentText) => {
    if (appState.activeSentId === sentId) {
      // Toggle off
      setAppState((prev) => ({ ...prev, activeSentId: null }));
      clearExplanation();
    } else {
      // Select and explain
      setAppState((prev) => ({ ...prev, activeSentId: sentId }));
      getExplanation(sentText);
    }
  };

  // Find the active sentence object for ExplainPanel
  const activeSentence = report?.sections
    ?.flatMap((s) => s.sentences)
    ?.find((s) => s.id === appState.activeSentId);

  // Show empty state when image is cleared (reset)
  const effectiveReport = appState.img ? report : null;
  const effectiveError = appState.img ? reportError : null;

  return (
    <>
      <div className="panel-header">
        <div className="panel-title">Radiology Report</div>
      </div>
      <ConfigStrip />
      <div className="report-split">
        <ReportBody
          report={effectiveReport}
          reportLoading={reportLoading}
          reportError={effectiveError}
          activeSentId={appState.activeSentId}
          onSentenceClick={handleSentenceClick}
        />
        <ExplainPanel
          sentence={activeSentence}
          explanation={explanation}
          explanationError={explainError}
          isLoading={explainLoading}
        />
      </div>
      <StatusBar
        type={status.type}
        message={status.message}
        showHint={!!effectiveReport && !reportLoading}
      />
    </>
  );
}
