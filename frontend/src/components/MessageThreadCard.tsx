import { MessageCircle, Clock } from 'lucide-react';
import { Card } from './Card';
import type { MessageThread } from '@/types/message';

interface MessageThreadCardProps {
  thread: MessageThread;
  onClick?: () => void;
  currentUserId?: string;
}

export function MessageThreadCard({
  thread,
  onClick,
  currentUserId,
}: MessageThreadCardProps) {
  const otherParticipants = thread.participants.filter(
    (p) => p !== currentUserId
  );
  const participantLabel =
    otherParticipants.length > 0
      ? `User ${otherParticipants[0].slice(0, 8)}`
      : 'Thread';

  const timeAgo = thread.last_message_at
    ? formatTimeAgo(new Date(thread.last_message_at))
    : 'No messages yet';

  return (
    <Card hoverable onClick={onClick} className="relative">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-solarpunk-100 rounded-full flex items-center justify-center">
            <MessageCircle className="w-6 h-6 text-solarpunk-600" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-1">
            <h3 className="text-base font-semibold text-gray-900 truncate">
              {participantLabel}
            </h3>
            <div className="flex items-center gap-1 text-xs text-gray-500 ml-2">
              <Clock className="w-3 h-3" />
              <span>{timeAgo}</span>
            </div>
          </div>

          {thread.last_message_preview && (
            <p className="text-sm text-gray-600 line-clamp-2 mb-2">
              {thread.last_message_preview}
            </p>
          )}

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 capitalize">
              {thread.thread_type}
            </span>
            {thread.unread_count > 0 && (
              <span className="bg-solarpunk-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                {thread.unread_count > 9 ? '9+' : thread.unread_count}
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
