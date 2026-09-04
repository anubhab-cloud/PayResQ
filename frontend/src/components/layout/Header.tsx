import React, { useState } from 'react';
import { Sun, Moon, Play, Loader2, Sparkles, Menu } from 'lucide-react';
import { dashboardApi } from '../../api/client';
import { DemoRunResponse } from '../../types';

interface HeaderProps {
  darkMode: boolean;
  onToggleTheme: () => void;
  onDemoCompleted?: (demoResult: DemoRunResponse) => void;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  darkMode,
  onToggleTheme,
  onDemoCompleted,
  onToggleMobileMenu,
}) => {
  const [isExecutingDemo, setIsExecutingDemo] = useState(false);

  const handleRunDemo = async () => {
    try {
      setIsExecutingDemo(true);
      const res = await dashboardApi.runDemo();
      if (onDemoCompleted) {
        onDemoCompleted(res);
      }
    } catch (err) {
      console.error('Demo run error:', err);
    } finally {
      setIsExecutingDemo(false);
    }
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 backdrop-blur-md px-4 sm:px-6 dark:border-slate-800 dark:bg-slate-900/90 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        {/* Mobile Hamburger Toggle */}
        <button
          onClick={onToggleMobileMenu}
          className="md:hidden flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 dark:border-slate-800 dark:text-slate-300"
          aria-label="Toggle Mobile Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <h2 className="text-xs sm:text-sm font-semibold tracking-wide text-slate-700 dark:text-slate-200 truncate">
          Autonomous Revenue Ops
        </h2>
        <span className="hidden lg:inline-block rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-medium text-indigo-500 border border-indigo-500/20">
          Agent-Driven Recovery
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Interactive Run Demo Scenario Button */}
        <button
          onClick={handleRunDemo}
          disabled={isExecutingDemo}
          className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm shadow-indigo-500/30 transition-all hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/50 disabled:opacity-50"
        >
          {isExecutingDemo ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>Running Agent Loop...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Run Demo Scenario</span>
              <Sparkles className="h-3 w-3 opacity-80" />
            </>
          )}
        </button>

        {/* Dark/Light Theme Toggle */}
        <button
          onClick={onToggleTheme}
          aria-label="Toggle Theme"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {darkMode ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-600" />
          )}
        </button>
      </div>
    </header>
  );
};
