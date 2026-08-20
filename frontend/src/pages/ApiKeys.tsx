import React, { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { Key, Plus, Copy, Check, Trash2 } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';

export default function ApiKeys() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);

  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [newKeyName, setNewKeyName] = useState('');
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [creating, setCreating] = useState(false);
  const [revokeConfirm, setRevokeConfirm] = useState<number | null>(null);

  const fetchKeys = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/api_keys/?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { logout(); return; }
      if (res.ok) setApiKeys(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchKeys(); }, [projectId, token]);

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName) return;
    setCreating(true);
    try {
      const res = await fetch((import.meta.env.VITE_API_URL || '') + '/api/v1/api_keys/', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newKeyName, project_id: Number(projectId) }),
      });
      if (res.status === 401) { logout(); return; }
      if (res.ok) {
        const data = await res.json();
        setRevealedKey(data.raw_key);
        setNewKeyName('');
        setCopied(false);
        fetchKeys();
      }
    } catch (e) { console.error(e); }
    finally { setCreating(false); }
  };

  const handleRevokeApiKey = async (id: number) => {
    setRevokeConfirm(null);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/api_keys/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { logout(); return; }
      if (res.ok) fetchKeys();
    } catch (e) { console.error(e); }
  };

  const copyToClipboard = () => {
    if (revealedKey) {
      navigator.clipboard.writeText(revealedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <PageHeader
        title="API Keys"
        icon={<Key size={24} />}
        description="Manage API keys for authenticating your services with the Conductor gateway."
      />

      {revealedKey && (
        <div className="card" style={{ borderLeft: '3px solid var(--success)', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--success)' }}>API Key Created</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0 0 14px' }}>
            Copy this key now. You will not be able to view it again.
          </p>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <code style={{
              flex: 1, padding: '10px 14px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)', fontSize: '0.9375rem', color: 'var(--text-primary)',
              border: '1px solid var(--border)', overflowX: 'auto', whiteSpace: 'nowrap',
            }}>
              {revealedKey}
            </code>
            <button className="btn btn-primary btn-sm" onClick={copyToClipboard}>
              {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => setRevealedKey(null)}>Done</button>
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-header" style={{ marginBottom: '14px' }}>
          <span className="card-title">Generate New Key</span>
        </div>
        <form onSubmit={handleCreateApiKey} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Key name (e.g. Production Gateway)"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            style={{ flex: 1 }}
            required
          />
          <button type="submit" className="btn btn-primary" disabled={creating || !newKeyName}>
            {creating ? 'Generating...' : <><Plus size={15} /> Generate</>}
          </button>
        </form>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading-container"><div className="loading-spinner" /></div>
        ) : apiKeys.length === 0 ? (
          <EmptyState
            title="No API keys"
            description="Generate an API key to authenticate requests through the Conductor gateway."
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Prefix</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map((k) => (
                  <tr key={k.id}>
                    <td><strong>{k.name}</strong></td>
                    <td className="mono">{k.prefix}...</td>
                    <td>
                      {k.is_active ? (
                        <span className="badge badge-success"><span className="badge-dot" /> Active</span>
                      ) : (
                        <span className="badge badge-error"><span className="badge-dot" /> Revoked</span>
                      )}
                    </td>
                    <td className="text-muted">{new Date(k.created_at).toLocaleDateString()}</td>
                    <td style={{ textAlign: 'right' }}>
                      {k.is_active && (
                        <button onClick={() => setRevokeConfirm(k.id)} className="btn btn-ghost btn-sm" style={{ color: 'var(--error)' }}>
                          <Trash2 size={13} /> Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Revoke Confirmation Modal */}
      <div className="modal-overlay" style={{ display: revokeConfirm === null ? 'none' : 'flex' }} onClick={() => setRevokeConfirm(null)} role="dialog" aria-modal="true" aria-label="Revoke API Key">
        <div className="modal-content" style={{ maxWidth: '420px' }} onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3 className="modal-title">Revoke API Key</h3>
          </div>
          <div className="modal-body">
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
              Active integrations using this key will immediately start failing. This action cannot be undone.
            </p>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setRevokeConfirm(null)}>Cancel</button>
            <button className="btn btn-danger" onClick={() => revokeConfirm !== null && handleRevokeApiKey(revokeConfirm)}>
              <Trash2 size={14} /> Revoke Key
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
