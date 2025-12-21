import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { valueflowsApi } from '@/api/valueflows';
import { useCommunity } from '@/contexts/CommunityContext';
import type { Exchange, CreateExchangeRequest, CreateEventRequest } from '@/types/valueflows';

export function useExchanges() {
  const { currentCommunity } = useCommunity();

  return useQuery({
    queryKey: ['exchanges', currentCommunity?.id],
    queryFn: async () => {
      try {
        return await valueflowsApi.getExchanges(currentCommunity?.id);
      } catch (error) {
        console.warn('Failed to fetch exchanges:', error);
        return [];
      }
    },
    enabled: !!currentCommunity,
    retry: false,
    staleTime: 30000,
  });
}

export function useExchange(id: string) {
  return useQuery({
    queryKey: ['exchanges', id],
    queryFn: () => valueflowsApi.getExchange(id),
    enabled: !!id,
  });
}

export function useCreateExchange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateExchangeRequest) => valueflowsApi.createExchange(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exchanges'] });
    },
  });
}

export function useUpdateExchange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Exchange> }) =>
      valueflowsApi.updateExchange(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['exchanges'] });
      queryClient.invalidateQueries({ queryKey: ['exchanges', variables.id] });
    },
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateEventRequest) => valueflowsApi.createEvent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['exchanges'] });
    },
  });
}

export function useMatches() {
  const { currentCommunity } = useCommunity();

  return useQuery({
    queryKey: ['matches', currentCommunity?.id],
    queryFn: () => valueflowsApi.getMatches(currentCommunity?.id),
    enabled: !!currentCommunity,
  });
}

export function useAcceptMatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => valueflowsApi.acceptMatch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] });
    },
  });
}

export function useRejectMatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => valueflowsApi.rejectMatch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] });
    },
  });
}

export function useCompleteExchange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ exchangeId, agentId }: { exchangeId: string; agentId: string }) => {
      // First, create an event for the transfer
      const event = await valueflowsApi.createEvent({
        action: 'transfer',
        provider_id: agentId,
        resource_specification_id: 'placeholder', // Will be filled by backend from exchange
        quantity: 0, // Will be filled by backend from exchange
        unit: 'items',
      });

      // Then mark the exchange as complete with the event ID
      return valueflowsApi.completeExchange(exchangeId, agentId, event.id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exchanges'] });
    },
  });
}
