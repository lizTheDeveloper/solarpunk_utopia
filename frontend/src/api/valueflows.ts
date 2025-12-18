// ValueFlows API Client
import axios from 'axios';
import type {
  Agent,
  Intent,
  EconomicResource,
  ResourceSpecification,
  EconomicEvent,
  Exchange,
  Match,
  Commitment,
  CreateIntentRequest,
  CreateEventRequest,
  CreateExchangeRequest,
} from '@/types/valueflows';

const api = axios.create({
  baseURL: '/api/vf',
});

export const valueflowsApi = {
  // Agents
  getAgents: async (): Promise<Agent[]> => {
    const response = await api.get<Agent[]>('/agents');
    return response.data;
  },

  getAgent: async (id: string): Promise<Agent> => {
    const response = await api.get<Agent>(`/agents/${id}`);
    return response.data;
  },

  createAgent: async (data: Partial<Agent>): Promise<Agent> => {
    const response = await api.post<Agent>('/agents', data);
    return response.data;
  },

  // Resource Specifications
  getResourceSpecifications: async (): Promise<ResourceSpecification[]> => {
    const response = await api.get<ResourceSpecification[]>('/resource-specifications');
    return response.data;
  },

  getResourceSpecification: async (id: string): Promise<ResourceSpecification> => {
    const response = await api.get<ResourceSpecification>(`/resource-specifications/${id}`);
    return response.data;
  },

  createResourceSpecification: async (
    data: Partial<ResourceSpecification>
  ): Promise<ResourceSpecification> => {
    const response = await api.post<ResourceSpecification>('/resource-specifications', data);
    return response.data;
  },

  // Economic Resources
  getResources: async (): Promise<EconomicResource[]> => {
    const response = await api.get<EconomicResource[]>('/resources');
    return response.data;
  },

  getResource: async (id: string): Promise<EconomicResource> => {
    const response = await api.get<EconomicResource>(`/resources/${id}`);
    return response.data;
  },

  // Intents (Offers & Needs)
  getIntents: async (type?: 'offer' | 'need'): Promise<Intent[]> => {
    const url = type ? `/intents?type=${type}` : '/intents';
    const response = await api.get<Intent[]>(url);
    return response.data;
  },

  getIntent: async (id: string): Promise<Intent> => {
    const response = await api.get<Intent>(`/intents/${id}`);
    return response.data;
  },

  createIntent: async (data: CreateIntentRequest): Promise<Intent> => {
    const response = await api.post<Intent>('/intents', data);
    return response.data;
  },

  updateIntent: async (id: string, data: Partial<Intent>): Promise<Intent> => {
    const response = await api.put<Intent>(`/intents/${id}`, data);
    return response.data;
  },

  deleteIntent: async (id: string): Promise<void> => {
    await api.delete(`/intents/${id}`);
  },

  // Offers
  getOffers: async (): Promise<Intent[]> => {
    return valueflowsApi.getIntents('offer');
  },

  // Needs
  getNeeds: async (): Promise<Intent[]> => {
    return valueflowsApi.getIntents('need');
  },

  // Matches
  getMatches: async (): Promise<Match[]> => {
    const response = await api.get<Match[]>('/matches');
    return response.data;
  },

  getMatch: async (id: string): Promise<Match> => {
    const response = await api.get<Match>(`/matches/${id}`);
    return response.data;
  },

  acceptMatch: async (id: string): Promise<Match> => {
    const response = await api.post<Match>(`/matches/${id}/accept`);
    return response.data;
  },

  rejectMatch: async (id: string): Promise<Match> => {
    const response = await api.post<Match>(`/matches/${id}/reject`);
    return response.data;
  },

  // Commitments
  getCommitments: async (): Promise<Commitment[]> => {
    const response = await api.get<Commitment[]>('/commitments');
    return response.data;
  },

  getCommitment: async (id: string): Promise<Commitment> => {
    const response = await api.get<Commitment>(`/commitments/${id}`);
    return response.data;
  },

  // Economic Events
  getEvents: async (): Promise<EconomicEvent[]> => {
    const response = await api.get<EconomicEvent[]>('/events');
    return response.data;
  },

  getEvent: async (id: string): Promise<EconomicEvent> => {
    const response = await api.get<EconomicEvent>(`/events/${id}`);
    return response.data;
  },

  createEvent: async (data: CreateEventRequest): Promise<EconomicEvent> => {
    const response = await api.post<EconomicEvent>('/events', data);
    return response.data;
  },

  // Exchanges
  getExchanges: async (): Promise<Exchange[]> => {
    const response = await api.get<Exchange[]>('/exchanges');
    return response.data;
  },

  getExchange: async (id: string): Promise<Exchange> => {
    const response = await api.get<Exchange>(`/exchanges/${id}`);
    return response.data;
  },

  createExchange: async (data: CreateExchangeRequest): Promise<Exchange> => {
    const response = await api.post<Exchange>('/exchanges', data);
    return response.data;
  },

  updateExchange: async (id: string, data: Partial<Exchange>): Promise<Exchange> => {
    const response = await api.put<Exchange>(`/exchanges/${id}`, data);
    return response.data;
  },
};
