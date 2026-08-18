import { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { FileText, Copy, Check } from 'lucide-react';

export default function Integration() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);
  const [services, setServices] = useState<any[]>([]);
  const [selectedService, setSelectedService] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/services/?project_id=${projectId}`, {
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
        if (Array.isArray(data)) {
          setServices(data);
          if (data.length > 0) setSelectedService(data[0]);
        }
      })
      .catch(console.error);
  }, [projectId, token]);

  // Determine Gateway Base URL dynamically
  const gatewayHost = import.meta.env.VITE_GATEWAY_URL || window.location.hostname;
  const gatewayPort = import.meta.env.VITE_GATEWAY_PORT || '8000';
  const gatewayScheme = import.meta.env.VITE_GATEWAY_SCHEME || 'http';
  
  const getGatewayUrl = () => {
    if (!selectedService) return '';
    // E.g. http://demo.api.localhost:8000/api/v1/gateway/demo/health
    // Or if production: https://api.conductor.dev/api/v1/gateway/demo/health
    if (gatewayHost === 'localhost' || gatewayHost === '127.0.0.1') {
      return `${gatewayScheme}://${selectedService.service_name}.api.localhost:${gatewayPort}/api/v1/gateway/${selectedService.service_name}`;
    }
    return `${gatewayScheme}://${gatewayHost}/api/v1/gateway/${selectedService.service_name}`;
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (services.length === 0) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '64px' }}>
        <h3>No Services Found</h3>
        <p style={{ color: 'var(--text-secondary)' }}>You must create a service in this project before viewing integration instructions.</p>
      </div>
    );
  }

  const curlCommand = `curl -X GET ${getGatewayUrl()}${selectedService?.health_check_path || '/health'} \\
  -H "Authorization: Bearer <YOUR_API_KEY>"`;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2><FileText size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} /> Integration Guide</h2>
      </div>

      <div style={{ display: 'flex', gap: '32px' }}>
        <div style={{ flex: 2 }}>
          <div className="glass-panel" style={{ marginBottom: '24px' }}>
            <h3 style={{ marginTop: 0 }}>Gateway Request Lifecycle</h3>
            <div style={{ 
              display: 'flex', alignItems: 'center', gap: '8px', 
              padding: '16px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px',
              fontFamily: 'monospace', fontSize: '0.9rem', color: 'var(--accent-primary)',
              overflowX: 'auto', whiteSpace: 'nowrap'
            }}>
              Your App → Conductor → [ Auth → Rate Limit → Circuit Breaker ] → Upstream API
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '16px' }}>
              Conductor intercepts traffic to your upstream service. It applies authentication, rate limits, and resilience policies before safely routing the request downstream.
            </p>
          </div>

          <div className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>Quick Start Example</h3>
              <select 
                className="form-input" 
                value={selectedService?.id || ''} 
                onChange={(e) => setSelectedService(services.find(s => s.id === Number(e.target.value)))}
              >
                {services.map(s => <option key={s.id} value={s.id}>{s.service_name}</option>)}
              </select>
            </div>
            
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '16px' }}>
              Replace <code>&lt;YOUR_API_KEY&gt;</code> with an active API Key generated for this project.
            </p>

            <div style={{ position: 'relative' }}>
              <pre style={{ 
                background: 'rgba(0,0,0,0.5)', padding: '24px 16px', borderRadius: '8px', 
                overflowX: 'auto', color: '#a6e22e', fontFamily: 'monospace', margin: 0,
                border: '1px solid rgba(255,255,255,0.1)'
              }}>
                {curlCommand}
              </pre>
              <button 
                onClick={() => copyCode(curlCommand)}
                style={{ 
                  position: 'absolute', top: '8px', right: '8px', background: 'rgba(255,255,255,0.1)', 
                  border: 'none', color: '#fff', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem'
                }}
              >
                {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            
            {selectedService?.authentication_mode === 'API_KEY_REQUIRED' && (
              <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255,204,0,0.1)', borderLeft: '4px solid var(--warning-color)', borderRadius: '4px' }}>
                <strong style={{ color: 'var(--warning-color)' }}>Note:</strong> This service enforces API Key Authentication. Conductor will validate the key and strip the <code>Authorization</code> header before sending the request to your upstream, ensuring your upstream doesn't need to handle auth logic.
              </div>
            )}
          </div>
        </div>
        
        <div style={{ flex: 1 }}>
          <div className="glass-panel">
            <h3 style={{ marginTop: 0 }}>Service Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.9rem' }}>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Service Name:</span>
                <div style={{ fontWeight: 'bold' }}>{selectedService?.service_name}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Target Upstream:</span>
                <div style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>{selectedService?.base_url}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Auth Mode:</span>
                <div><span className="status-badge" style={{background: 'rgba(255,255,255,0.1)'}}>{selectedService?.authentication_mode}</span></div>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Gateway URL:</span>
                <div style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>{getGatewayUrl()}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
