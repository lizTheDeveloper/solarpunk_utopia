// Network and Bridge Management types

export interface AccessPoint {
  ssid: string;
  bssid: string;
  signal_strength: number;
  frequency: number;
  channel: number;
  security: string;
  last_seen: string;
}

export interface IslandTopology {
  island_id: string;
  access_points: AccessPoint[];
  connected_nodes: string[];
  node_count: number;
  created_at: string;
}

export interface BridgeNode {
  id: string;
  node_id: string;
  current_island_id: string;
  islands_visited: string[];
  bundles_carried: number;
  bundles_delivered: number;
  mode: 'A' | 'C';
  battery_level?: number;
  status: 'active' | 'inactive' | 'traveling';
  last_seen: string;
  created_at: string;
}

export interface BridgeMetrics {
  node_id: string;
  total_islands_visited: number;
  total_bundles_carried: number;
  total_bundles_delivered: number;
  average_delivery_time_seconds: number;
  current_island: string;
  uptime_seconds: number;
}

export interface NetworkStatus {
  node_id: string;
  current_island_id: string;
  mode: 'A' | 'C';
  connected_to_internet: boolean;
  active_bridges: number;
  known_islands: number;
  bundles_in_outbox: number;
  last_bridge_contact?: string;
}

export interface IslandTransition {
  bridge_node_id: string;
  from_island_id: string;
  to_island_id: string;
  timestamp: string;
  bundles_carried: number;
}

export interface ModeConfig {
  mode: 'A' | 'C';
  auto_switch: boolean;
  stay_duration_seconds?: number;
}

export interface BridgeConfig {
  enabled: boolean;
  mode: 'A' | 'C';
  auto_mode_switch: boolean;
  stay_duration_seconds: number;
  max_bundle_storage: number;
}
