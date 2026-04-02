import './ExplainPanel.css';

export default function ExplainPanel({ sentence, explanation, explanationError, isLoading }) {
  return (
    <div className="explain-panel">
      <div className="explain-header">What this means</div>
      <div className="explain-content">
        {!sentence ? (
          <div className="explain-placeholder">
            Click a sentence to see the explanation here.
          </div>
        ) : (
          <div>
            <div className="explain-sentence">{sentence.text}</div>
            {isLoading ? (
              <div className="explain-loading">
                <div className="spinner" />
                Loading explanation&hellip;
              </div>
            ) : explanationError ? (
              <div className="explain-error">{explanationError}</div>
            ) : explanation ? (
              <>
                <div className="explain-text">{explanation}</div>
                {sentence.tag && <div className="explain-tag">{sentence.tag}</div>}
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
