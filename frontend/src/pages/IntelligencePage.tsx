import React, { useEffect, useState } from 'react';
import { intelligenceApi } from '../api/client';
import { ModelInfo } from '../types';
import { MlPerformanceCard } from '../components/intelligence/MlPerformanceCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

export const IntelligencePage: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        setIsLoading(true);
        const data = await intelligenceApi.getModelInfo();
        setModelInfo(data);
      } catch (err) {
        console.error('Failed to load intelligence metrics:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchInfo();
  }, []);

  if (isLoading) {
    return <LoadingSkeleton rows={4} />;
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4 dark:border-slate-800">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">
          Intelligence & Supervised Model Performance
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          XGBoost classifier benchmarks, features, and baseline comparisons
        </p>
      </div>

      <MlPerformanceCard modelInfo={modelInfo} />
    </div>
  );
};
