import React from 'react';
import { Clock, CheckCircle2, ShieldCheck, Bot, Cpu, AlertCircle, RefreshCw } from 'lucide-react';
import { AuditLog } from '../../types';

interface LiveRecoveryTimelineProps {
  auditLogs: AuditLog[];
}

export const LiveRecoveryTimeline: React.FC<LiveRecoveryTimelineProps> = ({ auditLogs }) => {
  const getIcon = (eventType: string) => {
    switch (eventType) {
      case 'AGENT_DECISION':
        return Bot;
      case 'POLICY_DECISION':
        return ShieldCheck;
      case 'RECOVERY_EXECUTED':
      case 'RECOVERY_COMPLETED':
        return CheckCircle2;
      case 'RECOVERY_SKIPPED':
        return AlertCircle;
      default:
        return Clock;
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3 dark:border-slate-800">
        <Clock className="h-4 w-4 text-indigo-500" />
        <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
          Real-Time Audit Event Timeline
        </h3>
      </div>

      <div className="mt-4 space-y-4">
        {auditLogs.length === 0 ? (
          <p className="text-xs text-slate-400 py-4 text-center">
            No audit events recorded for this transaction yet.
          </p>
        ) : (
          auditLogs.map((log, index) => {
            const Icon = getIcon(log.event_type);
            const time = new Date(log.created_at).toLocaleTimeString();

            return (
              <div key={log.id || index} className="relative flex gap-3 text-xs">
                {index < auditLogs.length - 1 && (
                  <span className="absolute left-3.5 top-7 -bottom-4 w-0.5 bg-slate-200 dark:bg-slate-800" />
                )}
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-white">
                      [{log.actor_type}] {log.event_type}
                    </span>
                    <span className="font-mono text-[10px] text-slate-400">{time}</span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-300 font-medium">
                    {log.action}: {log.reason}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
