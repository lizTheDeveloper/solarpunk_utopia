import { useNetworkStatus, useBridgeNodes, useCurrentIsland } from '@/hooks/useBridge';
import { useBundles, useBundleStats } from '@/hooks/useBundles';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Card } from '@/components/Card';
import { NetworkStatus } from '@/components/NetworkStatus';
import { BundleStatus } from '@/components/BundleStatus';
import { Radio, Package, Map } from 'lucide-react';
import { formatTimeAgo } from '@/utils/formatters';

export function NetworkPage() {
  const { data: networkStatus, isLoading: statusLoading, error: statusError } = useNetworkStatus();
  const { data: bridgeNodes, isLoading: nodesLoading } = useBridgeNodes();
  const { data: currentIsland, isLoading: islandLoading } = useCurrentIsland();
  const { data: bundleStats } = useBundleStats();
  const { data: bundles } = useBundles();

  const recentBundles = bundles?.slice(0, 5) || [];
  const activeBridges = bridgeNodes?.filter(b => b.status === 'active') || [];

  if (statusError) {
    return <ErrorMessage message="Failed to load network status. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Network Status</h1>
        <p className="text-gray-600 mt-1">
          Monitor network health, bridge nodes, and bundle propagation
        </p>
      </div>

      {/* Main Network Status */}
      {statusLoading ? (
        <Loading text="Loading network status..." />
      ) : networkStatus ? (
        <NetworkStatus status={networkStatus} />
      ) : null}

      {/* Bundle Statistics */}
      {bundleStats && (
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Bundle Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Delivered</p>
              <p className="text-2xl font-bold text-green-800">{bundleStats.total_delivered}</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Pending</p>
              <p className="text-2xl font-bold text-yellow-800">{bundleStats.total_pending}</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Avg Hops</p>
              <p className="text-2xl font-bold text-blue-800">{bundleStats.average_hops.toFixed(1)}</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Avg Delivery</p>
              <p className="text-2xl font-bold text-purple-800">
                {bundleStats.average_delivery_time_seconds.toFixed(0)}s
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Current Island */}
      {islandLoading ? (
        <Loading text="Loading island information..." />
      ) : currentIsland ? (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Map className="w-5 h-5 text-solarpunk-600" />
            <h2 className="text-xl font-semibold text-gray-900">Current Island</h2>
          </div>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600">Island ID</p>
              <p className="font-mono text-gray-900">{currentIsland.island_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">Connected Nodes</p>
              <p className="text-2xl font-bold text-gray-900">{currentIsland.node_count}</p>
            </div>
            {currentIsland.access_points.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Access Points</p>
                <div className="space-y-2">
                  {currentIsland.access_points.slice(0, 3).map((ap, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 rounded p-3 text-sm"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{ap.ssid}</span>
                        <span className="text-gray-600">Signal: {ap.signal_strength}dBm</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Channel {ap.channel} • {ap.security}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      ) : null}

      {/* Bridge Nodes */}
      {nodesLoading ? (
        <Loading text="Loading bridge nodes..." />
      ) : activeBridges.length > 0 ? (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Radio className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Active Bridge Nodes</h2>
          </div>
          <div className="space-y-3">
            {activeBridges.map((bridge) => (
              <div
                key={bridge.id}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-mono text-sm text-gray-900">
                      {bridge.node_id.slice(0, 16)}...
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Last seen {formatTimeAgo(bridge.last_seen)}
                    </p>
                  </div>
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    Mode {bridge.mode}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Bundles Carried</p>
                    <p className="font-bold text-gray-900">{bridge.bundles_carried}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Delivered</p>
                    <p className="font-bold text-gray-900">{bridge.bundles_delivered}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Islands Visited</p>
                    <p className="font-bold text-gray-900">{bridge.islands_visited.length}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : (
        <Card>
          <div className="text-center py-8">
            <Radio className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No active bridge nodes at the moment</p>
          </div>
        </Card>
      )}

      {/* Recent Bundles */}
      {recentBundles.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-5 h-5 text-orange-600" />
            <h2 className="text-xl font-semibold text-gray-900">Recent Bundles</h2>
          </div>
          <div className="space-y-3">
            {recentBundles.map((bundle) => (
              <BundleStatus key={bundle.id} bundle={bundle} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
