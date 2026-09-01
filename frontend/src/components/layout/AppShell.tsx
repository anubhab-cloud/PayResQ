import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { DemoRunResponse } from '../../types';

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
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Sidebar */}
      <Sidebar
        currentPath={currentPath}
        onNavigate={onNavigate}
        pendingApprovalsCount={pendingApprovalsCount}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          darkMode={darkMode}
          onToggleTheme={onToggleTheme}
          onDemoCompleted={onDemoCompleted}
        />
        <main className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
};
