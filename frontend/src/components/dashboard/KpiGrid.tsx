import React from 'react';
import { DashboardSummary } from '../../types';
import { Zap, CheckCircle2, TrendingUp, CreditCard, UserCheck } from 'lucide-react';

interface KpiGridProps {
  summary?: DashboardSummary | null;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ summary }) => {
  const atRisk = summary?.revenue_at_risk ?? 200951.07;
  const recovered = summary?.recovered_revenue ?? 60370.99;
  const rate = summary?.recovery_rate ?? 23.1;
  const failedCount = summary?.failed_transactions ?? 51;
  const approvalsCount = summary?.pending_human_approvals ?? 11;

  const kpis = [
    {
      title: 'Revenue at Risk',
      value: `₹${atRisk.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      trend: '↑ 12%',
      trendSub: 'vs. previous period',
      trendPositive: false,
      icon: Zap,
      iconBg: 'bg-red-500/10 text-red-500 border border-red-500/20',
    },
    {
      title: 'Recovered Revenue',
      value: `₹${recovered.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      trend: '↑ 28%',
      trendSub: 'vs. previous period',
      trendPositive: true,
      icon: CheckCircle2,
      iconBg: 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20',
    },
    {
      title: 'Recovery Rate',
      value: `${rate}%`,
      trend: '↑ 6.4%',
      trendSub: 'vs. previous period',
      trendPositive: true,
      icon: TrendingUp,
      iconBg: 'bg-blue-500/10 text-blue-500 border border-blue-500/20',
    },
    {
      title: 'Failed Payments',
      value: failedCount.toString(),
      trend: '↓ 18%',
      trendSub: 'awaiting/processed',
      trendPositive: true,
      icon: CreditCard,
      iconBg: 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20',
    },
    {
      title: 'Human Approvals',
      value: approvalsCount.toString(),
      trend: '',
      trendSub: 'gated high-value items',
      trendPositive: true,
      icon: UserCheck,
      iconBg: 'bg-amber-500/10 text-amber-500 border border-amber-500/20',
    },
  ];

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div
            key={idx}
            className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                {kpi.title}
              </span>
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${kpi.iconBg}`}>
                <Icon className="h-4.5 w-4.5" />
              </div>
            </div>

            <div className="mt-4">
              <div className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                {kpi.value}
              </div>

              <div className="mt-2 flex items-center gap-1.5 text-[11px]">
                {kpi.trend && (
                  <span
                    className={`font-bold ${
                      kpi.trendPositive
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-500 dark:text-red-400'
                    }`}
                  >
                    {kpi.trend}
                  </span>
                )}
                <span className="text-slate-400 dark:text-slate-500 font-medium truncate">
                  {kpi.trendSub}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
