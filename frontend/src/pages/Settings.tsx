import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Settings as SettingsIcon, Trash2, AlertTriangle } from 'lucide-react';

export default function Settings() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { token, logout } = useContext(AuthContext);
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
        setProject(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [projectId, token]);

  const handleDeleteProject = async () => {
    if (!window.confirm("DANGER: Are you absolutely sure you want to permanently delete this project? This will destroy all associated services, analytics metrics, and API keys. This action CANNOT be undone.")) {
      return;
    }
    
    try {
      const res = await fetch(`/api/v1/projects/${projectId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        navigate('/projects');
      } else {
        alert("Failed to delete project. Make sure you have the correct permissions.");
      }
    } catch (e) {
      console.error(e);
      alert("Error deleting project.");
    }
  };

  if (loading) {
    return <div className="glass-panel">Loading settings...</div>;
  }

  if (!project) {
    return <div className="glass-panel">Project not found.</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2><SettingsIcon size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px', color: 'var(--text-secondary)' }} /> Project Settings</h2>
      </div>

      <main className="dashboard-layout">
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h3 style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>General Information</h3>
          
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Project Name</label>
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '1.1rem' }}>
              {project.name}
            </div>
          </div>

          <div style={{ marginBottom: '32px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Project Description</label>
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}>
              {project.description || <span style={{ color: 'var(--text-secondary)' }}>No description provided.</span>}
            </div>
          </div>

          <h3 style={{ marginBottom: '24px', color: 'var(--error-color)', borderBottom: '1px solid rgba(255,0,0,0.2)', paddingBottom: '12px' }}>Danger Zone</h3>
          
          <div style={{ border: '1px solid var(--error-color)', borderRadius: '8px', padding: '24px', background: 'rgba(255,0,0,0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} color="var(--error-color)" />
                  Delete Project
                </h4>
                <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Permanently remove this project and all associated services, analytics, and API keys. This cannot be undone.
                </p>
              </div>
              <button 
                onClick={handleDeleteProject}
                style={{ 
                  background: 'var(--error-color)', 
                  color: 'white', 
                  border: 'none', 
                  padding: '10px 16px', 
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#d32f2f'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'var(--error-color)'}
              >
                <Trash2 size={16} /> Delete Project
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
