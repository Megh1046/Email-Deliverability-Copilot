"use client";

import React, { useState } from 'react';
import { AppHeader } from '../components/AppHeader';
import { HeaderInput } from '../components/HeaderInput';
import { AnalysisLoading } from '../components/AnalysisLoading';
import { AnalysisResults } from '../components/AnalysisResults';
import { analyzeHeaders } from '../services/header-api';
import { HeaderAnalysisResponse } from '../types/header-analysis';

type State = 'idle' | 'loading' | 'success' | 'error';

export function PageContent() {
  const [state, setState] = useState<State>('idle');
  const [rawInput, setRawInput] = useState<string>('');
  const [result, setResult] = useState<HeaderAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (headers: string) => {
    setState('loading');
    setRawInput(headers);
    setError(null);
    setResult(null);

    try {
      // Default to relaxed alignment for a non-technical audience
      const data = await analyzeHeaders(headers, undefined, 'relaxed', 'relaxed');
      setResult(data);
      setState('success');
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during analysis.');
      setState('error');
    }
  };

  const handleReset = () => {
    setState('idle');
    setResult(null);
    setError(null);
    setRawInput('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-brand-bg text-brand-text font-sans selection:bg-accent/20">
      <AppHeader />

      <main className="px-6 md:px-8 py-12 md:py-20 max-w-5xl mx-auto">
        
        {state === 'idle' && (
          <div className="flex flex-col items-center max-w-3xl mx-auto text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h1 className="text-4xl md:text-5xl font-bold text-brand-text mb-6 tracking-tight">
              Understand why your emails pass, fail, or land in spam.
            </h1>
            <p className="text-lg md:text-xl text-brand-text-secondary leading-relaxed">
              Paste the email headers from a delivered message and we'll check SPF, DKIM, DMARC, alignment, and explain exactly what needs fixing.
            </p>
            
            <div className="w-full mt-12 text-left">
              <HeaderInput onAnalyze={handleAnalyze} />
            </div>
          </div>
        )}

        {state === 'loading' && (
          <AnalysisLoading />
        )}

        {state === 'error' && (
          <div className="w-full max-w-2xl mx-auto mt-12 p-8 bg-status-error-bg border border-status-error/30 rounded-xl text-center">
            <h3 className="text-xl font-bold text-status-error mb-4">Analysis Failed</h3>
            <p className="text-brand-text mb-8">{error}</p>
            <button 
              onClick={() => setState('idle')}
              className="px-6 py-2 bg-brand-surface border border-brand-border rounded-lg shadow-sm hover:bg-brand-surface-secondary transition-colors font-medium"
            >
              Try Again
            </button>
          </div>
        )}

        {state === 'success' && result && (
          <AnalysisResults 
            data={result} 
            rawHeaders={rawInput} 
            onReset={handleReset} 
          />
        )}

      </main>
    </div>
  );
}
