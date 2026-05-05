import apiClient from './client';
import type { AiChatRequest } from '@/lib/types/aiChat';

export const countriesApi = {
  getAll: () => apiClient.get('/api/v1/countries'),
  getFullAnalytics: (code: string) => apiClient.get(`/api/v1/countries/${code}/full-analytics`),
  getClusterBenchmark: (code: string, indicator: string, year: number) =>
    apiClient.get(`/api/v1/countries/${code}/cluster-benchmark`, { params: { indicator, year } }),
};

export const indicatorsApi = {
  getAll: () => apiClient.get('/api/v1/indicators'),
  getByCategory: (category: string) => apiClient.get(`/api/v1/indicators?category=${category}`),
};

export const analyticsApi = {
  getClusters: (year: number) => apiClient.get(`/api/v1/analytics/clusters?year=${year}`),
  getAnomalies: (params?: { country?: string; indicator?: string; threshold?: number; limit?: number; offset?: number }) =>
    apiClient.get('/api/v1/analytics/anomalies', { params }),
};

export const aiChatApi = {
  sendMessage: (payload: AiChatRequest) =>
    apiClient.post('/api/v1/ai/chat', payload, {
      timeout: 120000,
    }),
  health: () => apiClient.get('/api/v1/ai/health'),
};
