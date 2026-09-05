import React from 'react';
import { ArrowRight } from 'lucide-react';

export const WelcomeBanner: React.FC = () => {
  return (
    <div className="relative overflow-hidden rounded-xl bg-white p-6 sm:p-7 text-slate-900 shadow-xs border border-slate-200 dark:border-slate-800 dark:bg-slate-900 dark:text-white">
      <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="space-y-1.5 max-w-2xl">
          <span className="text-[11px] font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">
            WELCOME BACK
          </span>

          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Maximize your revenue recovery with{' '}
            <span className="text-blue-600 dark:text-blue-400">AI</span>
          </h1>

          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            PayResQ analyzes failed payments, predicts optimal recovery actions, and safely executes them — so you don't lose good customers.
          </p>
        </div>

        {/* Right Watermark Graphic / Callout */}
        <div className="hidden lg:flex flex-col items-end text-right shrink-0">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 dark:bg-slate-800 text-blue-600 dark:text-blue-400 mb-1">
            <svg viewBox="0 0 100 100" className="h-6 w-6" fill="currentColor">
              <path d="M20 85L55 15H80L45 85H20Z" />
              <path d="M45 45L75 15H92L62 45H45Z" />
            </svg>
          </div>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 max-w-[180px] leading-snug">
            Turn failed payments into growth opportunities.
          </p>
        </div>
      </div>
    </div>
  );
};
