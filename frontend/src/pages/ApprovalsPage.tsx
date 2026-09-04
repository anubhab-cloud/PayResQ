import React from 'react';
import { ShieldAlert, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface ApprovalItem {
  id: string;
  txId: string;
  customer: string;
  amount: string;
  bank: string;
  recommendedAction: string;
  reason: string;
  riskScore: number;
  time: string;
}

const mockApprovals: ApprovalItem[] = [
  {
    id: 'app-1',
    txId: 'TX-948201',
    customer: 'Reliance Retail Ltd',
    amount: '₹1,25,000.00',
    bank: 'HDFC Bank',
    recommendedAction: 'Send Custom Payment Link',
    reason: 'Amount exceeds automatic threshold (₹50,000)',
    riskScore: 0.12,
    time: '10m ago',
  },
  {
    id: 'app-2',
    txId: 'TX-948194',
    customer: 'TechCorp Solutions',
    amount: '₹84,500.00',
    bank: 'ICICI Bank',
    recommendedAction: 'Retry after 20 minute delay',
    reason: 'High value B2B transaction requires sign-off',
    riskScore: 0.08,
    time: '25m ago',
  },
  {
    id: 'app-3',
    txId: 'TX-948188',
    customer: 'Apex Logistics',
    amount: '₹62,300.00',
    bank: 'SBI',
    recommendedAction: 'Request Payment Method Change',
    reason: 'Card expired & amount > ₹50,000 limit',
    riskScore: 0.15,
    time: '42m ago',
  },
];

export const ApprovalsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Human Approvals Queue
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            High-value and policy-gated recovery actions requiring manual operator authorization.
          </p>
        </div>
        <span className="inline-flex items-center rounded-full bg-red-100 dark:bg-red-950/60 px-3 py-1 text-xs font-bold text-red-700 dark:text-red-400">
          11 Pending Approvals
        </span>
      </div>

      <div className="grid gap-4">
        {mockApprovals.map((item) => (
          <div
            key={item.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
          >
            <div className="space-y-2">
              <div className="flex items-center space-x-3">
                <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                  {item.txId}
                </span>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {item.customer}
                </span>
                <span className="inline-flex items-center rounded bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700 dark:bg-amber-950/50 dark:text-amber-400">
                  <AlertTriangle className="mr-1 h-3 w-3" /> Policy Gated
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                <strong className="text-slate-900 dark:text-slate-200">Recommended Action:</strong>{' '}
                {item.recommendedAction} — <em>"{item.reason}"</em>
              </p>
              <div className="flex items-center space-x-4 text-[11px] text-slate-500 dark:text-slate-400">
                <span>Bank: {item.bank}</span>
                <span>•</span>
                <span>Risk Score: {(item.riskScore * 100).toFixed(0)}%</span>
                <span>•</span>
                <span>Received {item.time}</span>
              </div>
            </div>

            <div className="flex items-center space-x-4 justify-between md:justify-end border-t pt-3 md:border-t-0 md:pt-0 border-slate-100 dark:border-slate-800">
              <span className="text-lg font-extrabold text-slate-900 dark:text-white">
                {item.amount}
              </span>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  <XCircle className="h-3.5 w-3.5 text-red-500" />
                  <span>Reject</span>
                </button>
                <button
                  type="button"
                  className="inline-flex items-center space-x-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  <span>Approve & Execute</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
