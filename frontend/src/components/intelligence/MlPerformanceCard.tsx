import React from 'react';
import { ModelInfo } from '../../types';
import { BrainCircuit, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react';

interface MlPerformanceCardProps {
  modelInfo?: ModelInfo | null;
}

export const MlPerformanceCard: React.FC<MlPerformanceCardProps> = ({ modelInfo }) => {
  const info = modelInfo || {
    model_version: 'v1.0',
    algorithm: 'XGBoost Classifier',
    training_samples: 75000,
    roc_auc: 0.812,
    precision: 0.784,
    recall: 0.741,
    f1_score: 0.762,
    log_loss: 0.435,
    baseline_recovery_rate: 22.1,
    ml_recovery_rate: 44.7,
    improvement_factor: '2.02x',
    note: 'EXPERIMENTAL — offline evaluation metrics on synthetic payment dataset',
  };

  return (
    <div className="space-y-6">
      {/* Model Identity Banner */}
      <div className="rounded-xl border border-indigo-200 bg-gradient-to-r from-indigo-900 to-slate-900 p-6 text-white shadow-lg dark:border-indigo-800">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 shadow-md">
              <BrainCircuit className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">{info.algorithm} ({info.model_version})</h2>
              <p className="text-xs text-indigo-300 font-medium">
                Trained on {info.training_samples.toLocaleString()} payment transactions • Leakage-free feature engineering
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2 backdrop-blur-sm border border-white/10">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            <div>
              <span className="text-[10px] uppercase tracking-wider text-indigo-200">
                Recovery Uplift
              </span>
              <p className="text-lg font-extrabold text-emerald-400">
                {info.improvement_factor} Improvement
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Baseline vs ML Comparison */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Naive Immediate Retry Baseline
          </span>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-slate-600 dark:text-slate-400">
              {info.baseline_recovery_rate}%
            </span>
            <span className="text-xs text-slate-400">Single retry attempt</span>
          </div>
          <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div
              className="h-full bg-slate-400 dark:bg-slate-600"
              style={{ width: `${info.baseline_recovery_rate}%` }}
            />
          </div>
        </div>

        <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-5 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            PayResQ XGBoost + AI Agent Strategy
          </span>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
              {info.ml_recovery_rate}%
            </span>
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
              +{(info.ml_recovery_rate - info.baseline_recovery_rate).toFixed(1)}% Net Lift
            </span>
          </div>
          <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-emerald-100 dark:bg-emerald-900/40">
            <div
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${info.ml_recovery_rate}%` }}
            />
          </div>
        </div>
      </div>

      {/* Model Benchmark Grid */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white border-b border-slate-200 pb-3 dark:border-slate-800">
          Supervised Classification Metrics
        </h3>

        <div className="mt-4 grid gap-4 grid-cols-2 sm:grid-cols-5 text-center">
          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60">
            <span className="text-[10px] font-bold uppercase text-slate-400">ROC-AUC</span>
            <p className="mt-1 text-xl font-bold text-indigo-600 dark:text-indigo-400 font-mono">
              {info.roc_auc}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60">
            <span className="text-[10px] font-bold uppercase text-slate-400">Precision</span>
            <p className="mt-1 text-xl font-bold text-indigo-600 dark:text-indigo-400 font-mono">
              {info.precision}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60">
            <span className="text-[10px] font-bold uppercase text-slate-400">Recall</span>
            <p className="mt-1 text-xl font-bold text-indigo-600 dark:text-indigo-400 font-mono">
              {info.recall}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60">
            <span className="text-[10px] font-bold uppercase text-slate-400">F1-Score</span>
            <p className="mt-1 text-xl font-bold text-indigo-600 dark:text-indigo-400 font-mono">
              {info.f1_score}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60 col-span-2 sm:col-span-1">
            <span className="text-[10px] font-bold uppercase text-slate-400">Log Loss</span>
            <p className="mt-1 text-xl font-bold text-slate-700 dark:text-slate-300 font-mono">
              {info.log_loss}
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 rounded-lg bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-300 border border-amber-500/20">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{info.note || 'EXPERIMENTAL — offline evaluation metrics on synthetic payment dataset'}</span>
        </div>
      </div>
    </div>
  );
};
