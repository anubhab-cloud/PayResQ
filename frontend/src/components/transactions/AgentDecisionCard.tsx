import React from 'react';
import { Bot, Sparkles } from 'lucide-react';
import { AgentDecision } from '../../types';

interface AgentDecisionCardProps {
  decision?: AgentDecision | null;
}

export const AgentDecisionCard: React.FC<AgentDecisionCardProps> = ({ decision }) => {
  const action = decision?.action || 'RETRY_AFTER_DELAY';
  const confidence = decision?.confidence || 0.91;
  const reason =
    decision?.reason ||
    'Root cause analysis indicates temporary bank degradation. XGBoost predicts RETRY_AFTER_DELAY has the highest recovery probability (0.71). A 20-minute delay allows acquiring bank systems to recover.';
  const delayMinutes = decision?.delay_minutes;

  return (
    <div className="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white p-5 shadow-sm dark:border-indigo-900/50 dark:from-indigo-950/20 dark:to-slate-900">
      <div className="flex items-center justify-between border-b border-indigo-100 pb-3 dark:border-indigo-900/40">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <span>AI Agent Recommendation</span>
              <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
            </h3>
            <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium">
              Contextual Agent Reasoning
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Confidence
          </span>
          <p className="text-base font-extrabold text-indigo-600 dark:text-indigo-400">
            {(confidence * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Selected Action
          </span>
          <div className="mt-1 flex items-center gap-2">
            <span className="rounded-lg bg-indigo-600 px-3 py-1 text-xs font-bold text-white shadow-sm">
              {action.replace(/_/g, ' ')}
            </span>
            {delayMinutes && (
              <span className="rounded-lg border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
                Delay: {delayMinutes} Minutes
              </span>
            )}
          </div>
        </div>

        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Structured Explanation
          </span>
          <p className="mt-1 text-xs leading-relaxed text-slate-700 dark:text-slate-300 bg-white/80 dark:bg-slate-900/80 p-3 rounded-lg border border-slate-200/60 dark:border-slate-800/60 font-medium">
            "{reason}"
          </p>
        </div>
      </div>
    </div>
  );
};
