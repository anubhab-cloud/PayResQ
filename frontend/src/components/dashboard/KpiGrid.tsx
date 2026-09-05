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
      iconColor: 'text-rose-500',
      iconBg: 'bg-rose-50 dark:bg-rose-950/30',
    },
    {
      title: 'Recovered Revenue',
      value: `₹${recovered.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      trend: '↑ 28%',
      trendSub: 'vs. previous period',
      trendPositive: true,
      icon: CheckCircle2,
      iconColor: 'text-emerald-500',
      iconBg: 'bg-emerald-50 dark:bg-emerald-950/30',
    },
    {
      title: 'Recovery Rate',
      value: `${rate}%`,
      trend: '↑ 6.4%',
      trendSub: 'vs. previous period',
      trendPositive: true,
      icon: TrendingUp,
      iconColor: 'text-blue-600 dark:text-blue-400',
      iconBg: 'bg-blue-50 dark:bg-blue-950/30',
    },
    {
      title: 'Failed Payments',
      value: failedCount.toString(),
      trend: '↓ 18%',
      trendSub: 'awaiting/processed',
      trendPositive: true,
      icon: CreditCard,
      iconColor: 'text-indigo-500',
      iconBg: 'bg-indigo-50 dark:bg-indigo-950/30',
    },
    {
      title: 'Human Approvals',
      value: approvalsCount.toString(),
      trend: '',
      trendSub: 'gated high-value items',
      trendPositive: true,
      icon: UserCheck,
      iconColor: 'text-amber-500',
      iconBg: 'bg-amber-50 dark:bg-amber-950/30',
    },
  ];

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div
            key={idx}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-colors dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                {kpi.title}
              </span>
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${kpi.iconBg} ${kpi.iconColor}`}>
                <Icon className="h-4 w-4" />
              </div>
            </div>

            <div className="mt-3">
              <div className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {kpi.value}
              </div>

              <div className="mt-1.5 flex items-center gap-1.5 text-[11px]">
                {kpi.trend && (
                  <span
                    className={`font-semibold ${
                      kpi.trendPositive
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {kpi.trend}
                  </span>
                )}
                <span className="text-slate-400 dark:text-slate-500 truncate">
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
