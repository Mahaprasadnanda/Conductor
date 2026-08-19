interface LoadingSkeletonProps {
  count?: number;
  type?: 'card' | 'metric' | 'row';
  lines?: number;
}

export default function LoadingSkeleton({ count = 3, type = 'card', lines }: LoadingSkeletonProps) {
  const n = lines ?? count;
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: type === 'metric' ? 'repeat(auto-fit, minmax(180px, 1fr))' : '1fr',
      gap: type === 'metric' ? '12px' : '8px'
    }}>
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className={'skeleton skeleton-' + type} />
      ))}
    </div>
  );
}
