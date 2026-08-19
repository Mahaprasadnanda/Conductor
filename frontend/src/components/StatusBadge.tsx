type StatusBadgeProps = {
  status: string;
  variant?: 'success' | 'warning' | 'error' | 'neutral';
  showDot?: boolean;
};

function getVariant(status: string, override?: string): 'success' | 'warning' | 'error' | 'neutral' {
  if (override) return override as 'success' | 'warning' | 'error' | 'neutral';
  const s = status.toLowerCase();
  if (['healthy', 'active', 'enabled', 'ok', 'running', 'online'].includes(s)) return 'success';
  if (['unhealthy', 'degraded', 'warning', 'pending', 'unknown'].includes(s)) return 'warning';
  if (['error', 'failed', 'revoked', 'disabled', 'down', 'offline', 'critical'].includes(s)) return 'error';
  return 'neutral';
}

export default function StatusBadge({ status, variant, showDot = true }: StatusBadgeProps) {
  const v = getVariant(status, variant);

  return (
    <span className={`badge badge-${v}`}>
      {showDot && <span className="badge-dot" />}
      {status}
    </span>
  );
}
