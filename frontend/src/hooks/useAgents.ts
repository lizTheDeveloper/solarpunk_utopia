import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentsApi } from '@/api/agents';
import type { AgentType } from '@/types/agents';

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.getAgents(),
  });
}

export function useAgent(type: AgentType) {
  return useQuery({
    queryKey: ['agents', type],
    queryFn: () => agentsApi.getAgent(type),
    enabled: !!type,
  });
}

export function useAgentStats(type: AgentType) {
  return useQuery({
    queryKey: ['agent-stats', type],
    queryFn: () => agentsApi.getAgentStats(type),
    enabled: !!type,
  });
}

export function useAllAgentStats() {
  return useQuery({
    queryKey: ['agent-stats'],
    queryFn: () => agentsApi.getAllAgentStats(),
  });
}

export function useProposals(status?: 'pending' | 'approved' | 'rejected') {
  return useQuery({
    queryKey: ['proposals', status],
    queryFn: () => agentsApi.getProposals(status),
  });
}

export function useProposal(id: string) {
  return useQuery({
    queryKey: ['proposals', id],
    queryFn: () => agentsApi.getProposal(id),
    enabled: !!id,
  });
}

export function useProposalsByAgent(type: AgentType) {
  return useQuery({
    queryKey: ['proposals', 'agent', type],
    queryFn: () => agentsApi.getProposalsByAgent(type),
    enabled: !!type,
  });
}

export function useRunAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (type: AgentType) => agentsApi.runAgent(type),
    onSuccess: (_, type) => {
      queryClient.invalidateQueries({ queryKey: ['agents', type] });
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      queryClient.invalidateQueries({ queryKey: ['agent-stats', type] });
    },
  });
}

export function useReviewProposal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      action,
      note,
    }: {
      id: string;
      action: 'approve' | 'reject';
      note?: string;
    }) => agentsApi.reviewProposal(id, action, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      queryClient.invalidateQueries({ queryKey: ['agent-stats'] });
    },
  });
}

export function useToggleAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ type, enabled }: { type: AgentType; enabled: boolean }) =>
      agentsApi.toggleAgent(type, enabled),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agents', variables.type] });
    },
  });
}

export function useSetOptIn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ type, optIn }: { type: AgentType; optIn: boolean }) =>
      agentsApi.setOptIn(type, optIn),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agents', variables.type] });
    },
  });
}
