export type TransactionStatus = 'FAILED' | 'SUCCESS' | 'PENDING';
export type RecoveryActionStatus = 'PENDING' | 'APPROVED' | 'EXECUTING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
export type PolicyOutcome = 'ALLOW' | 'BLOCK' | 'HUMAN_APPROVAL';

export interface Merchant {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface Customer {
  id: string;
  merchant_id: string;
  external_customer_id: string;
  name?: string;
  email?: string;
  phone?: string;
  created_at: string;
}

export interface PaymentAttempt {
  id: string;
  transaction_id: string;
  attempt_number: number;
  payment_method: string;
  bank?: string;
  status: string;
  failure_reason?: string;
  attempted_at: string;
}

export interface Transaction {
  id: string;
  merchant_id: string;
  customer_id: string;
  external_transaction_id: string;
  amount: number;
  currency: string;
  status: TransactionStatus;
  created_at: string;
  updated_at?: string;
  merchant_name?: string;
  customer_name?: string;
  payment_attempts?: PaymentAttempt[];
}

export interface RecoveryOutcome {
  id: string;
  recovery_action_id: string;
  success: boolean;
  recovered_amount?: number;
  failure_reason?: string;
  completed_at: string;
}

export interface RecoveryAction {
  id: string;
  transaction_id: string;
  action_type: string;
  status: RecoveryActionStatus;
  reason?: string;
  confidence?: number;
  scheduled_for?: string;
  executed_at?: string;
  created_at: string;
  outcome?: RecoveryOutcome;
}

export interface AgentDecision {
  action: string;
  delay_minutes?: number;
  reason: string;
  confidence: number;
  transaction_id?: string;
  selected_probability?: number;
  root_cause?: string;
  model_version?: string;
}

export interface PolicyDecision {
  outcome: PolicyOutcome;
  reason: string;
  policy_version: string;
  rule_triggered?: string;
}

export interface AuditLog {
  id: string;
  transaction_id?: string;
  event_type: string;
  actor_type: string;
  action: string;
  reason?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface DashboardSummary {
  revenue_at_risk: number;
  recovered_revenue: number;
  recovery_rate: number;
  total_transactions: number;
  failed_transactions: number;
  successful_transactions: number;
  pending_human_approvals: number;
  active_interventions: number;
  note?: string;
}

export interface DailyTrendPoint {
  date: string;
  failed_volume: number;
  recovered_volume: number;
  failed_count: number;
  recovered_count: number;
}

export interface DashboardTrends {
  timeframe_days: number;
  trends: DailyTrendPoint[];
}

export interface BankFailureStat {
  bank: string;
  failed_count: number;
  total_count: number;
  failure_rate: number;
}

export interface MethodFailureStat {
  payment_method: string;
  failed_count: number;
  total_count: number;
  failure_rate: number;
}

export interface DashboardFailureBreakdown {
  by_bank: BankFailureStat[];
  by_method: MethodFailureStat[];
}

export interface DemoRunResponse {
  transaction_id: string;
  amount: number;
  bank: string;
  payment_method: string;
  failure_reason: string;
  agent_action: string;
  agent_confidence: number;
  policy_outcome: string;
  job_id?: string;
  execution_success?: boolean;
  recovered_amount?: number;
  status: string;
}

export interface ModelInfo {
  model_version: string;
  algorithm: string;
  training_samples: number;
  roc_auc: number;
  precision: number;
  recall: number;
  f1_score: number;
  log_loss: number;
  baseline_recovery_rate: number;
  ml_recovery_rate: number;
  improvement_factor: string;
  note?: string;
}
