import React from 'react';
import { StatCard } from '../common/StatCard';
import { DashboardSummary } from '../../types';
import { IndianRupee, ShieldAlert, CheckCircle2, AlertTriangle, Activity } from 'lucide-react';

interface KpiGridProps {
  summary: DashboardSummary | null;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ summary }) => {
  const atRisk = summary ? `₹${summary.revenue_at_risk.toLocaleString('en-IN')}` : '₹0';
  const recovered = summary ? `₹${summary.recovered_revenue.toLocaleString('en-IN')}` : '₹0';
  const rate = summary ? `${summary.recovery_rate}%` : '0.0%';
  const failedCount = summary ? summary.failed_transactions : 0;
  const pendingApprovals = summary ? summary.pending_human_approvals : 0;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <StatCard
        title="Revenue at Risk"
        value={atRisk}
        subtitle="Total failed transactions"
        icon={IndianRupee}
        accentColor="rose"
      />
      <StatCard
        title="Recovered Revenue"
        value={recovered}
        subtitle="Successfully recovered"
        icon={CheckCircle2}
        accentColor="emerald"
        trend={{ value: 'Real-time', isPositive: true }}
      />
      <StatCard
        title="Recovery Rate"
        value={rate}
        subtitle="AI strategy efficiency"
        icon={Activity}
        accentColor="indigo"
      />
      <StatCard
        title="Failed Payments"
        value={failedCount}
        subtitle="Awaiting/processed"
        icon={ShieldAlert}
        accentColor="sky"
      />
      <StatCard
        title="Human Approvals"
        value={pendingApprovals}
        subtitle="Gated high-value items"
        icon={AlertTriangle}
        accentColor="amber"
      />
    </div>
  );
};
