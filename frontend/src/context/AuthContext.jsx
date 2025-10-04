// ✅ AuthContext.jsx (Fixed and Final)
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('access') || null);
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access'));

  useEffect(() => {
    const storedToken = localStorage.getItem('access');
    setIsLoggedIn(!!storedToken);
    setToken(storedToken);
  }, []);

  const login = (access, refresh) => {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    setToken(access);
    setIsLoggedIn(true);
  };

  const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setToken(null);
    setIsLoggedIn(false);
  };

  return (
    <AuthContext.Provider value={{ token, isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
