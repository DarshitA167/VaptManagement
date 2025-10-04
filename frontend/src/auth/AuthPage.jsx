import React, { useState } from 'react';

import AuthForm from './AuthForm';
import '../styles/auth.css';

const AuthPage = () => {
  const [mode, setMode] = useState('login');

  return (
    <div className="auth-container">
      <h1 className="auth-title">Welcome to <span className="auth-highlight">Trust Grid</span></h1>
      <div className="auth-card">

        <AuthForm mode={mode} />
      </div>
    </div>
  );
};

export default AuthPage;
