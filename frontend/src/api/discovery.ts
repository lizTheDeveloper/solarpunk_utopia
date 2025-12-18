// Discovery & Search API Client
import axios from 'axios';
import type {
  IndexEntry,
  SearchQuery,
  SearchResponse,
  IndexStats,
  DistributedIndex,
} from '@/types/discovery';

const api = axios.create({
  baseURL: '/api/discovery',
});

export const discoveryApi = {
  // Search
  search: async (query: SearchQuery): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>('/search', query);
    return response.data;
  },

  // Quick search (string only)
  quickSearch: async (queryString: string): Promise<SearchResponse> => {
    return discoveryApi.search({ query: queryString });
  },

  // Get local index
  getLocalIndex: async (): Promise<DistributedIndex> => {
    const response = await api.get<DistributedIndex>('/index');
    return response.data;
  },

  // Get index stats
  getIndexStats: async (): Promise<IndexStats> => {
    const response = await api.get<IndexStats>('/index/stats');
    return response.data;
  },

  // Add entry to index
  addIndexEntry: async (entry: Omit<IndexEntry, 'id' | 'created_at'>): Promise<IndexEntry> => {
    const response = await api.post<IndexEntry>('/index/entries', entry);
    return response.data;
  },

  // Update index entry
  updateIndexEntry: async (id: string, entry: Partial<IndexEntry>): Promise<IndexEntry> => {
    const response = await api.put<IndexEntry>(`/index/entries/${id}`, entry);
    return response.data;
  },

  // Delete index entry
  deleteIndexEntry: async (id: string): Promise<void> => {
    await api.delete(`/index/entries/${id}`);
  },

  // Sync indexes (trigger manual sync)
  syncIndexes: async (): Promise<{ synced: number; cached: number }> => {
    const response = await api.post<{ synced: number; cached: number }>('/index/sync');
    return response.data;
  },

  // Get cached indexes
  getCachedIndexes: async (): Promise<DistributedIndex[]> => {
    const response = await api.get<DistributedIndex[]>('/index/cached');
    return response.data;
  },
};
