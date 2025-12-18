// AI Agent System types

export type AgentType =
  | 'unused_resource_matcher'
  | 'seasonal_need_predictor'
  | 'knowledge_sharer'
  | 'bridge_optimizer'
  | 'need_aggregator'
  | 'reciprocity_balancer'
  | 'resource_lifespan_tracker';

export interface Agent {
  id: string;
  type: AgentType;
  name: string;
  description: string;
  enabled: boolean;
  opt_in: boolean;
  last_run?: string;
  next_scheduled_run?: string;
  run_interval_seconds: number;
  config: Record<string, any>;
}

export interface AgentProposal {
  id: string;
  agent_type: AgentType;
  agent_name: string;
  proposal_type: 'intent' | 'match' | 'action' | 'notification';
  title: string;
  description: string;
  reasoning: string;
  confidence: number; // 0-1
  data: any; // Proposal-specific data
  constraints: string[];
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  created_at: string;
  expires_at?: string;
  reviewed_at?: string;
  reviewed_by?: string;
}

export interface UnusedResourceProposal extends AgentProposal {
  data: {
    resource_id: string;
    resource_name: string;
    last_used?: string;
    suggested_action: 'offer' | 'redistribute' | 'archive';
    potential_recipients?: string[];
  };
}

export interface SeasonalNeedProposal extends AgentProposal {
  data: {
    resource_category: string;
    predicted_need_quantity: number;
    prediction_date: string;
    historical_pattern: string;
    suggested_agents: string[];
  };
}

export interface KnowledgeShareProposal extends AgentProposal {
  data: {
    file_id: string;
    filename: string;
    relevant_agents: string[];
    relevance_reason: string;
    priority: 'low' | 'medium' | 'high';
  };
}

export interface BridgeOptimizationProposal extends AgentProposal {
  data: {
    bridge_node_id: string;
    current_route: string[];
    suggested_route: string[];
    estimated_improvement: string;
    bundle_priorities: string[];
  };
}

export interface NeedAggregationProposal extends AgentProposal {
  data: {
    need_ids: string[];
    resource_specification_id: string;
    total_quantity: number;
    participating_agents: string[];
    bulk_offer_suggestion: boolean;
  };
}

export interface ReciprocityProposal extends AgentProposal {
  data: {
    agent_id: string;
    agent_name: string;
    balance_score: number; // negative = more receiving, positive = more giving
    suggested_action: 'encourage_offering' | 'encourage_receiving' | 'balanced';
    recent_exchanges: number;
  };
}

export interface ResourceLifespanProposal extends AgentProposal {
  data: {
    resource_id: string;
    resource_name: string;
    expiration_date?: string;
    estimated_remaining_lifespan: string;
    suggested_action: 'use_soon' | 'offer_now' | 'preserve' | 'compost';
    urgency: 'low' | 'medium' | 'high';
  };
}

export interface AgentRunResult {
  agent_type: AgentType;
  run_id: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  proposals_created: number;
  success: boolean;
  error?: string;
}

export interface AgentStats {
  total_runs: number;
  total_proposals: number;
  approved_proposals: number;
  rejected_proposals: number;
  pending_proposals: number;
  average_confidence: number;
  last_run?: string;
}

export interface RunAgentRequest {
  agent_type: AgentType;
}

export interface ReviewProposalRequest {
  proposal_id: string;
  action: 'approve' | 'reject';
  note?: string;
}
