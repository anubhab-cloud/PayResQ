import React from 'react';
import { Landmark, CreditCard, ArrowRight } from 'lucide-react';
import { DashboardFailureBreakdown } from '../../types';

interface FailureDistributionProps {
  breakdown: DashboardFailureBreakdown | null;
}

const fallbackBankData = [
  { name: 'HDFC', rate: 15.6 },
  { name: 'SBI', rate: 12.4 },
  { name: 'ICICI', rate: 11.2 },
  { name: 'Axis Bank', rate: 8.9 },
];

const fallbackMethodData = [
  { name: 'UPI', rate: 10.9 },
  { name: 'Credit Card', rate: 8.3 },
  { name: 'Debit Card', rate: 6.1 },
  { name: 'Net Banking', rate: 4.2 },
];

export const FailureDistribution: React.FC<FailureDistributionProps> = ({ breakdown }) => {
  const bankStats = breakdown?.by_bank?.length
    ? breakdown.by_bank.map((b) => ({
        name: b.bank,
        rate: Number((b.failure_rate * 100).toFixed(1)),
      }))
    : fallbackBankData;

  const methodStats = breakdown?.by_method?.length
    ? breakdown.by_method.map((m) => ({
        name: m.payment_method,
        rate: Number((m.failure_rate * 100).toFixed(1)),
      }))
    : fallbackMethodData;

  return (
    <>
      {/* Bank Breakdown */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <Landmark className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Failure Rate by Bank
            </h3>
          </div>
          <button
            type="button"
            className="flex items-center space-x-1 text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            <span>View all</span>
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="mt-4 space-y-3.5">
          {bankStats.map((stat) => (
            <div key={stat.name} className="flex items-center justify-between space-x-4 text-xs">
              <span className="w-20 font-semibold text-slate-700 dark:text-slate-300 truncate">
                {stat.name}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full bg-blue-600 rounded-full transition-all"
                  style={{ width: `${Math.min((stat.rate / 25) * 100, 100)}%` }}
                />
              </div>
              <span className="w-12 text-right font-bold text-slate-700 dark:text-slate-300">
                {stat.rate}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Payment Method Breakdown */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <CreditCard className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Failure Rate by Payment Method
            </h3>
          </div>
          <button
            type="button"
            className="flex items-center space-x-1 text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            <span>View all</span>
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="mt-4 space-y-3.5">
          {methodStats.map((stat) => (
            <div key={stat.name} className="flex items-center justify-between space-x-4 text-xs">
              <span className="w-24 font-semibold text-slate-700 dark:text-slate-300 truncate">
                {stat.name}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full bg-blue-600 rounded-full transition-all"
                  style={{ width: `${Math.min((stat.rate / 20) * 100, 100)}%` }}
                />
              </div>
              <span className="w-12 text-right font-bold text-slate-700 dark:text-slate-300">
                {stat.rate}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};
