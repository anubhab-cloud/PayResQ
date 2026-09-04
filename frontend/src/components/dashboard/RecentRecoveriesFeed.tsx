import React from 'react';
import { Zap, ArrowRight } from 'lucide-react';

interface RecoveryItem {
  id: string;
  merchant: string;
  brandBg: string;
  brandChar: string;
  amount: string;
  status: 'Recovered' | 'In Progress' | 'Escalated';
  time: string;
}

const mockRecoveries: RecoveryItem[] = [
  {
    id: '1',
    merchant: 'Netflix',
    brandBg: 'bg-black text-red-600 font-extrabold',
    brandChar: 'N',
    amount: '₹499.00',
    status: 'Recovered',
    time: '2m ago',
  },
  {
    id: '2',
    merchant: 'Swiggy',
    brandBg: 'bg-orange-500 text-white font-bold',
    brandChar: 'S',
    amount: '₹234.00',
    status: 'Recovered',
    time: '5m ago',
  },
  {
    id: '3',
    merchant: 'Amazon',
    brandBg: 'bg-slate-900 text-amber-400 font-bold',
    brandChar: 'a',
    amount: '₹1,299.00',
    status: 'Recovered',
    time: '12m ago',
  },
  {
    id: '4',
    merchant: 'Zomato',
    brandBg: 'bg-red-600 text-white font-bold italic',
    brandChar: 'z',
    amount: '₹399.00',
    status: 'In Progress',
    time: '18m ago',
  },
  {
    id: '5',
    merchant: 'Spotify',
    brandBg: 'bg-emerald-500 text-white font-bold',
    brandChar: 'S',
    amount: '₹119.00',
    status: 'Recovered',
    time: '24m ago',
  },
];

export const RecentRecoveriesFeed: React.FC = () => {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 h-full">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <Zap className="h-4 w-4 text-blue-600 dark:text-blue-400 fill-blue-600/10" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Recent Recoveries
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
          {mockRecoveries.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 p-1.5 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-lg shadow-xs text-xs ${item.brandBg}`}
                >
                  {item.brandChar}
                </div>
                <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {item.merchant}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {item.amount}
                </span>
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    item.status === 'Recovered'
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400'
                      : 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
                  }`}
                >
                  {item.status}
                </span>
                <span className="text-[11px] text-slate-400 w-12 text-right">
                  {item.time}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
