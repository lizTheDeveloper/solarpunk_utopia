// ValueFlows types for the Solarpunk Gift Economy
// Based on the ValueFlows specification

export interface Agent {
  id: string;
  name: string;
  type: 'person' | 'organization' | 'network';
  note?: string;
  location?: string;
  created_at: string;
}

export interface ResourceSpecification {
  id: string;
  name: string;
  category: string;
  subcategory?: string;
  unit?: string;
  note?: string;
}

export interface EconomicResource {
  id: string;
  resource_specification_id: string;
  resource_specification?: ResourceSpecification;
  quantity: number;
  unit: string;
  location?: string;
  current_owner_id: string;
  current_owner?: Agent;
  note?: string;
  created_at: string;
}

export interface Listing {
  id: string;
  listing_type: 'offer' | 'need';
  agent_id: string;
  agent?: Agent;
  resource_spec_id: string;
  resource_specification?: ResourceSpecification;
  quantity: number;
  unit: string;
  location_id?: string;
  location?: string; // Legacy field, maps to location_id
  available_from?: string;
  available_until?: string;
  title?: string;
  description?: string;
  note?: string; // Legacy field, maps to description
  image_url?: string;
  status: 'active' | 'matched' | 'fulfilled' | 'cancelled';
  community_id?: string;

  // Inter-community sharing (GAP: inter-community-sharing)
  anonymous?: boolean; // GAP-61: Anonymous gifts
  visibility?: 'my_cell' | 'my_community' | 'trusted_network' | 'anyone_local' | 'network_wide';

  created_at: string;
  updated_at: string;
}

// Sharing preference for inter-community resource visibility
export interface SharingPreference {
  user_id: string;
  visibility: 'my_cell' | 'my_community' | 'trusted_network' | 'anyone_local' | 'network_wide';
  location_precision: 'exact' | 'neighborhood' | 'city' | 'region';
  local_radius_km: number;
  updated_at?: string;
}

// Legacy alias for backward compatibility
export type Intent = Listing;

export interface Commitment {
  id: string;
  provider_id: string;
  provider?: Agent;
  receiver_id: string;
  receiver?: Agent;
  resource_specification_id: string;
  resource_specification?: ResourceSpecification;
  quantity: number;
  unit: string;
  due_date?: string;
  note?: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  created_at: string;
}

export interface EconomicEvent {
  id: string;
  action: 'transfer' | 'produce' | 'consume' | 'use' | 'accept' | 'modify';
  provider_id?: string;
  provider?: Agent;
  receiver_id?: string;
  receiver?: Agent;
  resource_id?: string;
  resource?: EconomicResource;
  resource_specification_id?: string;
  resource_specification?: ResourceSpecification;
  quantity: number;
  unit: string;
  timestamp: string;
  location?: string;
  note?: string;
  agreement_id?: string;
  commitment_id?: string;
}

export interface Agreement {
  id: string;
  name: string;
  participants: string[]; // Agent IDs
  description?: string;
  created_at: string;
  status: 'proposed' | 'active' | 'completed' | 'cancelled';
}

export interface Satisfaction {
  id: string;
  intent_id: string;
  intent?: Intent;
  event_id?: string;
  event?: EconomicEvent;
  commitment_id?: string;
  commitment?: Commitment;
  quantity_satisfied: number;
  note?: string;
  created_at: string;
}

export interface Match {
  id: string;
  offer_id: string;
  offer?: Intent;
  need_id: string;
  need?: Intent;
  quantity: number;
  unit: string;
  score: number;
  reason?: string;
  status: 'proposed' | 'accepted' | 'rejected' | 'fulfilled';
  community_id?: string;
  created_at: string;
}

export interface Exchange {
  id: string;
  name: string;
  provider_id: string;
  provider?: Agent;
  receiver_id: string;
  receiver?: Agent;
  resource_specification_id: string;
  resource_specification?: ResourceSpecification;
  quantity: number;
  unit: string;
  status: 'proposed' | 'in_progress' | 'completed' | 'cancelled';
  provider_completed?: boolean;
  receiver_completed?: boolean;
  events: EconomicEvent[];
  community_id?: string;
  created_at: string;
  updated_at: string;
}

// Request/Response types
export interface CreateListingRequest {
  listing_type: 'offer' | 'need';
  agent_id: string;
  resource_spec_id: string;
  quantity: number;
  unit: string;
  location_id?: string;
  available_from?: string;
  available_until?: string;
  title?: string;
  description?: string;
  image_url?: string;
  community_id?: string;
}

// Legacy alias for backward compatibility
export type CreateIntentRequest = CreateListingRequest;

export interface CreateEventRequest {
  action: 'transfer' | 'produce' | 'consume' | 'use' | 'accept' | 'modify';
  provider_id?: string;
  receiver_id?: string;
  resource_id?: string;
  resource_specification_id?: string;
  quantity: number;
  unit: string;
  location?: string;
  note?: string;
  agreement_id?: string;
  commitment_id?: string;
}

export interface CreateExchangeRequest {
  name: string;
  provider_id: string;
  receiver_id: string;
  resource_specification_id: string;
  quantity: number;
  unit: string;
}

export interface Community {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  settings?: Record<string, any>;
  is_public: boolean;
}
