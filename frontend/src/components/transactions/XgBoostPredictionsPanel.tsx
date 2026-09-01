import React from 'react';
import { Cpu, CheckCircle } from 'lucide-react';

interface XgBoostPredictionsPanelProps {
  predictions?: Record<string, number>;
  recommendedAction?: string;
  modelVersion?: string;
}

export const XgBoostPredictionsPanel: React.FC<XgBoostPredictionsPanelProps> = ({
  predictions = {
    RETRY_NOW: 0.4403,
    RETRY_AFTER_DELAY: 0.4925,
    SEND_PAYMENT_LINK: 0.5340,
    CHANGE_PAYMENT_METHOD: 0.6681,
  },
  recommendedAction = 'CHANGE_PAYMENT_METHOD',
  modelVersion = 'v1.0',
}) => {
  const actions = Object.entries(predictions);
  const highestScore = Math.max(...Object.values(predictions));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
            XGBoost Predictive Intelligence
          </h3>
        </div>
        <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
          Model: recovery_model ({modelVersion})
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {actions.map(([action, score]) => {
          const isHighest = score === highestScore;
          const percentage = (score * 100).toFixed(1);

          return (
            <div key={action} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-semibold">
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-800 dark:text-slate-200">
                    {action.replace(/_/g, ' ')}
                  </span>
                  {isHighest && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/10 px-2 py-0.5 text-[10px] font-bold text-violet-600 dark:text-violet-400">
                      <CheckCircle className="h-3 w-3" />
                      Highest Predicted
                    </span>
                  )}
                </div>
                <span className={`font-mono ${isHighest ? 'text-violet-600 dark:text-violet-400 font-bold' : 'text-slate-500'}`}>
                  {percentage}%
                </span>
              </div>

              <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className={`h-full rounded-full transition-all ${
                    isHighest
                      ? 'bg-gradient-to-r from-violet-600 to-indigo-600 shadow-sm'
                      : 'bg-slate-400 dark:bg-slate-600'
                  }`}
                  style={{ width: `${Math.max(score * 100, 5)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-4 text-[11px] text-slate-400 dark:text-slate-500 italic">
        * Probabilities represent action-specific statistical recovery estimates derived from historical failure features.
      </p>
    </div>
  );
};
