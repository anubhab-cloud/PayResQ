import React from 'react';
import { RecoveryAction } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { ChevronRight } from 'lucide-react';

interface RecoveryOperationsTableProps {
  actions: RecoveryAction[];
  onSelectAction: (action: RecoveryAction) => void;
  onOpenApproval?: (tx: any) => void;
}

export const RecoveryOperationsTable: React.FC<RecoveryOperationsTableProps> = ({
  actions,
  onSelectAction,
  onOpenApproval,
}) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-200 p-5 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
            Recovery Action Queue & Audit Status
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Pending, Executing, and Completed recovery actions
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 uppercase text-slate-500 dark:bg-slate-950 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="px-5 py-3">Action ID</th>
              <th className="px-5 py-3">Action Type</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Confidence</th>
              <th className="px-5 py-3">Created Time</th>
              <th className="px-5 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
            {actions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                  No recovery actions currently in queue
                </td>
              </tr>
            ) : (
              actions.map((act) => (
                <tr
                  key={act.id}
                  onClick={() => onSelectAction(act)}
                  className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <td className="px-5 py-3.5 font-mono text-indigo-600 dark:text-indigo-400 font-semibold">
                    {act.id.slice(0, 8)}
                  </td>
                  <td className="px-5 py-3.5 font-semibold text-slate-800 dark:text-slate-200">
                    {act.action_type.replace(/_/g, ' ')}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={act.status} size="sm" />
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-600 dark:text-slate-300">
                    {act.confidence ? `${(act.confidence * 100).toFixed(0)}%` : 'N/A'}
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {new Date(act.created_at).toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    {act.status === 'PENDING' && onOpenApproval ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenApproval({ id: act.transaction_id, amount: 75000, currency: 'INR' });
                        }}
                        className="rounded-lg bg-amber-500 px-2.5 py-1 text-xs font-semibold text-white hover:bg-amber-600 shadow-sm"
                      >
                        Review
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectAction(act);
                        }}
                        className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 font-semibold"
                      >
                        <span>Details</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    )}
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
