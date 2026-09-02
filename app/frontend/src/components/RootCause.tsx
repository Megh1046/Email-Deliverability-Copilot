import React from 'react';
import { RootCause as RootCauseType } from '../types/header-analysis';
import { AlertCircle } from 'lucide-react';

interface Props {
  rootCause: RootCauseType;
}

export function RootCause({ rootCause }: Props) {
  return (
    <div className="bg-status-error-bg border border-status-error/30 rounded-xl p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="mt-1 bg-status-error/10 p-2 rounded-full text-status-error">
          <AlertCircle size={24} />
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold tracking-wider text-status-error uppercase mb-1">
            What went wrong
          </div>
          <h3 className="text-xl font-bold text-brand-text mb-3">
            {rootCause.title}
          </h3>
          <p className="text-brand-text-secondary leading-relaxed">
            {rootCause.description}
          </p>
        </div>
      </div>
    </div>
  );
}
