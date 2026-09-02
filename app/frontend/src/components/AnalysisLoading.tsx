import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle } from 'lucide-react';

export function AnalysisLoading() {
  const [step, setStep] = useState(0);

  const steps = [
    "Reading email headers",
    "Checking SPF, DKIM & DMARC",
    "Checking domain alignment",
    "Identifying the likely cause",
    "Preparing recommendations"
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((s) => (s < steps.length - 1 ? s + 1 : s));
    }, 600);

    return () => clearInterval(timer);
  }, [steps.length]);

  return (
    <div className="w-full max-w-lg mx-auto py-12">
      <div className="flex flex-col gap-6 p-8 bg-brand-surface border border-brand-border rounded-xl shadow-sm">
        <h3 className="text-xl font-semibold text-brand-text mb-2">Analyzing your email...</h3>
        <div className="flex flex-col gap-4">
          {steps.map((label, index) => {
            const isCompleted = index < step;
            const isCurrent = index === step;
            const isPending = index > step;

            return (
              <div key={label} className="flex items-center gap-3">
                <div className="w-5 h-5 flex items-center justify-center shrink-0">
                  <AnimatePresence mode="wait">
                    {isCompleted ? (
                      <motion.div
                        key="completed"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="text-status-success"
                      >
                        <CheckCircle2 size={20} />
                      </motion.div>
                    ) : isCurrent ? (
                      <motion.div
                        key="current"
                        animate={{ opacity: [1, 0.5, 1] }}
                        transition={{ repeat: Infinity, duration: 1.5 }}
                        className="text-accent"
                      >
                        <Circle size={20} />
                      </motion.div>
                    ) : (
                      <motion.div key="pending" className="text-brand-border">
                        <Circle size={20} />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
                <span className={`text-sm ${
                  isCompleted ? "text-brand-text font-medium" : 
                  isCurrent ? "text-brand-text font-medium" : 
                  "text-brand-text-secondary"
                }`}>
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
