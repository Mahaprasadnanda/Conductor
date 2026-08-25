import { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import { useParams } from 'react-router-dom';
import {
  Activity, Users, Zap, Shield, AlertTriangle,
  Clock, Server, AlertCircle, Info, CheckCircle,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts';
import PageHeader from '../components/PageHeader';

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
      const headers = { Authorization: `Bearer ${token}` };

      const [overviewRes, tsRes, reqRes, errRes, intelRes] = await Promise.all([
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/analytics/overview?project_id=${projectId}&time_range=${timeRange}${serviceFilter ? `&service_name=${serviceFilter}` : ''}`, { headers }),
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/analytics/timeseries?project_id=${projectId}&time_range=${timeRange}${serviceFilter ? `&service_name=${serviceFilter}` : ''}`, { headers }),
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/analytics/recent-requests?project_id=${projectId}&limit=10`, { headers }),
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/analytics/recent-errors?project_id=${projectId}&limit=10`, { headers }),
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/intelligence/overview?project_id=${projectId}`, { headers }),
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

  const chartData = timeseries?.traffic?.map((t: any, index: number) => ({
    time: formatTime(t.timestamp),
    requests: t.value,
    error_rate: timeseries.error_rate?.[index]?.value || 0,
    p50: timeseries.p50_latency?.[index]?.value || 0,
    p95: timeseries.p95_latency?.[index]?.value || 0,
  })) || [];

  const hasData = overview && (
    overview.requests_per_second > 0 ||
    overview.healthy_services > 0 ||
    recentRequests.length > 0
  );

  return (
    <div>
      <PageHeader
        title="Overview"
        icon={<Activity size={24} />}
        description="Real-time observability for your API gateway traffic."
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              className="form-input form-select"
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              style={{ width: 'auto', minWidth: '130px' }}
            >
              <option value="">All Services</option>
              <option value="demo">Demo Service</option>
            </select>
            <select
              className="form-input form-select"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              style={{ width: 'auto', minWidth: '140px' }}
            >
              <option value="5m">Last 5 minutes</option>
              <option value="15m">Last 15 minutes</option>
              <option value="1h">Last 1 hour</option>
              <option value="6h">Last 6 hours</option>
              <option value="24h">Last 24 hours</option>
            </select>
          </div>
        }
      />

      {loading && !overview ? (
        <div className="loading-container">
          <div className="loading-spinner" />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Intelligence Banner */}
          {intelligence && intelligence.status !== 'HEALTHY' && (
            <div className="card" style={{ borderLeft: `3px solid ${intelligence.status === 'CRITICAL' ? 'var(--error)' : 'var(--warning)'}`, padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <AlertCircle size={18} style={{ color: intelligence.status === 'CRITICAL' ? 'var(--error)' : 'var(--warning)' }} />
                <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                  Traffic Intelligence — {intelligence.active_anomaly_count} Anomal{intelligence.active_anomaly_count === 1 ? 'y' : 'ies'} Detected
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                <div>
                  <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>Anomalies</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {intelligence.recent_anomalies.map((a: any, i: number) => (
                      <div key={i} style={{ background: 'var(--bg-elevated)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span className={`badge badge-${a.severity === 'CRITICAL' ? 'error' : 'warning'}`}>{a.anomaly_type}</span>
                          <span className="text-xs text-muted">{new Date(a.detected_at).toLocaleTimeString()}</span>
                        </div>
                        <p style={{ fontSize: '0.8125rem', margin: '0 0 6px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{a.explanation}</p>
                        <p className="text-xs text-muted" style={{ margin: 0 }}>
                          Baseline: {a.baseline_value} &middot; Current: {a.current_value} ({a.deviation})
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>Recommendations</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {intelligence.recommendations.map((r: any, i: number) => (
                      <div key={i} style={{ background: 'var(--bg-elevated)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                          <Info size={14} style={{ color: 'var(--accent)' }} />
                          <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{r.title}</span>
                        </div>
                        <p style={{ fontSize: '0.8125rem', margin: '0 0 6px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{r.evidence}</p>
                        <p className="text-xs" style={{ margin: 0, padding: '8px', background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)', color: 'var(--text-secondary)' }}>
                          {r.recommended_action}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {intelligence && intelligence.status === 'HEALTHY' && (
            <div className="alert alert-success">
              <CheckCircle size={18} />
              <span><strong>Systems healthy.</strong> No anomalies detected. Traffic patterns are normal.</span>
            </div>
          )}

          {/* Metric Cards */}
          <div className="metrics-grid">
            <div className="card metric-card">
              <div className="metric-card-header">
                <span className="metric-card-label"><Zap size={14} /> Requests / sec</span>
              </div>
              <div className="metric-card-value">{overview?.requests_per_second ?? 0}</div>
            </div>
            <div className="card metric-card">
              <div className="metric-card-header">
                <span className="metric-card-label"><AlertTriangle size={14} /> Error Rate</span>
              </div>
              <div className="metric-card-value">
                {(overview?.error_rate ?? 0).toFixed(1)}<span className="metric-card-unit">%</span>
              </div>
            </div>
            <div className="card metric-card">
              <div className="metric-card-header">
                <span className="metric-card-label"><Clock size={14} /> P95 Latency</span>
              </div>
              <div className="metric-card-value">
                {((overview?.p95_latency ?? 0) * 1000).toFixed(1)}<span className="metric-card-unit">ms</span>
              </div>
            </div>
            <div className="card metric-card">
              <div className="metric-card-header">
                <span className="metric-card-label"><Users size={14} /> Active Connections</span>
              </div>
              <div className="metric-card-value">{overview?.active_connections ?? 0}</div>
            </div>
            <div className="card metric-card">
              <div className="metric-card-header">
                <span className="metric-card-label"><Shield size={14} /> Healthy Services</span>
              </div>
              <div className="metric-card-value">{overview?.healthy_services ?? 0}</div>
            </div>
            <div className="card metric-card">
              <div className="metric-card-header">
                <span className="metric-card-label"><Server size={14} /> Healthy Instances</span>
              </div>
              <div className="metric-card-value">{overview?.healthy_instances ?? 0}</div>
            </div>
          </div>

          {/* Charts */}
          <div className="charts-grid">
            <div className="card">
              <div className="card-header">
                <span className="card-title">Traffic</span>
              </div>
              {!hasData ? (
                <div style={{ height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                  No traffic data yet
                </div>
              ) : (
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="gradReq" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="time" stroke="var(--text-muted)" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis stroke="var(--text-muted)" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem' }}
                        itemStyle={{ color: 'var(--text-secondary)' }}
                        labelStyle={{ color: 'var(--text-muted)', marginBottom: '4px' }}
                      />
                      <Area type="monotone" dataKey="requests" name="Req/s" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#gradReq)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title">Latency (P50 &amp; P95)</span>
              </div>
              {!hasData ? (
                <div style={{ height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                  No latency data yet
                </div>
              ) : (
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="time" stroke="var(--text-muted)" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis stroke="var(--text-muted)" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => (Number(v) * 1000).toFixed(0) + 'ms'} />
                      <Tooltip
                        contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem' }}
                        formatter={(val: any) => (Number(val) * 1000).toFixed(2) + ' ms'}
                      />
                      <Legend wrapperStyle={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} />
                      <Line type="monotone" dataKey="p50" name="P50" stroke="#22c55e" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="p95" name="P95" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          {/* Tables */}
          <div className="charts-grid">
            <div className="card">
              <div className="card-header">
                <span className="card-title">Recent Requests</span>
              </div>
              <div className="table-wrap">
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
                        <td><span className={`method-badge method-${req.method.toLowerCase()}`}>{req.method}</span></td>
                        <td className="mono">{req.path}</td>
                        <td>
                          <span className={`status-code ${req.status_code < 300 ? 'status-2xx' : req.status_code < 500 ? 'status-4xx' : 'status-5xx'}`}>
                            {req.status_code}
                          </span>
                        </td>
                        <td>{req.latency}</td>
                        <td style={{ color: 'var(--text-primary)' }}>{req.service_name}</td>
                        <td className="mono text-xs text-muted">{req.lb_selected_instance?.substring(0, 8) || 'N/A'}</td>
                      </tr>
                    ))}
                    {recentRequests.length === 0 && (
                      <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px' }}>No recent requests recorded</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title" style={{ color: 'var(--error)' }}>Recent Errors</span>
              </div>
              <div className="table-wrap">
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
                        <td><span className={`method-badge method-${err.method.toLowerCase()}`}>{err.method}</span></td>
                        <td className="mono">{err.path}</td>
                        <td><span className="status-code status-5xx">{err.status_code}</span></td>
                        <td className="text-xs">{err.res_failure_reason || err.lb_routing_reason || 'Upstream Error'}</td>
                        <td style={{ color: 'var(--text-primary)' }}>{err.service_name}</td>
                      </tr>
                    ))}
                    {recentErrors.length === 0 && (
                      <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px' }}>No recent errors — all clear</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
