import React, { useState } from 'react';
import { loginUser } from '../services/auth';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const AuthForm = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await loginUser({
        username: formData.username,
        password: formData.password,
      });
      const { access, refresh } = res.data;
      login(access, refresh);
      navigate('/home');
    } catch (err) {
      setMessage('❌ ' + (err.response?.data?.detail || 'Something went wrong'));
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h1 class ="anan">Log In</h1>

      <input type="text" name="username" placeholder="Username" onChange={handleChange} required />
      <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
      <button type="submit" className="auth-btn" disabled={loading}>
        {loading ? 'Loading...' : 'Login'}
      </button>
      {message && <p className="auth-message">{message}</p>}
    </form>
  );
};

export default AuthForm;
