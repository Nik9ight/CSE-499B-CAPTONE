import { useCallback, useState } from 'react';
import { useAppContext } from '../context/AppContext';

export function useSegmentation() {
  const { config, appState, setAppState } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);

  const runSegmentation = useCallback(
    async (setStatus) => {
      if (!appState.dataUrl) return false;

      if (!config.endpoint) {
        setStatus({ type: 'er', message: 'No endpoint configured \u2014 open CONFIG' });
        return false;
      }

      const activeType = config.types?.find((t) => t.id === config.activeType);
      setIsLoading(true);
      setStatus({ type: 'ld', message: `Calling ${activeType?.label || 'segmentation'} API\u2026` });

      try {
        const base = config.endpoint.replace(/\/+$/, '');
        const url = `${base}/segment?modality=${encodeURIComponent(config.activeType)}`;
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_base64: appState.dataUrl.split(',')[1] }),
        });

        if (!resp.ok) throw new Error(`Server returned HTTP ${resp.status} ${resp.statusText}`);
        const data = await resp.json();
        if (!data.mask_base64) throw new Error('Response missing "mask_base64" field');

        // Decode mask image
        const maskImg = new Image();
        await new Promise((resolve, reject) => {
          maskImg.onload = resolve;
          maskImg.onerror = () => reject(new Error('Invalid mask PNG'));
          maskImg.src = 'data:image/png;base64,' + data.mask_base64;
        });

        // Extract raw ImageData
        const tmp = document.createElement('canvas');
        tmp.width = maskImg.naturalWidth;
        tmp.height = maskImg.naturalHeight;
        tmp.getContext('2d').drawImage(maskImg, 0, 0);
        const rawMask = tmp.getContext('2d').getImageData(0, 0, maskImg.naturalWidth, maskImg.naturalHeight);

        setAppState((prev) => ({ ...prev, hasMask: true, rawMask, maskImg }));
        setStatus({ type: 'ok', message: `Segmentation complete \u2014 ${config.label} mask applied` });
        return true;
      } catch (err) {
        setStatus({ type: 'er', message: 'Segmentation failed: ' + err.message });
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [appState.dataUrl, config, setAppState],
  );

  return { runSegmentation, isLoading };
}
