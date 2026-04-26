import React, { useEffect, useRef } from 'react';
import './LandingPage.css';

// Import preset images
import img1 from '../../assets/1.png';
import img2 from '../../assets/2.png';
import img3 from '../../assets/3.jpg';
import img4 from '../../assets/4.jpg';
import img5 from '../../assets/5.png';
import img6 from '../../assets/6.png';

// ---------- Icon system (inline SVG, Lucide-style) ----------
const Icon = ({ name, size = 22, stroke = 1.6 }) => {
  const paths = {
    scan: (
      <>
        <path d="M3 7V5a2 2 0 0 1 2-2h2" />
        <path d="M17 3h2a2 2 0 0 1 2 2v2" />
        <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
        <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
        <line x1="7" y1="12" x2="17" y2="12" />
      </>
    ),
    file: (
      <>
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
        <polyline points="14 3 14 8 19 8" />
        <line x1="9" y1="13" x2="15" y2="13" />
        <line x1="9" y1="17" x2="13" y2="17" />
      </>
    ),
    brain: (
      <>
        <path d="M12 5a3 3 0 0 0-3 3v1a3 3 0 0 0-3 3 3 3 0 0 0 3 3v1a3 3 0 0 0 3 3 3 3 0 0 0 3-3v-1a3 3 0 0 0 3-3 3 3 0 0 0-3-3V8a3 3 0 0 0-3-3z" />
        <path d="M12 5v14" />
        <path d="M9 9h.01M15 9h.01M9 15h.01M15 15h.01" />
      </>
    ),
    layers: (
      <>
        <polygon points="12 2 2 7 12 12 22 7 12 2" />
        <polyline points="2 17 12 22 22 17" />
        <polyline points="2 12 12 17 22 12" />
      </>
    ),
    upload: (
      <>
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </>
    ),
    fileCheck: (
      <>
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
        <polyline points="14 3 14 8 19 8" />
        <polyline points="9 14 11 16 15 12" />
      </>
    ),
    arrow: (
      <>
        <line x1="5" y1="12" x2="19" y2="12" />
        <polyline points="12 5 19 12 12 19" />
      </>
    ),
    play: (
      <>
        <polygon points="6 4 20 12 6 20 6 4" />
      </>
    )
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
};

// ---------- Navbar ----------
const Navbar = ({ onGetStarted }) => (
  <nav className="nav">
    <div className="nav-brand">
      <div className="nav-logo-mark"></div>
      <div className="nav-brand-text">RAD<span className="hl">VISION</span></div>
      <div className="pulse-dot" style={{marginLeft: 8}}></div>
    </div>
    <div className="nav-links">
      <a href="#features" className="nav-link">FEATURES</a>
      <a href="#how" className="nav-link">HOW IT WORKS</a>
      <a href="#presets" className="nav-link">PRESETS</a>
    </div>
    <button className="btn btn-primary nav-cta" onClick={onGetStarted}>
      Get Started <Icon name="arrow" size={14} />
    </button>
  </nav>
);

// ---------- Brain MRI demo (left) + segmented (right) ----------
const BrainScan = ({ segmented }) => (
  <svg viewBox="0 0 400 280" preserveAspectRatio="xMidYMid slice">
    <defs>
      <radialGradient id={`brainGrad-${segmented ? 's' : 'o'}`} cx="50%" cy="50%" r="55%">
        <stop offset="0%" stopColor={segmented ? "#1a3a2e" : "#2a2e38"} />
        <stop offset="60%" stopColor={segmented ? "#0c1f18" : "#15181f"} />
        <stop offset="100%" stopColor="#06080b" />
      </radialGradient>
      <radialGradient id={`tissue-${segmented ? 's' : 'o'}`} cx="50%" cy="45%" r="48%">
        <stop offset="0%" stopColor={segmented ? "#3d6b58" : "#4a4f5b"} stopOpacity="1" />
        <stop offset="70%" stopColor={segmented ? "#1c3a2e" : "#26292f"} stopOpacity="1" />
        <stop offset="100%" stopColor="#0a0c10" stopOpacity="0.7" />
      </radialGradient>
      <filter id="noise">
        <feTurbulence baseFrequency="0.9" numOctaves="2" />
        <feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.08 0" />
        <feComposite operator="in" in2="SourceGraphic" />
      </filter>
      <filter id="softglow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="2" />
      </filter>
    </defs>
    <rect width="400" height="280" fill={`url(#brainGrad-${segmented ? 's' : 'o'})`} />

    {/* Skull outline */}
    <ellipse cx="200" cy="140" rx="130" ry="108" fill="none" stroke={segmented ? "#2a4a3c" : "#2a2e36"} strokeWidth="1.2" opacity="0.8" />
    <ellipse cx="200" cy="140" rx="120" ry="99" fill="none" stroke={segmented ? "#1c3a2e" : "#1e2128"} strokeWidth="0.8" opacity="0.6" />

    {/* Brain tissue base */}
    <ellipse cx="200" cy="140" rx="115" ry="94" fill={`url(#tissue-${segmented ? 's' : 'o'})`} />

    {/* Central fissure */}
    <path d="M 200 55 Q 195 140 200 225" stroke={segmented ? "#0c1f18" : "#0d1015"} strokeWidth="2.5" fill="none" />

    {/* Gyri/sulci (squiggles) */}
    <g stroke={segmented ? "#2f5a48" : "#383c47"} strokeWidth="1" fill="none" opacity="0.75">
      <path d="M 100 90 Q 130 80 150 95 T 190 85" />
      <path d="M 210 85 Q 240 75 265 92 T 300 95" />
      <path d="M 95 130 Q 125 120 150 135 T 188 130" />
      <path d="M 212 130 Q 240 120 270 135 T 305 130" />
      <path d="M 100 170 Q 130 160 152 175 T 190 170" />
      <path d="M 210 172 Q 240 162 270 175 T 302 170" />
      <path d="M 115 205 Q 140 195 160 208 T 190 203" />
      <path d="M 210 205 Q 240 195 265 208 T 290 200" />
    </g>

    {/* Ventricles (dark inside) */}
    <path d="M 175 115 Q 170 140 180 165 L 195 165 Q 192 140 195 115 Z" fill={segmented ? "#06120d" : "#08090d"} opacity="0.9" />
    <path d="M 225 115 Q 230 140 220 165 L 205 165 Q 208 140 205 115 Z" fill={segmented ? "#06120d" : "#08090d"} opacity="0.9" />

    {/* SEGMENTATION overlay */}
    {segmented && (
      <g>
        {/* Cortex / outer ring — teal */}
        <path d="M 200 46 Q 85 46 85 140 Q 85 234 200 234 Q 315 234 315 140 Q 315 46 200 46 Z
                 M 200 60 Q 100 60 100 140 Q 100 220 200 220 Q 300 220 300 140 Q 300 60 200 60 Z"
              fill="#10b981" opacity="0.28" fillRule="evenodd" />

        {/* White matter — green blob */}
        <ellipse cx="200" cy="140" rx="82" ry="64" fill="#00ff88" opacity="0.18" />

        {/* Ventricle highlights — brighter green */}
        <path d="M 175 115 Q 170 140 180 165 L 195 165 Q 192 140 195 115 Z" fill="#00ff88" opacity="0.55" />
        <path d="M 225 115 Q 230 140 220 165 L 205 165 Q 208 140 205 115 Z" fill="#00ff88" opacity="0.55" />

        {/* Focal region / suspected lesion (highlighted) */}
        <circle cx="248" cy="118" r="14" fill="#00ff88" opacity="0.6" filter="url(#softglow)" />
        <circle cx="248" cy="118" r="14" fill="none" stroke="#00ff88" strokeWidth="1.5" strokeDasharray="3 3">
          <animate attributeName="stroke-dashoffset" values="0;-12" dur="1.2s" repeatCount="indefinite" />
        </circle>

        {/* Contour lines */}
        <g fill="none" stroke="#00ff88" strokeWidth="0.8" opacity="0.55">
          <ellipse cx="200" cy="140" rx="112" ry="90" />
          <ellipse cx="200" cy="140" rx="85" ry="66" strokeDasharray="2 3" />
          <ellipse cx="200" cy="140" rx="55" ry="40" />
        </g>

        {/* Label tick */}
        <g fontFamily="JetBrains Mono, monospace" fontSize="7" fill="#00ff88" letterSpacing="1">
          <line x1="262" y1="118" x2="295" y2="98" stroke="#00ff88" strokeWidth="0.6" />
          <text x="297" y="96">ROI · 1.4cm</text>
        </g>
      </g>
    )}

    {/* Crosshair */}
    <g stroke={segmented ? "#00ff88" : "#4a4f5b"} strokeWidth="0.5" opacity="0.4">
      <line x1="0" y1="140" x2="400" y2="140" strokeDasharray="2 4" />
      <line x1="200" y1="0" x2="200" y2="280" strokeDasharray="2 4" />
    </g>

    {/* Frame ticks */}
    <g fontFamily="JetBrains Mono, monospace" fontSize="6" fill={segmented ? "#00ff88" : "#5a606c"} letterSpacing="1">
      <text x="8" y="14" opacity="0.7">T1 · AX · 3.0T</text>
      <text x="322" y="14" opacity="0.7">SL 42/120</text>
      <text x="8" y="272" opacity="0.7">FOV 220</text>
      <text x="338" y="272" opacity="0.7">{segmented ? "SEG" : "RAW"}</text>
    </g>
  </svg>
);

// ---------- Hero ----------
const Hero = ({ onGetStarted }) => (
  <section className="hero">
    <div className="container hero-grid">
      <div>
        <div className="hero-pill">
          <span className="dot"></span>
          AI-POWERED MEDICAL IMAGING
        </div>
        <h1>
          <span className="word">Segment<span className="period">.</span></span>
          <span className="word">Analyze<span className="period">.</span></span>
          <span className="word">Understand<span className="period">.</span></span>
        </h1>
        <p className="hero-sub">
          Upload any medical image — get precise segmentation masks, detailed reports,
          and AI-powered explanations in seconds.
        </p>
        <div className="hero-ctas">
          <button className="btn btn-primary" onClick={onGetStarted}>
            Get Started <Icon name="arrow" size={14} />
          </button>
          <a href="#how" className="btn btn-ghost">
            <Icon name="play" size={12} /> See How It Works
          </a>
        </div>
        <div className="hero-meta">
          <div className="item">
            <div className="num">12</div>
            <div className="lbl">Modalities</div>
          </div>
          <div className="item">
            <div className="num">&lt; 4s</div>
            <div className="lbl">Avg. Inference</div>
          </div>
          <div className="item">
            <div className="num">98.4%</div>
            <div className="lbl">Dice Score</div>
          </div>
        </div>
      </div>

      {/* Demo card */}
      <div className="demo-card">
        <span className="corner tl"></span>
        <span className="corner tr"></span>
        <span className="corner bl"></span>
        <span className="corner br"></span>
        <div className="demo-head">
          <span>● REC · CASE #RV-0421</span>
          <div className="dots"><span></span><span></span><span></span></div>
        </div>
        <div className="demo-stage">
          <div className="demo-half left">
            <BrainScan segmented={false} />
            <div className="demo-label-mini">Original</div>
          </div>
          <div className="demo-divider"></div>
          <div className="demo-half right">
            <BrainScan segmented={true} />
            <div className="demo-label-mini">Segmented</div>
          </div>
        </div>
        <div className="demo-footer">
          <span>ORIGINAL <span className="arrow">→</span> SEGMENTED</span>
          <span>AXIAL · T1 · BRAIN MRI</span>
        </div>
      </div>
    </div>
  </section>
);

// ---------- Scroll reveal helper ----------
const useReveal = (ref) => {
  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.15 });
    const kids = ref.current.querySelectorAll('.reveal, .feature');
    kids.forEach(k => io.observe(k));
    return () => io.disconnect();
  }, []);
};

// ---------- Features ----------
const Features = () => {
  const ref = useRef(null);
  useReveal(ref);
  const items = [
    { icon: 'scan', title: 'Precise Segmentation',
      desc: 'State-of-the-art deep learning models segment anatomical structures with pixel-level accuracy.' },
    { icon: 'file', title: 'Report Generation',
      desc: 'Automatically generate structured medical reports with findings and impressions from segmented images.' },
    { icon: 'brain', title: 'AI Explanations',
      desc: "Don't understand the report? Ask our AI to explain any term, finding, or impression in plain language." },
    { icon: 'layers', title: 'Multi-Modality Support',
      desc: 'Supports X-Ray, MRI, CT, Retinal scans, and more across multiple body regions.' },
  ];
  return (
    <section id="features" ref={ref}>
      <div className="container">
        <div className="section-heading reveal">
          <span className="kicker">// 01 · Capabilities</span>
          <h2>What RadVision Does</h2>
          <div className="bar"></div>
        </div>
        <div className="features-grid">
          {items.map((it, i) => (
            <div className="feature" key={i}>
              <div className="num">0{i+1} / 04</div>
              <div className="feature-icon"><Icon name={it.icon} size={22} /></div>
              <h3>{it.title}</h3>
              <p>{it.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// ---------- How it works ----------
const HowItWorks = () => {
  const ref = useRef(null);
  useReveal(ref);
  return (
    <section id="how" ref={ref} className="compact">
      <div className="container">
        <div className="section-heading reveal">
          <span className="kicker">// 02 · Workflow</span>
          <h2>How It Works</h2>
          <div className="bar"></div>
        </div>
        <div className="steps">
          <div className="step-connector c1"></div>
          <div className="step-connector c2"></div>

          <div className="step reveal">
            <div className="step-circle">
              <Icon name="upload" size={32} stroke={1.4} />
              <div className="step-num">1</div>
            </div>
            <span className="kicker">Step 01</span>
            <h3>Upload</h3>
            <p>Upload your medical image — X-Ray, MRI, CT scan, or retinal image.</p>
          </div>

          <div className="step reveal">
            <div className="step-circle">
              <Icon name="scan" size={32} stroke={1.4} />
              <div className="step-num">2</div>
            </div>
            <span className="kicker">Step 02</span>
            <h3>Segment</h3>
            <p>Our AI model processes the image and generates a precise segmentation mask.</p>
          </div>

          <div className="step reveal">
            <div className="step-circle">
              <Icon name="fileCheck" size={32} stroke={1.4} />
              <div className="step-num">3</div>
            </div>
            <span className="kicker">Step 03</span>
            <h3>Report & Understand</h3>
            <p>Get a detailed report with findings. Ask AI to explain anything you don't understand.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

// ---------- Preset silhouettes ----------
const Silhouette = ({ kind }) => {
  const common = { viewBox: "0 0 220 140", preserveAspectRatio: "xMidYMid meet" };
  const stroke = "#10b981";
  const fill = "rgba(0,255,136,0.08)";
  const faint = "rgba(0,255,136,0.18)";
  const by = {
    brain: (
      <g>
        <path d="M 110 30 Q 70 30 70 65 Q 55 65 55 85 Q 55 105 75 108 Q 80 120 100 120 L 120 120 Q 140 120 145 108 Q 165 105 165 85 Q 165 65 150 65 Q 150 30 110 30 Z"
              fill={fill} stroke={stroke} strokeWidth="1.4" />
        <path d="M 110 40 V 115" stroke={stroke} strokeWidth="1" opacity="0.6" />
        <path d="M 85 55 Q 95 50 105 58" stroke={stroke} strokeWidth="0.9" fill="none" opacity="0.7"/>
        <path d="M 115 55 Q 125 50 135 58" stroke={stroke} strokeWidth="0.9" fill="none" opacity="0.7"/>
        <path d="M 80 80 Q 95 76 108 82" stroke={stroke} strokeWidth="0.9" fill="none" opacity="0.7"/>
        <path d="M 112 80 Q 125 76 140 82" stroke={stroke} strokeWidth="0.9" fill="none" opacity="0.7"/>
        <path d="M 85 100 Q 95 95 105 102" stroke={stroke} strokeWidth="0.9" fill="none" opacity="0.7"/>
        <path d="M 115 100 Q 125 95 135 102" stroke={stroke} strokeWidth="0.9" fill="none" opacity="0.7"/>
      </g>
    ),
    chest: (
      <g>
        {/* Ribcage */}
        <path d="M 60 35 Q 110 25 160 35 L 165 105 Q 110 120 55 105 Z" fill={fill} stroke={stroke} strokeWidth="1.4"/>
        <path d="M 110 30 V 115" stroke={stroke} strokeWidth="1" opacity="0.6" />
        {[45,58,71,84,97].map((y,i) => (
          <g key={i}>
            <path d={`M 62 ${y} Q 110 ${y-4} 158 ${y}`} stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.7"/>
          </g>
        ))}
        {/* Lungs outline */}
        <path d="M 75 50 Q 70 85 90 100" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.5"/>
        <path d="M 145 50 Q 150 85 130 100" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.5"/>
      </g>
    ),
    eye: (
      <g>
        <ellipse cx="110" cy="70" rx="70" ry="32" fill={fill} stroke={stroke} strokeWidth="1.4" />
        <circle cx="110" cy="70" r="22" fill="rgba(0,255,136,0.12)" stroke={stroke} strokeWidth="1.2"/>
        <circle cx="110" cy="70" r="9" fill={stroke} opacity="0.7"/>
        {/* Vessels */}
        <path d="M 50 70 Q 70 55 85 65" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.6"/>
        <path d="M 170 70 Q 150 55 135 65" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.6"/>
        <path d="M 50 75 Q 72 82 88 75" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.6"/>
        <path d="M 170 75 Q 148 82 132 75" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.6"/>
        <circle cx="110" cy="70" r="3" fill="#00ff88"/>
      </g>
    ),
    abdomen: (
      <g>
        <path d="M 55 30 L 165 30 Q 175 70 165 110 L 55 110 Q 45 70 55 30 Z" fill={fill} stroke={stroke} strokeWidth="1.4" />
        {/* Liver */}
        <path d="M 65 50 Q 95 45 115 55 Q 115 75 95 78 Q 75 75 65 65 Z" fill="rgba(0,255,136,0.18)" stroke={stroke} strokeWidth="0.8" opacity="0.9"/>
        {/* Kidney */}
        <ellipse cx="130" cy="62" rx="12" ry="8" fill={faint} stroke={stroke} strokeWidth="0.8"/>
        {/* Spine */}
        <rect x="108" y="30" width="4" height="80" fill="none" stroke={stroke} strokeWidth="0.8" opacity="0.5"/>
        {/* Vessels */}
        <path d="M 110 35 Q 105 70 110 105" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.5"/>
      </g>
    ),
    lung: (
      <g>
        <path d="M 80 35 Q 50 60 60 105 Q 80 115 95 100 Q 95 70 90 35 Z" fill={fill} stroke={stroke} strokeWidth="1.4"/>
        <path d="M 140 35 Q 170 60 160 105 Q 140 115 125 100 Q 125 70 130 35 Z" fill={fill} stroke={stroke} strokeWidth="1.4"/>
        {/* Trachea */}
        <path d="M 110 25 V 60 M 110 60 L 95 75 M 110 60 L 125 75" stroke={stroke} strokeWidth="1.2" fill="none"/>
        {/* Bronchi tree */}
        <path d="M 95 75 Q 85 85 80 100" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.6"/>
        <path d="M 125 75 Q 135 85 140 100" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.6"/>
        <path d="M 85 80 L 75 88 M 90 85 L 78 93" stroke={stroke} strokeWidth="0.7" opacity="0.5"/>
        <path d="M 135 80 L 145 88 M 130 85 L 142 93" stroke={stroke} strokeWidth="0.7" opacity="0.5"/>
      </g>
    ),
    heart: (
      <g>
        <path d="M 110 110 C 60 90 55 55 80 45 C 95 38 108 48 110 60 C 112 48 125 38 140 45 C 165 55 160 90 110 110 Z"
              fill={fill} stroke={stroke} strokeWidth="1.4"/>
        {/* Vessels */}
        <path d="M 110 60 Q 100 48 90 42" stroke={stroke} strokeWidth="1" fill="none" opacity="0.7"/>
        <path d="M 110 60 Q 120 48 130 42" stroke={stroke} strokeWidth="1" fill="none" opacity="0.7"/>
        {/* Chambers hint */}
        <path d="M 110 70 L 110 100" stroke={stroke} strokeWidth="0.8" opacity="0.5"/>
        <path d="M 85 75 Q 110 80 135 75" stroke={stroke} strokeWidth="0.8" fill="none" opacity="0.5"/>
        {/* ECG pulse */}
        <path d="M 40 130 L 70 130 L 78 120 L 86 140 L 94 110 L 102 130 L 180 130"
              stroke="#00ff88" strokeWidth="1.2" fill="none" opacity="0.9">
          <animate attributeName="stroke-dashoffset" from="0" to="40" dur="1.5s" repeatCount="indefinite" />
        </path>
      </g>
    ),
  };
  return (
    <svg {...common}>
      <defs>
        <linearGradient id={`gb-${kind}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#0a0d12" />
          <stop offset="100%" stopColor="#06080b" />
        </linearGradient>
      </defs>
      <rect width="220" height="140" fill={`url(#gb-${kind})`} />
      {/* grid */}
      <g stroke="#152019" strokeWidth="0.5" opacity="0.7">
        {[...Array(10)].map((_,i) => <line key={`v${i}`} x1={22*i} y1="0" x2={22*i} y2="140"/>)}
        {[...Array(7)].map((_,i) => <line key={`h${i}`} x1="0" y1={20*i} x2="220" y2={20*i}/>)}
      </g>
      {by[kind]}
    </svg>
  );
};

// ---------- Presets ----------
const Presets = ({ onSelectPreset }) => {
  const ref = useRef(null);
  useReveal(ref);
  const items = [
    { key: 'brain',   label: 'Brain MRI',    tag: 'MRI',   id: 'RV-001', img: img1 },
    { key: 'chest',   label: 'Chest X-Ray',  tag: 'X-Ray', id: 'RV-002', img: img2 },
    { key: 'eye',     label: 'Retinal Scan', tag: 'OCT',   id: 'RV-003', img: img3 },
    { key: 'abdomen', label: 'CT Abdomen',   tag: 'CT',    id: 'RV-004', img: img4 },
    { key: 'lung',    label: 'Lung CT',      tag: 'CT',    id: 'RV-005', img: img5 },
    { key: 'heart',   label: 'Cardiac MRI',  tag: 'MRI',   id: 'RV-006', img: img6 },
  ];
  return (
    <section id="presets" ref={ref}>
      <div className="container">
        <div className="preset-head">
          <div className="section-heading reveal">
            <span className="kicker">// 03 · Sample Cases</span>
            <h2>Try a Sample</h2>
            <div className="bar"></div>
          </div>
          <p className="reveal">Click any preset to jump straight into the app with the image pre-loaded.</p>
        </div>
        <div className="preset-grid">
          {items.map((p) => (
            <div className="preset reveal" key={p.key}
                 onClick={() => onSelectPreset(p.img, p.label)}>
              <div className="preset-id">{p.id}</div>
              <div className="preset-image">
                <img src={p.img} alt={p.label} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              <div className="preset-foot">
                <div className="preset-title">{p.label}</div>
                <div className="preset-tag">{p.tag}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// ---------- Footer ----------
const Footer = ({ onGetStarted }) => (
  <footer>
    <div className="container footer-grid">
      <div className="footer-brand">
        RAD<span style={{color: 'var(--neon)'}}>VISION</span>
        <span className="copy">© 2026. AI-powered medical image analysis.</span>
      </div>
      <div className="footer-links">
        <a href="#">Privacy</a>
        <a href="#">Terms</a>
        <a href="#">Contact</a>
      </div>
      <button className="footer-cta" onClick={onGetStarted} style={{background: 'none', border: 'none', cursor: 'pointer'}}>Ready to start? →</button>
    </div>
  </footer>
);

// ---------- Main Component ----------
const LandingPage = ({ onGetStarted, onSelectPreset }) => {
  return (
    <div className="landing-page-root">
      <div className="bg-atmos"></div>
      <div className="bg-dots"></div>
      <div className="bg-scan"></div>
      <div id="landing-app">
        <Navbar onGetStarted={onGetStarted} />
        <Hero onGetStarted={onGetStarted} />
        <Features />
        <HowItWorks />
        <Presets onSelectPreset={onSelectPreset} />
        <Footer onGetStarted={onGetStarted} />
      </div>
    </div>
  );
};

export default LandingPage;
