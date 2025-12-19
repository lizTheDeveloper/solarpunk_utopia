import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSendMessage } from '@/hooks/useMessages';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ArrowLeft, Send } from 'lucide-react';

export function NewMessagePage() {
  const navigate = useNavigate();
  const [recipientId, setRecipientId] = useState('');
  const [messageText, setMessageText] = useState('');
  const [error, setError] = useState<string | null>(null);

  const sendMutation = useSendMessage();

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!recipientId.trim() || !messageText.trim()) {
      setError('Please fill in all fields');
      return;
    }

    try {
      const message = await sendMutation.mutateAsync({
        recipient_id: recipientId,
        content: messageText,
      });
      // Navigate to the thread
      if (message.thread_id) {
        navigate(`/messages/${message.thread_id}`);
      } else {
        navigate('/messages');
      }
    } catch (err) {
      setError('Failed to send message. Please try again.');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate('/messages')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Messages
      </button>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">New Message</h1>
        <p className="text-gray-600 mt-1">
          Send an encrypted message to another community member
        </p>
      </div>

      {/* Form */}
      <Card>
        <form onSubmit={handleSend} className="space-y-6">
          {/* Recipient */}
          <div>
            <label
              htmlFor="recipient"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Recipient User ID *
            </label>
            <input
              id="recipient"
              type="text"
              value={recipientId}
              onChange={(e) => setRecipientId(e.target.value)}
              placeholder="Enter user ID"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              You can find user IDs in your cell member lists or exchanges
            </p>
          </div>

          {/* Message */}
          <div>
            <label
              htmlFor="message"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Message *
            </label>
            <textarea
              id="message"
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Type your message..."
              required
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Your message will be end-to-end encrypted and delivered over the DTN mesh
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* Submit */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/messages')}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={sendMutation.isPending}>
              <Send className="w-4 h-4 mr-2" />
              {sendMutation.isPending ? 'Sending...' : 'Send Message'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
