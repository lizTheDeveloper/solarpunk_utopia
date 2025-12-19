import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
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
  MessageCircle
} from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/offers', label: 'Offers', icon: Gift },
  { path: '/needs', label: 'Needs', icon: Heart },
  { path: '/exchanges', label: 'Exchanges', icon: ArrowLeftRight },
  { path: '/cells', label: 'Cells', icon: Users },
  { path: '/messages', label: 'Messages', icon: MessageCircle },
  { path: '/discovery', label: 'Search', icon: Search },
  { path: '/knowledge', label: 'Knowledge', icon: BookOpen },
  { path: '/network', label: 'Network', icon: Radio },
  { path: '/agents', label: 'AI Agents', icon: Bot, showBadge: true },
];

export function Navigation() {
  // Poll for pending proposals count every 30 seconds
  // TODO: Replace with actual user ID from auth context
  const userId = 'current-user';

  const { data: pendingData } = useQuery({
    queryKey: ['pendingProposals', userId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8000/agents/proposals/pending/${userId}/count`);
      if (!response.ok) return { pending_count: 0 };
      return response.json();
    },
    refetchInterval: 30000, // Poll every 30 seconds
    retry: false,
  });

  const pendingCount = pendingData?.pending_count || 0;
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-solarpunk-400 to-solarpunk-600 rounded-lg flex items-center justify-center">
              <Gift className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Solarpunk Mesh</h1>
              <p className="text-xs text-gray-600">Gift Economy Network</p>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors relative',
                    isActive
                      ? 'bg-solarpunk-100 text-solarpunk-800'
                      : 'text-gray-700 hover:bg-gray-100'
                  )
                }
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
                {item.showBadge && pendingCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {pendingCount > 9 ? '9+' : pendingCount}
                  </span>
                )}
              </NavLink>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <NavLink
              to="/offers/create"
              className="flex items-center gap-2 bg-solarpunk-600 text-white px-4 py-2 rounded-lg hover:bg-solarpunk-700 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">New Offer</span>
            </NavLink>
            <NavLink
              to="/needs/create"
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">New Need</span>
            </NavLink>
          </div>
        </div>

        {/* Mobile navigation */}
        <div className="md:hidden flex overflow-x-auto pb-3 gap-1 scrollbar-hide">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap relative',
                  isActive
                    ? 'bg-solarpunk-100 text-solarpunk-800'
                    : 'text-gray-700 hover:bg-gray-100'
                )
              }
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
              {item.showBadge && pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {pendingCount > 9 ? '9+' : pendingCount}
                </span>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
