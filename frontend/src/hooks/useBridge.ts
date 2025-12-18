import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bridgeApi } from '@/api/bridge';
import type { BridgeConfig } from '@/types/network';

export function useNetworkStatus() {
  return useQuery({
    queryKey: ['network-status'],
    queryFn: () => bridgeApi.getNetworkStatus(),
    refetchInterval: 10000, // Poll every 10 seconds
  });
}

export function useBridgeNodes() {
  return useQuery({
    queryKey: ['bridge-nodes'],
    queryFn: () => bridgeApi.getBridgeNodes(),
  });
}

export function useBridgeNode(id: string) {
  return useQuery({
    queryKey: ['bridge-nodes', id],
    queryFn: () => bridgeApi.getBridgeNode(id),
    enabled: !!id,
  });
}

export function useBridgeMetrics(nodeId: string) {
  return useQuery({
    queryKey: ['bridge-metrics', nodeId],
    queryFn: () => bridgeApi.getBridgeMetrics(nodeId),
    enabled: !!nodeId,
  });
}

export function useCurrentIsland() {
  return useQuery({
    queryKey: ['current-island'],
    queryFn: () => bridgeApi.getCurrentIsland(),
    refetchInterval: 15000, // Poll every 15 seconds
  });
}

export function useIslands() {
  return useQuery({
    queryKey: ['islands'],
    queryFn: () => bridgeApi.getIslands(),
  });
}

export function useIslandTransitions() {
  return useQuery({
    queryKey: ['island-transitions'],
    queryFn: () => bridgeApi.getIslandTransitions(),
  });
}

export function useBridgeConfig() {
  return useQuery({
    queryKey: ['bridge-config'],
    queryFn: () => bridgeApi.getBridgeConfig(),
  });
}

export function useUpdateBridgeConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: Partial<BridgeConfig>) => bridgeApi.updateBridgeConfig(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bridge-config'] });
    },
  });
}

export function useSetMode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mode: 'A' | 'C') => bridgeApi.setMode(mode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['network-status'] });
      queryClient.invalidateQueries({ queryKey: ['bridge-config'] });
    },
  });
}

export function useScanIslands() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => bridgeApi.scanIslands(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['islands'] });
    },
  });
}

export function useBridgeStats() {
  return useQuery({
    queryKey: ['bridge-stats'],
    queryFn: () => bridgeApi.getBridgeStats(),
  });
}
