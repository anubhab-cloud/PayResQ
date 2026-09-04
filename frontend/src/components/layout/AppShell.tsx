import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { DemoRunResponse } from '../../types';
import { X } from 'lucide-react';

interface AppShellProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  darkMode: boolean;
  onToggleTheme: () => void;
  onDemoCompleted?: (demoResult: DemoRunResponse) => void;
  pendingApprovalsCount?: number;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentPath,
  onNavigate,
  darkMode,
  onToggleTheme,
  onDemoCompleted,
  pendingApprovalsCount = 0,
  children,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Desktop Sidebar (hidden on mobile) */}
      <div className="hidden md:flex md:shrink-0">
        <Sidebar
          currentPath={currentPath}
          onNavigate={onNavigate}
          pendingApprovalsCount={pendingApprovalsCount}
        />
      </div>

      {/* Mobile Sidebar Overlay / Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          {/* Backdrop blur overlay */}
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />

          {/* Slide-out Drawer */}
          <div className="relative flex w-4/5 max-w-xs flex-1 flex-col bg-white dark:bg-slate-900 shadow-2xl">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 dark:border-slate-800 dark:text-slate-400"
              aria-label="Close menu"
            >
              <X className="h-4 w-4" />
            </button>
            <Sidebar
              currentPath={currentPath}
              onNavigate={onNavigate}
              pendingApprovalsCount={pendingApprovalsCount}
              onCloseMobile={() => setMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          darkMode={darkMode}
          onToggleTheme={onToggleTheme}
          onDemoCompleted={onDemoCompleted}
          onToggleMobileMenu={() => setMobileMenuOpen(true)}
        />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
};
