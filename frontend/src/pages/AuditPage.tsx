import React, { useEffect, useState } from 'react';
import { transactionsApi } from '../api/client';
import { AuditLog } from '../types';
import { AuditStreamTable } from '../components/audit/AuditStreamTable';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { Filter } from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [actorFilter, setActorFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAuditLogs = async () => {
      try {
        setIsLoading(true);
        const txs = await transactionsApi.list(15, 0);
        const allLogs: AuditLog[] = [];

        for (const t of txs) {
          try {
            const auditRes = await transactionsApi.getAuditTrail(t.id);
            if (auditRes.audit_trail) {
              allLogs.push(...auditRes.audit_trail);
            }
          } catch (e) {
            /* Skip */
          }
        }
        setLogs(allLogs);
      } catch (err) {
        console.error('Failed to load audit logs:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAuditLogs();
  }, []);

  const filtered = logs.filter((log) => {
    if (actorFilter === 'ALL') return true;
    return log.actor_type === actorFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            System Audit Stream
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time immutable audit trail for governance and observability
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1 dark:border-slate-800 dark:bg-slate-900">
          {['ALL', 'AI_AGENT', 'POLICY_ENGINE', 'SYSTEM'].map((actor) => (
            <button
              key={actor}
              onClick={() => setActorFilter(actor)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                actorFilter === actor
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
              }`}
            >
              {actor}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <AuditStreamTable logs={filtered} />
      )}
    </div>
  );
};
