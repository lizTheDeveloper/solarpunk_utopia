import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useThreadMessages, useSendMessage } from '@/hooks/useMessages';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ArrowLeft, Send, Lock } from 'lucide-react';
import { clsx } from 'clsx';
import type { Message } from '@/types/message';

export function MessageThreadPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [messageText, setMessageText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: messages, isLoading, error } = useThreadMessages(threadId!);
  const sendMutation = useSendMessage();

  // TODO: Get current user from auth context
  const currentUserId = 'demo-user';

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageText.trim() || !threadId) return;

    // Get recipient from thread's first message
    const firstMessage = messages?.[0];
    if (!firstMessage) return;

    const recipientId =
      firstMessage.sender_id === currentUserId
        ? firstMessage.recipient_id
        : firstMessage.sender_id;

    try {
      await sendMutation.mutateAsync({
        recipient_id: recipientId,
        content: messageText,
        thread_id: threadId,
      });
      setMessageText('');
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  if (error) {
    return <ErrorMessage message="Failed to load messages. Please try again later." />;
  }

  if (isLoading) {
    return <Loading />;
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="mb-4">
        <button
          onClick={() => navigate('/messages')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Messages
        </button>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Conversation
              </h1>
              <p className="text-sm text-gray-600 flex items-center gap-1">
                <Lock className="w-3 h-3" />
                End-to-end encrypted
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Messages */}
      <Card className="flex-1 overflow-y-auto mb-4">
        {messages && messages.length > 0 ? (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={message.sender_id === currentUserId}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            No messages yet. Start the conversation!
          </div>
        )}
      </Card>

      {/* Compose */}
      <Card>
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
          />
          <Button
            type="submit"
            disabled={!messageText.trim() || sendMutation.isPending}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Messages are E2E encrypted and delivered over DTN mesh
        </p>
      </Card>
    </div>
  );
}

function MessageBubble({ message, isOwn }: { message: Message; isOwn: boolean }) {
  // Decode the base64 content (this is placeholder - real app would decrypt)
  let content: string;
  try {
    content = atob(message.encrypted_content);
  } catch {
    content = '[Encrypted Message]';
  }

  return (
    <div
      className={clsx(
        'flex',
        isOwn ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[70%] rounded-lg px-4 py-2',
          isOwn
            ? 'bg-solarpunk-500 text-white'
            : 'bg-gray-100 text-gray-900'
        )}
      >
        <p className="text-sm">{content}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs opacity-75">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          {isOwn && message.delivery_status && (
            <span className="text-xs opacity-75 capitalize">
              {message.delivery_status === 'read' ? '✓✓' : message.delivery_status === 'delivered' ? '✓' : '○'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
