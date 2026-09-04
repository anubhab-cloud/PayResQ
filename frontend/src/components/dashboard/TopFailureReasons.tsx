import React from 'react';
import { AlertTriangle, ArrowRight } from 'lucide-react';

interface ReasonItem {
  reason: string;
  percentage: number;
  colorBg: string;
}

const defaultReasons: ReasonItem[] = [
  { reason: 'Insufficient Balance', percentage: 32, colorBg: 'bg-red-500' },
  { reason: 'UPI Timeout', percentage: 24, colorBg: 'bg-orange-500' },
  { reason: 'Bank Declined', percentage: 18, colorBg: 'bg-amber-500' },
  { reason: 'Incorrect Details', percentage: 14, colorBg: 'bg-blue-500' },
  { reason: 'Risk Control', percentage: 12, colorBg: 'bg-slate-400' },
];

export const TopFailureReasons: React.FC = () => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Top Failure Reasons
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
        {defaultReasons.map((item) => (
          <div key={item.reason} className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2.5">
              <span className={`h-2.5 w-2.5 rounded-full ${item.colorBg}`} />
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                {item.reason}
              </span>
            </div>
            <span className="font-bold text-slate-900 dark:text-white">
              {item.percentage}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
