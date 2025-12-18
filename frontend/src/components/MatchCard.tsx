import { Match } from '@/types/valueflows';
import { Card } from './Card';
import { Button } from './Button';
import { ArrowRight, Sparkles } from 'lucide-react';
import { formatTimeAgo, formatQuantity, formatPercentage } from '@/utils/formatters';

interface MatchCardProps {
  match: Match;
  onAccept?: (match: Match) => void;
  onReject?: (match: Match) => void;
  showActions?: boolean;
}

export function MatchCard({ match, onAccept, onReject, showActions = true }: MatchCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'proposed':
        return 'bg-yellow-100 text-yellow-800';
      case 'accepted':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'fulfilled':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-solarpunk-600" />
            <h3 className="font-semibold text-lg text-gray-900">Match Found</h3>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(match.status)}`}>
            {match.status}
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1 bg-solarpunk-50 rounded-lg p-3">
            <p className="text-xs text-gray-600 mb-1">Offer</p>
            <p className="font-medium text-gray-900">{match.offer?.agent?.name}</p>
            <p className="text-sm text-gray-700">{match.offer?.resource_specification?.name}</p>
          </div>
          <ArrowRight className="w-6 h-6 text-gray-400 flex-shrink-0" />
          <div className="flex-1 bg-blue-50 rounded-lg p-3">
            <p className="text-xs text-gray-600 mb-1">Need</p>
            <p className="font-medium text-gray-900">{match.need?.agent?.name}</p>
            <p className="text-sm text-gray-700">{match.need?.resource_specification?.name}</p>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div>
            <span className="text-gray-600">Quantity: </span>
            <span className="font-medium text-gray-900">{formatQuantity(match.quantity, match.unit)}</span>
          </div>
          <div>
            <span className="text-gray-600">Match Score: </span>
            <span className="font-medium text-solarpunk-700">{formatPercentage(match.score, 1)}</span>
          </div>
        </div>

        {match.reason && (
          <p className="text-sm text-gray-700 bg-gray-50 rounded p-2 italic">
            {match.reason}
          </p>
        )}

        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Matched {formatTimeAgo(match.created_at)}
          </span>
          {showActions && match.status === 'proposed' && (
            <div className="flex gap-2">
              {onReject && (
                <Button size="sm" variant="secondary" onClick={() => onReject(match)}>
                  Reject
                </Button>
              )}
              {onAccept && (
                <Button size="sm" onClick={() => onAccept(match)}>
                  Accept
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
