import { useState } from 'react';
import { X, Check, XCircle } from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

interface Proposal {
  id: string;
  agent_name: string;
  title: string;
  description?: string;
  priority: string;
  created_at: string;
  rationale?: string;
}

interface ProposalApprovalModalProps {
  proposal: Proposal | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (proposalId: string) => Promise<void>;
  onReject: (proposalId: string, reason: string) => Promise<void>;
  isLoading?: boolean;
}

export function ProposalApprovalModal({
  proposal,
  isOpen,
  onClose,
  onApprove,
  onReject,
  isLoading = false,
}: ProposalApprovalModalProps) {
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);

  if (!isOpen || !proposal) return null;

  const handleApprove = async () => {
    await onApprove(proposal.id);
    onClose();
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    await onReject(proposal.id, rejectReason);
    setRejectReason('');
    setShowRejectForm(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <Card>
          {/* Header */}
          <div className="flex items-center justify-between mb-4 pb-4 border-b">
            <h2 className="text-2xl font-bold text-gray-900">Agent Proposal</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Proposal Details */}
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Agent</label>
              <p className="text-gray-900">{proposal.agent_name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <p className="text-gray-900 font-medium">{proposal.title}</p>
            </div>

            {proposal.description && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <p className="text-gray-700 whitespace-pre-wrap">{proposal.description}</p>
              </div>
            )}

            {proposal.rationale && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rationale</label>
                <p className="text-gray-700 whitespace-pre-wrap">{proposal.rationale}</p>
              </div>
            )}

            <div className="flex gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <span className={`px-3 py-1 rounded text-sm font-medium ${
                  proposal.priority === 'emergency' || proposal.priority === 'critical'
                    ? 'bg-red-100 text-red-800'
                    : proposal.priority === 'high'
                    ? 'bg-orange-100 text-orange-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {proposal.priority}
                </span>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                <p className="text-gray-700">
                  {new Date(proposal.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Reject Form (conditional) */}
          {showRejectForm && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded">
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Rejection Reason *
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="Explain why this proposal is being rejected..."
                required
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            {!showRejectForm ? (
              <>
                <Button
                  onClick={handleApprove}
                  disabled={isLoading}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <Check className="w-4 h-4 mr-2" />
                  {isLoading ? 'Approving...' : 'Approve'}
                </Button>
                <Button
                  onClick={() => setShowRejectForm(true)}
                  disabled={isLoading}
                  variant="secondary"
                  className="flex-1 border-red-300 text-red-700 hover:bg-red-50"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Reject
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={handleReject}
                  disabled={isLoading || !rejectReason.trim()}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  {isLoading ? 'Rejecting...' : 'Confirm Rejection'}
                </Button>
                <Button
                  onClick={() => {
                    setShowRejectForm(false);
                    setRejectReason('');
                  }}
                  disabled={isLoading}
                  variant="secondary"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
