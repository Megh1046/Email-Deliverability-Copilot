import React from 'react';
import { HeaderAnalysisResponse } from '../types/header-analysis';
import { AuthenticationStatus } from './AuthenticationStatus';
import { AlignmentStatus } from './AlignmentStatus';
import { RootCause } from './RootCause';
import { RemediationGuide } from './RemediationGuide';
import { TechnicalDetails } from './TechnicalDetails';
import { CheckCircle2, AlertTriangle, ArrowLeft } from 'lucide-react';

interface Props {
  data: HeaderAnalysisResponse;
  rawHeaders: string;
  onReset: () => void;
}

export function AnalysisResults({ data, rawHeaders, onReset }: Props) {
  return (
    <div className="w-full max-w-5xl mx-auto pb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Top action bar */}
      <div className="mb-8">
        <button 
          onClick={onReset}
          className="flex items-center gap-2 text-sm font-medium text-brand-text-secondary hover:text-brand-text transition-colors"
        >
          <ArrowLeft size={16} />
          Analyze another email
        </button>
      </div>

      {/* Main Status Header */}
      <div className="mb-10 text-center md:text-left flex flex-col md:flex-row md:items-center justify-between gap-6 bg-brand-surface p-8 rounded-2xl border border-brand-border shadow-sm">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-center md:justify-start gap-3 mb-2">
            {data.passed ? (
              <CheckCircle2 size={32} className="text-status-success" />
            ) : (
              <AlertTriangle size={32} className="text-status-error" />
            )}
            <h2 className="text-3xl font-bold text-brand-text">
              {data.passed ? "Authentication looks healthy." : "There's an authentication issue."}
            </h2>
          </div>
          
          <p className="text-lg text-brand-text-secondary max-w-2xl">
            {data.passed 
              ? "Your message successfully authenticated and at least one authentication mechanism is aligned with the From domain."
              : data.root_cause?.title 
                ? `We found a problem with ${data.root_cause.title}.`
                : "We found an authentication problem that may affect deliverability."}
          </p>
        </div>

        {data.provider && (
          <div className="bg-brand-surface-secondary px-6 py-4 rounded-xl border border-brand-border flex flex-col items-center md:items-end min-w-[200px]">
            <span className="text-xs font-bold text-brand-text-secondary uppercase tracking-wider mb-1">Email Provider</span>
            <span className="font-semibold text-brand-text text-lg">{data.provider.name}</span>
            <span className="text-xs text-brand-text-secondary mt-1">Confidence: {data.provider.confidence}</span>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-10">
        
        {/* If there is a root cause, show it prominently before the detailed breakdown */}
        {data.root_cause && (
          <RootCause rootCause={data.root_cause} />
        )}

        <section>
          <h3 className="text-xl font-bold text-brand-text mb-4">Authentication Status</h3>
          <AuthenticationStatus spf={data.spf} dkim={data.dkim} dmarc={data.dmarc} />
        </section>

        <section>
          <AlignmentStatus 
            alignment={data.alignment} 
            fromDomain={data.from_domain}
            spfDomain={data.spf.domain}
            dkimDomain={data.dkim.domain}
          />
        </section>

        {data.remediation && data.remediation.length > 0 && (
          <section>
            <RemediationGuide steps={data.remediation} providerName={data.provider?.name} />
          </section>
        )}

        <TechnicalDetails 
          evidence={data.evidence} 
          authenticationResults={data.authentication_results}
          rawHeaders={rawHeaders}
          rootCause={data.root_cause}
        />
        
      </div>
    </div>
  );
}
