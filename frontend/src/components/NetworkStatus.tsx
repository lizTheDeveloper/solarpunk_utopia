import { NetworkStatus as NetworkStatusType } from '@/types/network';
import { Card } from './Card';
import { Wifi, WifiOff, Radio, Package, Map } from 'lucide-react';
import { formatTimeAgo } from '@/utils/formatters';

interface NetworkStatusProps {
  status: NetworkStatusType;
}

export function NetworkStatus({ status }: NetworkStatusProps) {
  return (
    <Card>
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg text-gray-900">Network Status</h3>
          <div className="flex items-center gap-2">
            {status.connected_to_internet ? (
              <Wifi className="w-5 h-5 text-green-600" />
            ) : (
              <WifiOff className="w-5 h-5 text-gray-400" />
            )}
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              status.connected_to_internet
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {status.connected_to_internet ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-solarpunk-50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Radio className="w-4 h-4 text-solarpunk-700" />
              <p className="text-sm font-medium text-gray-700">Mode</p>
            </div>
            <p className="text-2xl font-bold text-solarpunk-800">{status.mode}</p>
            <p className="text-xs text-gray-600 mt-1">
              {status.mode === 'A' ? 'Anchored' : 'Courier'}
            </p>
          </div>

          <div className="bg-blue-50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Map className="w-4 h-4 text-blue-700" />
              <p className="text-sm font-medium text-gray-700">Island</p>
            </div>
            <p className="text-lg font-bold text-blue-800 truncate" title={status.current_island_id}>
              {status.current_island_id.slice(0, 8)}...
            </p>
          </div>

          <div className="bg-purple-50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Radio className="w-4 h-4 text-purple-700" />
              <p className="text-sm font-medium text-gray-700">Active Bridges</p>
            </div>
            <p className="text-2xl font-bold text-purple-800">{status.active_bridges}</p>
          </div>

          <div className="bg-orange-50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Package className="w-4 h-4 text-orange-700" />
              <p className="text-sm font-medium text-gray-700">Outbox</p>
            </div>
            <p className="text-2xl font-bold text-orange-800">{status.bundles_in_outbox}</p>
            <p className="text-xs text-gray-600 mt-1">bundles pending</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Node ID</p>
            <p className="font-mono text-gray-900 truncate" title={status.node_id}>
              {status.node_id.slice(0, 16)}...
            </p>
          </div>
          <div>
            <p className="text-gray-600">Known Islands</p>
            <p className="font-medium text-gray-900">{status.known_islands}</p>
          </div>
        </div>

        {status.last_bridge_contact && (
          <div className="pt-3 border-t text-xs text-gray-500">
            Last bridge contact {formatTimeAgo(status.last_bridge_contact)}
          </div>
        )}
      </div>
    </Card>
  );
}
