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
      badgeColor: 'bg-blue-600 text-white',
    },
    {
      label: 'Approvals',
      path: '/recoveries',
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
    <aside className="w-64 h-full bg-[#0B1120] text-slate-300 flex flex-col justify-between select-none border-r border-slate-800/80 shrink-0">
      <div>
        {/* Brand Header */}
        <div className="flex h-20 items-center px-6 border-b border-slate-800/60">
          <PayResQLogo size="md" showTagline={true} />
        </div>

        {/* Navigation List */}
        <nav className="p-4 space-y-1.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.path;

            return (
              <button
                key={item.path + item.label}
                onClick={() => handleNavClick(item.path)}
                className={`flex w-full items-center justify-between rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-600/30 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-3.5">
                  <Icon
                    className={`h-4.5 w-4.5 ${
                      isActive ? 'text-white' : 'text-slate-400'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                <div className="flex items-center gap-2">
                  {item.badgeText && (
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold uppercase ${item.badgeColor}`}>
                      {item.badgeText}
                    </span>
                  )}
                  {item.countBadge !== undefined && item.countBadge > 0 && (
                    <span className="rounded-full bg-red-500 px-2 py-0.5 text-[11px] font-extrabold text-white">
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
      <div className="p-4">
        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 to-[#0F172A] p-4 text-white shadow-lg">
          <div className="relative z-10 space-y-1.5">
            <div className="flex items-center gap-1.5 text-blue-400 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="h-3.5 w-3.5" />
              <span>AI Working for Your Revenue</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Smarter retries. Higher recovery. Happier customers.
            </p>
          </div>

          {/* Background Watermark emblem */}
          <div className="absolute right-[-10px] bottom-[-10px] opacity-10 pointer-events-none">
            <svg viewBox="0 0 100 100" className="h-24 w-24 text-blue-400" fill="currentColor">
              <path d="M20 85L55 15H80L45 85H20Z" />
              <path d="M45 45L75 15H92L62 45H45Z" />
            </svg>
          </div>
        </div>
      </div>
    </aside>
  );
};
