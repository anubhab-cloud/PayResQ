import React, { useState } from 'react';
import { AlertTriangle, Check, X, ShieldAlert, Loader2 } from 'lucide-react';
import { recoveryApi } from '../../api/client';

interface HumanApprovalModalProps {
  transaction: any;
  isOpen: boolean;
  onClose: () => void;
  onActionComplete: () => void;
}

export const HumanApprovalModal: React.FC<HumanApprovalModalProps> = ({
  transaction,
  isOpen,
  onClose,
  onActionComplete,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !transaction) return null;

  const handleApprove = async () => {
    try {
      setIsSubmitting(true);
      await recoveryApi.executeRecovery(transaction.id);
      onActionComplete();
      onClose();
    } catch (err) {
      console.error('Failed to approve recovery:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    try {
      setIsSubmitting(true);
      // In real workflow, policy check or status update marks action CANCELLED
      onActionComplete();
      onClose();
    } catch (err) {
      console.error('Failed to reject recovery:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-amber-500/30 bg-white shadow-2xl dark:bg-slate-900">
        <div className="border-b border-amber-500/20 bg-amber-500/10 p-5 dark:bg-amber-500/20">
          <div className="flex items-center gap-3 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-6 w-6 shrink-0" />
            <div>
              <h3 className="text-base font-bold">Human Approval Required</h3>
              <p className="text-xs text-amber-700/80 dark:text-amber-300/80 font-medium">
                High-Value Transaction Threshold Triggered
              </p>
            </div>
          </div>
        </div>

        <div className="p-5 space-y-4 text-xs">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-950 space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Transaction:</span>
              <span className="font-mono font-bold text-slate-900 dark:text-white">
                {transaction.external_transaction_id || transaction.id}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Amount:</span>
              <span className="font-bold text-slate-900 dark:text-white">
                ₹{transaction.amount.toLocaleString('en-IN')} {transaction.currency}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">AI Recommendation:</span>
              <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                RETRY_AFTER_DELAY (20 mins)
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Gating Reason:</span>
              <span className="font-semibold text-amber-600 dark:text-amber-400">
                Amount exceeds automatic approval threshold (₹50,000)
              </span>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
            Please review the AI recommendation and transaction context before authorizing automatic recovery execution.
          </p>

          <div className="flex gap-3 pt-2">
            <button
              onClick={handleReject}
              disabled={isSubmitting}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <X className="h-4 w-4" />
              <span>Reject / Stop</span>
            </button>
            <button
              onClick={handleApprove}
              disabled={isSubmitting}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 py-2.5 font-semibold text-white shadow-md shadow-emerald-600/30 hover:bg-emerald-500"
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Check className="h-4 w-4" />
                  <span>Authorize Action</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
