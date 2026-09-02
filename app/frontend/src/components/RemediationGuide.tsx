import React, { useState } from 'react';
import { RemediationStep } from '../types/header-analysis';
import { Copy, Check } from 'lucide-react';

interface Props {
  steps: RemediationStep[];
  providerName?: string;
}

export function RemediationGuide({ steps, providerName }: Props) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-brand-text mb-1">How to fix this</h3>
        {providerName ? (
          <p className="text-sm text-brand-text-secondary">
            Follow these steps for <strong>{providerName}</strong> to resolve the authentication issue.
          </p>
        ) : (
          <p className="text-sm text-brand-text-secondary">
            Your email provider could not be confidently identified. Here is the generic process to resolve this issue.
          </p>
        )}
      </div>

      <div className="space-y-6 relative">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-brand-border/60 z-0"></div>
        {steps.map((step) => (
          <div key={step.step} className="relative z-10 flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-surface border-2 border-accent text-accent font-bold flex items-center justify-center text-sm shadow-sm bg-white mt-1">
              {step.step}
            </div>
            <div className="flex-1 pb-2">
              <h4 className="text-base font-semibold text-brand-text mb-1">{step.action}</h4>
              
              {step.detail && (
                <div className="text-sm text-brand-text-secondary whitespace-pre-line mb-3 bg-brand-surface-secondary/50 p-3 rounded-lg border border-brand-border/30">
                  {step.detail}
                </div>
              )}
              
              {step.sample_record && (
                <CopyableBlock label="DNS Record" content={step.sample_record} />
              )}
              
              {step.validation_cmd && (
                <CopyableBlock label="Validation Command" content={step.validation_cmd} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CopyableBlock({ label, content }: { label: string; content: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-2 bg-brand-surface border border-brand-border rounded-lg overflow-hidden flex flex-col">
      <div className="bg-brand-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-text-secondary uppercase tracking-wider flex justify-between items-center border-b border-brand-border">
        {label}
      </div>
      <div className="relative group">
        <pre className="p-3 text-sm font-mono text-brand-text overflow-x-auto bg-[#FDFCF9]">
          {content}
        </pre>
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-1.5 bg-white border border-brand-border rounded shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-brand-surface focus:opacity-100"
          title="Copy to clipboard"
        >
          {copied ? <Check size={14} className="text-status-success" /> : <Copy size={14} className="text-brand-text-secondary" />}
        </button>
      </div>
    </div>
  );
}
