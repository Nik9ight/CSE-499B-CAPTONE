import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'rv2';

const defaultConfig = {
  types: [{ id: 'chest_xray', label: 'Chest X-ray', endpoint: 'http://localhost:5000/segment' }],
  activeType: 'chest_xray',
  label: 'Segmented region',
  color: '59,130,246',
  token: '',
  model: 'google/medgemma-4b-it',
  modality: '',
};

const defaultAppState = {
  file: null,
  dataUrl: null,
  img: null,
  hasMask: false,
  rawMask: null,
  maskImg: null,
  sentences: [],
  cache: {},
  activeSentId: null,
};

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [config, setConfig] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return { ...defaultConfig, ...JSON.parse(stored) };
    } catch (_) { /* ignore */ }
    return defaultConfig;
  });

  const [appState, setAppState] = useState(defaultAppState);

  // Persist config to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    } catch (_) { /* ignore */ }
  }, [config]);

  const resetAppState = useCallback(() => {
    setAppState(defaultAppState);
  }, []);

  return (
    <AppContext.Provider value={{ config, setConfig, appState, setAppState, resetAppState }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppProvider');
  return ctx;
}
