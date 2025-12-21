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
    try {
      const response = await api.get<BundleStats>('/stats/queues');
      return response.data;
    } catch (error) {
      // Fallback: return empty stats if endpoint doesn't exist
      console.warn('Stats endpoint not available, returning empty stats');
      return {
        queue_counts: {
          inbox: 0,
          outbox: 0,
          pending: 0,
          delivered: 0,
          expired: 0,
          quarantine: 0
        }
      };
    }
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

  // Mesh sync API endpoints

  // Get bundles ready for forwarding to peers
  getBundlesForForwarding: async (): Promise<Bundle[]> => {
    const response = await api.get<{ bundles: Bundle[] }>('/sync/pull?max_bundles=50');
    return response.data.bundles;
  },

  // Receive bundles from a peer
  receiveBundles: async (bundles: Bundle[]): Promise<{ accepted: number; rejected: number }> => {
    const response = await api.post<{ accepted: number; rejected: number }>('/sync/push', bundles);
    return response.data;
  },

  // Get sync statistics
  getSyncStats: async (): Promise<any> => {
    const response = await api.get('/sync/stats');
    return response.data;
  },
};
