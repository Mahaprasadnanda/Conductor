import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Activity, Plus, Folder, Trash2 } from 'lucide-react';

export default function Projects() {
  const { token, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const fetchProjects = async () => {
    try {
      const res = await fetch('/api/v1/projects/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.ok) {
        setProjects(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [token]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName) return;
    try {
      const res = await fetch('/api/v1/projects/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newProjectName, description: newProjectDesc })
      });
      if (res.ok) {
        const p = await res.json();
        setShowModal(false);
        navigate(`/projects/${p.id}`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteProject = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to completely delete this project and all of its associated API keys and services?")) return;
    
    try {
      const res = await fetch(`/api/v1/projects/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchProjects();
      } else {
        alert("Failed to delete project");
      }
    } catch (e) {
      console.error(e);
      alert("Error deleting project");
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '48px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Activity color="var(--accent-primary)" /> Conductor Developer Portal
        </h1>
        <button className="btn-primary" onClick={logout} style={{ background: 'transparent', border: '1px solid var(--border-color)' }}>
          Logout
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>Your Projects</h2>
        <button className="btn-primary" onClick={() => setShowModal(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus size={16} /> Create Project
        </button>
      </div>

      {loading ? (
        <div className="glass-panel">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '64px' }}>
          <Folder size={48} color="var(--text-secondary)" style={{ marginBottom: '16px' }} />
          <h3>No projects yet</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
            Create a project to start configuring your API gateway services and generating keys.
          </p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>Create your first Project</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          {projects.map(p => (
            <div 
              key={p.id} 
              className="glass-panel" 
              style={{ cursor: 'pointer', transition: 'all 0.2s ease', border: '1px solid rgba(255,255,255,0.1)' }}
              onClick={() => navigate(`/projects/${p.id}`)}
              onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
              onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <h3 style={{ margin: 0 }}>{p.name}</h3>
                <button 
                  onClick={(e) => handleDeleteProject(e, p.id)}
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '4px' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = 'red'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
                  title="Delete Project"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {p.description || 'No description provided'}
              </p>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '400px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '24px' }}>Create New Project</h3>
            <form onSubmit={handleCreateProject} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Project Name" 
                value={newProjectName} 
                onChange={e => setNewProjectName(e.target.value)} 
                required
              />
              <textarea 
                className="form-input" 
                placeholder="Description (optional)" 
                value={newProjectDesc} 
                onChange={e => setNewProjectDesc(e.target.value)} 
                rows={3}
              />
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button type="button" className="btn-primary" style={{ background: 'transparent' }} onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
