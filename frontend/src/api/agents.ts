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
  baseURL: '/api/vf', // Agents are part of the VF service
});

export const agentsApi = {
  // Get all agents
  getAgents: async (): Promise<Agent[]> => {
    const response = await api.get<Agent[]>('/ai-agents');
    return response.data;
  },

  // Get specific agent
  getAgent: async (type: AgentType): Promise<Agent> => {
    const response = await api.get<Agent>(`/ai-agents/${type}`);
    return response.data;
  },

  // Update agent configuration
  updateAgent: async (type: AgentType, config: Partial<Agent>): Promise<Agent> => {
    const response = await api.put<Agent>(`/ai-agents/${type}`, config);
    return response.data;
  },

  // Enable/disable agent
  toggleAgent: async (type: AgentType, enabled: boolean): Promise<Agent> => {
    const response = await api.patch<Agent>(`/ai-agents/${type}`, { enabled });
    return response.data;
  },

  // Opt in/out of agent
  setOptIn: async (type: AgentType, optIn: boolean): Promise<Agent> => {
    const response = await api.patch<Agent>(`/ai-agents/${type}`, { opt_in: optIn });
    return response.data;
  },

  // Run agent manually
  runAgent: async (type: AgentType): Promise<AgentRunResult> => {
    const response = await api.post<AgentRunResult>(`/ai-agents/${type}/run`);
    return response.data;
  },

  // Get all proposals
  getProposals: async (status?: 'pending' | 'approved' | 'rejected'): Promise<AgentProposal[]> => {
    const url = status ? `/ai-agents/proposals?status=${status}` : '/ai-agents/proposals';
    const response = await api.get<AgentProposal[]>(url);
    return response.data;
  },

  // Get proposals by agent type
  getProposalsByAgent: async (type: AgentType): Promise<AgentProposal[]> => {
    const response = await api.get<AgentProposal[]>(`/ai-agents/${type}/proposals`);
    return response.data;
  },

  // Get specific proposal
  getProposal: async (id: string): Promise<AgentProposal> => {
    const response = await api.get<AgentProposal>(`/ai-agents/proposals/${id}`);
    return response.data;
  },

  // Review proposal (approve or reject)
  reviewProposal: async (id: string, action: 'approve' | 'reject', note?: string): Promise<AgentProposal> => {
    const response = await api.post<AgentProposal>(`/ai-agents/proposals/${id}/review`, {
      action,
      note,
    });
    return response.data;
  },

  // Get agent statistics
  getAgentStats: async (type: AgentType): Promise<AgentStats> => {
    const response = await api.get<AgentStats>(`/ai-agents/${type}/stats`);
    return response.data;
  },

  // Get all agent statistics
  getAllAgentStats: async (): Promise<Record<AgentType, AgentStats>> => {
    const response = await api.get<Record<AgentType, AgentStats>>('/ai-agents/stats');
    return response.data;
  },
};
