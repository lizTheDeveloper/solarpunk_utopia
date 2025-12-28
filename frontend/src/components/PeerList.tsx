import { Users, Radio, Wifi, WifiOff, Activity } from 'lucide-react';
import { Card } from './Card';
import { formatTimeAgo } from '@/utils/formatters';
import type { AccessPoint } from '@/types/network';

interface PeerListProps {
  connectedNodes: string[];
  accessPoints: AccessPoint[];
  showAccessPoints?: boolean;
}

function getSignalStrength(rssi: number): { level: 'excellent' | 'good' | 'fair' | 'weak'; color: string; bars: number } {
  if (rssi >= -50) return { level: 'excellent', color: 'text-green-600', bars: 4 };
  if (rssi >= -60) return { level: 'good', color: 'text-blue-600', bars: 3 };
  if (rssi >= -70) return { level: 'fair', color: 'text-yellow-600', bars: 2 };
  return { level: 'weak', color: 'text-red-600', bars: 1 };
}

function SignalBars({ rssi }: { rssi: number }) {
  const { bars, color } = getSignalStrength(rssi);

  return (
    <div className="flex items-end gap-0.5 h-4">
      {[1, 2, 3, 4].map((bar) => (
        <div
          key={bar}
          className={`w-1 rounded-sm transition-colors ${
            bar <= bars ? color.replace('text-', 'bg-') : 'bg-gray-300'
          }`}
          style={{ height: `${bar * 25}%` }}
        />
      ))}
    </div>
  );
}

export function PeerList({ connectedNodes, accessPoints, showAccessPoints = true }: PeerListProps) {
  const hasNodes = connectedNodes.length > 0;
  const hasAPs = accessPoints.length > 0;

  if (!hasNodes && !hasAPs) {
    return (
      <Card>
        <div className="text-center py-8">
          <Users className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 mb-2">No connected peers</p>
          <p className="text-sm text-gray-500">
            Scanning for nearby nodes...
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Connected Nodes */}
      {hasNodes && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-solarpunk-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Connected Peers ({connectedNodes.length})
            </h2>
            <div className="ml-auto flex items-center gap-2 text-green-600">
              <Activity className="w-4 h-4 animate-pulse" />
              <span className="text-sm font-medium">Live</span>
            </div>
          </div>

          <div className="space-y-2">
            {connectedNodes.map((nodeId, index) => {
              // Extract a friendly name from node ID (first 8 chars + index)
              const shortId = nodeId.slice(0, 8);
              const displayName = `node-${shortId}`;

              return (
                <div
                  key={nodeId}
                  className="flex items-center justify-between p-3 bg-solarpunk-50 border border-solarpunk-200 rounded-lg hover:bg-solarpunk-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <div>
                      <p className="font-medium text-gray-900">{displayName}</p>
                      <p className="text-xs text-gray-500 font-mono">{nodeId}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Radio className="w-4 h-4" />
                      <span>Peer {index + 1}</span>
                    </div>
                    <span className="text-green-600 font-medium">Online</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              <span className="font-medium">{connectedNodes.length}</span> peer{connectedNodes.length !== 1 ? 's' : ''} connected via mesh network
            </p>
          </div>
        </Card>
      )}

      {/* Access Points */}
      {showAccessPoints && hasAPs && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Wifi className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Access Points ({accessPoints.length})
            </h2>
          </div>

          <div className="space-y-2">
            {accessPoints.map((ap) => {
              const { level, color } = getSignalStrength(ap.signal_strength);
              const timeAgo = formatTimeAgo(ap.last_seen);

              return (
                <div
                  key={ap.bssid}
                  className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg"
                >
                  <div className="flex items-center gap-3 flex-1">
                    {ap.signal_strength ? (
                      <Wifi className={`w-5 h-5 ${color}`} />
                    ) : (
                      <WifiOff className="w-5 h-5 text-gray-400" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{ap.ssid}</p>
                      <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                        <span className="font-mono">{ap.bssid.slice(0, 17)}</span>
                        <span>•</span>
                        <span>Ch {ap.channel}</span>
                        <span>•</span>
                        <span>{ap.security}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-right">
                      <SignalBars rssi={ap.signal_strength} />
                      <p className={`text-xs mt-1 ${color}`}>
                        {ap.signal_strength} dBm
                      </p>
                    </div>
                    <div className="text-xs text-gray-500 min-w-[60px] text-right">
                      {timeAgo}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              <span className="font-medium">{accessPoints.length}</span> WiFi access point{accessPoints.length !== 1 ? 's' : ''} detected
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
