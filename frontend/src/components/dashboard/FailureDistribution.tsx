import React from 'react';
import { DashboardFailureBreakdown } from '../../types';

interface FailureDistributionProps {
  breakdown: DashboardFailureBreakdown | null;
}

export const FailureDistribution: React.FC<FailureDistributionProps> = ({ breakdown }) => {
  const byBank = breakdown?.by_bank || [];
  const byMethod = breakdown?.by_method || [];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Bank Breakdown */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white border-b border-slate-200 pb-3 dark:border-slate-800">
          Failure Rate by Bank
        </h3>
        <div className="mt-4 space-y-3">
          {byBank.length === 0 ? (
            <p className="text-xs text-slate-400">No bank failure statistics</p>
          ) : (
            byBank.map((stat) => (
              <div key={stat.bank} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-700 dark:text-slate-300">{stat.bank}</span>
                  <span className="text-slate-500">
                    {stat.failed_count}/{stat.total_count} ({(stat.failure_rate * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all"
                    style={{ width: `${Math.min(stat.failure_rate * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Payment Method Breakdown */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white border-b border-slate-200 pb-3 dark:border-slate-800">
          Failure Rate by Payment Method
        </h3>
        <div className="mt-4 space-y-3">
          {byMethod.length === 0 ? (
            <p className="text-xs text-slate-400">No payment method statistics</p>
          ) : (
            byMethod.map((stat) => (
              <div key={stat.payment_method} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-700 dark:text-slate-300">{stat.payment_method}</span>
                  <span className="text-slate-500">
                    {stat.failed_count}/{stat.total_count} ({(stat.failure_rate * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <div
                    className="h-full bg-violet-500 rounded-full transition-all"
                    style={{ width: `${Math.min(stat.failure_rate * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
