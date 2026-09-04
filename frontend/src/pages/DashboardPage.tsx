import React, { useEffect, useState } from 'react';
import { dashboardApi, transactionsApi } from '../api/client';
import { DashboardSummary, DashboardTrends, DashboardFailureBreakdown, Transaction } from '../types';
import { WelcomeBanner } from '../components/dashboard/WelcomeBanner';
import { KpiGrid } from '../components/dashboard/KpiGrid';
import { RecoveryChart } from '../components/dashboard/RecoveryChart';
import { RecentRecoveriesFeed } from '../components/dashboard/RecentRecoveriesFeed';
import { FailureDistribution } from '../components/dashboard/FailureDistribution';
import { TopFailureReasons } from '../components/dashboard/TopFailureReasons';
import { RecentTransactionsTable } from '../components/dashboard/RecentTransactionsTable';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

interface DashboardPageProps {
  onSelectTransaction: (id: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onSelectTransaction }) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<DashboardTrends | null>(null);
  const [breakdown, setBreakdown] = useState<DashboardFailureBreakdown | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [sumData, trendData, breakData, txData] = await Promise.all([
          dashboardApi.getSummary(),
          dashboardApi.getTrends(7),
          dashboardApi.getFailureBreakdown(),
          transactionsApi.list(10, 0),
        ]);
        setSummary(sumData);
        setTrends(trendData);
        setBreakdown(breakData);
        setTransactions(txData);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton rows={2} />
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-8">
      {/* Hero Welcome Banner */}
      <WelcomeBanner />

      {/* Top 5 KPI Cards */}
      <KpiGrid summary={summary} />

      {/* Middle Row: Recovery Chart + Recent Recoveries Feed */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <RecoveryChart trends={trends} />
        </div>
        <div className="lg:col-span-4">
          <RecentRecoveriesFeed />
        </div>
      </div>

      {/* Bottom Row: Failure Rate by Bank, Failure Rate by Payment Method, Top Failure Reasons */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <FailureDistribution breakdown={breakdown} />
        <TopFailureReasons />
      </div>

      {/* Recent Live Transactions */}
      <div className="pt-2">
        <RecentTransactionsTable
          transactions={transactions}
          onSelectTransaction={onSelectTransaction}
        />
      </div>
    </div>
  );
};
