import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { GitBranch, Mail, ArrowRight, Terminal, Zap, Shield, BarChart2 } from 'lucide-react';

export default function Home() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        <div style={styles.navBrand}>Conductor</div>
        <div style={styles.navLinks}>
          <Link to="/login" style={styles.navLink}>Login</Link>
          <Link to="/signup" className="btn btn-primary" style={styles.navBtn}>Get Started</Link>
        </div>
      </nav>

      <main style={styles.main}>
        <div style={{...styles.hero, opacity: isVisible ? 1 : 0, transform: isVisible ? 'translateY(0)' : 'translateY(20px)', transition: 'all 0.8s ease-out'}}>
          <div style={styles.badge}>v1.0.0 is live</div>
          <h1 style={styles.title}>
            The Developer-First <br/>
            <span style={styles.highlight}>API Gateway</span>
          </h1>
          <p style={styles.subtitle}>
            A high-performance, open-source API Gateway built for modern microservices. 
            Route, monitor, and secure your traffic with zero friction.
          </p>

          <div style={styles.ctaGroup}>
            <Link to="/signup" className="btn btn-primary" style={styles.primaryBtn}>
              Start Building <ArrowRight size={18} />
            </Link>
            <a href="https://github.com/Mahaprasadnanda/Conductor" target="_blank" rel="noreferrer" style={styles.secondaryBtn}>
              <GitBranch size={18} /> View on GitHub
            </a>
          </div>

          <div style={styles.terminal}>
            <div style={styles.terminalHeader}>
              <div style={styles.dotGroup}>
                <div style={{...styles.dot, backgroundColor: '#ff5f56'}}></div>
                <div style={{...styles.dot, backgroundColor: '#ffbd2e'}}></div>
                <div style={{...styles.dot, backgroundColor: '#27c93f'}}></div>
              </div>
              <div style={styles.terminalTitle}>bash</div>
            </div>
            <div style={styles.terminalBody}>
              <span style={styles.prompt}>$</span> git clone https://github.com/Mahaprasadnanda/Conductor.git
              <br/>
              <span style={styles.prompt}>$</span> cd Conductor && docker compose up -d
              <br/>
              <span style={styles.success}>?  Backend deployed successfully on :8000</span>
            </div>
          </div>
        </div>

        <div style={{...styles.features, opacity: isVisible ? 1 : 0, transition: 'all 0.8s ease-out 0.3s'}}>
          <FeatureCard icon={<Zap size={24} color="#a78bfa" />} title="Lightning Fast" desc="Built for extremely low latency request proxying and routing." />
          <FeatureCard icon={<Shield size={24} color="#a78bfa" />} title="Secure by Default" desc="Built-in JWT auth, rate limiting, and CORS management." />
          <FeatureCard icon={<BarChart2 size={24} color="#a78bfa" />} title="Deep Analytics" desc="Prometheus & Grafana integrated straight out of the box." />
          <FeatureCard icon={<Terminal size={24} color="#a78bfa" />} title="Developer Friendly" desc="Extensive API support, easy deployment, and beautiful UI." />
        </div>
      </main>

      <footer style={styles.footer}>
        <div style={styles.footerContent}>
          <div>
            <div style={styles.footerBrand}>Conductor</div>
            <p style={styles.footerText}>Open Source API Gateway</p>
          </div>
          <div style={styles.footerLinks}>
            <h4 style={styles.footerHeading}>Contact & Contribution</h4>
            <a href="mailto:Mahaprasad.programmer@gmail.com" style={styles.footerLink}>
              <Mail size={16} /> Mahaprasad.programmer@gmail.com
            </a>
            <a href="https://github.com/Mahaprasadnanda/Conductor" target="_blank" rel="noreferrer" style={styles.footerLink}>
              <GitBranch size={16} /> GitHub Repository
            </a>
            <p style={styles.footerThanks}>Happy to accept any pull requests! Contributions are welcome.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

const FeatureCard = ({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) => (
  <div style={styles.featureCard}>
    <div style={styles.featureIconWrapper}>{icon}</div>
    <h3 style={styles.featureTitle}>{title}</h3>
    <p style={styles.featureDesc}>{desc}</p>
  </div>
);

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#09090b',
    color: '#fafafa',
    fontFamily: 'system-ui, -apple-system, sans-serif'
  },
  nav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '24px 48px',
    borderBottom: '1px solid rgba(255,255,255,0.05)'
  },
  navBrand: {
    fontSize: '1.25rem',
    fontWeight: 700,
    letterSpacing: '-0.025em',
    color: '#fff'
  },
  navLinks: {
    display: 'flex',
    gap: '24px',
    alignItems: 'center'
  },
  navLink: {
    color: '#a1a1aa',
    textDecoration: 'none',
    fontWeight: 500,
    fontSize: '0.95rem',
    transition: 'color 0.2s'
  },
  navBtn: {
    padding: '8px 16px',
    fontSize: '0.9rem'
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '80px 24px',
    maxWidth: '1200px',
    margin: '0 auto',
    width: '100%'
  },
  hero: {
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    maxWidth: '800px',
    marginBottom: '80px'
  },
  badge: {
    background: 'rgba(167, 139, 250, 0.1)',
    color: '#a78bfa',
    padding: '6px 12px',
    borderRadius: '999px',
    fontSize: '0.875rem',
    fontWeight: 600,
    marginBottom: '24px',
    border: '1px solid rgba(167, 139, 250, 0.2)'
  },
  title: {
    fontSize: '4.5rem',
    fontWeight: 800,
    lineHeight: 1.1,
    letterSpacing: '-0.04em',
    marginBottom: '24px',
    color: '#fff'
  },
  highlight: {
    background: 'linear-gradient(to right, #a78bfa, #c084fc)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    fontSize: '1.25rem',
    color: '#a1a1aa',
    lineHeight: 1.6,
    marginBottom: '40px',
    maxWidth: '600px'
  },
  ctaGroup: {
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
    marginBottom: '60px'
  },
  primaryBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    fontSize: '1rem',
    fontWeight: 600,
    borderRadius: '8px'
  },
  secondaryBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    fontSize: '1rem',
    fontWeight: 600,
    borderRadius: '8px',
    backgroundColor: '#18181b',
    color: '#fff',
    textDecoration: 'none',
    border: '1px solid #27272a',
    transition: 'background-color 0.2s'
  },
  terminal: {
    background: '#000',
    borderRadius: '12px',
    border: '1px solid #27272a',
    width: '100%',
    maxWidth: '600px',
    overflow: 'hidden',
    textAlign: 'left',
    boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
  },
  terminalHeader: {
    background: '#18181b',
    padding: '12px 16px',
    display: 'flex',
    alignItems: 'center',
    borderBottom: '1px solid #27272a'
  },
  dotGroup: {
    display: 'flex',
    gap: '6px'
  },
  dot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%'
  },
  terminalTitle: {
    flex: 1,
    textAlign: 'center',
    color: '#a1a1aa',
    fontSize: '0.875rem',
    fontFamily: 'monospace',
    marginLeft: '-42px'
  },
  terminalBody: {
    padding: '24px',
    fontFamily: 'monospace',
    fontSize: '0.9rem',
    color: '#e4e4e7',
    lineHeight: 1.8
  },
  prompt: {
    color: '#a78bfa'
  },
  success: {
    color: '#34d399'
  },
  features: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '24px',
    width: '100%'
  },
  featureCard: {
    background: '#18181b',
    border: '1px solid #27272a',
    padding: '32px',
    borderRadius: '16px',
    transition: 'transform 0.2s, border-color 0.2s',
  },
  featureIconWrapper: {
    background: 'rgba(167, 139, 250, 0.1)',
    width: '48px',
    height: '48px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '20px'
  },
  featureTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    marginBottom: '12px',
    color: '#fff'
  },
  featureDesc: {
    color: '#a1a1aa',
    lineHeight: 1.6,
    fontSize: '0.95rem'
  },
  footer: {
    borderTop: '1px solid #27272a',
    padding: '48px 24px',
    marginTop: 'auto'
  },
  footerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '40px'
  },
  footerBrand: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#fff',
    marginBottom: '8px'
  },
  footerText: {
    color: '#a1a1aa',
    fontSize: '0.9rem'
  },
  footerLinks: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  footerHeading: {
    color: '#fff',
    fontWeight: 600,
    marginBottom: '8px'
  },
  footerLink: {
    color: '#a1a1aa',
    textDecoration: 'none',
    fontSize: '0.9rem',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'color 0.2s'
  },
  footerThanks: {
    color: '#34d399',
    fontSize: '0.85rem',
    marginTop: '8px',
    maxWidth: '300px',
    fontStyle: 'italic'
  }
};
