import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Settings as SettingsIcon, Trash2, AlertTriangle } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import Modal from '../components/Modal';

export default function Settings() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { token, logout } = useContext(AuthContext);
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/projects/${projectId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
        return res.json();
      })
      .then((data) => { setProject(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [projectId, token, logout]);

  const handleDeleteProject = async () => {
    setDeleting(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/projects/${projectId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        navigate('/projects');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div>
        <PageHeader title="Settings" icon={<SettingsIcon size={24} />} />
        <div className="loading-container"><div className="loading-spinner" /></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div>
        <PageHeader title="Settings" icon={<SettingsIcon size={24} />} />
        <div className="card">
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>Project not found.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Settings" icon={<SettingsIcon size={24} />} description="Manage project configuration and danger zone operations." />

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '640px' }}>
        {/* General */}
        <div className="card">
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 20px', paddingBottom: '12px', borderBottom: '1px solid var(--border)' }}>
            General
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Project Name</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', fontSize: '0.9375rem', fontWeight: 500 }}>
                {project.name}
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', fontSize: '0.875rem', color: project.description ? 'var(--text-secondary)' : 'var(--text-muted)' }}>
                {project.description || 'No description provided.'}
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Project ID</label>
              <div className="mono text-sm" style={{ padding: '10px 14px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                {projectId}
              </div>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="card" style={{ borderColor: 'var(--error-border)' }}>
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 14px', color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} /> Danger Zone
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0 0 16px', lineHeight: 1.5 }}>
            Permanently delete this project and all associated services, analytics data, and API keys. This action cannot be undone.
          </p>
          <button className="btn btn-danger" onClick={() => setShowDeleteModal(true)}>
            <Trash2 size={14} /> Delete Project
          </button>
        </div>
      </div>

      {/* Delete Confirmation */}
      <Modal open={showDeleteModal} onClose={() => setShowDeleteModal(false)} title="Delete Project" maxWidth={440}>
        <div className="modal-body">
          <div className="alert alert-error">
            This will permanently delete this project and all associated services, analytics metrics, and API keys. This action cannot be undone.
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={() => setShowDeleteModal(false)}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDeleteProject} disabled={deleting}>
            <Trash2 size={14} /> {deleting ? 'Deleting...' : 'Delete Project'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
