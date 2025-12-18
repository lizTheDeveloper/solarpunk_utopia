// DTN Bundle System types

export interface Bundle {
  id: string;
  source: string;
  destination: string;
  payload: string | object;
  payload_type: string;
  priority: number;
  ttl: number;
  created_at: string;
  expires_at: string;
  status: 'pending' | 'in_transit' | 'delivered' | 'expired' | 'failed';
  hop_count?: number;
  route?: string[];
}

export interface BundleMetadata {
  bundle_id: string;
  size_bytes: number;
  created_at: string;
  last_forwarded?: string;
  times_forwarded: number;
}

export interface BundleStatus {
  bundle_id: string;
  status: 'pending' | 'in_transit' | 'delivered' | 'expired' | 'failed';
  current_holder?: string;
  destination: string;
  hops: number;
  created_at: string;
  updated_at: string;
}

export interface CreateBundleRequest {
  destination: string;
  payload: any;
  payload_type: string;
  priority?: number;
  ttl?: number;
}

export interface BundleStats {
  total_created: number;
  total_delivered: number;
  total_pending: number;
  total_expired: number;
  average_hops: number;
  average_delivery_time_seconds: number;
}

export interface OutboxStatus {
  bundles_pending: number;
  bundles_in_transit: number;
  last_sync?: string;
}
