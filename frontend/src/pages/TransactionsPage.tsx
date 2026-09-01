import React, { useEffect, useState } from 'react';
import { transactionsApi } from '../api/client';
import { Transaction } from '../types';
import { RecentTransactionsTable } from '../components/dashboard/RecentTransactionsTable';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { Search, Filter } from 'lucide-react';

interface TransactionsPageProps {
  onSelectTransaction: (id: string) => void;
}

export const TransactionsPage: React.FC<TransactionsPageProps> = ({ onSelectTransaction }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setIsLoading(true);
        const filterStatus = statusFilter === 'ALL' ? undefined : statusFilter;
        const data = await transactionsApi.list(100, 0, filterStatus);
        setTransactions(data);
      } catch (err) {
        console.error('Failed to load transactions:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTransactions();
  }, [statusFilter]);

  const filtered = transactions.filter((tx) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      tx.id.toLowerCase().includes(query) ||
      (tx.external_transaction_id && tx.external_transaction_id.toLowerCase().includes(query))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Transactions & Recovery Cases
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Search and filter all payment transactions across merchants
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-xs text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            />
          </div>

          {/* Status Filter Dropdown */}
          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1 dark:border-slate-800 dark:bg-slate-900">
            {['ALL', 'FAILED', 'SUCCESS'].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                  statusFilter === s
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <RecentTransactionsTable
          transactions={filtered}
          onSelectTransaction={onSelectTransaction}
        />
      )}
    </div>
  );
};
