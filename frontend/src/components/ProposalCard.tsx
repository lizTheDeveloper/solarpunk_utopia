import { AgentProposal } from '@/types/agents';
import { Card } from './Card';
import { Button } from './Button';
import { Bot, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import { formatTimeAgo, formatAgentName, formatConfidence } from '@/utils/formatters';

interface ProposalCardProps {
  proposal: AgentProposal;
  onApprove?: (proposal: AgentProposal) => void;
  onReject?: (proposal: AgentProposal) => void;
  showActions?: boolean;
}

export function ProposalCard({ proposal, onApprove, onReject, showActions = true }: ProposalCardProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <TrendingUp className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="bg-solarpunk-100 rounded-full p-2">
              <Bot className="w-5 h-5 text-solarpunk-700" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-gray-900">{proposal.title}</h3>
              <p className="text-sm text-gray-600">{formatAgentName(proposal.agent_type)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon(proposal.status)}
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(proposal.status)}`}>
              {proposal.status}
            </span>
          </div>
        </div>

        <p className="text-gray-700">{proposal.description}</p>

        <div className="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
          <p className="text-sm font-medium text-blue-900 mb-1">Agent Reasoning</p>
          <p className="text-sm text-blue-800">{proposal.reasoning}</p>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-gray-600">Confidence: </span>
            <span className="font-medium text-gray-900">{formatConfidence(proposal.confidence)}</span>
          </div>
          <div>
            <span className="text-gray-600">Type: </span>
            <span className="font-medium text-gray-900">{proposal.proposal_type}</span>
          </div>
        </div>

        {proposal.constraints && proposal.constraints.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Constraints:</p>
            <ul className="text-sm text-gray-600 space-y-1">
              {proposal.constraints.map((constraint, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-solarpunk-600 mt-1">•</span>
                  <span>{constraint}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-xs text-gray-500">
            Proposed {formatTimeAgo(proposal.created_at)}
          </span>
          {showActions && proposal.status === 'pending' && (
            <div className="flex gap-2">
              {onReject && (
                <Button size="sm" variant="secondary" onClick={() => onReject(proposal)}>
                  Reject
                </Button>
              )}
              {onApprove && (
                <Button size="sm" onClick={() => onApprove(proposal)}>
                  Approve
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
