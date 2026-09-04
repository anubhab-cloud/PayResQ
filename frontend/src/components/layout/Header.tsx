import React, { useState } from 'react';
import { Search, Calendar, Play, Loader2, ChevronDown, Menu, Sun, Moon } from 'lucide-react';
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
  const [searchQuery, setSearchQuery] = useState('');

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
    <header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 backdrop-blur-md px-4 sm:px-8 dark:border-slate-800/80 dark:bg-slate-900/95 sticky top-0 z-30">
      {/* Left: Mobile Toggle + Search Bar */}
      <div className="flex items-center gap-4 flex-1 max-w-xl">
        <button
          onClick={onToggleMobileMenu}
          className="md:hidden flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 dark:border-slate-800 dark:text-slate-300"
          aria-label="Toggle Mobile Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Global Search Bar */}
        <div className="relative w-full max-w-md hidden sm:block">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transactions, customers, or insights..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50/80 py-2.5 pl-10 pr-12 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-950/60 dark:text-white"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 rounded bg-slate-200/70 dark:bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500 dark:text-slate-400">
            <span>Ctrl</span>
            <span>K</span>
          </div>
        </div>
      </div>

      {/* Right Actions Header */}
      <div className="flex items-center gap-3">
        {/* Timeframe Filter Dropdown */}
        <div className="hidden md:flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
          <Calendar className="h-4 w-4 text-slate-400" />
          <span>Last 7 days</span>
          <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
        </div>

        {/* Primary Action Button: Run Demo Scenario */}
        <button
          onClick={handleRunDemo}
          disabled={isExecutingDemo}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/30 transition-all hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/50 active:scale-95 disabled:opacity-50"
        >
          {isExecutingDemo ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Executing Loop...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Run Demo Scenario</span>
            </>
          )}
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          aria-label="Toggle Theme"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {darkMode ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-600" />
          )}
        </button>

        {/* User Profile Dropdown */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 font-bold text-white shadow-sm text-xs">
            A
          </div>
          <span className="hidden lg:inline-block text-xs font-semibold text-slate-700 dark:text-slate-200">
            Anubhab
          </span>
          <ChevronDown className="hidden lg:inline-block h-3.5 w-3.5 text-slate-400" />
        </div>
      </div>
    </header>
  );
};
