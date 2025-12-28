import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { NotificationItem } from './NotificationItem';

interface Proposal {
  id: string;
  agent_name: string;
  title: string;
  priority: 'low' | 'medium' | 'high' | 'critical' | 'emergency';
  created_at: string;
  status: string;
}

interface NotificationDropdownProps {
  proposals: Proposal[];
  isOpen: boolean;
  onClose: () => void;
  onProposalClick: (proposalId: string) => void;
}

export function NotificationDropdown({
  proposals,
  isOpen,
  onClose,
  onProposalClick,
}: NotificationDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Close on Escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
      role="dialog"
      aria-label="Notifications"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Notifications</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
          aria-label="Close notifications"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Proposals List */}
      <div className="max-h-96 overflow-y-auto">
        {proposals.length > 0 ? (
          <div>
            {proposals.map((proposal) => (
              <NotificationItem
                key={proposal.id}
                proposal={proposal}
                onClick={() => onProposalClick(proposal.id)}
              />
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">
            <p>No pending notifications</p>
          </div>
        )}
      </div>
    </div>
  );
}
