import { useState } from 'react';
import { useAgents, useProposals, useRunAgent, useReviewProposal, useToggleAgent } from '@/hooks/useAgents';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { ProposalCard } from '@/components/ProposalCard';
import { Bot, Play, Power } from 'lucide-react';
import { formatTimeAgo, formatAgentName } from '@/utils/formatters';
import type { AgentType, AgentProposal } from '@/types/agents';

export function AgentsPage() {
  const { data: agents, isLoading: agentsLoading, error } = useAgents();
  const { data: proposals, isLoading: proposalsLoading } = useProposals();
  const runAgent = useRunAgent();
  const reviewProposal = useReviewProposal();
  const toggleAgent = useToggleAgent();

  const [selectedTab, setSelectedTab] = useState<'agents' | 'proposals'>('agents');
  const [runningAgent, setRunningAgent] = useState<AgentType | null>(null);

  const pendingProposals = proposals?.filter(p => p.status === 'pending') || [];
  const reviewedProposals = proposals?.filter(p => p.status !== 'pending') || [];

  const handleRunAgent = async (type: AgentType) => {
    setRunningAgent(type);
    try {
      await runAgent.mutateAsync(type);
    } finally {
      setRunningAgent(null);
    }
  };

  const handleToggleAgent = async (type: AgentType, enabled: boolean) => {
    await toggleAgent.mutateAsync({ type, enabled });
  };

  const handleApprove = async (proposal: AgentProposal) => {
    await reviewProposal.mutateAsync({ id: proposal.id, action: 'approve' });
  };

  const handleReject = async (proposal: AgentProposal) => {
    await reviewProposal.mutateAsync({ id: proposal.id, action: 'reject' });
  };

  if (error) {
    return <ErrorMessage message="Failed to load AI agents. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Agents</h1>
        <p className="text-gray-600 mt-1">
          Autonomous assistants that help optimize the gift economy
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          <button
            onClick={() => setSelectedTab('agents')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'agents'
                ? 'border-solarpunk-600 text-solarpunk-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Agents ({agents?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('proposals')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'proposals'
                ? 'border-solarpunk-600 text-solarpunk-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Proposals ({proposals?.length || 0})
            {pendingProposals.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-full text-xs">
                {pendingProposals.length} pending
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* Agents Tab */}
      {selectedTab === 'agents' && (
        <div>
          {agentsLoading ? (
            <Loading text="Loading AI agents..." />
          ) : agents && agents.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {agents.map((agent) => (
                <Card key={agent.id}>
                  <div className="flex flex-col gap-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`rounded-full p-3 ${
                          agent.enabled ? 'bg-solarpunk-100' : 'bg-gray-100'
                        }`}>
                          <Bot className={`w-6 h-6 ${
                            agent.enabled ? 'text-solarpunk-700' : 'text-gray-400'
                          }`} />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg text-gray-900">
                            {formatAgentName(agent.type)}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleToggleAgent(agent.type as AgentType, !agent.enabled)}
                        className={`p-2 rounded-lg transition-colors ${
                          agent.enabled
                            ? 'bg-green-100 text-green-700 hover:bg-green-200'
                            : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                        }`}
                        title={agent.enabled ? 'Disable agent' : 'Enable agent'}
                      >
                        <Power className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Status</p>
                        <p className="font-medium text-gray-900">
                          {agent.enabled ? 'Enabled' : 'Disabled'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600">Opt-in</p>
                        <p className="font-medium text-gray-900">
                          {agent.opt_in ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>

                    {agent.last_run && (
                      <p className="text-xs text-gray-500">
                        Last run {formatTimeAgo(agent.last_run)}
                      </p>
                    )}

                    <Button
                      size="sm"
                      onClick={() => handleRunAgent(agent.type as AgentType)}
                      disabled={!agent.enabled || runningAgent === agent.type}
                      fullWidth
                    >
                      {runningAgent === agent.type ? (
                        <>Running...</>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Run Agent
                        </>
                      )}
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <div className="text-center py-12">
                <Bot className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No AI agents configured</p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Proposals Tab */}
      {selectedTab === 'proposals' && (
        <div className="space-y-6">
          {proposalsLoading ? (
            <Loading text="Loading proposals..." />
          ) : (
            <>
              {/* Pending Proposals */}
              {pendingProposals.length > 0 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Pending Review ({pendingProposals.length})
                  </h2>
                  <div className="space-y-4">
                    {pendingProposals.map((proposal) => (
                      <ProposalCard
                        key={proposal.id}
                        proposal={proposal}
                        onApprove={handleApprove}
                        onReject={handleReject}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Reviewed Proposals */}
              {reviewedProposals.length > 0 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Reviewed ({reviewedProposals.length})
                  </h2>
                  <div className="space-y-4">
                    {reviewedProposals.map((proposal) => (
                      <ProposalCard
                        key={proposal.id}
                        proposal={proposal}
                        showActions={false}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {proposals?.length === 0 && (
                <Card>
                  <div className="text-center py-12">
                    <Bot className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 mb-2">No proposals yet</p>
                    <p className="text-sm text-gray-500">
                      AI agents will create proposals based on patterns they detect
                    </p>
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <Bot className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-blue-900 mb-2">About AI Agents</h3>
            <p className="text-sm text-blue-800">
              These autonomous agents analyze patterns in the gift economy and make suggestions
              to optimize resource sharing. All proposals require human approval before taking
              effect. Agents respect your privacy and only work with data you've opted into sharing.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
