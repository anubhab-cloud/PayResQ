import React from 'react';
import {
  Home,
  CreditCard,
  RefreshCw,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Settings,
  Sparkles,
} from 'lucide-react';
import { PayResQLogo } from '../common/PayResQLogo';

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  pendingApprovalsCount?: number;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPath,
  onNavigate,
  pendingApprovalsCount = 11,
  onCloseMobile,
}) => {
  const navItems = [
    { label: 'Overview', path: '/', icon: Home },
    { label: 'Payments', path: '/transactions', icon: CreditCard },
    { label: 'Recoveries', path: '/recoveries', icon: RefreshCw },
    {
      label: 'Intelligence',
      path: '/intelligence',
      icon: BrainCircuit,
      badgeText: 'AI',
      badgeColor: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    },
    {
      label: 'Approvals',
      path: '/approvals',
      icon: CheckCircle2,
      countBadge: pendingApprovalsCount,
    },
    { label: 'Audit Log', path: '/audit', icon: FileText },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleNavClick = (path: string) => {
    onNavigate(path);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  return (
    <aside className="w-64 h-full bg-[#0A0E1A] text-slate-300 flex flex-col justify-between select-none border-r border-slate-800/70 shrink-0">
      <div>
        {/* Brand Header */}
        <div className="flex h-20 items-center px-6 border-b border-slate-800/60">
          <PayResQLogo size="md" showTagline={true} />
        </div>

        {/* Navigation List */}
        <nav className="p-3.5 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.path;

            return (
              <button
                key={item.path + item.label}
                onClick={() => handleNavClick(item.path)}
                className={`flex w-full items-center justify-between rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'bg-blue-600 text-white font-semibold shadow-sm'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-100'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`h-4.5 w-4.5 ${
                      isActive ? 'text-white' : 'text-slate-400'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                <div className="flex items-center gap-2">
                  {item.badgeText && (
                    <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold tracking-wider ${item.badgeColor}`}>
                      {item.badgeText}
                    </span>
                  )}
                  {item.countBadge !== undefined && item.countBadge > 0 && (
                    <span className="rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 text-[11px] font-bold">
                      {item.countBadge}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* AI Working Banner Footer */}
      <div className="p-3.5">
        <div className="relative overflow-hidden rounded-xl border border-slate-800/80 bg-[#111625] p-4 text-white shadow-xs">
          <div className="relative z-10 space-y-1">
            <div className="flex items-center gap-1.5 text-blue-400 text-xs font-semibold uppercase tracking-wider">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Autonomous AI Agent</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed pt-0.5">
              Intelligent RCA & recovery decisioning active.
            </p>
          </div>

          {/* Background emblem watermark */}
          <div className="absolute right-[-8px] bottom-[-8px] opacity-10 pointer-events-none">
            <svg viewBox="0 0 100 100" className="h-20 w-20 text-blue-400" fill="currentColor">
              <path d="M20 85L55 15H80L45 85H20Z" />
              <path d="M45 45L75 15H92L62 45H45Z" />
            </svg>
          </div>
        </div>
      </div>
    </aside>
  );
};
