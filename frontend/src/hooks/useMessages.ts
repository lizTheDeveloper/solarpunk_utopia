import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Message, MessageThread, SendMessageRequest } from '@/types/message';

export function useInbox(limit = 100) {
  return useQuery({
    queryKey: ['messages', 'inbox', limit],
    queryFn: async () => {
      const response = await apiClient.get<Message[]>('/messages/inbox', {
        params: { limit },
      });
      return response.data;
    },
  });
}

export function useThreads() {
  return useQuery({
    queryKey: ['messages', 'threads'],
    queryFn: async () => {
      const response = await apiClient.get<MessageThread[]>('/messages/threads');
      return response.data;
    },
  });
}

export function useThreadMessages(threadId: string) {
  return useQuery({
    queryKey: ['messages', 'threads', threadId],
    queryFn: async () => {
      const response = await apiClient.get<Message[]>(
        `/messages/threads/${threadId}/messages`
      );
      return response.data;
    },
    enabled: !!threadId,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: SendMessageRequest) => {
      const response = await apiClient.post<Message>('/messages', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
    },
  });
}

export function useMarkDelivered(messageId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(
        `/messages/messages/${messageId}/mark-delivered`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
    },
  });
}

export function useSendCellBroadcast(cellId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (content: string) => {
      const response = await apiClient.post(`/messages/cells/${cellId}/broadcast`, {
        content,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] });
    },
  });
}
