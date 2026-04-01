import { useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import './UploadZone.css';

export default function UploadZone({ setStatus }) {
  const { setAppState } = useAppContext();
  const [dragOver, setDragOver] = useState(false);

  const loadImage = (file) => {
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      const img = new Image();
      img.onload = () => {
        setAppState((prev) => ({ ...prev, file, dataUrl, img }));
        setStatus({
          type: 'ok',
          message: `Loaded: ${file.name} (${img.naturalWidth}\u00d7${img.naturalHeight}px)`,
        });
      };
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.type.startsWith('image/')) loadImage(file);
  };

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) loadImage(file);
  };

  return (
    <div
      className={`upload-zone${dragOver ? ' dg-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input type="file" accept="image/*" onChange={handleChange} />
      <div className="uicon">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="var(--muted)" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
        </svg>
      </div>
      <div className="ulabel">
        <strong>Upload medical image</strong>
        Drag &amp; drop or click to browse
      </div>
      <div className="ufmt">PNG &middot; JPG &middot; BMP &middot; TIFF</div>
    </div>
  );
}
