import React, { useEffect, useState } from 'react';
import { transactionsApi, intelligenceApi, recoveryApi } from '../api/client';
import { Transaction, AgentDecision, PolicyDecision, AuditLog } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { FailureAnalysisCard } from '../components/transactions/FailureAnalysisCard';
import { XgBoostPredictionsPanel } from '../components/transactions/XgBoostPredictionsPanel';
import { AgentDecisionCard } from '../components/transactions/AgentDecisionCard';
import { PolicyCheckCard } from '../components/transactions/PolicyCheckCard';
import { LiveRecoveryTimeline } from '../components/transactions/LiveRecoveryTimeline';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ArrowLeft, Play, RefreshCw, CheckCircle, Loader2 } from 'lucide-react';

interface TransactionDetailPageProps {
  transactionId: string;
  onBack: () => void;
}

export const TransactionDetailPage: React.FC<TransactionDetailPageProps> = ({
  transactionId,
  onBack,
}) => {
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [attempts, setAttempts] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<Record<string, number>>({});
  const [rootCause, setRootCause] = useState<any>(null);
  const [decision, setDecision] = useState<AgentDecision | null>(null);
  const [policy, setPolicy] = useState<PolicyDecision | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);

  const loadAll = async () => {
    try {
      setIsLoading(true);
      const [txData, attData, auditData] = await Promise.all([
        transactionsApi.getById(transactionId),
        transactionsApi.getAttempts(transactionId),
        transactionsApi.getAuditTrail(transactionId),
      ]);
      setTransaction(txData);
      setAttempts(attData);
      setAuditLogs(auditData.audit_trail || []);

      // Fetch Root Cause & Agent analysis
      try {
        const rcData = await intelligenceApi.getRootCause(transactionId);
        setRootCause(rcData);
      } catch (e) {
        /* Ignore if no root cause endpoint data yet */
      }

      try {
        const agentRes = await recoveryApi.analyzeAgent(transactionId);
        setDecision(agentRes.agent_decision);
        setPolicy({
          outcome: agentRes.policy_outcome,
          reason: agentRes.policy_reason,
          policy_version: 'v1',
        });
      } catch (e) {
        /* Ignore */
      }

      // Default XGBoost predictions
      setPredictions({
        RETRY_NOW: 0.4403,
        RETRY_AFTER_DELAY: 0.4925,
        SEND_PAYMENT_LINK: 0.5340,
        CHANGE_PAYMENT_METHOD: 0.6681,
      });
    } catch (err) {
      console.error('Failed to load transaction details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [transactionId]);

  const handleExecuteRecovery = async () => {
    try {
      setIsExecuting(true);
      await recoveryApi.executeRecovery(transactionId);
      await loadAll();
    } catch (err) {
      console.error('Recovery execution error:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  if (isLoading || !transaction) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton rows={2} />
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  const lastAttempt = attempts[0] || {};

  return (
    <div className="space-y-6">
      {/* Header & Back Action */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-mono font-bold text-slate-900 dark:text-white">
                {transaction.external_transaction_id || transaction.id}
              </h2>
              <StatusBadge status={transaction.status} />
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Created: {new Date(transaction.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Action Button */}
        {transaction.status === 'FAILED' && (
          <button
            onClick={handleExecuteRecovery}
            disabled={isExecuting}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50"
          >
            {isExecuting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Executing Recovery...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-current" />
                <span>Execute Recovery Pipeline</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Top Grid: Context & Analysis */}
      <div className="grid gap-6 lg:grid-cols-2">
        <FailureAnalysisCard attempt={lastAttempt} rootCause={rootCause} />
        <XgBoostPredictionsPanel predictions={predictions} />
      </div>

      {/* Middle Grid: AI Agent & Policy Guardrails */}
      <div className="grid gap-6 lg:grid-cols-2">
        <AgentDecisionCard decision={decision} />
        <PolicyCheckCard policy={policy} amount={transaction.amount} />
      </div>

      {/* Audit Event Timeline */}
      <LiveRecoveryTimeline auditLogs={auditLogs} />
    </div>
  );
};
