import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { valueflowsApi } from '@/api/valueflows';
import type { Intent, CreateIntentRequest } from '@/types/valueflows';

export function useNeeds() {
  return useQuery({
    queryKey: ['needs'],
    queryFn: () => valueflowsApi.getNeeds(),
  });
}

export function useNeed(id: string) {
  return useQuery({
    queryKey: ['needs', id],
    queryFn: () => valueflowsApi.getIntent(id),
    enabled: !!id,
  });
}

export function useCreateNeed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateIntentRequest) => valueflowsApi.createIntent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['needs'] });
      queryClient.invalidateQueries({ queryKey: ['intents'] });
    },
  });
}

export function useUpdateNeed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Intent> }) =>
      valueflowsApi.updateIntent(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['needs'] });
      queryClient.invalidateQueries({ queryKey: ['needs', variables.id] });
    },
  });
}

export function useDeleteNeed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => valueflowsApi.deleteIntent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['needs'] });
    },
  });
}
