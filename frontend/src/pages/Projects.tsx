import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Plus, Folder, Trash2, ArrowRight } from 'lucide-react';
import Modal from '../components/Modal';

import EmptyState from '../components/EmptyState';

export default function Projects() {
  const { token, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const fetchProjects = async () => {
    try {
      const res = await fetch((import.meta.env.VITE_API_URL || '') + '/api/v1/projects/', {
        headers: { Authorization: `Bearer ${token}` },
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
    setCreating(true);
    try {
      const res = await fetch((import.meta.env.VITE_API_URL || '') + '/api/v1/projects/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newProjectName, description: newProjectDesc }),
      });
      if (res.ok) {
        const p = await res.json();
        setShowModal(false);
        setNewProjectName('');
        setNewProjectDesc('');
        navigate(`/projects/${p.id}`);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (id: number) => {
    setDeleteConfirm(null);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/projects/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchProjects();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <div>
          <h1 style={{ fontSize: '1.375rem', fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>Conductor</span>
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px' }}>API Gateway Developer Portal</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={logout}>
          Sign Out
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Projects</h2>
        <button className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>
          <Plus size={15} /> New Project
        </button>
      </div>

      {loading ? (
        <div className="card">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '12px' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton" style={{ height: '80px', width: '100%', borderRadius: 'var(--radius-md)' }} />
            ))}
          </div>
        </div>
      ) : projects.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={<Folder size={40} />}
            title="No projects yet"
            description="Create a project to start configuring your API gateway services and managing API keys."
            action={
              <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                <Plus size={15} /> Create your first project
              </button>
            }
          />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '12px' }}>
          {projects.map((p) => (
            <div
              key={p.id}
              className="card"
              style={{ cursor: 'pointer', padding: '20px', position: 'relative' }}
              onClick={() => navigate(`/projects/${p.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/projects/${p.id}`); }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: 0 }}>{p.name}</h3>
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteConfirm(p.id); }}
                  className="btn btn-ghost btn-icon btn-sm"
                  title="Delete Project"
                  aria-label={`Delete project ${p.name}`}
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <p style={{ margin: '0 0 14px', color: 'var(--text-muted)', fontSize: '0.8125rem', lineHeight: 1.5 }}>
                {p.description || 'No description'}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                Open <ArrowRight size={12} />
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} title="Create Project">
        <form onSubmit={handleCreateProject}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="proj-name">Project Name</label>
              <input
                id="proj-name"
                type="text"
                className="form-input"
                placeholder="e.g. Production API"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="proj-desc">Description</label>
              <textarea
                id="proj-desc"
                className="form-input form-textarea"
                placeholder="Optional description"
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={creating || !newProjectName}>
              {creating ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={deleteConfirm !== null} onClose={() => setDeleteConfirm(null)} title="Delete Project" maxWidth={420}>
        <div className="modal-body">
          <div className="alert alert-error" style={{ marginBottom: '0' }}>
            This will permanently delete this project and all associated services, analytics, and API keys. This action cannot be undone.
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={() => setDeleteConfirm(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={() => deleteConfirm !== null && handleDeleteProject(deleteConfirm)}>
            <Trash2 size={14} /> Delete Project
          </button>
        </div>
      </Modal>
    </div>
  );
}
