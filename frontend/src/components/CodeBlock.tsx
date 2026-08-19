import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  label?: string;
  showCopy?: boolean;
}

export default function CodeBlock({ code, label = 'bash', showCopy = true }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span>{label}</span>
        {showCopy && (
          <button className="btn btn-ghost btn-sm" onClick={copy} style={{ gap: '4px', padding: '2px 8px', fontSize: '0.72rem' }}>
            {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
          </button>
        )}
      </div>
      <pre className="code-block-content">{code}</pre>
    </div>
  );
}
