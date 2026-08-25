import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectLayout from './layouts/ProjectLayout';
import Services from './pages/Services';
import ApiKeys from './pages/ApiKeys';
import Integration from './pages/Integration';
import Settings from './pages/Settings';

import Home from './pages/Home';

export const AuthContext = React.createContext<{
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
}>({ token: null, login: () => {}, logout: () => {} });

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token } = React.useContext(AuthContext);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

function App() {
  const [token, setToken] = useState<string | null>(() => {
    const storedToken = sessionStorage.getItem('conductor_token');
    if (!storedToken) return null;

    try {
      const payloadBase64 = storedToken.split('.')[1];
      const decodedPayload = JSON.parse(atob(payloadBase64));

      if (decodedPayload.exp && decodedPayload.exp * 1000 < Date.now()) {
        sessionStorage.removeItem('conductor_token');
        return null;
      }
      return storedToken;
    } catch (e) {
      sessionStorage.removeItem('conductor_token');
      return null;
    }
  });

  useEffect(() => {
    if (token) {
      sessionStorage.setItem('conductor_token', token);
    } else {
      sessionStorage.removeItem('conductor_token');
    }
  }, [token]);

  const login = (newToken: string) => setToken(newToken);
  const logout = () => {
    setToken(null);
    sessionStorage.removeItem('conductor_token');
    localStorage.removeItem('conductor_token'); // Clear legacy token if present
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route path="/projects" element={
            <ProtectedRoute>
              <Projects />
            </ProtectedRoute>
          } />

          <Route path="/projects/:projectId" element={
            <ProtectedRoute>
              <ProjectLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="analytics" replace />} />
            <Route path="analytics" element={<Dashboard />} />
            <Route path="services" element={<Services />} />
            <Route path="keys" element={<ApiKeys />} />
            <Route path="integration" element={<Integration />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
