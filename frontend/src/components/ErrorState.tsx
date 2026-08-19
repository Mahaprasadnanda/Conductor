import { AlertCircle } from 'lucide-react';

export default function ErrorState({ message = 'Something went wrong' }: { message?: string }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '16px 20px', borderColor: 'var(--error-border)' }}>
      <AlertCircle size={16} color="var(--error)" style={{ flexShrink: 0 }} />
      <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{message}</span>
    </div>
  );
}
