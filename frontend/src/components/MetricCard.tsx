import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
}

export default function MetricCard({ label, value, unit, icon: Icon }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        <Icon /> {label}
      </div>
      <div className="metric-value">
        {value}{unit && <span className="metric-unit">{unit}</span>}
      </div>
    </div>
  );
}
