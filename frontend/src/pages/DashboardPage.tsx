import React, { useEffect, useState } from 'react';
import { dashboardApi, transactionsApi } from '../api/client';
import { DashboardSummary, DashboardTrends, DashboardFailureBreakdown, Transaction } from '../types';
import { KpiGrid } from '../components/dashboard/KpiGrid';
import { RecoveryChart } from '../components/dashboard/RecoveryChart';
import { FailureDistribution } from '../components/dashboard/FailureDistribution';
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
    <div className="space-y-6">
      {/* Top KPI Cards */}
      <KpiGrid summary={summary} />

      {/* Main Chart */}
      <RecoveryChart trends={trends} />

      {/* Failure Breakdown & Recent Table */}
      <FailureDistribution breakdown={breakdown} />

      <RecentTransactionsTable
        transactions={transactions}
        onSelectTransaction={onSelectTransaction}
      />
    </div>
  );
};
