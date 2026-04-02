import { useState, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import './ConfigDrawer.css';

const COLOR_OPTIONS = [
  '59,130,246',
  '248,113,113',
  '16,185,129',
  '251,191,36',
  '167,139,250',
  '251,113,133',
];

const PRECODED_TYPES = [
  { id: 'chest_xray', label: 'Chest X-ray' },
  { id: 'lung_ct', label: 'Lung CT' },
  { id: 'brain_mri', label: 'Brain MRI' },
  { id: 'bone_xray', label: 'Bone X-ray' },
  { id: 'retinal_scan', label: 'Retinal Scan' },
];

export default function ConfigDrawer({ open, onClose }) {
  const { config, setConfig } = useAppContext();

  // Local draft state for editing — initialized from config when drawer opens
  const [draft, setDraft] = useState(() => structuredClone(config));

  useEffect(() => {
    if (open) setDraft(structuredClone(config));
  }, [open, config]);

  /* ── Save ── */
  function handleSave() {
    setConfig({
      ...draft,
      types: PRECODED_TYPES,
      endpoint: draft.endpoint.trim() || 'http://localhost:5000',
      label: draft.label.trim() || 'Segmented region',
      modality: draft.modality.trim(),
      token: draft.token.trim(),
    });
    onClose();
  }

  return (
    <div className={`drawer${open ? ' open' : ''}`}>
      <div className="drawer-head">
        <span>Configuration</span>
        <button className="close-x" onClick={onClose}>
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="drawer-body">
        {/* Radiology image types — pre-coded radio selection */}
        <div className="dg">
          <label>Radiology image type</label>
          <div className="type-radio-list">
            {PRECODED_TYPES.map(t => (
              <label key={t.id} className="type-radio">
                <input
                  type="radio"
                  name="activeType"
                  checked={t.id === draft.activeType}
                  onChange={() => setDraft(prev => ({ ...prev, activeType: t.id }))}
                />
                <span className="type-radio-label">{t.label}</span>
              </label>
            ))}
          </div>
          <div className="note">
            Select the active type. It is passed as <code>?modality=</code> to the API.
          </div>
        </div>

        {/* Server endpoint */}
        <div className="dg">
          <label>Server endpoint</label>
          <input
            type="text"
            value={draft.endpoint}
            placeholder="http://localhost:5000"
            onChange={e => setDraft(prev => ({ ...prev, endpoint: e.target.value }))}
          />
          <div className="note">
            Base URL for segmentation, report, and explanation APIs.<br />
            <code>/segment?modality=...</code> &middot; <code>/report</code> &middot; <code>/explain</code>
          </div>
        </div>

        {/* Mask label */}
        <div className="dg">
          <label>What the mask represents</label>
          <input
            type="text"
            value={draft.label}
            placeholder="e.g. Tumor, Nodule, Lesion, Lung field"
            onChange={e => setDraft(prev => ({ ...prev, label: e.target.value }))}
          />
        </div>

        {/* Color picker */}
        <div className="dg">
          <label>Mask overlay color</label>
          <div className="color-row">
            {COLOR_OPTIONS.map(c => (
              <div
                key={c}
                className={`cpill${c === draft.color ? ' sel' : ''}`}
                style={{ background: `rgba(${c},.75)` }}
                onClick={() => setDraft(prev => ({ ...prev, color: c }))}
              />
            ))}
          </div>
        </div>

        {/* Modality */}
        <div className="dg">
          <label>Imaging modality</label>
          <input
            type="text"
            value={draft.modality}
            placeholder="e.g. Chest X-Ray PA, CT Chest Axial, MRI Brain T2"
            onChange={e => setDraft(prev => ({ ...prev, modality: e.target.value }))}
          />
          <div className="note">Tells MedGemma exactly what it&#39;s analyzing. Leave blank to let the model infer.</div>
        </div>

        <hr className="dsep" />

        {/* HuggingFace token */}
        <div className="dg">
          <label>HuggingFace token</label>
          <input
            type="password"
            value={draft.token}
            placeholder="hf_..."
            onChange={e => setDraft(prev => ({ ...prev, token: e.target.value }))}
          />
          <div className="note">
            Must have access to the MedGemma gated model.<br />
            Request access at <code>huggingface.co/google/medgemma-4b-it</code>
          </div>
        </div>

        {/* Model variant */}
        <div className="dg">
          <label>MedGemma model variant</label>
          <select
            value={draft.model}
            onChange={e => setDraft(prev => ({ ...prev, model: e.target.value }))}
          >
            <option value="google/medgemma-4b-it">medgemma-4b-it (faster, lighter)</option>
            <option value="google/medgemma-27b-it">medgemma-27b-it (higher quality)</option>
          </select>
        </div>

        <hr className="dsep" />
        <button className="save-btn" onClick={handleSave}>Save &amp; close</button>
      </div>
    </div>
  );
}
