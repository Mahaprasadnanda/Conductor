import { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import { useParams } from 'react-router-dom';
import { 
  Activity, Users, Zap, Shield, AlertTriangle,
  Clock, Server, AlertCircle, Info, CheckCircle
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts';

export default function Dashboard() {
  const { projectId } = useParams<{ projectId: string }>();
  const { token, logout } = useContext(AuthContext);

  const [timeRange, setTimeRange] = useState('1h');
  const [serviceFilter, setServiceFilter] = useState('');
  
  const [overview, setOverview] = useState<any>(null);
  const [timeseries, setTimeseries] = useState<any>(null);
  const [recentRequests, setRecentRequests] = useState<any[]>([]);
  const [recentErrors, setRecentErrors] = useState<any[]>([]);
  const [intelligence, setIntelligence] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [overviewRes, tsRes, reqRes, errRes, intelRes] = await Promise.all([
        fetch(`/api/v1/analytics/overview?project_id=${projectId}`, { headers }),
        fetch(`/api/v1/analytics/timeseries?project_id=${projectId}&time_range=${timeRange}${serviceFilter ? `&service_name=${serviceFilter}` : ''}`, { headers }),
        fetch(`/api/v1/analytics/recent-requests?project_id=${projectId}&limit=10`, { headers }),
        fetch(`/api/v1/analytics/recent-errors?project_id=${projectId}&limit=10`, { headers }),
        fetch(`/api/v1/intelligence/overview?project_id=${projectId}`, { headers })
      ]);
      
      if (
        overviewRes.status === 401 || tsRes.status === 401 ||
        reqRes.status === 401 || errRes.status === 401 || intelRes.status === 401
      ) {
        logout();
        return;
      }
      
      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (tsRes.ok) setTimeseries(await tsRes.json());
      if (reqRes.ok) setRecentRequests(await reqRes.json());
      if (errRes.ok) setRecentErrors(await errRes.json());
      if (intelRes.ok) setIntelligence(await intelRes.json());
      
      setLoading(false);
    } catch (e) {
      console.error('Failed to fetch analytics', e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [timeRange, serviceFilter, token, projectId]);

  const formatTime = (ts: number) => {
    return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading && !overview) {
    return <div className="glass-panel">Loading Analytics...</div>;
  }

  // Combine timeseries data for Recharts
  const chartData = timeseries?.traffic?.map((t: any, index: number) => ({
    time: formatTime(t.timestamp),
    requests: t.value,
    error_rate: timeseries.error_rate?.[index]?.value || 0,
    p50: timeseries.p50_latency?.[index]?.value || 0,
    p95: timeseries.p95_latency?.[index]?.value || 0,
  })) || [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2><Activity size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px', color: 'var(--accent-primary)' }} /> Analytics</h2>
        <div style={{ display: 'flex', gap: '16px' }}>
          <select 
            className="form-input" 
            value={serviceFilter} 
            onChange={e => setServiceFilter(e.target.value)}
          >
            <option value="">All Services</option>
            <option value="demo">Demo Service</option>
          </select>
          
          <select 
            className="form-input" 
            value={timeRange} 
            onChange={e => setTimeRange(e.target.value)}
          >
            <option value="5m">Last 5 Minutes</option>
            <option value="15m">Last 15 Minutes</option>
            <option value="1h">Last 1 Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
          </select>
        </div>
      </div>
      
      <main className="dashboard-layout">
        <div style={{display: 'contents'}}>
        {intelligence && intelligence.status !== 'HEALTHY' && (
          <section className="glass-panel" style={{ borderLeft: intelligence.status === 'CRITICAL' ? '4px solid var(--error-color)' : '4px solid var(--warning-color)', marginBottom: '24px' }}>
            <div className="chart-header" style={{ marginBottom: '16px' }}>
              <div className="chart-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: intelligence.status === 'CRITICAL' ? 'var(--error-color)' : 'var(--warning-color)' }}>
                <AlertCircle size={20} /> AI Traffic Intelligence ({intelligence.active_anomaly_count} Anomalies)
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div>
                <h4 style={{ marginBottom: '12px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Recent Anomalies</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {intelligence.recent_anomalies.map((a: any, i: number) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <strong style={{ color: a.severity === 'CRITICAL' ? 'var(--error-color)' : 'var(--warning-color)' }}>{a.anomaly_type}</strong>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{new Date(a.detected_at).toLocaleTimeString()}</span>
                      </div>
                      <p style={{ fontSize: '0.9rem', margin: '0 0 8px 0' }}>{a.explanation}</p>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Baseline: {a.baseline_value} | Current: {a.current_value} ({a.deviation})
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 style={{ marginBottom: '12px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Recommendations</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {intelligence.recommendations.map((r: any, i: number) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                        <Info size={16} color="var(--accent-primary)" />
                        <strong>{r.title}</strong>
                      </div>
                      <p style={{ fontSize: '0.9rem', margin: '0 0 8px 0', color: 'var(--text-secondary)' }}>{r.evidence}</p>
                      <p style={{ fontSize: '0.9rem', margin: '0', padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
                        💡 {r.recommended_action}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}
        
        {intelligence && intelligence.status === 'HEALTHY' && (
          <section className="glass-panel" style={{ borderLeft: '4px solid var(--success-color)', marginBottom: '24px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success-color)' }}>
              <CheckCircle size={20} />
              <strong>AI Traffic Intelligence: Healthy</strong>
              <span style={{ color: 'var(--text-secondary)', marginLeft: '8px', fontSize: '0.9rem' }}>No anomalies detected. Traffic patterns are normal.</span>
            </div>
          </section>
        )}

        <section className="metrics-grid">
          <div className="glass-panel metric-card">
            <div className="metric-title"><Zap size={16} /> Requests / Sec</div>
            <div className="metric-value">{overview?.requests_per_second || 0}</div>
          </div>
          <div className="glass-panel metric-card">
            <div className="metric-title"><AlertTriangle size={16} /> Error Rate</div>
            <div className="metric-value">
              {overview?.error_rate || 0}<span className="metric-unit">%</span>
            </div>
          </div>
          <div className="glass-panel metric-card">
            <div className="metric-title"><Clock size={16} /> P95 Latency</div>
            <div className="metric-value">
              {((overview?.p95_latency || 0) * 1000).toFixed(1)}<span className="metric-unit">ms</span>
            </div>
          </div>
          <div className="glass-panel metric-card">
            <div className="metric-title"><Users size={16} /> Active Connections</div>
            <div className="metric-value">{overview?.active_connections || 0}</div>
          </div>
          <div className="glass-panel metric-card">
            <div className="metric-title"><Shield size={16} /> Healthy Services</div>
            <div className="metric-value">{overview?.healthy_services || 0}</div>
          </div>
          <div className="glass-panel metric-card">
            <div className="metric-title"><Server size={16} /> Healthy Instances</div>
            <div className="metric-value">{overview?.healthy_instances || 0}</div>
          </div>
        </section>

        <section className="charts-grid">
          <div className="glass-panel">
            <div className="chart-header">
              <div className="chart-title">Traffic Overview</div>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-secondary)" tick={{fontSize: 12}} />
                  <YAxis stroke="var(--text-secondary)" tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px'}} />
                  <Area type="monotone" dataKey="requests" name="Req/s" stroke="var(--accent-primary)" fillOpacity={1} fill="url(#colorRequests)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="glass-panel">
            <div className="chart-header">
              <div className="chart-title">Latency (P50 & P95)</div>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-secondary)" tick={{fontSize: 12}} />
                  <YAxis stroke="var(--text-secondary)" tick={{fontSize: 12}} tickFormatter={v => (Number(v) * 1000).toFixed(0) + 'ms'} />
                  <Tooltip contentStyle={{background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px'}} formatter={(val: any) => (Number(val) * 1000).toFixed(2) + ' ms'} />
                  <Legend />
                  <Line type="monotone" dataKey="p50" name="P50" stroke="var(--success)" dot={false} />
                  <Line type="monotone" dataKey="p95" name="P95" stroke="var(--warning)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* Tables */}
        <section className="charts-grid">
          <div className="glass-panel" style={{ overflowX: 'auto' }}>
            <div className="chart-header">
              <div className="chart-title">Recent Requests</div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Path</th>
                  <th>Status</th>
                  <th>Latency</th>
                  <th>Service</th>
                  <th>Instance</th>
                </tr>
              </thead>
              <tbody>
                {recentRequests.map((req, i) => (
                  <tr key={i}>
                    <td><span className="status-badge" style={{background: 'rgba(255,255,255,0.1)', color: 'white'}}>{req.method}</span></td>
                    <td style={{fontFamily: 'monospace'}}>{req.path}</td>
                    <td>
                      <span className={`status-badge ${req.status_code >= 400 ? 'status-error' : 'status-success'}`}>
                        {req.status_code}
                      </span>
                    </td>
                    <td>{req.latency}</td>
                    <td>{req.service_name}</td>
                    <td style={{fontSize: '0.75rem', color: 'var(--text-secondary)'}}>{req.lb_selected_instance?.substring(0,8) || 'N/A'}</td>
                  </tr>
                ))}
                {recentRequests.length === 0 && (
                  <tr><td colSpan={6} style={{textAlign: 'center', opacity: 0.5}}>No recent requests recorded.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="glass-panel" style={{ overflowX: 'auto' }}>
            <div className="chart-header">
              <div className="chart-title" style={{color: 'var(--error)'}}>Recent Errors</div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Path</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th>Service</th>
                </tr>
              </thead>
              <tbody>
                {recentErrors.map((err, i) => (
                  <tr key={i}>
                    <td><span className="status-badge" style={{background: 'rgba(255,255,255,0.1)', color: 'white'}}>{err.method}</span></td>
                    <td style={{fontFamily: 'monospace'}}>{err.path}</td>
                    <td><span className="status-badge status-error">{err.status_code}</span></td>
                    <td style={{fontSize: '0.75rem'}}>{err.res_failure_reason || err.lb_routing_reason || 'Upstream Error'}</td>
                    <td>{err.service_name}</td>
                  </tr>
                ))}
                {recentErrors.length === 0 && (
                  <tr><td colSpan={5} style={{textAlign: 'center', opacity: 0.5}}>No recent errors recorded. Great job!</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
        </div>
      </main>
    </div>
  );
}
