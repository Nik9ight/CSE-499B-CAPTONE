import { useCallback, useState } from 'react';
import { useAppContext } from '../context/AppContext';

function parseReport(raw) {
  let sentId = 0;
  const assignIds = (sections) =>
    sections.map((sec) => ({
      title: sec.title || 'Findings',
      sentences: (Array.isArray(sec.sentences) ? sec.sentences : [sec.text || '']).flat().map((s) => {
        const text = typeof s === 'string' ? s : s.text || String(s);
        return { id: `s${sentId++}`, text: text.trim(), tag: (typeof s === 'object' && s.tag) || '' };
      }).filter((s) => s.text),
    }));

  // 1. Strip ```json fences
  let cleaned = raw;
  const fence = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) cleaned = fence[1].trim();

  // 2. Try JSON.parse
  try {
    const obj = JSON.parse(cleaned);
    if (obj.sections) return { modality: obj.modality || '', sections: assignIds(obj.sections) };
  } catch (_) { /* not JSON */ }

  // 3. Try extracting first { ... }
  const braces = cleaned.match(/\{[\s\S]*\}/);
  if (braces) {
    try {
      const obj = JSON.parse(braces[0]);
      if (obj.sections) return { modality: obj.modality || '', sections: assignIds(obj.sections) };
    } catch (_) { /* not valid JSON */ }
  }

  // 4. Fallback: split by newlines into single section
  const lines = raw.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  const sentences = lines.map((text) => ({ id: `s${sentId++}`, text, tag: '' }));
  return { modality: '', sections: [{ title: 'Findings', sentences }] };
}

export function useReport() {
  const { config } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const generateReport = useCallback(async (imageBase64, setStatus) => {
    setIsLoading(true);
    setError(null);
    setReport(null);
    setStatus({ type: 'ld', message: 'Generating report\u2026' });

    const base = (config.endpoint || 'http://localhost:5000').replace(/\/+$/, '');
    try {
      const resp = await fetch(`${base}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: imageBase64 }),
      });

      if (!resp.ok) throw new Error(`Server returned HTTP ${resp.status} ${resp.statusText}`);
      const data = await resp.json();
      if (!data.report) throw new Error('Response missing "report" field');

      const parsed = parseReport(data.report);
      setReport(parsed);
      setStatus({ type: 'ok', message: 'Report generated \u2014 click any sentence for explanation' });
      return true;
    } catch (err) {
      setError(err.message);
      setStatus({ type: 'er', message: 'Report generation failed: ' + err.message });
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [config.endpoint]);

  const clearReport = useCallback(() => {
    setReport(null);
    setError(null);
  }, []);

  return { generateReport, clearReport, isLoading, report, error };
}
