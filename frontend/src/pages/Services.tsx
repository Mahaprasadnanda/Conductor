import React, { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { Plus, Server, Trash2, Edit2, Play, Pause } from 'lucide-react';

export default function Services() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentServiceId, setCurrentServiceId] = useState<number | null>(null);
  const [newServiceName, setNewServiceName] = useState('');
  const [newBaseUrl, setNewBaseUrl] = useState('');
  const [newHealthCheckPath, setNewHealthCheckPath] = useState('/health');
  const [newAuthMode, setNewAuthMode] = useState('API_KEY_REQUIRED');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchServices = async () => {
    try {
      const res = await fetch(`/api/v1/services/?project_id=${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.ok) {
        setServices(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, [projectId, token]);

  const handleDeleteService = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this service?")) return;
    
    try {
      const res = await fetch(`/api/v1/services/${id}?project_id=${projectId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchServices();
      } else {
        alert("Failed to delete service.");
      }
    } catch (err) {
      console.error(err);
      alert("Error deleting service.");
    }
  };

  const handleToggleStatus = async (service: any, e: React.MouseEvent) => {
    e.stopPropagation();
    const newStatus = service.status === 'Disabled' ? 'Unknown' : 'Disabled';
    
    try {
      const res = await fetch(`/api/v1/services/${service.id}?project_id=${projectId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          status: newStatus
        })
      });
      if (res.ok) {
        fetchServices();
      } else {
        alert(`Failed to ${newStatus === 'Disabled' ? 'disable' : 'enable'} service.`);
      }
    } catch (err) {
      console.error(err);
      alert("Error updating service status.");
    }
  };

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newServiceName || !newBaseUrl) return;
    try {
      const res = await fetch(`/api/v1/services/?project_id=${projectId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          service_name: newServiceName, 
          base_url: newBaseUrl,
          health_check_path: newHealthCheckPath,
          authentication_mode: newAuthMode
        })
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.ok) {
        setShowModal(false);
        setNewServiceName('');
        setNewBaseUrl('');
        setNewHealthCheckPath('/health');
        setErrorMsg('');
        fetchServices();
      } else {
        const errorData = await res.json();
        setErrorMsg(errorData.detail || 'Failed to create service');
      }
    } catch (e) {
      console.error(e);
    }
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
    try {
      const res = await fetch(`/api/v1/services/${currentServiceId}?project_id=${projectId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          base_url: newBaseUrl,
          health_check_path: newHealthCheckPath,
          authentication_mode: newAuthMode
        })
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.ok) {
        setShowEditModal(false);
        fetchServices();
      } else {
        const errorData = await res.json();
        setErrorMsg(errorData.detail || 'Failed to update service');
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2><Server size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} /> Services</h2>
        <button className="btn-primary" onClick={() => {
            setNewServiceName('');
            setNewBaseUrl('');
            setNewHealthCheckPath('/health');
            setNewAuthMode('API_KEY_REQUIRED');
            setErrorMsg('');
            setShowModal(true);
        }} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus size={16} /> Add Service
        </button>
      </div>

      <div className="glass-panel" style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Upstream Base URL</th>
              <th>Health Check</th>
              <th>Auth Mode</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {services.map(s => (
              <tr key={s.id} style={{ opacity: s.status === 'Disabled' ? 0.6 : 1 }}>
                <td><strong>{s.service_name}</strong></td>
                <td style={{fontFamily: 'monospace'}}>{s.base_url}</td>
                <td style={{fontFamily: 'monospace', color: 'var(--text-secondary)'}}>{s.health_check_path || '/health'}</td>
                <td><span className="status-badge" style={{background: 'rgba(255,255,255,0.1)'}}>{s.authentication_mode}</span></td>
                <td>
                  <span className={`status-badge ${s.status === 'Healthy' ? 'status-success' : s.status === 'Disabled' ? '' : s.status === 'Unknown' ? '' : 'status-error'}`}>
                    {s.status}
                  </span>
                </td>
                <td>{new Date(s.created_at).toLocaleDateString()}</td>
                <td>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                      onClick={(e) => handleToggleStatus(s, e)}
                      style={{ 
                        background: 'rgba(255,255,255,0.1)', 
                        border: '1px solid rgba(255,255,255,0.2)', 
                        cursor: 'pointer', 
                        color: 'white',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s',
                        fontWeight: 'bold',
                        fontSize: '0.8rem'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
                      title={s.status === 'Disabled' ? "Enable Service" : "Disable Service"}
                    >
                      {s.status === 'Disabled' ? <Play size={14} /> : <Pause size={14} />} 
                      {s.status === 'Disabled' ? "Enable" : "Disable"}
                    </button>
                    <button 
                      onClick={() => openEditModal(s)}
                      style={{ 
                        background: 'rgba(255,255,255,0.1)', 
                        border: '1px solid rgba(255,255,255,0.2)', 
                        cursor: 'pointer', 
                        color: 'white',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s',
                        fontWeight: 'bold',
                        fontSize: '0.8rem'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
                      title="Edit Service"
                    >
                      <Edit2 size={14} /> Edit
                    </button>
                    <button 
                      onClick={(e) => handleDeleteService(s.id, e)}
                      style={{ 
                        background: 'rgba(255,0,0,0.1)', 
                        border: '1px solid rgba(255,0,0,0.2)', 
                        cursor: 'pointer', 
                        color: 'var(--error-color)',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s',
                        fontWeight: 'bold',
                        fontSize: '0.8rem'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--error-color)'; e.currentTarget.style.color = 'white'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,0,0,0.1)'; e.currentTarget.style.color = 'var(--error-color)'; }}
                      title="Delete Service"
                    >
                      <Trash2 size={14} /> Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!loading && services.length === 0 && (
              <tr><td colSpan={7} style={{textAlign: 'center', opacity: 0.5}}>No services defined for this project.</td></tr>
            )}
            {loading && (
              <tr><td colSpan={7} style={{textAlign: 'center'}}>Loading...</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {(showModal || showEditModal) && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '24px' }}>
              {showEditModal ? 'Edit Upstream Service' : 'Add Upstream Service'}
            </h3>
            {errorMsg && (
              <div style={{ background: 'var(--error-color)', padding: '12px', borderRadius: '4px', marginBottom: '16px', color: 'white' }}>
                {errorMsg}
              </div>
            )}
            <form onSubmit={showEditModal ? handleEditService : handleCreateService} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Service Name (used for routing)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. demo" 
                  value={newServiceName} 
                  onChange={e => setNewServiceName(e.target.value)} 
                  required
                  disabled={showEditModal}
                  style={{ opacity: showEditModal ? 0.6 : 1 }}
                />
                {showEditModal && <span style={{fontSize: '0.75rem', color: 'var(--text-secondary)'}}>Service name is immutable to ensure routing consistency.</span>}
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Upstream Base URL</label>
                <input 
                  type="url" 
                  className="form-input" 
                  placeholder="e.g. http://host.docker.internal:8001" 
                  value={newBaseUrl} 
                  onChange={e => setNewBaseUrl(e.target.value)} 
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Health Check Path</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. /health" 
                  value={newHealthCheckPath} 
                  onChange={e => setNewHealthCheckPath(e.target.value)} 
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Authentication Mode</label>
                <select className="form-input" value={newAuthMode} onChange={e => setNewAuthMode(e.target.value)}>
                  <option value="API_KEY_REQUIRED">API Key Required (Recommended)</option>
                  <option value="JWT_REQUIRED">JWT Required</option>
                  <option value="PUBLIC">Public (No Auth)</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button type="button" className="btn-primary" style={{ background: 'transparent' }} onClick={() => { setShowModal(false); setShowEditModal(false); setErrorMsg(''); }}>Cancel</button>
                <button type="submit" className="btn-primary">{showEditModal ? 'Save Changes' : 'Create Service'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
