import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

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
  const [token, setToken] = useState<string | null>(localStorage.getItem('conductor_token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('conductor_token', token);
    } else {
      localStorage.removeItem('conductor_token');
    }
  }, [token]);

  const login = (newToken: string) => setToken(newToken);
  const logout = () => setToken(null);

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      <div className="background-glow"></div>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
