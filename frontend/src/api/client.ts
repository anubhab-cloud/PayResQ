/// <reference types="vite/client" />
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Response error handler
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API modules
export const dashboardApi = {
  getSummary: async () => {
    const res = await apiClient.get('/dashboard/summary');
    return res.data;
  },
  getTrends: async (days = 7) => {
    const res = await apiClient.get(`/dashboard/recovery-trends?days=${days}`);
    return res.data;
  },
  getFailureBreakdown: async () => {
    const res = await apiClient.get('/dashboard/failure-breakdown');
    return res.data;
  },
  runDemo: async () => {
    const res = await apiClient.post('/dashboard/demo-run');
    return res.data;
  },
};

export const transactionsApi = {
  list: async (limit = 50, offset = 0, status?: string) => {
    let url = `/transactions?limit=${limit}&offset=${offset}`;
    if (status) url += `&status=${status}`;
    const res = await apiClient.get(url);
    return res.data;
  },
  getById: async (id: string) => {
    const res = await apiClient.get(`/transactions/${id}`);
    return res.data;
  },
  getAttempts: async (id: string) => {
    const res = await apiClient.get(`/transactions/${id}/attempts`);
    return res.data;
  },
  getRecoveryActions: async (id: string) => {
    const res = await apiClient.get(`/transactions/${id}/recovery-actions`);
    return res.data;
  },
  getAuditTrail: async (id: string) => {
    const res = await apiClient.get(`/transactions/${id}/audit`);
    return res.data;
  },
};

export const intelligenceApi = {
  predict: async (data: any) => {
    const res = await apiClient.post('/intelligence/recovery-predict', data);
    return res.data;
  },
  getRootCause: async (transactionId: string) => {
    const res = await apiClient.get(`/intelligence/root-cause/${transactionId}`);
    return res.data;
  },
  getModelInfo: async () => {
    const res = await apiClient.get('/intelligence/model-info');
    return res.data;
  },
};

export const recoveryApi = {
  analyzeAgent: async (transactionId: string) => {
    const res = await apiClient.post(`/agent/analyze/${transactionId}`);
    return res.data;
  },
  policyCheck: async (transactionId: string, action: string, delayMinutes?: number) => {
    const res = await apiClient.post(`/recovery/policy-check/${transactionId}`, {
      action,
      delay_minutes: delayMinutes,
      confidence: 0.85,
    });
    return res.data;
  },
  executeRecovery: async (transactionId: string) => {
    const res = await apiClient.post(`/recovery/execute/${transactionId}`);
    return res.data;
  },
  getStatus: async (recoveryActionId: string) => {
    const res = await apiClient.get(`/recovery/${recoveryActionId}`);
    return res.data;
  },
};
