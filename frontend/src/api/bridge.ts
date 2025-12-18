// Bridge Management API Client
import axios from 'axios';
import type {
  BridgeNode,
  BridgeMetrics,
  NetworkStatus,
  IslandTopology,
  IslandTransition,
  BridgeConfig,
  ModeConfig,
} from '@/types/network';

const api = axios.create({
  baseURL: '/api/bridge',
});

export const bridgeApi = {
  // Get network status
  getNetworkStatus: async (): Promise<NetworkStatus> => {
    const response = await api.get<NetworkStatus>('/status');
    return response.data;
  },

  // Get all bridge nodes
  getBridgeNodes: async (): Promise<BridgeNode[]> => {
    const response = await api.get<BridgeNode[]>('/bridges');
    return response.data;
  },

  // Get specific bridge node
  getBridgeNode: async (id: string): Promise<BridgeNode> => {
    const response = await api.get<BridgeNode>(`/bridges/${id}`);
    return response.data;
  },

  // Get bridge metrics
  getBridgeMetrics: async (nodeId: string): Promise<BridgeMetrics> => {
    const response = await api.get<BridgeMetrics>(`/bridges/${nodeId}/metrics`);
    return response.data;
  },

  // Get current island topology
  getCurrentIsland: async (): Promise<IslandTopology> => {
    const response = await api.get<IslandTopology>('/islands/current');
    return response.data;
  },

  // Get all known islands
  getIslands: async (): Promise<IslandTopology[]> => {
    const response = await api.get<IslandTopology[]>('/islands');
    return response.data;
  },

  // Get island transitions
  getIslandTransitions: async (): Promise<IslandTransition[]> => {
    const response = await api.get<IslandTransition[]>('/transitions');
    return response.data;
  },

  // Get bridge configuration
  getBridgeConfig: async (): Promise<BridgeConfig> => {
    const response = await api.get<BridgeConfig>('/config');
    return response.data;
  },

  // Update bridge configuration
  updateBridgeConfig: async (config: Partial<BridgeConfig>): Promise<BridgeConfig> => {
    const response = await api.put<BridgeConfig>('/config', config);
    return response.data;
  },

  // Set mode (A or C)
  setMode: async (mode: 'A' | 'C'): Promise<ModeConfig> => {
    const response = await api.post<ModeConfig>('/mode', { mode });
    return response.data;
  },

  // Get current mode
  getMode: async (): Promise<ModeConfig> => {
    const response = await api.get<ModeConfig>('/mode');
    return response.data;
  },

  // Trigger island scan
  scanIslands: async (): Promise<IslandTopology[]> => {
    const response = await api.post<IslandTopology[]>('/islands/scan');
    return response.data;
  },

  // Get bridge statistics
  getBridgeStats: async (): Promise<{
    total_bridges: number;
    active_bridges: number;
    total_islands: number;
    total_transitions: number;
  }> => {
    const response = await api.get('/stats');
    return response.data;
  },
};
