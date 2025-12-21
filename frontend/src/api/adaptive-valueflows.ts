// Adaptive ValueFlows API - switches between online and offline
// Provides seamless fallback when internet is unavailable
import { getLocalAPI, LocalValueFlowsAPI } from '../storage/local-api';
import type {
  Listing,
  CreateListingRequest,
  Agent,
  ResourceSpecification,
  Match,
  Exchange,
  EconomicEvent,
  CreateEventRequest,
  CreateExchangeRequest,
} from '../types/valueflows';

// Online API client (existing implementation)
const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

class OnlineAPI {
  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async getAgents(): Promise<Agent[]> {
    return this.fetch<Agent[]>('/agents');
  }

  async getAgent(id: string): Promise<Agent> {
    return this.fetch<Agent>(`/agents/${id}`);
  }

  async createAgent(agent: Omit<Agent, 'created_at'>): Promise<Agent> {
    return this.fetch<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(agent),
    });
  }

  async getResourceSpecs(): Promise<ResourceSpecification[]> {
    return this.fetch<ResourceSpecification[]>('/resource-specifications');
  }

  async getResourceSpec(id: string): Promise<ResourceSpecification> {
    return this.fetch<ResourceSpecification>(`/resource-specifications/${id}`);
  }

  async getListings(type?: 'offer' | 'need'): Promise<Listing[]> {
    const query = type ? `?listing_type=${type}` : '';
    return this.fetch<Listing[]>(`/listings${query}`);
  }

  async getListing(id: string): Promise<Listing> {
    return this.fetch<Listing>(`/listings/${id}`);
  }

  async createListing(request: CreateListingRequest): Promise<Listing> {
    return this.fetch<Listing>('/listings', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async updateListing(id: string, updates: Partial<Listing>): Promise<Listing> {
    return this.fetch<Listing>(`/listings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async getMatches(agentId?: string): Promise<Match[]> {
    const query = agentId ? `?agent_id=${agentId}` : '';
    return this.fetch<Match[]>(`/matches${query}`);
  }

  async getExchanges(agentId?: string): Promise<Exchange[]> {
    const query = agentId ? `?agent_id=${agentId}` : '';
    return this.fetch<Exchange[]>(`/exchanges${query}`);
  }

  async createExchange(request: CreateExchangeRequest): Promise<Exchange> {
    return this.fetch<Exchange>('/exchanges', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async completeExchange(exchangeId: string, agentId: string, role: 'provider' | 'receiver'): Promise<void> {
    await this.fetch(`/exchanges/${exchangeId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, role }),
    });
  }

  async createEvent(request: CreateEventRequest): Promise<EconomicEvent> {
    return this.fetch<EconomicEvent>('/events', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

// Adaptive API that switches between online and offline
export class AdaptiveValueFlowsAPI {
  private onlineAPI = new OnlineAPI();
  private localAPI: LocalValueFlowsAPI | null = null;
  private isOnline = navigator.onLine;
  private preferLocal = false; // Set to true to prefer local storage even when online

  constructor() {
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true;
      console.log('Network: online');
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      console.log('Network: offline');
    });

    // Initialize local API
    this.initializeLocalAPI();
  }

  private async initializeLocalAPI() {
    try {
      this.localAPI = await getLocalAPI();
      console.log('Local API initialized');
    } catch (error) {
      console.error('Failed to initialize local API:', error);
    }
  }

  private async ensureLocalAPI(): Promise<LocalValueFlowsAPI> {
    if (!this.localAPI) {
      this.localAPI = await getLocalAPI();
    }
    return this.localAPI;
  }

  private shouldUseLocal(): boolean {
    return this.preferLocal || !this.isOnline;
  }

  // ============================================================================
  // AGENTS
  // ============================================================================

  async getAgents(): Promise<Agent[]> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getAgents();
    }

    try {
      const agents = await this.onlineAPI.getAgents();
      // Sync to local storage
      // TODO: implement sync
      return agents;
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getAgents();
    }
  }

  async getAgent(id: string): Promise<Agent | null> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getAgent(id);
    }

    try {
      return await this.onlineAPI.getAgent(id);
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getAgent(id);
    }
  }

  async createAgent(agent: Omit<Agent, 'created_at'>): Promise<Agent | null> {
    const local = await this.ensureLocalAPI();

    if (this.isOnline) {
      try {
        const created = await this.onlineAPI.createAgent(agent);
        // TODO: sync to local
        return created;
      } catch (error) {
        console.warn('Online API failed, saving locally:', error);
        return local.createAgent(agent);
      }
    }

    return local.createAgent(agent);
  }

  // ============================================================================
  // RESOURCE SPECIFICATIONS
  // ============================================================================

  async getResourceSpecs(): Promise<ResourceSpecification[]> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getResourceSpecs();
    }

    try {
      return await this.onlineAPI.getResourceSpecs();
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getResourceSpecs();
    }
  }

  async getResourceSpec(id: string): Promise<ResourceSpecification | null> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getResourceSpec(id);
    }

    try {
      return await this.onlineAPI.getResourceSpec(id);
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getResourceSpec(id);
    }
  }

  // ============================================================================
  // LISTINGS
  // ============================================================================

  async getListings(type?: 'offer' | 'need'): Promise<Listing[]> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getListings(type);
    }

    try {
      return await this.onlineAPI.getListings(type);
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getListings(type);
    }
  }

  async getListing(id: string): Promise<Listing | null> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getListing(id);
    }

    try {
      return await this.onlineAPI.getListing(id);
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getListing(id);
    }
  }

  async createListing(request: CreateListingRequest): Promise<Listing | null> {
    const local = await this.ensureLocalAPI();

    if (this.isOnline) {
      try {
        const created = await this.onlineAPI.createListing(request);
        // TODO: sync to local
        return created;
      } catch (error) {
        console.warn('Online API failed, saving locally:', error);
        return local.createListing(request);
      }
    }

    return local.createListing(request);
  }

  async updateListing(id: string, updates: Partial<Listing>): Promise<Listing | null> {
    const local = await this.ensureLocalAPI();

    if (this.isOnline) {
      try {
        const updated = await this.onlineAPI.updateListing(id, updates);
        // TODO: sync to local
        return updated;
      } catch (error) {
        console.warn('Online API failed, updating locally:', error);
        return local.updateListing(id, updates);
      }
    }

    return local.updateListing(id, updates);
  }

  // ============================================================================
  // MATCHES
  // ============================================================================

  async getMatches(agentId?: string): Promise<Match[]> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getMatches(agentId);
    }

    try {
      return await this.onlineAPI.getMatches(agentId);
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getMatches(agentId);
    }
  }

  // ============================================================================
  // EXCHANGES
  // ============================================================================

  async getExchanges(agentId?: string): Promise<Exchange[]> {
    if (this.shouldUseLocal()) {
      const local = await this.ensureLocalAPI();
      return local.getExchanges(agentId);
    }

    try {
      return await this.onlineAPI.getExchanges(agentId);
    } catch (error) {
      console.warn('Online API failed, falling back to local:', error);
      const local = await this.ensureLocalAPI();
      return local.getExchanges(agentId);
    }
  }

  async createExchange(request: CreateExchangeRequest): Promise<Exchange | null> {
    const local = await this.ensureLocalAPI();

    if (this.isOnline) {
      try {
        const created = await this.onlineAPI.createExchange(request);
        // TODO: sync to local
        return created;
      } catch (error) {
        console.warn('Online API failed, saving locally:', error);
        return local.createExchange(request);
      }
    }

    return local.createExchange(request);
  }

  async completeExchange(exchangeId: string, agentId: string, role: 'provider' | 'receiver'): Promise<void> {
    const local = await this.ensureLocalAPI();

    if (this.isOnline) {
      try {
        await this.onlineAPI.completeExchange(exchangeId, agentId, role);
        await local.completeExchange(exchangeId, agentId, role);
      } catch (error) {
        console.warn('Online API failed, updating locally:', error);
        await local.completeExchange(exchangeId, agentId, role);
      }
    } else {
      await local.completeExchange(exchangeId, agentId, role);
    }
  }

  // ============================================================================
  // EVENTS
  // ============================================================================

  async createEvent(request: CreateEventRequest): Promise<EconomicEvent | null> {
    const local = await this.ensureLocalAPI();

    if (this.isOnline) {
      try {
        const created = await this.onlineAPI.createEvent(request);
        // TODO: sync to local
        return created;
      } catch (error) {
        console.warn('Online API failed, saving locally:', error);
        return local.createEvent(request);
      }
    }

    return local.createEvent(request);
  }

  // ============================================================================
  // SYNC CONTROL
  // ============================================================================

  setPreferLocal(prefer: boolean) {
    this.preferLocal = prefer;
  }

  getNetworkStatus(): 'online' | 'offline' {
    return this.isOnline ? 'online' : 'offline';
  }
}

// Singleton instance
let adaptiveAPI: AdaptiveValueFlowsAPI | null = null;

export function getAdaptiveAPI(): AdaptiveValueFlowsAPI {
  if (!adaptiveAPI) {
    adaptiveAPI = new AdaptiveValueFlowsAPI();
  }
  return adaptiveAPI;
}

// Initialize storage for offline-first operation
export async function initializeStorage(): Promise<void> {
  const api = getAdaptiveAPI();
  await api['ensureLocalAPI']();
  console.log('Storage initialized successfully');
}
