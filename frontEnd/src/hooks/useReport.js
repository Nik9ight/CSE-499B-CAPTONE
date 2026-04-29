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

  // Pull heading-like sentences (e.g. "FINDINGS:", "IMPRESSIONS:") out as section breaks
  const splitHeadings = (sections) => {
    const result = [];
    for (const sec of sections) {
      let cur = { title: sec.title, sentences: [] };
      for (const s of sec.sentences) {
        const hm = s.text.match(/^([A-Za-z][A-Za-z\s]{0,38}):\s*(.*)$/);
        if (hm && hm[1].trim().split(/\s+/).length <= 5) {
          if (cur.sentences.length) result.push(cur);
          cur = { title: hm[1].trim(), sentences: [] };
          const rest = hm[2].trim();
          if (rest) {
            for (const t of rest.split(/(?<=\.)\s+/).map((x) => x.trim()).filter(Boolean))
              cur.sentences.push({ id: `s${sentId++}`, text: t, tag: s.tag });
          }
        } else {
          cur.sentences.push(s);
        }
      }
      if (cur.sentences.length) result.push(cur);
    }
    return result.length ? result : sections;
  };

  // 1. Strip ```json fences
  let cleaned = raw;
  const fence = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) cleaned = fence[1].trim();

  // 2. Try JSON.parse
  try {
    const obj = JSON.parse(cleaned);
    if (obj.sections) return { modality: obj.modality || '', sections: splitHeadings(assignIds(obj.sections)) };
  } catch (_) { /* not JSON */ }

  // 3. Try extracting first { ... }
  const braces = cleaned.match(/\{[\s\S]*\}/);
  if (braces) {
    try {
      const obj = JSON.parse(braces[0]);
      if (obj.sections) return { modality: obj.modality || '', sections: splitHeadings(assignIds(obj.sections)) };
    } catch (_) { /* not valid JSON */ }
  }

  // 4. Fallback: detect headings (word(s) ending with :) and split sentences by period
  const rawLines = raw.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  const sections = [];
  let cur = { title: 'Findings', sentences: [] };

  for (const line of rawLines) {
    const hm = line.match(/^([A-Za-z][A-Za-z\s]{0,38}):\s*(.*)$/);
    if (hm && hm[1].trim().split(/\s+/).length <= 5) {
      if (cur.sentences.length) sections.push(cur);
      cur = { title: hm[1].trim(), sentences: [] };
      const rest = hm[2].trim();
      if (rest) {
        for (const t of rest.split(/(?<=\.)\s+/).map((s) => s.trim()).filter(Boolean))
          cur.sentences.push({ id: `s${sentId++}`, text: t, tag: '' });
      }
    } else {
      for (const t of line.split(/(?<=\.)\s+/).map((s) => s.trim()).filter(Boolean))
        cur.sentences.push({ id: `s${sentId++}`, text: t, tag: '' });
    }
  }
  if (cur.sentences.length) sections.push(cur);
  if (!sections.length) sections.push({ title: 'Findings', sentences: [] });
  return { modality: '', sections };
}

export function useReport() {
  const { config, appState } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [prefetchedReport, setPrefetchedReport] = useState(null);
  const [error, setError] = useState(null);

  const fetchReport = useCallback(async (imageBase64) => {
    setIsLoading(true);
    setError(null);
    setPrefetchedReport(null);

    const base = config.endpoint.replace(/\/+$/, '');
    const filename = appState.file?.name || 'image.png';
    const url = `${base}/report?modality=${encodeURIComponent(config.activeType)}&image_filename=${encodeURIComponent(filename)}`;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: imageBase64 }),
      });

      if (!resp.ok) throw new Error(`Server returned HTTP ${resp.status} ${resp.statusText}`);
      const data = await resp.json();
      if (!data.report) throw new Error('Response missing "report" field');

      const parsed = parseReport(data.report);
      setPrefetchedReport(parsed);
      return parsed;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [config, appState.file]);

  const generateReport = useCallback((setStatus) => {
    if (prefetchedReport) {
      setReport(prefetchedReport);
      setStatus({ type: 'ok', message: 'Report generated \u2014 click any sentence for explanation' });
      return true;
    }
    
    if (isLoading) {
      setStatus({ type: 'ld', message: 'Generating report\u2026' });
      // We need a way to wait for the loading to finish and then show it.
      // For simplicity, we can just poll or use a more complex state.
      // However, if we are already loading, we can just wait for prefetchedReport to be set.
      // But generateReport is called once on click.
      return 'loading';
    }

    if (error) {
      setStatus({ type: 'er', message: 'Report generation failed: ' + error });
      return false;
    }

    setStatus({ type: 'er', message: 'No report available. Please wait or re-upload.' });
    return false;
  }, [prefetchedReport, isLoading, error]);

  const clearReport = useCallback(() => {
    setReport(null);
    setPrefetchedReport(null);
    setError(null);
  }, []);

  return { fetchReport, generateReport, clearReport, isLoading, report, error, prefetchedReport };
}
