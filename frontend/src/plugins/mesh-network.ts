// Mesh Network Plugin for WiFi Direct and Bluetooth
// Provides peer discovery and data sync over local mesh

import { registerPlugin } from '@capacitor/core';

export interface MeshNetworkPlugin {
  /**
   * Initialize mesh networking
   */
  initialize(): Promise<{ initialized: boolean }>;

  /**
   * Start WiFi Direct discovery
   */
  startWiFiDirectDiscovery(): Promise<{ started: boolean }>;

  /**
   * Stop WiFi Direct discovery
   */
  stopWiFiDirectDiscovery(): Promise<{ stopped: boolean }>;

  /**
   * Get discovered peers
   */
  getDiscoveredPeers(): Promise<{ peers: MeshPeer[] }>;

  /**
   * Connect to a peer
   */
  connectToPeer(options: { peerId: string }): Promise<{ connected: boolean }>;

  /**
   * Disconnect from a peer
   */
  disconnectFromPeer(options: { peerId: string }): Promise<{ disconnected: boolean }>;

  /**
   * Send data to a peer (DTN bundle)
   */
  sendData(options: { peerId: string; data: string }): Promise<{ sent: boolean }>;

  /**
   * Receive pending data from peers
   */
  receiveData(): Promise<{ messages: MeshMessage[] }>;

  /**
   * Start Bluetooth discovery (fallback)
   */
  startBluetoothDiscovery(): Promise<{ started: boolean }>;

  /**
   * Stop Bluetooth discovery
   */
  stopBluetoothDiscovery(): Promise<{ stopped: boolean }>;

  /**
   * Get mesh network status
   */
  getStatus(): Promise<MeshStatus>;
}

export interface MeshPeer {
  id: string;
  name: string;
  address: string;
  isConnected: boolean;
  lastSeen: string;
  signalStrength?: number;
}

export interface MeshMessage {
  from: string;
  data: string;
  receivedAt: string;
  bundleId?: string;
}

export interface MeshStatus {
  wifiDirectEnabled: boolean;
  bluetoothEnabled: boolean;
  connectedPeers: number;
  discoveredPeers: number;
  pendingMessages: number;
}

const MeshNetwork = registerPlugin<MeshNetworkPlugin>('MeshNetwork', {
  web: () => import('./mesh-network-web').then(m => new m.MeshNetworkWeb()),
});

export default MeshNetwork;
