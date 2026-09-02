import React from 'react';

export function AppHeader() {
  return (
    <header className="border-b border-brand-border bg-brand-surface py-4 px-6 md:px-8">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-accent text-white font-bold p-1.5 rounded text-xs tracking-wider">
            EDC
          </div>
          <span className="font-semibold text-lg text-brand-text">
            Email Deliverability Copilot
          </span>
        </div>
        <button
          onClick={() => alert("Gmail: Open email → three dots → 'Show original' → Copy everything.\n\nOutlook: Open message → More actions → View → View message details.\n\nApple Mail: View → Message → All Headers.")}
          className="text-sm text-brand-text-secondary hover:text-brand-text transition-colors"
        >
          Where do I find my email headers?
        </button>
      </div>
    </header>
  );
}
