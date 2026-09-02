import React from 'react';
import { AlignmentResult } from '../types/header-analysis';
import { Check, X, Minus } from 'lucide-react';

interface Props {
  alignment: AlignmentResult;
  fromDomain: string | null;
  spfDomain: string | null;
  dkimDomain: string | null;
}

export function AlignmentStatus({ alignment, fromDomain, spfDomain, dkimDomain }: Props) {
  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl p-6">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Authentication Alignment</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AlignmentItem 
          title="SPF Alignment" 
          status={alignment.spf} 
          mode={alignment.spf_mode}
          domain={spfDomain}
          fromDomain={fromDomain}
        />
        <AlignmentItem 
          title="DKIM Alignment" 
          status={alignment.dkim} 
          mode={alignment.dkim_mode}
          domain={dkimDomain}
          fromDomain={fromDomain}
        />
        <div className="md:border-l border-brand-border md:pl-6 flex flex-col justify-center">
          <span className="text-sm text-brand-text-secondary mb-1">Overall Alignment</span>
          <div className="flex items-center gap-2">
            {alignment.overall === true ? (
              <><Check className="text-status-success" size={20} /><span className="font-semibold text-status-success">Healthy</span></>
            ) : alignment.overall === false ? (
              <><X className="text-status-error" size={20} /><span className="font-semibold text-status-error">Needs attention</span></>
            ) : (
              <><Minus className="text-brand-text-secondary" size={20} /><span className="font-semibold text-brand-text-secondary">Unknown</span></>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AlignmentItem({ title, status, mode, domain, fromDomain }: { title: string; status: boolean | null; mode: string; domain: string | null; fromDomain: string | null }) {
  const isAligned = status === true;
  const isMisaligned = status === false;
  
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="font-medium text-brand-text">{title}</span>
        {isAligned ? (
          <span className="text-xs font-medium text-status-success bg-status-success-bg px-2 py-0.5 rounded border border-status-success/20">Aligned</span>
        ) : isMisaligned ? (
          <span className="text-xs font-medium text-status-error bg-status-error-bg px-2 py-0.5 rounded border border-status-error/20">Not aligned</span>
        ) : (
          <span className="text-xs font-medium text-brand-text-secondary bg-brand-surface-secondary px-2 py-0.5 rounded border border-brand-border">N/A</span>
        )}
      </div>
      
      {status !== null && (
        <div className="text-xs text-brand-text-secondary space-y-1 mt-1 bg-brand-surface-secondary p-2 rounded">
          <div className="flex justify-between">
            <span>From:</span><span className="font-mono truncate ml-2" title={fromDomain || ''}>{fromDomain || 'unknown'}</span>
          </div>
          <div className="flex justify-between">
            <span>Auth:</span><span className="font-mono truncate ml-2" title={domain || ''}>{domain || 'none'}</span>
          </div>
          <div className="text-[10px] uppercase tracking-wider mt-1 pt-1 border-t border-brand-border/50 text-right opacity-60">
            {mode} mode
          </div>
        </div>
      )}
      {status === null && (
        <p className="text-xs text-brand-text-secondary mt-1">Authentication did not pass, so alignment is not applicable.</p>
      )}
    </div>
  );
}
