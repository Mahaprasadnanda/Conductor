import { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import { 
  Activity, Users, Zap, Shield, AlertTriangle,
  Clock, Server, LogOut, RefreshCw 
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts';

export default function Dashboard() {
  const { token, logout } = useContext(AuthContext);
  const [timeRange, setTimeRange] = useState('1h');
  const [serviceFilter, setServiceFilter] = useState('');
  
  const [overview, setOverview] = useState<any>(null);
  const [timeseries, setTimeseries] = useState<any>(null);
  const [recentRequests, setRecentRequests] = useState<any[]>([]);
  const [recentErrors, setRecentErrors] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [overviewRes, tsRes, reqRes, errRes] = await Promise.all([
        fetch('/api/v1/analytics/overview', { headers }),
        fetch(`/api/v1/analytics/timeseries?time_range=${timeRange}${serviceFilter ? `&service_name=${serviceFilter}` : ''}`, { headers }),
        fetch('/api/v1/analytics/recent-requests?limit=10', { headers }),
        fetch('/api/v1/analytics/recent-errors?limit=10', { headers })
      ]);
      
      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (tsRes.ok) setTimeseries(await tsRes.json());
      if (reqRes.ok) setRecentRequests(await reqRes.json());
      if (errRes.ok) setRecentErrors(await errRes.json());
      
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
  }, [timeRange, serviceFilter, token]);

  const formatTime = (ts: number) => {
    return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading && !overview) {
    return <div className="login-container"><div className="glass-panel">Loading Analytics...</div></div>;
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
      <header className="dashboard-header">
        <div className="header-brand">
          <Activity size={28} color="var(--accent-primary)" />
          Conductor Dashboard
        </div>
        
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
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
          
          <button className="btn-primary" onClick={fetchData} title="Refresh" style={{ padding: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RefreshCw size={16} />
          </button>
          
          <button className="btn-primary" onClick={logout} style={{ background: 'transparent', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>
      
      <main className="dashboard-layout">
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

      </main>
    </div>
  );
}
