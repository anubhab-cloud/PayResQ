import React from 'react';
import {
  LayoutDashboard,
  CreditCard,
  RefreshCw,
  BrainCircuit,
  FileText,
  ShieldAlert,
} from 'lucide-react';

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  pendingApprovalsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPath,
  onNavigate,
  pendingApprovalsCount = 0,
}) => {
  const navItems = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Payments', path: '/transactions', icon: CreditCard },
    {
      label: 'Recoveries',
      path: '/recoveries',
      icon: RefreshCw,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
    },
    { label: 'Intelligence', path: '/intelligence', icon: BrainCircuit },
    { label: 'Audit Log', path: '/audit', icon: FileText },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
      <div>
        {/* Brand */}
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-6 dark:border-slate-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 font-bold text-white shadow-md shadow-indigo-500/30">
            P
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
              PayResQ
            </h1>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-indigo-500">
              Autonomous Recovery
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.path;

            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={`flex w-full items-center justify-between rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 font-semibold'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`h-4 w-4 ${
                      isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="rounded-full bg-amber-500 px-2 py-0.5 text-[10px] font-bold text-white">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Engine Status
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-500">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-ring" />
              Online
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
            XGBoost v1.0 • Redis Worker Active
          </p>
        </div>
      </div>
    </aside>
  );
};
