// AI Agent System API Client
import axios from 'axios';
import type {
  Agent,
  AgentProposal,
  AgentRunResult,
  AgentStats,
  AgentType,
} from '@/types/agents';

const api = axios.create({
  baseURL: '/agents', // AI Agents API (DTN service on port 8000)
});

export const agentsApi = {
  // Get all agents
  getAgents: async (): Promise<Agent[]> => {
    const response = await api.get<{ agents: Agent[]; total: number }>('');
    // GAP-55: Backend now returns full agent objects with metadata
    return response.data.agents;
  },

  // Get specific agent settings
  getAgent: async (type: AgentType): Promise<Agent> => {
    const response = await api.get<Agent>(`/settings/${type}`);
    return response.data;
  },

  // Update agent configuration
  updateAgent: async (type: AgentType, config: Partial<Agent>): Promise<Agent> => {
    const response = await api.put<Agent>(`/settings/${type}`, config);
    return response.data;
  },

  // Enable/disable agent
  toggleAgent: async (type: AgentType, enabled: boolean): Promise<Agent> => {
    const response = await api.put<Agent>(`/settings/${type}`, { enabled });
    return response.data;
  },

  // Opt in/out of agent
  setOptIn: async (type: AgentType, optIn: boolean): Promise<Agent> => {
    const response = await api.put<Agent>(`/settings/${type}`, { opt_in: optIn });
    return response.data;
  },

  // Run agent manually
  runAgent: async (type: AgentType): Promise<AgentRunResult> => {
    const response = await api.post<AgentRunResult>(`/run/${type}`);
    return response.data;
  },

  // Get all proposals
  getProposals: async (status?: 'pending' | 'approved' | 'rejected'): Promise<AgentProposal[]> => {
    const url = status ? `/proposals?status=${status}` : '/proposals';
    const response = await api.get<{ proposals: AgentProposal[]; total: number }>(url);
    return response.data.proposals;
  },

  // Get proposals by agent type
  getProposalsByAgent: async (type: AgentType): Promise<AgentProposal[]> => {
    const response = await api.get<{ proposals: AgentProposal[]; total: number }>(`/proposals?agent_name=${type}`);
    return response.data.proposals;
  },

  // Get specific proposal
  getProposal: async (id: string): Promise<AgentProposal> => {
    const response = await api.get<AgentProposal>(`/proposals/${id}`);
    return response.data;
  },

  // Review proposal (approve or reject)
  reviewProposal: async (id: string, action: 'approve' | 'reject', note?: string): Promise<AgentProposal> => {
    // Backend extracts user_id from auth token (GAP-02)
    // Just send approved and reason
    const response = await api.post<AgentProposal>(`/proposals/${id}/approve`, {
      approved: action === 'approve',
      reason: note,
    });
    return response.data;
  },

  // Get agent statistics
  getAgentStats: async (type: AgentType): Promise<AgentStats> => {
    const response = await api.get<{ stats: AgentStats }>(`/stats/${type}`);
    return response.data.stats;
  },

  // Get all agent statistics
  getAllAgentStats: async (): Promise<Record<AgentType, AgentStats>> => {
    const response = await api.get<Record<AgentType, { stats: AgentStats }>>('/stats');
    // Transform {agent_name: {stats: {...}}} to {agent_name: {...}}
    const transformed: Record<string, AgentStats> = {};
    for (const [key, value] of Object.entries(response.data)) {
      transformed[key] = value.stats;
    }
    return transformed as Record<AgentType, AgentStats>;
  },

  // Get pending proposal count for current user
  getPendingCount: async (): Promise<number> => {
    const response = await api.get<{ user_id: string; pending_count: number }>('/proposals/pending/count');
    return response.data.pending_count;
  },
};
