import { useContext, useEffect, useState, useCallback } from 'react';
import { Outlet, NavLink, useParams, useNavigate, useLocation } from 'react-router-dom';
import { Activity, Server, Key, FileText, ChevronLeft, LogOut, Settings as SettingsIcon, Menu, X } from 'lucide-react';
import { AuthContext } from '../App';

const NAV_ITEMS = [
  { to: 'analytics', label: 'Overview', icon: Activity },
  { to: 'services', label: 'Services', icon: Server },
  { to: 'keys', label: 'API Keys', icon: Key },
  { to: 'integration', label: 'Integration', icon: FileText },
  { to: 'settings', label: 'Settings', icon: SettingsIcon },
];

export default function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { token, logout } = useContext(AuthContext);
  const [projectName, setProjectName] = useState('Loading...');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchProject = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.ok) {
        const data = await res.json();
        if (data.name) setProjectName(data.name);
      }
    } catch {
      setProjectName('Unknown Project');
    }
  }, [projectId, token, logout]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="app-layout">
      {sidebarOpen && <div className="sidebar-overlay visible" onClick={() => setSidebarOpen(false)} />}

      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`} role="navigation" aria-label="Project navigation">
        <div className="sidebar-brand">
          <span className="sidebar-brand-name">Conductor</span>
        </div>

        <div className="sidebar-project">
          <button className="sidebar-project-back" onClick={() => navigate('/projects')}>
            <ChevronLeft size={14} /> All Projects
          </button>
          <div className="sidebar-project-name" title={projectName}>{projectName}</div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Navigation</div>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={`/projects/${projectId}/${item.to}`}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="sidebar-logout" onClick={logout}>
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="content-area">
        <div className="mobile-header">
          <button className="mobile-hamburger" onClick={() => setSidebarOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <span className="mobile-project-name">{projectName}</span>
          {sidebarOpen && (
            <button className="mobile-hamburger" onClick={() => setSidebarOpen(false)} aria-label="Close navigation" style={{ marginLeft: 'auto' }}>
              <X size={20} />
            </button>
          )}
        </div>

        <main className="content-scroll">
          <div className="page-container">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
