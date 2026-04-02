import { useCallback, useRef, useState } from 'react';
import { useAppContext } from '../context/AppContext';

export function useExplanation() {
  const { config } = useAppContext();
  const cacheRef = useRef({});
  const [isLoading, setIsLoading] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState(null);

  const getExplanation = useCallback(
    async (sentenceText) => {
      setError(null);

      // Check cache
      if (cacheRef.current[sentenceText]) {
        setExplanation(cacheRef.current[sentenceText]);
        return;
      }

      // Check token
      // if (!config.token) {
      //   setExplanation('Add your HuggingFace token in CONFIG to enable AI explanations.');
      //   return;
      // }

      setIsLoading(true);
      setExplanation(null);

      const base = (config.endpoint || 'http://localhost:5000').replace(/\/+$/, '');
      try {
        const resp = await fetch(`${base}/explain`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({sentenceText: sentenceText}),
        });

        if (!resp.ok) throw new Error(`HF API returned ${resp.status}`);
        const data = await resp.json();
        const text = data.explanation || 'No explanation provided.';
        console.log('Explanation response:', text);
        cacheRef.current[sentenceText] = text;
        setExplanation(text);
      } catch (err) {
        setError(err.message);
        setExplanation(null);
      } finally {
        setIsLoading(false);
      }
    },
    [config.endpoint, config.token, config.model],
  );

  const clearExplanation = useCallback(() => {
    setExplanation(null);
    setError(null);
  }, []);

  return { getExplanation, isLoading, explanation, error, clearExplanation };
}
