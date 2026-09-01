import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// Mock API client
vi.mock('./api/client', () => ({
  dashboardApi: {
    getSummary: vi.fn().mockResolvedValue({
      revenue_at_risk: 1840000,
      recovered_revenue: 580000,
      recovery_rate: 31.5,
      total_transactions: 1284,
      failed_transactions: 800,
      successful_transactions: 484,
      pending_human_approvals: 2,
      active_interventions: 5,
    }),
    getTrends: vi.fn().mockResolvedValue({ timeframe_days: 7, trends: [] }),
    getFailureBreakdown: vi.fn().mockResolvedValue({ by_bank: [], by_method: [] }),
    runDemo: vi.fn().mockResolvedValue({ transaction_id: 'DEMO-TX-1', status: 'ENQUEUED' }),
  },
  transactionsApi: {
    list: vi.fn().mockResolvedValue([]),
    getById: vi.fn().mockResolvedValue({ id: 'TX-1', amount: 7500, currency: 'INR', status: 'FAILED' }),
    getAttempts: vi.fn().mockResolvedValue([]),
    getAuditTrail: vi.fn().mockResolvedValue({ audit_trail: [] }),
  },
  intelligenceApi: {
    getModelInfo: vi.fn().mockResolvedValue({
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
    }),
  },
  recoveryApi: {
    analyzeAgent: vi.fn().mockResolvedValue({
      agent_decision: { action: 'RETRY_AFTER_DELAY', confidence: 0.91, reason: 'Temporary outage' },
      policy_outcome: 'ALLOW',
      policy_reason: 'Approved',
    }),
  },
}));

describe('PayResQ App Component', () => {
  it('renders application shell and wordmark', async () => {
    render(<App />);
    expect(screen.getAllByText('PayResQ')[0]).toBeInTheDocument();
  });

  it('renders Run Demo Scenario action button', async () => {
    render(<App />);
    expect(screen.getByText(/Run Demo Scenario/i)).toBeInTheDocument();
  });
});
