import { useNetworkStatus, useBridgeNodes, useCurrentIsland } from '@/hooks/useBridge';
import { useBundles, useBundleStats } from '@/hooks/useBundles';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Card } from '@/components/Card';
import { NetworkStatus } from '@/components/NetworkStatus';
import { BundleStatus } from '@/components/BundleStatus';
import { PeerList } from '@/components/PeerList';
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
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Network Status</h1>
          <p className="text-gray-600 mt-1">
            Monitor network health, bridge nodes, and bundle propagation
          </p>
        </div>
        <Card className="bg-blue-50 border-blue-200">
          <div className="flex items-start gap-3">
            <Radio className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">Development Mode</h3>
              <p className="text-sm text-blue-800 mb-3">
                The mesh network features require actual DTN/BATMAN-adv hardware to show live data.
                You're currently running in development mode without mesh network connectivity.
              </p>
              <div className="space-y-2 text-sm text-blue-700">
                <p><strong>To enable full mesh networking:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Deploy to Android devices with WiFi Direct</li>
                  <li>Configure BATMAN-adv mesh protocol</li>
                  <li>Run bridge nodes to connect islands</li>
                </ul>
                <p className="mt-3">
                  <strong>Currently available:</strong> ValueFlows gift economy features, agent proposals, community management
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <h3 className="font-semibold text-gray-900 mb-3">Mock Network Data</h3>
          <p className="text-sm text-gray-600 mb-4">
            Here's what the network page will show when connected to actual mesh hardware:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-1">Mode</p>
              <p className="text-xl font-bold text-gray-400">A / C</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-1">Connected Peers</p>
              <p className="text-xl font-bold text-gray-400">0-50+</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-1">Active Bridges</p>
              <p className="text-xl font-bold text-gray-400">0-10+</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-1">Bundles Pending</p>
              <p className="text-xl font-bold text-gray-400">0-100+</p>
            </div>
          </div>
        </Card>
      </div>
    );
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

      {/* Current Island Summary */}
      {islandLoading ? (
        <Loading text="Loading island information..." />
      ) : currentIsland ? (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Map className="w-5 h-5 text-solarpunk-600" />
            <h2 className="text-xl font-semibold text-gray-900">Current Island</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Island ID</p>
              <p className="font-mono text-gray-900 text-sm">{currentIsland.island_id.slice(0, 16)}...</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Connected Nodes</p>
              <p className="text-2xl font-bold text-solarpunk-700">{currentIsland.node_count}</p>
            </div>
          </div>
        </Card>
      ) : null}

      {/* Detailed Peer List */}
      {islandLoading ? null : currentIsland ? (
        <PeerList
          connectedNodes={currentIsland.connected_nodes}
          accessPoints={currentIsland.access_points}
          showAccessPoints={true}
        />
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
