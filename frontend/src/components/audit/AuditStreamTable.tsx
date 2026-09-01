import React, { useState } from 'react';
import { AuditLog } from '../../types';
import { FileText, ChevronDown, ChevronUp, Bot, ShieldCheck, Cpu } from 'lucide-react';

interface AuditStreamTableProps {
  logs: AuditLog[];
}

export const AuditStreamTable: React.FC<AuditStreamTableProps> = ({ logs }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getActorBadge = (actor: string) => {
    switch (actor) {
      case 'AI_AGENT':
        return 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20';
      case 'POLICY_ENGINE':
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'SYSTEM':
      case 'WORKER':
        return 'bg-sky-500/10 text-sky-500 border-sky-500/20';
      case 'HUMAN':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      default:
        return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-200 p-5 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
            System Audit Stream
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Immutable audit record of all AI agent decisions, policy validations, and executions
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 uppercase text-slate-500 dark:bg-slate-950 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="px-5 py-3">Timestamp</th>
              <th className="px-5 py-3">Actor</th>
              <th className="px-5 py-3">Event Type</th>
              <th className="px-5 py-3">Action</th>
              <th className="px-5 py-3">Reason Summary</th>
              <th className="px-5 py-3 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                  No audit log entries recorded
                </td>
              </tr>
            ) : (
              logs.map((log) => {
                const isExpanded = expandedId === log.id;

                return (
                  <React.Fragment key={log.id}>
                    <tr
                      onClick={() => toggleExpand(log.id)}
                      className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    >
                      <td className="px-5 py-3.5 font-mono text-slate-500">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-bold ${getActorBadge(log.actor_type)}`}>
                          {log.actor_type}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-bold text-slate-800 dark:text-slate-200">
                        {log.event_type}
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-indigo-600 dark:text-indigo-400">
                        {log.action}
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 dark:text-slate-300 max-w-xs truncate">
                        {log.reason || 'N/A'}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </button>
                      </td>
                    </tr>
                    {isExpanded && log.metadata && (
                      <tr className="bg-slate-50 dark:bg-slate-950">
                        <td colSpan={6} className="px-5 py-3">
                          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                              Metadata Payload
                            </span>
                            <pre className="mt-1 font-mono text-[11px] text-slate-700 dark:text-slate-300 overflow-x-auto">
                              {JSON.stringify(log.metadata, null, 2)}
                            </pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
