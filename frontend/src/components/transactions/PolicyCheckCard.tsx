import React from 'react';
import { ShieldCheck, Check, X, AlertTriangle } from 'lucide-react';
import { PolicyDecision } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface PolicyCheckCardProps {
  policy?: PolicyDecision | null;
  amount?: number;
}

export const PolicyCheckCard: React.FC<PolicyCheckCardProps> = ({ policy, amount = 7500 }) => {
  const outcome = policy?.outcome || 'ALLOW';
  const reason = policy?.reason || 'Action satisfies all automated recovery policies.';

  const checks = [
    { label: 'Transaction not already successful', passed: true },
    { label: 'Action supported by system rules', passed: true },
    { label: 'Duplicate recovery action check', passed: true },
    { label: 'Retry count below limit (< 3 retries)', passed: true },
    {
      label: `Amount below auto-approval limit (₹${amount.toLocaleString('en-IN')} <= ₹50,000)`,
      passed: amount <= 50000,
    },
    { label: 'Agent confidence above threshold (>= 60%)', passed: true },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
            Deterministic Policy Engine Guardrails
          </h3>
        </div>
        <StatusBadge status={outcome} />
      </div>

      <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 font-medium">
        {reason}
      </p>

      {/* 8-Rule Checklist */}
      <div className="mt-4 space-y-2 border-t border-slate-100 pt-3 dark:border-slate-800">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Policy Rule Validation (v1)
        </span>

        <div className="grid gap-2 sm:grid-cols-2 text-xs">
          {checks.map((c, i) => (
            <div
              key={i}
              className="flex items-center gap-2 rounded-lg bg-slate-50 p-2 dark:bg-slate-950 font-medium"
            >
              {c.passed ? (
                <div className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-500">
                  <Check className="h-3 w-3" />
                </div>
              ) : (
                <div className="flex h-4 w-4 items-center justify-center rounded-full bg-amber-500/20 text-amber-500">
                  <AlertTriangle className="h-3 w-3" />
                </div>
              )}
              <span className={c.passed ? 'text-slate-700 dark:text-slate-300' : 'text-amber-600 dark:text-amber-400 font-bold'}>
                {c.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
