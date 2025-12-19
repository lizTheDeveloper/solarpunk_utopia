/**
 * Mesh Sync Status Component
 *
 * Shows current mesh network sync status:
 * - Connection status (online/offline)
 * - Number of peers
 * - Last sync time
 * - Bundles sent/received
 */

import { useEffect, useState } from 'react';
import { meshSyncService } from '../services/meshSync';
import MeshNetwork from '../plugins/mesh-network';
import type { MeshStatus } from '../plugins/mesh-network';

export function MeshSyncStatus() {
  const [meshStatus, setMeshStatus] = useState<MeshStatus | null>(null);
  const [syncStats, setSyncStats] = useState(meshSyncService.getStats());

  useEffect(() => {
    // Start mesh sync on mount
    meshSyncService.start().catch(console.error);

    // Update status every 5 seconds
    const interval = setInterval(async () => {
      try {
        const status = await MeshNetwork.getStatus();
        setMeshStatus(status);
        setSyncStats(meshSyncService.getStats());
      } catch (error) {
        console.error('Error getting mesh status:', error);
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      // Don't stop sync service on unmount - let it run in background
    };
  }, []);

  const getStatusColor = () => {
    if (!meshStatus) return 'text-gray-500';
    if (meshStatus.connectedPeers > 0) return 'text-green-500';
    if (meshStatus.discoveredPeers > 0) return 'text-yellow-500';
    return 'text-gray-500';
  };

  const getStatusText = () => {
    if (!meshStatus) return 'Initializing...';
    if (meshStatus.connectedPeers > 0) return 'Syncing';
    if (meshStatus.discoveredPeers > 0) return 'Peers found';
    return 'Offline';
  };

  const formatLastSync = () => {
    if (!syncStats.lastSyncTime) return 'Never';
    const seconds = Math.floor((Date.now() - syncStats.lastSyncTime) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <div className="fixed top-0 left-0 right-0 bg-gray-900 text-white px-4 py-2 flex items-center justify-between text-sm z-50">
      {/* Left: Status indicator */}
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`} />
        <span className="font-medium">{getStatusText()}</span>
      </div>

      {/* Center: Mesh stats */}
      {meshStatus && (
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span>
            Peers: {meshStatus.connectedPeers}/{meshStatus.discoveredPeers}
          </span>
          <span>↑ {syncStats.bundlesSent}</span>
          <span>↓ {syncStats.bundlesReceived}</span>
        </div>
      )}

      {/* Right: Last sync */}
      <div className="text-xs text-gray-400">
        {formatLastSync()}
      </div>
    </div>
  );
}
