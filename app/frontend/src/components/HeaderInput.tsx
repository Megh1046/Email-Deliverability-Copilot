import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface HeaderInputProps {
  onAnalyze: (headers: string) => void;
}

export function HeaderInput({ onAnalyze }: HeaderInputProps) {
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = input.trim();
    if (!trimmed) {
      setError("Please paste your email headers first.");
      return;
    }

    if (trimmed.length < 20) {
      setError("This input is too short to be valid email headers.");
      return;
    }

    // Try to parse as JSON in case user pasted JSON payload directly
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed && typeof parsed === 'object' && parsed.headers) {
        onAnalyze(parsed.headers);
        return;
      } else {
        setError("It looks like you pasted JSON. No worries — just paste the raw email headers instead.");
        return;
      }
    } catch (err) {
      // Not JSON, which is what we want!
    }

    onAnalyze(trimmed);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label htmlFor="headers" className="text-lg font-semibold text-brand-text">
            Paste email headers
          </label>
          <p className="text-sm text-brand-text-secondary mb-2">
            Paste the complete, raw headers from a delivered email to start the analysis.
          </p>
          <textarea
            id="headers"
            className="w-full h-80 p-4 border border-brand-border rounded-lg bg-brand-surface font-mono text-sm text-brand-text focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all resize-y"
            placeholder={`Authentication-Results: mx.google.com;\n    spf=pass (google.com: domain of sender@example.com designates 192.0.2.1 as permitted sender)\n    dkim=pass header.i=@example.com header.s=s1 header.b=...;\n    dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=example.com\nReceived: by 2002:a05:6e02:188a:b0:31b:7d4d:23f1 with SMTP id...\nDKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed...\nReturn-Path: <bounce@example.com>\nFrom: "Marketing Team" <marketing@example.com>\nTo: you@example.com\n...`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            spellCheck={false}
          />
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 bg-status-error-bg text-status-error text-sm rounded border border-status-error/20"
          >
            {error}
          </motion.div>
        )}

        <div className="flex justify-start">
          <button
            type="submit"
            className="px-6 py-3 bg-accent text-white font-medium rounded-lg hover:bg-accent/90 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent focus:ring-offset-brand-bg"
          >
            Analyze Email
          </button>
        </div>
      </form>
    </div>
  );
}
