import React from 'react';
import { AlertCircle, FileSearch, CheckCircle, ShieldAlert } from 'lucide-react';

interface FailureAnalysisCardProps {
  attempt?: any;
  rootCause?: any;
}

export const FailureAnalysisCard: React.FC<FailureAnalysisCardProps> = ({ attempt, rootCause }) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3 dark:border-slate-800">
        <FileSearch className="h-4 w-4 text-indigo-500" />
        <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
          Failure & Root Cause Analysis
        </h3>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        {/* Payment Attempt Breakdown */}
        <div className="rounded-lg border border-slate-200/80 bg-slate-50 p-3.5 dark:border-slate-800/80 dark:bg-slate-950">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Payment Method Context
          </span>
          <div className="mt-2 space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Method:</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {attempt?.payment_method || 'CARD'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Acquiring Bank:</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {attempt?.bank || 'ICICI'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Failure Code:</span>
              <span className="font-semibold text-rose-500">
                {attempt?.failure_reason || 'TIMEOUT'}
              </span>
            </div>
          </div>
        </div>

        {/* Deterministic Root Cause Analysis */}
        <div className="rounded-lg border border-slate-200/80 bg-slate-50 p-3.5 dark:border-slate-800/80 dark:bg-slate-950">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Statistical Diagnosis
          </span>
          <div className="mt-2 text-xs">
            <div className="flex items-center justify-between font-semibold text-indigo-600 dark:text-indigo-400">
              <span>{rootCause?.root_cause || 'TEMPORARY_BANK_DEGRADATION'}</span>
              <span>{((rootCause?.confidence || 0.89) * 100).toFixed(0)}% Conf.</span>
            </div>

            <ul className="mt-2 space-y-1 text-[11px] text-slate-500 dark:text-slate-400">
              {(rootCause?.evidence || [
                'Acquiring bank timeout rate elevated in current 15m window',
                'Baseline failure rate exceeded by 3.6x',
              ]).map((item: string, idx: number) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-indigo-500">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
