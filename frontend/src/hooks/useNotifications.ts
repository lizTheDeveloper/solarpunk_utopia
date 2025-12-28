import { useState } from 'react';
import { useProposals, usePendingCount } from './useAgents';

export function useNotifications() {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);

  const { data: pendingProposals = [], isLoading } = useProposals('pending');
  const { data: pendingCountData } = usePendingCount();

  const pendingCount = pendingCountData?.count ?? pendingProposals.length;

  return {
    proposals: pendingProposals,
    pendingCount,
    isLoading,
    isOpen,
    selectedProposalId,
    toggle: () => setIsOpen(!isOpen),
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    selectProposal: (id: string) => {
      setSelectedProposalId(id);
      setIsOpen(false);
    },
    clearSelection: () => setSelectedProposalId(null),
  };
}
