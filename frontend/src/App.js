// src/App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from './context/AuthContext';

import SSLScanner from "./features/sslscanner/SSLScanner";
import Layout from "./layout/Layout";
import AuthPage from "./auth/AuthPage";
import ApiScanner from "./features/apiscanner/ApiScanner";
import NetworkScanner from './features/networkscanner/NetworkScanner';
import WebAppScanner from './features/webappscanner/WebAppScanner';
import domainscannerScanner from './features/domainscanner/DomainScanner';

import HomePage from './features/home/HomePage';

import { ScanProvider } from './context/ScanContext';
import DomainScanner from "./features/domainscanner/DomainScanner";

const App = () => {
  const { isLoggedIn } = useAuth();

  return (
    <ScanProvider>
      <Router>
        <Routes>
          {/* Public Route */}
          <Route 
            path="/"
            element={isLoggedIn ? <Layout><HomePage /></Layout> : <AuthPage />}
          />

          {/* Protected Routes */}
          {isLoggedIn && (
            <>
              <Route path="/networkscanner" element={<Layout><NetworkScanner /></Layout>} />
              <Route path="/webappscanner" element={<Layout><WebAppScanner /></Layout>} />
              <Route path="/domainscanner" element={<Layout><DomainScanner /></Layout>} />
              <Route path="/apiscanner" element={<Layout><ApiScanner /></Layout>} />
              <Route path="/sslscanner" element={<Layout><SSLScanner /></Layout>} /> 
            </>
          )}

          {/* Catch-all Route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ScanProvider>
  );
};

export default App;
