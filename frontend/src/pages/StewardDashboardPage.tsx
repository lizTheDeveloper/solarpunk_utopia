import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useStewardDashboard, useManagedCells } from '@/hooks/useSteward';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import {
  Users,
  Gift,
  Heart,
  ArrowLeftRight,
  TrendingUp,
  AlertCircle,
  Clock,
  PartyPopper,
  Settings,
  ChevronDown,
} from 'lucide-react';
import { clsx } from 'clsx';

export function StewardDashboardPage() {
  const { cellId } = useParams<{ cellId?: string }>();
  const navigate = useNavigate();
  const [selectedCellId, setSelectedCellId] = useState(cellId || '');

  const { data: managedCells, isLoading: loadingCells } = useManagedCells();
  const {
    data: dashboardData,
    isLoading: loadingDashboard,
    error,
  } = useStewardDashboard(selectedCellId);

  // If no cell selected, select first managed cell
  if (!selectedCellId && managedCells && managedCells.length > 0 && !loadingCells) {
    setSelectedCellId(managedCells[0].id);
  }

  if (loadingCells) {
    return <Loading />;
  }

  if (!managedCells || managedCells.length === 0) {
    return (
      <Card>
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No cells to manage
          </h3>
          <p className="text-gray-600 mb-6">
            You need to be a steward of a cell to access this dashboard
          </p>
          <Button onClick={() => navigate('/cells')}>View All Cells</Button>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <ErrorMessage message="Failed to load dashboard. Please try again later." />
    );
  }

  const selectedCell = managedCells.find((c) => c.id === selectedCellId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Steward Dashboard
            </h1>
            <p className="text-gray-600 mt-1">Community leadership tools</p>
          </div>

          {/* Cell Selector */}
          {managedCells.length > 1 && (
            <div className="relative">
              <select
                value={selectedCellId}
                onChange={(e) => {
                  setSelectedCellId(e.target.value);
                  navigate(`/steward/${e.target.value}`);
                }}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              >
                {managedCells.map((cell) => (
                  <option key={cell.id} value={cell.id}>
                    {cell.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            </div>
          )}
        </div>

        <Button
          variant="secondary"
          onClick={() => navigate(`/cells/${selectedCellId}`)}
        >
          <Settings className="w-4 h-4 mr-2" />
          Cell Settings
        </Button>
      </div>

      {loadingDashboard ? (
        <Loading />
      ) : dashboardData ? (
        <>
          {/* Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              icon={Users}
              label="Members"
              value={dashboardData.metrics.member_count}
              change={dashboardData.metrics.new_members_this_week}
              changeLabel="new this week"
              color="blue"
            />
            <MetricCard
              icon={Gift}
              label="Active Offers"
              value={dashboardData.metrics.active_offers}
              color="green"
            />
            <MetricCard
              icon={ArrowLeftRight}
              label="Matches This Week"
              value={dashboardData.metrics.matches_this_week}
              color="purple"
            />
            <MetricCard
              icon={Heart}
              label="Exchanges This Week"
              value={dashboardData.metrics.exchanges_this_week || 0}
              color="yellow"
            />
          </div>

          {/* Attention Items */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <h2 className="text-xl font-semibold text-gray-900">
                Needs Attention
              </h2>
            </div>
            <div className="space-y-2">
              {dashboardData.attention_items.map((item, idx) => (
                <AttentionItemCard key={idx} item={item} />
              ))}
            </div>
          </Card>

          {/* Recent Activity */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">
                Recent Activity
              </h2>
            </div>
            {dashboardData.recent_activity.length > 0 ? (
              <div className="space-y-2">
                {dashboardData.recent_activity.map((activity, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0"
                  >
                    <span className="text-sm text-gray-600">
                      {activity.message}
                    </span>
                    <span className="text-xs text-gray-500 ml-auto whitespace-nowrap">
                      {formatTimeAgo(new Date(activity.timestamp))}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No recent activity</p>
            )}
          </Card>

          {/* Celebrations */}
          {dashboardData.celebrations.length > 0 && (
            <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
              <div className="flex items-center gap-2 mb-4">
                <PartyPopper className="w-5 h-5 text-yellow-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Celebrations
                </h2>
              </div>
              <div className="space-y-2">
                {dashboardData.celebrations.map((celebration, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-3 py-2 text-gray-900"
                  >
                    <span>{celebration.message}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
}

interface MetricCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  color: 'blue' | 'green' | 'purple' | 'yellow';
}

function MetricCard({
  icon: Icon,
  label,
  value,
  change,
  changeLabel,
  color,
}: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    yellow: 'bg-yellow-100 text-yellow-600',
  };

  return (
    <Card>
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('p-2 rounded-lg', colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {change !== undefined && change > 0 && (
        <p className="text-xs text-green-600 mt-1">
          +{change} {changeLabel}
        </p>
      )}
    </Card>
  );
}

interface AttentionItemCardProps {
  item: {
    type: string;
    priority: string;
    message: string;
  };
}

function AttentionItemCard({ item }: AttentionItemCardProps) {
  const priorityColors = {
    high: 'bg-red-100 border-red-200 text-red-700',
    medium: 'bg-yellow-100 border-yellow-200 text-yellow-700',
    low: 'bg-green-100 border-green-200 text-green-700',
  };

  const priorityIcons = {
    high: '🔴',
    medium: '🟡',
    low: '🟢',
  };

  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-lg border',
        priorityColors[item.priority as keyof typeof priorityColors] ||
          'bg-gray-100 border-gray-200 text-gray-700'
      )}
    >
      <span className="text-lg">
        {priorityIcons[item.priority as keyof typeof priorityIcons] || '⚪'}
      </span>
      <span className="font-medium">{item.message}</span>
    </div>
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
