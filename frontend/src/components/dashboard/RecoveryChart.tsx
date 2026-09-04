import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { DashboardTrends } from '../../types';
import { LineChart, ChevronDown, Sparkles } from 'lucide-react';

interface RecoveryChartProps {
  trends: DashboardTrends | null;
}

export const RecoveryChart: React.FC<RecoveryChartProps> = ({ trends }) => {
  const data = trends?.trends || [
    { date: 'Aug 28', failed_volume: 31000, recovered_volume: 0 },
    { date: 'Aug 29', failed_volume: 27000, recovered_volume: 0 },
    { date: 'Aug 30', failed_volume: 12000, recovered_volume: 0 },
    { date: 'Aug 31', failed_volume: 2000, recovered_volume: 0 },
    { date: 'Sep 01', failed_volume: 1000, recovered_volume: 1000 },
    { date: 'Sep 02', failed_volume: 1500, recovered_volume: 4000 },
    { date: 'Sep 03', failed_volume: 11000, recovered_volume: 12000 },
  ];

  return (
    <div className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
            <LineChart className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
              Recovery Performance
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Daily failed vs recovered transaction volume
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 text-xs font-semibold">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
              <span className="text-slate-600 dark:text-slate-300">Failed Payments</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              <span className="text-slate-600 dark:text-slate-300">Recovered Payments</span>
            </div>
          </div>

          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300">
            <span>Last 7 days</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </div>
        </div>
      </div>

      {/* Floating Pill Banner Tag */}
      <div className="absolute right-8 top-20 z-10 hidden lg:flex items-center gap-2 rounded-xl bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 border border-emerald-200/80 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800/80 shadow-sm">
        <Sparkles className="h-3.5 w-3.5" />
        <span>Recovery picking up +₹60.3K recovered</span>
      </div>

      <div className="mt-6 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <defs>
              <linearGradient id="colorFailedBlue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorRecoveredGreen" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.15} />
            <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              tickFormatter={(val) => `${val >= 1000 ? `${val / 1000}K` : val}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#1e293b',
                borderRadius: '0.75rem',
                fontSize: '0.75rem',
                color: '#fff',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
              }}
            />
            <Area
              type="monotone"
              dataKey="failed_volume"
              name="Failed (₹)"
              stroke="#2563EB"
              fillOpacity={1}
              fill="url(#colorFailedBlue)"
              strokeWidth={3}
              dot={{ r: 4, fill: '#2563EB' }}
            />
            <Area
              type="monotone"
              dataKey="recovered_volume"
              name="Recovered (₹)"
              stroke="#10B981"
              fillOpacity={1}
              fill="url(#colorRecoveredGreen)"
              strokeWidth={3}
              dot={{ r: 4, fill: '#10B981' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
