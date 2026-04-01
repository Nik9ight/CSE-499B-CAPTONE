import './StatusBar.css';

export default function StatusBar({ type, message, showHint }) {
  return (
    <div className="status-bar">
      <div className={`sdot${type ? ' ' + type : ''}`} />
      <span>{message}</span>
      {showHint && <span className="hint">click any sentence for explanation</span>}
    </div>
  );
}
