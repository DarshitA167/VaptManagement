// src/contexts/ScanContext.jsx
import React, { createContext, useContext, useState } from "react";

const ScanContext = createContext();

export const ScanProvider = ({ children }) => {
  const [scanRunning, setScanRunning] = useState(false);
  const [scanId, setScanId] = useState(null);

  return (
    <ScanContext.Provider value={{ scanRunning, setScanRunning, scanId, setScanId }}>
      {children}
    </ScanContext.Provider>
  );
};

export const useScan = () => useContext(ScanContext);
