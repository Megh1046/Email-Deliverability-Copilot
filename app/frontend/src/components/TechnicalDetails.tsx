import React, { useState } from 'react';
import { AuthEvidence, RootCause } from '../types/header-analysis';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  evidence: AuthEvidence[];
  authenticationResults: string[];
  rawHeaders: string;
  rootCause: RootCause | null;
}

export function TechnicalDetails({ evidence, authenticationResults, rawHeaders, rootCause }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl shadow-sm overflow-hidden mt-8">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-brand-surface hover:bg-brand-surface-secondary transition-colors"
      >
        <h3 className="font-semibold text-brand-text">Technical details</h3>
        {isOpen ? <ChevronUp size={20} className="text-brand-text-secondary" /> : <ChevronDown size={20} className="text-brand-text-secondary" />}
      </button>
      
      {isOpen && (
        <div className="p-4 border-t border-brand-border flex flex-col gap-6 bg-brand-bg/50">
          
          {rootCause && (
            <div>
              <h4 className="text-xs font-bold text-brand-text-secondary uppercase tracking-wider mb-2">Root Cause Code</h4>
              <div className="bg-brand-surface border border-brand-border rounded p-3 text-sm font-mono text-status-error">
                {rootCause.code}
              </div>
            </div>
          )}

          {authenticationResults && authenticationResults.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-brand-text-secondary uppercase tracking-wider mb-2">Authentication-Results Headers</h4>
              <div className="flex flex-col gap-2">
                {authenticationResults.map((ar, idx) => (
                  <div key={idx} className="bg-brand-surface border border-brand-border rounded p-3 text-sm font-mono text-brand-text whitespace-pre-wrap overflow-x-auto">
                    {ar}
                  </div>
                ))}
              </div>
            </div>
          )}

          {evidence && evidence.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-brand-text-secondary uppercase tracking-wider mb-2">Parsed Evidence Matrix</h4>
              <div className="overflow-x-auto border border-brand-border rounded bg-brand-surface">
                <table className="w-full text-left text-sm">
                  <thead className="bg-brand-surface-secondary border-b border-brand-border text-xs text-brand-text-secondary">
                    <tr>
                      <th className="p-2 font-semibold border-r border-brand-border">Server</th>
                      <th className="p-2 font-semibold border-r border-brand-border">SPF</th>
                      <th className="p-2 font-semibold border-r border-brand-border">DKIM</th>
                      <th className="p-2 font-semibold border-r border-brand-border">DMARC</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border">
                    {evidence.map((ev, i) => (
                      <tr key={i} className={i === 0 ? "bg-accent/5" : ""}>
                        <td className="p-2 font-mono text-xs border-r border-brand-border">{ev.authserv_id || '-'}</td>
                        <td className="p-2 border-r border-brand-border">
                          <div className="font-mono text-xs">{ev.spf_result || '-'}</div>
                          {ev.spf_domain && <div className="text-[10px] text-brand-text-secondary mt-1 max-w-[120px] truncate" title={ev.spf_domain}>{ev.spf_domain}</div>}
                        </td>
                        <td className="p-2 border-r border-brand-border">
                          <div className="font-mono text-xs">{ev.dkim_result || '-'}</div>
                          {ev.dkim_domain && <div className="text-[10px] text-brand-text-secondary mt-1 max-w-[120px] truncate" title={ev.dkim_domain}>{ev.dkim_domain}</div>}
                        </td>
                        <td className="p-2 font-mono text-xs">{ev.dmarc_result || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[10px] text-brand-text-secondary mt-1">Top row represents the most trusted verdict from the final receiving MTA.</p>
            </div>
          )}

          <div>
            <h4 className="text-xs font-bold text-brand-text-secondary uppercase tracking-wider mb-2">Original Headers</h4>
            <pre className="bg-brand-surface border border-brand-border rounded p-4 text-xs font-mono text-brand-text-secondary overflow-x-auto max-h-96 overflow-y-auto">
              {rawHeaders}
            </pre>
          </div>

        </div>
      )}
    </div>
  );
}
