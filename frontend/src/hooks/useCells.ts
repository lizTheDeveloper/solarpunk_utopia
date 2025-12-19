import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Cell, CellMembership, CreateCellRequest } from '@/types/cell';

export function useCells(params?: {
  lat?: number;
  lon?: number;
  radius_km?: number;
  accepting_members_only?: boolean;
}) {
  return useQuery({
    queryKey: ['cells', params],
    queryFn: async () => {
      const response = await apiClient.get<Cell[]>('/cells', { params });
      return response.data;
    },
  });
}

export function useMyCells() {
  return useQuery({
    queryKey: ['cells', 'my'],
    queryFn: async () => {
      const response = await apiClient.get<Cell[]>('/cells/my/cells');
      return response.data;
    },
  });
}

export function useCell(cellId: string) {
  return useQuery({
    queryKey: ['cells', cellId],
    queryFn: async () => {
      const response = await apiClient.get<Cell>(`/cells/${cellId}`);
      return response.data;
    },
    enabled: !!cellId,
  });
}

export function useCellMembers(cellId: string) {
  return useQuery({
    queryKey: ['cells', cellId, 'members'],
    queryFn: async () => {
      const response = await apiClient.get<CellMembership[]>(`/cells/${cellId}/members`);
      return response.data;
    },
    enabled: !!cellId,
  });
}

export function useCreateCell() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateCellRequest) => {
      const response = await apiClient.post<Cell>('/cells', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cells'] });
    },
  });
}

export function useInviteToCell(cellId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (inviteeId: string) => {
      const response = await apiClient.post(`/cells/${cellId}/invite`, {
        invitee_id: inviteeId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cells', cellId] });
    },
  });
}

export function useAcceptCellInvitation(cellId: string, invitationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(
        `/cells/${cellId}/invitations/${invitationId}/accept`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cells'] });
    },
  });
}
