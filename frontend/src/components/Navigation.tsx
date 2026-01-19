import { NavLink } from 'react-router-dom';
import {
  Home,
  Gift,
  Heart,
  ArrowLeftRight,
  Search,
  BookOpen,
  Radio,
  Bot,
  Plus,
  Users,
  MessageCircle,
  Package
} from 'lucide-react';
import { clsx } from 'clsx';
import { CommunitySelector } from './CommunitySelector';
import { NotificationBadge } from './NotificationBadge';
import { NotificationDropdown } from './NotificationDropdown';
import { ProposalApprovalModal } from './ProposalApprovalModal';
import { usePendingCount, useProposal, useReviewProposal } from '@/hooks/useAgents';
import { useNotifications } from '@/hooks/useNotifications';
import { toast } from 'sonner';

const navSections = [
  {
    id: 'home',
    label: 'Home',
    icon: Home,
    path: '/',
    items: []
  },
  {
    id: 'exchange',
    label: 'Exchange',
    icon: Gift,
    path: '/offers',
    items: [
      { path: '/offers', label: 'Offers', icon: Gift, tooltip: 'Things people are sharing' },
      { path: '/needs', label: 'Needs', icon: Heart, tooltip: 'Things people need' },
      { path: '/discovery', label: 'Search', icon: Search, tooltip: 'Find offers and needs' },
    ]
  },
  {
    id: 'community',
    label: 'Community',
    icon: Users,
    path: '/cells',
    items: [
      { path: '/community-shelf', label: 'Shelf', icon: Package, tooltip: 'Shared community resources' },
      { path: '/cells', label: 'Groups', icon: Users, tooltip: 'Connect with neighbors' },
      { path: '/messages', label: 'Messages', icon: MessageCircle, tooltip: 'Direct messages' },
    ]
  },
  {
    id: 'activity',
    label: 'My Activity',
    icon: ArrowLeftRight,
    path: '/exchanges',
    items: [
      { path: '/exchanges', label: 'Exchanges', icon: ArrowLeftRight, tooltip: 'Your active exchanges' },
      { path: '/agents', label: 'AI Helpers', icon: Bot, showBadge: true, tooltip: 'AI that helps match offers with needs' },
    ]
  },
  {
    id: 'system',
    label: 'System',
    icon: Radio,
    path: '/network',
    items: [
      { path: '/knowledge', label: 'Knowledge', icon: BookOpen, tooltip: 'Learn and share knowledge' },
      { path: '/network', label: 'Network', icon: Radio, tooltip: 'Mesh network status' },
    ]
  }
];

// Flatten for mobile view
const navItems = navSections.flatMap(section =>
  section.items.length > 0 ? section.items : [{ path: section.path, label: section.label, icon: section.icon, tooltip: undefined, showBadge: false }]
);

export function Navigation() {
  // Poll for pending proposals count every 30 seconds using new hook
  const { data: pendingCount } = usePendingCount();

  // Notification system
  const notifications = useNotifications();
  const { data: selectedProposal } = useProposal(notifications.selectedProposalId || '');
  const reviewProposal = useReviewProposal();

  const count = pendingCount || 0;

  // Determine active section based on current path
  const location = window.location.pathname;
  const activeSection = navSections.find(section =>
    section.path === location || section.items.some(item => item.path === location)
  ) || navSections[0];

  const handleApprove = async (proposalId: string) => {
    try {
      await reviewProposal.mutateAsync({ id: proposalId, action: 'approve' });
      toast.success('Proposal approved successfully');
      notifications.clearSelection();
    } catch (error) {
      console.error('Failed to approve proposal:', error);
      toast.error('Failed to approve proposal');
    }
  };

  const handleReject = async (proposalId: string, reason: string) => {
    try {
      await reviewProposal.mutateAsync({ id: proposalId, action: 'reject', note: reason });
      toast.success('Proposal rejected');
      notifications.clearSelection();
    } catch (error) {
      console.error('Failed to reject proposal:', error);
      toast.error('Failed to reject proposal');
    }
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm" role="navigation" aria-label="Main navigation">
      {/* Primary Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-solarpunk-400 to-solarpunk-600 rounded-lg flex items-center justify-center flex-shrink-0" aria-hidden="true">
              <Gift className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-xl font-bold text-gray-900 truncate">Solarpunk Mesh</h1>
              <p className="text-xs text-gray-600 hidden sm:block">Gift Economy Network</p>
            </div>
          </div>

          {/* Primary sections */}
          <div className="hidden md:flex items-center gap-1" role="navigation" aria-label="Primary sections">
            {navSections.map((section) => (
              <NavLink
                key={section.id}
                to={section.path}
                aria-label={`Navigate to ${section.label}`}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-solarpunk-500 focus:ring-offset-2',
                    isActive || activeSection.id === section.id
                      ? 'bg-solarpunk-100 text-solarpunk-800'
                      : 'text-gray-700 hover:bg-gray-100'
                  )
                }
              >
                <section.icon className="w-4 h-4" aria-hidden="true" />
                <span>{section.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <div className="flex items-center">
              <CommunitySelector />
            </div>

            {/* Notification Badge */}
            <div className="relative flex items-center">
              <NotificationBadge
                count={notifications.pendingCount}
                onClick={notifications.toggle}
                isOpen={notifications.isOpen}
              />
              <NotificationDropdown
                proposals={notifications.proposals}
                isOpen={notifications.isOpen}
                onClose={notifications.close}
                onProposalClick={notifications.selectProposal}
              />
            </div>

            {/* AI Helpers - always visible with badge */}
            <NavLink
              to="/agents"
              className="relative flex items-center justify-center gap-1 sm:gap-2 bg-purple-600 text-white px-2 sm:px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-xs sm:text-sm font-medium h-10 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              aria-label={`AI Helpers${count > 0 ? ` (${count} pending proposals)` : ''}`}
              title="AI that helps match offers with needs"
            >
              <Bot className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">AI</span>
              {count > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center" aria-label={`${count} pending proposals`}>
                  {count > 9 ? '9+' : count}
                </span>
              )}
            </NavLink>

            <NavLink
              to="/offers/create"
              className="flex items-center justify-center gap-1 sm:gap-2 bg-solarpunk-600 text-white px-2 sm:px-4 py-2 rounded-lg hover:bg-solarpunk-700 transition-colors text-xs sm:text-sm font-medium h-10 focus:outline-none focus:ring-2 focus:ring-solarpunk-500 focus:ring-offset-2"
              aria-label="Create new offer"
            >
              <Plus className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">New Offer</span>
            </NavLink>
            <NavLink
              to="/needs/create"
              className="flex items-center justify-center gap-1 sm:gap-2 bg-blue-600 text-white px-2 sm:px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-xs sm:text-sm font-medium h-10 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="Create new need"
            >
              <Plus className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">New Need</span>
            </NavLink>
          </div>
        </div>

        {/* Sub-navigation */}
        {activeSection.items.length > 0 && (
          <div className="hidden md:block border-t border-gray-100">
            <div className="flex items-center gap-1 py-2">
              {activeSection.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={item.tooltip}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors relative',
                      isActive
                        ? 'bg-solarpunk-50 text-solarpunk-700'
                        : 'text-gray-600 hover:bg-gray-50'
                    )
                  }
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.label}</span>
                  {item.showBadge && count > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                      {count > 9 ? '9+' : count}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        )}

        {/* Mobile navigation */}
        <div className="md:hidden relative">
          {/* Fade gradient indicators for scroll */}
          <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white to-transparent pointer-events-none z-10" />
          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent pointer-events-none z-10" />

          <div className="flex overflow-x-auto pb-3 gap-1 scrollbar-hide px-2 snap-x snap-mandatory">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                title={item.tooltip}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap relative flex-shrink-0 snap-start',
                    isActive
                      ? 'bg-solarpunk-100 text-solarpunk-800'
                      : 'text-gray-700 hover:bg-gray-100'
                  )
                }
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
                {item.showBadge && count > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {count > 9 ? '9+' : count}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        </div>
      </div>

      {/* Proposal Approval Modal */}
      <ProposalApprovalModal
        proposal={selectedProposal || null}
        isOpen={!!notifications.selectedProposalId && !!selectedProposal}
        onClose={notifications.clearSelection}
        onApprove={handleApprove}
        onReject={handleReject}
        isLoading={reviewProposal.isPending}
      />
    </nav>
  );
}
