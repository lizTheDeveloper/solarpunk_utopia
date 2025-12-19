export interface Cell {
  id: string;
  name: string;
  description?: string;
  location_lat?: number;
  location_lon?: number;
  radius_km: number;
  created_at: string;
  member_count: number;
  max_members: number;
  is_accepting_members: boolean;
  settings?: CellSettings;
}

export interface CellMembership {
  id: string;
  cell_id: string;
  user_id: string;
  role: 'member' | 'steward';
  joined_at: string;
  vouched_by?: string;
  is_active: boolean;
}

export interface CellSettings {
  min_trust_to_join?: number;
  offer_default_scope?: 'cell' | 'region' | 'network';
  vouch_requirement?: 'any_member' | 'steward_only' | 'consensus';
  max_members?: number;
  steward_term_days?: number;
}

export interface CreateCellRequest {
  name: string;
  description?: string;
  location_lat?: number;
  location_lon?: number;
  radius_km?: number;
  max_members?: number;
}
