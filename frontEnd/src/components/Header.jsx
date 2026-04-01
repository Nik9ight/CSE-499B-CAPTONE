import './Header.css';

export default function Header({ onToggleDrawer }) {
  return (
    <header>
      <div className="logo-mark">Rv</div>
      <div className="logo-text">Rad<span>Vision</span></div>
      <div className="header-right">
        <div className="header-badge">SEGMENTATION + REPORT EXPLAINER</div>
        <button className="cfg-btn" onClick={onToggleDrawer}>
          <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path strokeLinecap="round" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </svg>
          CONFIG
        </button>
      </div>
    </header>
  );
}
