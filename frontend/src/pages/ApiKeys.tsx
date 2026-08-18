import React, { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { Key, Plus, AlertTriangle, Copy, Check } from 'lucide-react';

export default function ApiKeys() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);
  
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [newKeyName, setNewKeyName] = useState('');
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchKeys = async () => {
    try {
      const res = await fetch(`/api/v1/api_keys/?project_id=${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (res.ok) {
        setApiKeys(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, [projectId, token]);

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName) return;
    
    try {
      const res = await fetch('/api/v1/api_keys/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newKeyName, project_id: Number(projectId) })
      });
      
      if (res.status === 401) {
        logout();
        return;
      }
      
      if (res.ok) {
        const data = await res.json();
        setRevealedKey(data.raw_key);
        setNewKeyName('');
        setCopied(false);
        fetchKeys();
      }
    } catch (e) {
      console.error(e);
    }
  };
  
  const handleRevokeApiKey = async (id: number) => {
    if (!window.confirm("Are you sure you want to revoke this API key? Active integrations using this key will immediately start failing.")) {
      return;
    }
    try {
      const res = await fetch(`/api/v1/api_keys/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401) {
        logout();
        return;
      }
      fetchKeys();
    } catch (e) {
      console.error(e);
    }
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2><Key size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} /> API Keys</h2>
      </div>

      <p style={{color: 'var(--text-secondary)', marginBottom: '32px'}}>
        Use API keys to authenticate your backend services with the Conductor gateway. Keys are project-scoped and should be kept secure.
      </p>

      {revealedKey && (
        <div style={{padding: '24px', background: 'rgba(46, 204, 113, 0.1)', border: '1px solid var(--success-color)', borderRadius: '8px', marginBottom: '32px'}}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success-color)', marginBottom: '16px' }}>
            <AlertTriangle size={20} /> 
            <h3 style={{ margin: 0 }}>API Key Created Successfully</h3>
          </div>
          <p style={{margin: '0 0 16px 0'}}>
            Please copy this key now and store it securely. <strong>You will not be able to see it again.</strong>
          </p>
          <div style={{display: 'flex', gap: '12px', alignItems: 'center'}}>
            <code style={{padding: '12px 16px', background: 'rgba(0,0,0,0.5)', borderRadius: '4px', flex: 1, fontFamily: 'monospace', fontSize: '1.2rem', color: '#fff', border: '1px solid rgba(255,255,255,0.1)'}}>
              {revealedKey}
            </code>
            <button className="btn-primary" onClick={copyToClipboard} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {copied ? <Check size={16} /> : <Copy size={16} />} {copied ? 'Copied!' : 'Copy'}
            </button>
            <button className="btn-primary" style={{background: 'transparent', border: '1px solid var(--border-color)'}} onClick={() => setRevealedKey(null)}>Done</button>
          </div>
        </div>
      )}

      <div className="glass-panel" style={{ marginBottom: '32px' }}>
        <h3 style={{ margin: '0 0 16px 0' }}>Generate New Key</h3>
        <form onSubmit={handleCreateApiKey} style={{display: 'flex', gap: '12px'}}>
          <input 
            type="text" 
            className="form-input" 
            placeholder="New API Key Name (e.g. Production Gateway)" 
            value={newKeyName} 
            onChange={e => setNewKeyName(e.target.value)} 
            style={{flex: 1}}
            required
          />
          <button type="submit" className="btn-primary" style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
            <Plus size={16} /> Generate Key
          </button>
        </form>
      </div>

      <div className="glass-panel" style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Prefix</th>
              <th>Status</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {apiKeys.map(k => (
              <tr key={k.id}>
                <td><strong>{k.name}</strong></td>
                <td style={{fontFamily: 'monospace'}}>{k.prefix}...</td>
                <td>
                  {k.is_active ? 
                    <span className="status-badge status-success">Active</span> : 
                    <span className="status-badge status-error">Revoked</span>
                  }
                </td>
                <td>{new Date(k.created_at).toLocaleDateString()}</td>
                <td>
                  {k.is_active && (
                    <button onClick={() => handleRevokeApiKey(k.id)} style={{background: 'transparent', border: '1px solid var(--error-color)', color: 'var(--error-color)', borderRadius: '4px', cursor: 'pointer', padding: '6px 12px', fontSize: '0.9rem'}}>
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!loading && apiKeys.length === 0 && (
              <tr><td colSpan={5} style={{textAlign: 'center', opacity: 0.5}}>No API keys found for this project.</td></tr>
            )}
            {loading && (
              <tr><td colSpan={5} style={{textAlign: 'center'}}>Loading...</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
