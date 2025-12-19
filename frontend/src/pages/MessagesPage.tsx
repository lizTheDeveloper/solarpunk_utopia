import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useThreads } from '@/hooks/useMessages';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { MessageThreadCard } from '@/components/MessageThreadCard';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { MessageCircle, Plus, Search } from 'lucide-react';

export function MessagesPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const { data: threads, isLoading, error } = useThreads();

  // TODO: Get current user from auth context
  const currentUserId = 'demo-user';

  // Filter threads
  const filteredThreads = threads?.filter((thread) => {
    if (!searchTerm) return true;
    // Search in participants or last message
    return (
      thread.participants.some((p) => p.toLowerCase().includes(searchTerm.toLowerCase())) ||
      thread.last_message_preview?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }) || [];

  if (error) {
    return <ErrorMessage message="Failed to load messages. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Messages</h1>
          <p className="text-gray-600 mt-1">
            E2E encrypted mesh messaging - works offline
          </p>
        </div>
        <Button onClick={() => navigate('/messages/new')}>
          <Plus className="w-4 h-4 mr-2" />
          New Message
        </Button>
      </div>

      {/* Search */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Search className="w-5 h-5 text-gray-600" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
          />
        </div>
      </Card>

      {/* Threads List */}
      {isLoading ? (
        <Loading />
      ) : filteredThreads.length > 0 ? (
        <div className="space-y-3">
          {filteredThreads.map((thread) => (
            <MessageThreadCard
              key={thread.id}
              thread={thread}
              currentUserId={currentUserId}
              onClick={() => navigate(`/messages/${thread.id}`)}
            />
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {searchTerm ? 'No messages found' : 'No messages yet'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchTerm
                ? 'Try a different search term'
                : 'Start a conversation with your community members'}
            </p>
            {!searchTerm && (
              <Button onClick={() => navigate('/messages/new')}>
                Send Your First Message
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
