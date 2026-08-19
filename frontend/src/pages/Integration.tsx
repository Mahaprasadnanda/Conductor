import { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../App';
import { Copy, Check, FileText, ArrowRight } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';

export default function Integration() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);
  const [services, setServices] = useState<any[]>([]);
  const [selectedService, setSelectedService] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/services/?project_id=${projectId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setServices(data);
          if (data.length > 0) setSelectedService(data[0]);
        }
      })
      .catch(console.error);
  }, [projectId, token, logout]);

  const gatewayHost = import.meta.env.VITE_GATEWAY_URL || window.location.hostname;
  const gatewayPort = import.meta.env.VITE_GATEWAY_PORT || '8000';
  const gatewayScheme = import.meta.env.VITE_GATEWAY_SCHEME || 'http';

  const getGatewayUrl = () => {
    if (!selectedService) return '';
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
      <div>
        <PageHeader title="Integration" icon={<FileText size={24} />} description="Connect your applications to the Conductor gateway." />
        <div className="card">
          <EmptyState
            title="No services configured"
            description="Create a service first to view integration instructions and example requests."
          />
        </div>
      </div>
    );
  }

  const curlCommand = `curl -X GET ${getGatewayUrl()}${selectedService?.health_check_path || '/health'} \\
  -H "Authorization: Bearer <YOUR_API_KEY>"`;

  return (
    <div>
      <PageHeader title="Integration" icon={<FileText size={24} />} description="Connect your applications to the Conductor gateway." />

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px', alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Request Lifecycle */}
          <div className="card">
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 14px' }}>Gateway Request Lifecycle</h3>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap',
              padding: '14px 16px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem',
            }}>
              <span style={{ color: 'var(--text-secondary)' }}>Your App</span>
              <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
              <span style={{ color: 'var(--accent)' }}>Conductor</span>
              <span style={{ color: 'var(--text-muted)' }}>[ Auth &middot; Rate Limit &middot; Circuit Breaker ]</span>
              <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Upstream API</span>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '12px 0 0', lineHeight: 1.6 }}>
              Conductor intercepts traffic to your upstream service, applies authentication, rate limits, and resilience policies, then safely routes the request downstream.
            </p>
          </div>

          {/* Quick Start */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: 0 }}>Quick Start</h3>
              <select
                className="form-input form-select"
                value={selectedService?.id || ''}
                onChange={(e) => setSelectedService(services.find((s) => s.id === Number(e.target.value)))}
                style={{ width: 'auto', minWidth: '150px', padding: '6px 32px 6px 10px', fontSize: '0.8125rem' }}
              >
                {services.map((s) => (
                  <option key={s.id} value={s.id}>{s.service_name}</option>
                ))}
              </select>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0 0 14px' }}>
              Replace <code style={{ padding: '1px 5px', background: 'var(--bg-elevated)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>&lt;YOUR_API_KEY&gt;</code> with an active API key for this project.
            </p>
            <div className="code-block">
              <div className="code-block-header">
                <span className="code-block-label">cURL</span>
                <button className="btn btn-ghost btn-sm" onClick={() => copyCode(curlCommand)} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
                  {copied ? <Check size={13} /> : <Copy size={13} />} {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <pre>{curlCommand}</pre>
            </div>
            {selectedService?.authentication_mode === 'API_KEY_REQUIRED' && (
              <div className="alert alert-warning" style={{ marginTop: '14px' }}>
                <span style={{ fontSize: '0.8125rem' }}>
                  This service enforces API Key authentication. Conductor validates the key and strips the <code>Authorization</code> header before forwarding to your upstream.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Service Details Sidebar */}
        <div className="card" style={{ position: 'sticky', top: '20px' }}>
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0 0 16px' }}>Service Details</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Name</span>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', marginTop: '4px' }}>{selectedService?.service_name}</div>
            </div>
            <div>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Target Upstream</span>
              <div className="mono text-sm" style={{ marginTop: '4px', wordBreak: 'break-all' }}>{selectedService?.base_url}</div>
            </div>
            <div>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Auth Mode</span>
              <div style={{ marginTop: '4px' }}>
                <span className="badge badge-neutral">{selectedService?.authentication_mode}</span>
              </div>
            </div>
            <div>
              <span className="text-xs text-muted" style={{ textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Gateway URL</span>
              <div className="mono text-sm" style={{ marginTop: '4px', wordBreak: 'break-all', color: 'var(--accent)' }}>{getGatewayUrl()}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
