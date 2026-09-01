import React from 'react';
import { Transaction } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { ChevronRight, ExternalLink } from 'lucide-react';

interface RecentTransactionsTableProps {
  transactions: Transaction[];
  onSelectTransaction: (txId: string) => void;
}

export const RecentTransactionsTable: React.FC<RecentTransactionsTableProps> = ({
  transactions,
  onSelectTransaction,
}) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-200 p-5 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
            Recent Payment Recovery Queue
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Live failed and recovered payment events
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 uppercase text-slate-500 dark:bg-slate-950 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="px-5 py-3">Transaction ID</th>
              <th className="px-5 py-3">Amount</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Created Time</th>
              <th className="px-5 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                  No payment transactions found in database
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr
                  key={tx.id}
                  onClick={() => onSelectTransaction(tx.id)}
                  className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <td className="px-5 py-3.5 font-mono text-indigo-600 dark:text-indigo-400 font-semibold">
                    {tx.external_transaction_id || tx.id.slice(0, 8)}
                  </td>
                  <td className="px-5 py-3.5 font-semibold text-slate-900 dark:text-white">
                    ₹{tx.amount.toLocaleString('en-IN')} {tx.currency}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={tx.status} size="sm" />
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {new Date(tx.created_at).toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectTransaction(tx.id);
                      }}
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 font-semibold"
                    >
                      <span>Investigate</span>
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
