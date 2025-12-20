import { Listing, SharingPreference } from '../types/valueflows';

const API_BASE = import.meta.env.VITE_VF_API_URL || 'http://localhost:8001';

export interface DiscoveryResult {
  listing: Listing;
  distance_km?: number;
  trust_score?: number;
  is_cross_community: boolean;
}

export interface DiscoveryFilters {
  user_id: string;
  resource_type?: 'offer' | 'need';
  category?: string;
  max_distance_km?: number;
  min_trust?: number;
}

/**
 * Discover resources from across communities based on trust and visibility preferences.
 */
export async function discoverResources(
  filters: DiscoveryFilters
): Promise<DiscoveryResult[]> {
  const params = new URLSearchParams();
  params.append('user_id', filters.user_id);

  if (filters.resource_type) {
    params.append('resource_type', filters.resource_type);
  }
  if (filters.category) {
    params.append('category', filters.category);
  }
  if (filters.max_distance_km) {
    params.append('max_distance_km', filters.max_distance_km.toString());
  }
  if (filters.min_trust !== undefined) {
    params.append('min_trust', filters.min_trust.toString());
  }

  const response = await fetch(`${API_BASE}/discovery/resources?${params}`);
  if (!response.ok) {
    throw new Error(`Discovery failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get sharing preference for a user.
 */
export async function getSharingPreference(
  userId: string
): Promise<SharingPreference> {
  const response = await fetch(`${API_BASE}/discovery/preferences/${userId}`);
  if (!response.ok) {
    throw new Error(`Failed to get sharing preference: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update sharing preference for a user.
 */
export async function updateSharingPreference(
  userId: string,
  updates: Partial<SharingPreference>
): Promise<SharingPreference> {
  const response = await fetch(`${API_BASE}/discovery/preferences/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update sharing preference: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Create sharing preference for a user.
 */
export async function createSharingPreference(
  userId: string,
  preference: Omit<SharingPreference, 'user_id' | 'updated_at'>
): Promise<SharingPreference> {
  const response = await fetch(`${API_BASE}/discovery/preferences/${userId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(preference),
  });

  if (!response.ok) {
    throw new Error(`Failed to create sharing preference: ${response.statusText}`);
  }

  return response.json();
}
