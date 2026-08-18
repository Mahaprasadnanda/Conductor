import { useContext, useEffect, useState } from 'react';
import { Outlet, NavLink, useParams, useNavigate } from 'react-router-dom';
import { Activity, Server, Key, FileText, ChevronLeft, LogOut, Settings as SettingsIcon } from 'lucide-react';
import { AuthContext } from '../App';

export default function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { token, logout } = useContext(AuthContext);
  const [projectName, setProjectName] = useState<string>('Loading...');

  useEffect(() => {
    fetch(`/api/v1/projects/${projectId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (res.status === 401) {
          logout();
          throw new Error("Unauthorized");
        }
        return res.json();
      })
      .then(data => {
        if (data.name) setProjectName(data.name);
      })
      .catch(() => setProjectName('Unknown Project'));
  }, [projectId, token]);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      {/* Sidebar */}
      <div style={{
        width: '240px', 
        borderRight: '1px solid var(--border-color)', 
        background: 'rgba(0,0,0,0.5)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ padding: '24px 16px', borderBottom: '1px solid var(--border-color)' }}>
          <button 
            onClick={() => navigate('/projects')}
            style={{ 
              background: 'transparent', border: 'none', color: 'var(--text-secondary)',
              display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer',
              marginBottom: '16px', padding: 0
            }}
          >
            <ChevronLeft size={16} /> All Projects
          </button>
          <div style={{ fontWeight: 'bold', fontSize: '1.2rem', color: 'var(--accent-primary)' }}>
            {projectName}
          </div>
        </div>
        
        <nav style={{ padding: '16px 0', flex: 1 }}>
          <NavLink 
            to={`/projects/${projectId}/analytics`}
            className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 24px', color: 'var(--text-secondary)', textDecoration: 'none' }}
          >
            <Activity size={18} /> Analytics
          </NavLink>
          <NavLink 
            to={`/projects/${projectId}/services`}
            className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 24px', color: 'var(--text-secondary)', textDecoration: 'none' }}
          >
            <Server size={18} /> Services
          </NavLink>
          <NavLink 
            to={`/projects/${projectId}/keys`}
            className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 24px', color: 'var(--text-secondary)', textDecoration: 'none' }}
          >
            <Key size={18} /> API Keys
          </NavLink>
          <NavLink 
            to={`/projects/${projectId}/integration`}
            className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 24px', color: 'var(--text-secondary)', textDecoration: 'none' }}
          >
            <FileText size={18} /> Integration
          </NavLink>
          <NavLink 
            to={`/projects/${projectId}/settings`}
            className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 24px', color: 'var(--text-secondary)', textDecoration: 'none' }}
          >
            <SettingsIcon size={18} /> Settings
          </NavLink>
        </nav>

        <div style={{ padding: '16px', borderTop: '1px solid var(--border-color)' }}>
          <button 
            className="btn-primary" 
            onClick={logout} 
            style={{ width: '100%', background: 'transparent', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
        <Outlet />
      </div>
    </div>
  );
}
