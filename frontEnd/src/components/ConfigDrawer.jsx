import { useState, useEffect, useRef } from 'react';
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

export default function ConfigDrawer({ open, onClose }) {
  const { config, setConfig } = useAppContext();

  // Local draft state for editing — initialized from config when drawer opens
  const [draft, setDraft] = useState(() => structuredClone(config));
  const lastRowRef = useRef(null);

  useEffect(() => {
    if (open) setDraft(structuredClone(config));
  }, [open, config]);

  /* ── Type list helpers ── */
  function updateType(index, field, value) {
    setDraft(prev => {
      const types = prev.types.map((t, i) =>
        i === index ? { ...t, [field]: value } : t
      );
      // Auto-derive id from label
      if (field === 'label') {
        types[index].id = value.toLowerCase().replace(/\s+/g, '_') || types[index].id;
      }
      return { ...prev, types };
    });
  }

  function setActiveType(id) {
    setDraft(prev => ({ ...prev, activeType: id }));
  }

  function addTypeRow() {
    const newId = 'type_' + Date.now();
    setDraft(prev => ({
      ...prev,
      types: [...prev.types, { id: newId, label: '', endpoint: '' }],
    }));
    // Focus will be handled via ref after render
    lastRowRef.current = true;
  }

  function removeTypeRow(index) {
    setDraft(prev => {
      const types = prev.types.filter((_, i) => i !== index);
      let activeType = prev.activeType;
      if (!types.find(t => t.id === activeType)) {
        activeType = types[0]?.id || '';
      }
      return { ...prev, types, activeType };
    });
  }

  /* ── Save ── */
  function handleSave() {
    setConfig({
      ...draft,
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
        {/* Radiology image types */}
        <div className="dg">
          <label>Radiology image types</label>
          <div>
            {draft.types.map((t, i) => (
              <div className="type-row" key={t.id}>
                <input
                  type="radio"
                  name="activeType"
                  checked={t.id === draft.activeType}
                  onChange={() => setActiveType(t.id)}
                />
                <div className="type-row-fields">
                  <input
                    type="text"
                    value={t.label}
                    placeholder="Label (e.g. Chest X-ray)"
                    onChange={e => updateType(i, 'label', e.target.value)}
                    ref={lastRowRef.current && i === draft.types.length - 1
                      ? el => { if (el) { el.focus(); lastRowRef.current = false; } }
                      : undefined}
                  />
                  <input
                    type="text"
                    value={t.endpoint}
                    placeholder="http://localhost:5000/segment"
                    onChange={e => updateType(i, 'endpoint', e.target.value)}
                  />
                </div>
                <button className="type-del" onClick={() => removeTypeRow(i)} title="Remove">
                  &#10005;
                </button>
              </div>
            ))}
          </div>
          <button className="add-type-btn" onClick={addTypeRow}>+ Add type</button>
          <div className="note">
            Select (&bull;) the active type. Each type has its own endpoint.<br />
            Request: <code>{`{ "image_base64": "..." }`}</code> &rarr; <code>{`{ "mask_base64": "..." }`}</code>
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
