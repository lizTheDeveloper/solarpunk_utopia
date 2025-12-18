import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { valueflowsApi } from '@/api/valueflows';
import type { Intent, CreateIntentRequest } from '@/types/valueflows';

export function useOffers() {
  return useQuery({
    queryKey: ['offers'],
    queryFn: () => valueflowsApi.getOffers(),
  });
}

export function useOffer(id: string) {
  return useQuery({
    queryKey: ['offers', id],
    queryFn: () => valueflowsApi.getIntent(id),
    enabled: !!id,
  });
}

export function useCreateOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateIntentRequest) => valueflowsApi.createIntent({ ...data, type: 'offer' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offers'] });
      queryClient.invalidateQueries({ queryKey: ['intents'] });
    },
  });
}

export function useUpdateOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Intent> }) =>
      valueflowsApi.updateIntent(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['offers'] });
      queryClient.invalidateQueries({ queryKey: ['offers', variables.id] });
    },
  });
}

export function useDeleteOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => valueflowsApi.deleteIntent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['offers'] });
    },
  });
}
