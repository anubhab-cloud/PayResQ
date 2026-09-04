import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

export const WelcomeBanner: React.FC = () => {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl border border-indigo-900/40">
      <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-500/10 px-3 py-1 text-[10px] font-extrabold uppercase tracking-widest text-blue-400 border border-blue-500/20">
            <Sparkles className="h-3 w-3" />
            <span>WELCOME BACK</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight leading-tight">
            Maximize your revenue recovery with{' '}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-blue-500 bg-clip-text text-transparent">
              AI
            </span>
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-medium">
            PayResQ analyzes failed payments, predicts the best recovery actions, and safely executes them — so you don't lose good customers.
          </p>
        </div>

        {/* Right Watermark Graphic / Callout */}
        <div className="hidden lg:flex flex-col items-end text-right shrink-0">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/20 border border-blue-500/30 mb-2">
            <svg viewBox="0 0 100 100" className="h-7 w-7 text-blue-400" fill="currentColor">
              <path d="M20 85L55 15H80L45 85H20Z" />
              <path d="M45 45L75 15H92L62 45H45Z" />
            </svg>
          </div>
          <p className="text-xs font-semibold text-slate-300 max-w-[180px] leading-snug">
            Turn failed payments into growth opportunities.
          </p>
        </div>
      </div>

      {/* Decorative Glow Background */}
      <div className="absolute right-0 top-0 h-full w-1/2 bg-gradient-to-l from-blue-600/10 to-transparent pointer-events-none" />
    </div>
  );
};
