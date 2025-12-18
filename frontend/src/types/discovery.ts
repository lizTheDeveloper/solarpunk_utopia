// Discovery & Search types

export interface IndexEntry {
  id: string;
  type: 'offer' | 'need' | 'resource' | 'agent' | 'file';
  title: string;
  description: string;
  keywords: string[];
  category?: string;
  location?: string;
  created_by: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface DistributedIndex {
  id: string;
  node_id: string;
  entries: IndexEntry[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface SearchQuery {
  query: string;
  type?: 'offer' | 'need' | 'resource' | 'agent' | 'file';
  category?: string;
  location?: string;
  limit?: number;
}

export interface SearchResult {
  entry: IndexEntry;
  score: number;
  source: 'local' | 'cached' | 'remote';
  source_node?: string;
  cached_at?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
  sources_searched: string[];
}

export interface CachedIndex {
  node_id: string;
  index: DistributedIndex;
  cached_at: string;
  expires_at: string;
}

export interface IndexStats {
  local_entries: number;
  cached_indexes: number;
  total_searchable_entries: number;
  last_sync?: string;
}
