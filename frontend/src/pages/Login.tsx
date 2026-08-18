import React, { useState, useContext, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { AuthContext } from '../App';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('registered') === 'true') {
      setSuccessMsg('Account created successfully, please log in.');
    }
  }, [location]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const form = new URLSearchParams();
      form.append('username', username);
      form.append('password', password);

      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString()
      });

      if (!res.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await res.json();
      login(data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="login-container">
      <div className="glass-panel login-card">
        <h1 className="login-title">
          <span className="header-brand">Conductor</span>
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Sign in to Analytics Dashboard</p>
        
        {successMsg && (
          <div className="status-badge status-success" style={{ justifyContent: 'center', padding: '8px', marginBottom: '16px' }}>
            {successMsg}
          </div>
        )}

        {error && (
          <div className="status-badge status-error" style={{ justifyContent: 'center', padding: '8px', marginBottom: '16px' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="form-group">
            <label style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Email Address</label>
            <input 
              type="text" 
              className="form-input" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required 
            />
          </div>
          
          <div className="form-group">
            <label style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Password</label>
            <input 
              type="password" 
              className="form-input" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>
          
          <button type="submit" className="btn-primary" style={{ marginTop: '8px' }}>
            Sign In
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Don't have an account?</span>{' '}
          <Link to="/signup" style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}>Sign up</Link>
        </div>
      </div>
    </div>
  );
}
