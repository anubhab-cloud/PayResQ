import React, { useEffect, useState } from 'react';
import { transactionsApi } from '../api/client';
import { RecoveryAction } from '../types';
import { RecoveryOperationsTable } from '../components/recovery/RecoveryOperationsTable';
import { HumanApprovalModal } from '../components/recovery/HumanApprovalModal';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

interface RecoveriesPageProps {
  onSelectTransaction: (id: string) => void;
}

export const RecoveriesPage: React.FC<RecoveriesPageProps> = ({ onSelectTransaction }) => {
  const [actions, setActions] = useState<RecoveryAction[]>([]);
  const [approvalTx, setApprovalTx] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchActions = async () => {
    try {
      setIsLoading(true);
      // Fetch recent transaction recovery actions
      const txs = await transactionsApi.list(30, 0);
      const allActions: RecoveryAction[] = [];

      for (const t of txs) {
        try {
          const raList = await transactionsApi.getRecoveryActions(t.id);
          allActions.push(...raList);
        } catch (e) {
          /* Skip */
        }
      }
      setActions(allActions);
    } catch (err) {
      console.error('Failed to load recovery actions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const handleOpenApproval = (tx: any) => {
    setApprovalTx(tx);
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4 dark:border-slate-800">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">
          Recovery Operations & Approvals
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Monitor queued recovery actions and process gated high-value items
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <RecoveryOperationsTable
          actions={actions}
          onSelectAction={(act) => onSelectTransaction(act.transaction_id)}
          onOpenApproval={handleOpenApproval}
        />
      )}

      {/* Human Approval Modal */}
      <HumanApprovalModal
        transaction={approvalTx}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onActionComplete={fetchActions}
      />
    </div>
  );
};
