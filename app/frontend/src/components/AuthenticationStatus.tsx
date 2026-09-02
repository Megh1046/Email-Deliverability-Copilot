import React from 'react';
import { AuthenticationResult } from '../types/header-analysis';
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react';

interface Props {
  spf: AuthenticationResult;
  dkim: AuthenticationResult;
  dmarc: AuthenticationResult;
}

export function AuthenticationStatus({ spf, dkim, dmarc }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <AuthCard title="SPF" data={spf} descriptionMap={{
        PASS: "The sending server is authorized to send email for this domain.",
        FAIL: "The sending server is NOT authorized by the domain's SPF record.",
        UNKNOWN: "SPF could not be verified (no record or unknown status)."
      }} />
      <AuthCard title="DKIM" data={dkim} descriptionMap={{
        PASS: "The message contains a valid cryptographic signature.",
        FAIL: "The cryptographic signature is invalid or missing.",
        UNKNOWN: "DKIM could not be verified."
      }} />
      <AuthCard title="DMARC" data={dmarc} descriptionMap={{
        PASS: "The authenticated domains satisfy the DMARC policy.",
        FAIL: "The authenticated domains do NOT satisfy the required DMARC policy.",
        UNKNOWN: "DMARC could not be verified."
      }} />
    </div>
  );
}

function AuthCard({ 
  title, 
  data, 
  descriptionMap 
}: { 
  title: string; 
  data: AuthenticationResult;
  descriptionMap: Record<string, string>;
}) {
  const isPass = data.result === 'PASS';
  const isFail = data.result === 'FAIL';
  
  const Icon = isPass ? CheckCircle2 : isFail ? XCircle : HelpCircle;
  const statusColor = isPass ? "text-status-success" : isFail ? "text-status-error" : "text-status-warning";
  const bgColor = isPass ? "bg-status-success-bg border-status-success/20" : 
                  isFail ? "bg-status-error-bg border-status-error/20" : 
                  "bg-status-warning-bg border-status-warning/20";

  return (
    <div className={`p-5 rounded-xl border ${bgColor} flex flex-col gap-3`}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-brand-text">{title}</h3>
        <div className={`flex items-center gap-1.5 ${statusColor}`}>
          <Icon size={18} />
          <span className="font-medium text-sm">
            {data.result === 'PASS' ? 'Passed' : data.result === 'FAIL' ? 'Failed' : 'Unknown'}
          </span>
        </div>
      </div>
      <p className="text-sm text-brand-text-secondary leading-relaxed">
        {descriptionMap[data.result] || descriptionMap.UNKNOWN}
      </p>
      {data.domain && (
        <div className="mt-auto pt-3 border-t border-brand-border/40">
          <span className="text-xs text-brand-text-secondary block">Domain:</span>
          <span className="text-sm font-mono truncate block" title={data.domain}>{data.domain}</span>
        </div>
      )}
    </div>
  );
}
