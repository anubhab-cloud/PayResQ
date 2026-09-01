import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = (status || '').toUpperCase();

  let colorClasses = 'bg-slate-500/10 text-slate-400 border-slate-500/20';

  if (['SUCCESS', 'ALLOW', 'COMPLETED', 'RECOVERED'].includes(normalized)) {
    colorClasses = 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30 dark:bg-emerald-500/20';
  } else if (['FAILED', 'BLOCK', 'CANCELLED'].includes(normalized)) {
    colorClasses = 'bg-rose-500/10 text-rose-500 border-rose-500/30 dark:bg-rose-500/20';
  } else if (['HUMAN_APPROVAL', 'AWAITING_HUMAN_APPROVAL'].includes(normalized)) {
    colorClasses = 'bg-amber-500/10 text-amber-500 border-amber-500/30 dark:bg-amber-500/20';
  } else if (['PENDING', 'QUEUED', 'EXECUTING', 'APPROVED', 'ENQUEUED'].includes(normalized)) {
    colorClasses = 'bg-sky-500/10 text-sky-500 border-sky-500/30 dark:bg-sky-500/20';
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs font-medium',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3 py-1.5 text-sm font-semibold',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${sizeClasses} ${colorClasses} tracking-wide`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {normalized.replace(/_/g, ' ')}
    </span>
  );
};
