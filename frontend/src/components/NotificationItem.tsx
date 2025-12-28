import { Bot, AlertCircle } from 'lucide-react';

interface Proposal {
  id: string;
  agent_name: string;
  title: string;
  priority: 'low' | 'medium' | 'high' | 'critical' | 'emergency';
  created_at: string;
}

interface NotificationItemProps {
  proposal: Proposal;
  onClick: () => void;
}

const priorityColors = {
  emergency: 'bg-red-100 border-red-300 text-red-900',
  critical: 'bg-red-50 border-red-200 text-red-800',
  high: 'bg-orange-50 border-orange-200 text-orange-800',
  medium: 'bg-gray-50 border-gray-200 text-gray-800',
  low: 'bg-gray-50 border-gray-200 text-gray-600',
};

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

export function NotificationItem({ proposal, onClick }: NotificationItemProps) {
  const priorityColor = priorityColors[proposal.priority] || priorityColors.medium;

  return (
    <button
      onClick={onClick}
      className={`w-full p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors text-left ${
        proposal.priority === 'emergency' || proposal.priority === 'critical'
          ? 'border-l-4 border-l-red-500'
          : proposal.priority === 'high'
          ? 'border-l-4 border-l-orange-500'
          : ''
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          {proposal.priority === 'emergency' || proposal.priority === 'critical' ? (
            <AlertCircle className="w-5 h-5 text-red-600" />
          ) : (
            <Bot className="w-5 h-5 text-blue-600" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="font-medium text-gray-900 text-sm">{proposal.agent_name}</p>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${priorityColor}`}>
              {proposal.priority}
            </span>
          </div>
          <p className="text-gray-700 text-sm mb-1 truncate">{proposal.title}</p>
          <p className="text-gray-500 text-xs">{formatTimeAgo(proposal.created_at)}</p>
        </div>
      </div>
    </button>
  );
}
