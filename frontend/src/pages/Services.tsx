import React, { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { Plus, Trash2, Edit2, Play, Pause } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import Modal from '../components/Modal';
import EmptyState from '../components/EmptyState';
import StatusBadge from '../components/StatusBadge';

export default function Services() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [currentServiceId, setCurrentServiceId] = useState<number | null>(null);
  const [newServiceName, setNewServiceName] = useState('');
  const [newBaseUrl, setNewBaseUrl] = useState('');
  const [newHealthCheckPath, setNewHealthCheckPath] = useState('/health');
  const [newAuthMode, setNewAuthMode] = useState('API_KEY_REQUIRED');
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchServices = async () => {
    try {
      const res = await fetch(`/api/v1/services/?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { logout(); return; }
      if (res.ok) setServices(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchServices(); }, [projectId, token]);

  const resetForm = () => {
    setNewServiceName('');
    setNewBaseUrl('');
    setNewHealthCheckPath('/health');
    setNewAuthMode('API_KEY_REQUIRED');
    setErrorMsg('');
  };

  const handleDeleteService = async (id: number) => {
    setDeleteConfirm(null);
    try {
      const res = await fetch(`/api/v1/services/${id}?project_id=${projectId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchServices();
    } catch (e) { console.error(e); }
  };

  const handleToggleStatus = async (service: any, e: React.MouseEvent) => {
    e.stopPropagation();
    const newStatus = service.status === 'Disabled' ? 'Unknown' : 'Disabled';
    try {
      const res = await fetch(`/api/v1/services/${service.id}?project_id=${projectId}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) fetchServices();
    } catch (e) { console.error(e); }
  };

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newServiceName || !newBaseUrl) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/v1/services/?project_id=${projectId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_name: newServiceName,
          base_url: newBaseUrl,
          health_check_path: newHealthCheckPath,
          authentication_mode: newAuthMode,
        }),
      });
      if (res.status === 401) { logout(); return; }
      if (res.ok) {
        setShowCreateModal(false);
        resetForm();
        fetchServices();
      } else {
        const errorData = await res.json();
        setErrorMsg(errorData.detail || 'Failed to create service');
      }
    } catch (e) { console.error(e); }
    finally { setSubmitting(false); }
  };

  const openEditModal = (service: any) => {
    setCurrentServiceId(service.id);
    setNewServiceName(service.service_name);
    setNewBaseUrl(service.base_url);
    setNewHealthCheckPath(service.health_check_path || '/health');
    setNewAuthMode(service.authentication_mode || 'API_KEY_REQUIRED');
    setErrorMsg('');
    setShowEditModal(true);
  };

  const handleEditService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentServiceId || !newBaseUrl) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/v1/services/${currentServiceId}?project_id=${projectId}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_url: newBaseUrl,
          health_check_path: newHealthCheckPath,
          authentication_mode: newAuthMode,
        }),
      });
      if (res.status === 401) { logout(); return; }
      if (res.ok) {
        setShowEditModal(false);
        resetForm();
        fetchServices();
      } else {
        const errorData = await res.json();
        setErrorMsg(errorData.detail || 'Failed to update service');
      }
    } catch (e) { console.error(e); }
    finally { setSubmitting(false); }
  };

  return (
    <div>
      <PageHeader
        title="Services"
        icon={<Play size={24} />}
        description="Manage upstream services connected to your API gateway."
        actions={
          <button className="btn btn-primary" onClick={() => { resetForm(); setShowCreateModal(true); }}>
            <Plus size={15} /> Add Service
          </button>
        }
      />

      <div className="card">
        {loading ? (
          <div className="loading-container"><div className="loading-spinner" /></div>
        ) : services.length === 0 ? (
          <EmptyState
            title="No services configured"
            description="Add an upstream service to start routing traffic through the Conductor gateway."
            action={
              <button className="btn btn-primary" onClick={() => { resetForm(); setShowCreateModal(true); }}>
                <Plus size={15} /> Add your first service
              </button>
            }
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Base URL</th>
                  <th>Health Check</th>
                  <th>Auth Mode</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {services.map((s) => (
                  <tr key={s.id} style={{ opacity: s.status === 'Disabled' ? 0.5 : 1 }}>
                    <td><strong>{s.service_name}</strong></td>
                    <td className="mono">{s.base_url}</td>
                    <td className="mono text-muted">{s.health_check_path || '/health'}</td>
                    <td><span className="badge badge-neutral">{s.authentication_mode}</span></td>
                    <td>
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="text-muted">{new Date(s.created_at).toLocaleDateString()}</td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '4px', justifyContent: 'flex-end' }}>
                        <button
                          onClick={(e) => handleToggleStatus(s, e)}
                          className="btn btn-ghost btn-icon btn-sm"
                          title={s.status === 'Disabled' ? 'Enable Service' : 'Disable Service'}
                        >
                          {s.status === 'Disabled' ? <Play size={14} /> : <Pause size={14} />}
                        </button>
                        <button onClick={() => openEditModal(s)} className="btn btn-ghost btn-icon btn-sm" title="Edit Service">
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => setDeleteConfirm(s.id)} className="btn btn-ghost btn-icon btn-sm" title="Delete Service" style={{ color: 'var(--error)' }}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Add Upstream Service">
        <form onSubmit={handleCreateService}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {errorMsg && <div className="alert alert-error">{errorMsg}</div>}
            <div className="form-group">
              <label className="form-label" htmlFor="svc-name">Service Name</label>
              <input id="svc-name" type="text" className="form-input" placeholder="e.g. my-api" value={newServiceName} onChange={(e) => setNewServiceName(e.target.value)} required autoFocus />
              <span className="form-hint">Used for routing. Must be unique within this project.</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-url">Upstream Base URL</label>
              <input id="svc-url" type="url" className="form-input" placeholder="http://host.docker.internal:8001" value={newBaseUrl} onChange={(e) => setNewBaseUrl(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-health">Health Check Path</label>
              <input id="svc-health" type="text" className="form-input" placeholder="/health" value={newHealthCheckPath} onChange={(e) => setNewHealthCheckPath(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-auth">Authentication Mode</label>
              <select id="svc-auth" className="form-input form-select" value={newAuthMode} onChange={(e) => setNewAuthMode(e.target.value)}>
                <option value="API_KEY_REQUIRED">API Key Required</option>
                <option value="JWT_REQUIRED">JWT Required</option>
                <option value="PUBLIC">Public (No Auth)</option>
              </select>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => { setShowCreateModal(false); setErrorMsg(''); }}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting || !newServiceName || !newBaseUrl}>
              {submitting ? 'Creating...' : 'Create Service'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title="Edit Service">
        <form onSubmit={handleEditService}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {errorMsg && <div className="alert alert-error">{errorMsg}</div>}
            <div className="form-group">
              <label className="form-label" htmlFor="svc-edit-name">Service Name</label>
              <input id="svc-edit-name" type="text" className="form-input" value={newServiceName} disabled style={{ opacity: 0.5 }} />
              <span className="form-hint">Service name is immutable to ensure routing consistency.</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-edit-url">Upstream Base URL</label>
              <input id="svc-edit-url" type="url" className="form-input" value={newBaseUrl} onChange={(e) => setNewBaseUrl(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-edit-health">Health Check Path</label>
              <input id="svc-edit-health" type="text" className="form-input" value={newHealthCheckPath} onChange={(e) => setNewHealthCheckPath(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-edit-auth">Authentication Mode</label>
              <select id="svc-edit-auth" className="form-input form-select" value={newAuthMode} onChange={(e) => setNewAuthMode(e.target.value)}>
                <option value="API_KEY_REQUIRED">API Key Required</option>
                <option value="JWT_REQUIRED">JWT Required</option>
                <option value="PUBLIC">Public (No Auth)</option>
              </select>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => { setShowEditModal(false); setErrorMsg(''); }}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting || !newBaseUrl}>
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={deleteConfirm !== null} onClose={() => setDeleteConfirm(null)} title="Delete Service" maxWidth="420px">
        <div className="modal-body">
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
            Are you sure you want to delete this service? Traffic will no longer be routed to its upstream.
          </p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={() => setDeleteConfirm(null)}>Cancel</button>
          <button className="btn btn-danger" onClick={() => deleteConfirm !== null && handleDeleteService(deleteConfirm)}>
            <Trash2 size={14} /> Delete Service
          </button>
        </div>
      </Modal>
    </div>
  );
}
