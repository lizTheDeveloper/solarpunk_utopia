// DTN Bundle System API Client
import axios from 'axios';
import type {
  Bundle,
  BundleStatus,
  CreateBundleRequest,
  BundleStats,
  OutboxStatus,
} from '@/types/bundles';

const api = axios.create({
  baseURL: '/api/dtn',
});

export const dtnApi = {
  // Create a new bundle
  createBundle: async (data: CreateBundleRequest): Promise<Bundle> => {
    const response = await api.post<Bundle>('/bundles', data);
    return response.data;
  },

  // Get all bundles
  getBundles: async (): Promise<Bundle[]> => {
    const response = await api.get<Bundle[]>('/bundles');
    return response.data;
  },

  // Get a specific bundle
  getBundle: async (id: string): Promise<Bundle> => {
    const response = await api.get<Bundle>(`/bundles/${id}`);
    return response.data;
  },

  // Get bundle status
  getBundleStatus: async (id: string): Promise<BundleStatus> => {
    const response = await api.get<BundleStatus>(`/bundles/${id}/status`);
    return response.data;
  },

  // Get outbox status
  getOutboxStatus: async (): Promise<OutboxStatus> => {
    const response = await api.get<OutboxStatus>('/outbox/status');
    return response.data;
  },

  // Get bundle statistics
  getBundleStats: async (): Promise<BundleStats> => {
    const response = await api.get<BundleStats>('/bundles/stats');
    return response.data;
  },

  // Get pending bundles
  getPendingBundles: async (): Promise<Bundle[]> => {
    const response = await api.get<Bundle[]>('/bundles?status=pending');
    return response.data;
  },

  // Get delivered bundles
  getDeliveredBundles: async (): Promise<Bundle[]> => {
    const response = await api.get<Bundle[]>('/bundles?status=delivered');
    return response.data;
  },

  // Acknowledge bundle receipt
  acknowledgeBundle: async (id: string): Promise<void> => {
    await api.post(`/bundles/${id}/acknowledge`);
  },
};
