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
  Plus
} from 'lucide-react';
import { clsx } from 'clsx';

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/offers', label: 'Offers', icon: Gift },
  { path: '/needs', label: 'Needs', icon: Heart },
  { path: '/exchanges', label: 'Exchanges', icon: ArrowLeftRight },
  { path: '/discovery', label: 'Search', icon: Search },
  { path: '/knowledge', label: 'Knowledge', icon: BookOpen },
  { path: '/network', label: 'Network', icon: Radio },
  { path: '/agents', label: 'AI Agents', icon: Bot },
];

export function Navigation() {
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
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-solarpunk-100 text-solarpunk-800'
                      : 'text-gray-700 hover:bg-gray-100'
                  )
                }
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
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
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap',
                  isActive
                    ? 'bg-solarpunk-100 text-solarpunk-800'
                    : 'text-gray-700 hover:bg-gray-100'
                )
              }
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
