import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dtnApi } from '@/api/dtn';
import type { CreateBundleRequest } from '@/types/bundles';

export function useBundles() {
  return useQuery({
    queryKey: ['bundles'],
    queryFn: () => dtnApi.getBundles(),
  });
}

export function useBundle(id: string) {
  return useQuery({
    queryKey: ['bundles', id],
    queryFn: () => dtnApi.getBundle(id),
    enabled: !!id,
  });
}

export function useBundleStatus(id: string) {
  return useQuery({
    queryKey: ['bundle-status', id],
    queryFn: () => dtnApi.getBundleStatus(id),
    enabled: !!id,
    refetchInterval: 5000, // Poll every 5 seconds for status updates
  });
}

export function useBundleStats() {
  return useQuery({
    queryKey: ['bundle-stats'],
    queryFn: () => dtnApi.getBundleStats(),
  });
}

export function useOutboxStatus() {
  return useQuery({
    queryKey: ['outbox-status'],
    queryFn: () => dtnApi.getOutboxStatus(),
    refetchInterval: 10000, // Poll every 10 seconds
  });
}

export function usePendingBundles() {
  return useQuery({
    queryKey: ['bundles', 'pending'],
    queryFn: () => dtnApi.getPendingBundles(),
  });
}

export function useDeliveredBundles() {
  return useQuery({
    queryKey: ['bundles', 'delivered'],
    queryFn: () => dtnApi.getDeliveredBundles(),
  });
}

export function useCreateBundle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateBundleRequest) => dtnApi.createBundle(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bundles'] });
      queryClient.invalidateQueries({ queryKey: ['outbox-status'] });
    },
  });
}
