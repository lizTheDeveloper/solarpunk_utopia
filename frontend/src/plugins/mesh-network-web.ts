// Web fallback implementation for mesh networking
// Used in browser/dev mode - provides mock data

import { WebPlugin } from '@capacitor/core';
import type { MeshNetworkPlugin, MeshPeer, MeshMessage, MeshStatus } from './mesh-network';

export class MeshNetworkWeb extends WebPlugin implements MeshNetworkPlugin {
  private mockPeers: MeshPeer[] = [];
  private mockMessages: MeshMessage[] = [];

  async initialize(): Promise<{ initialized: boolean }> {
    console.log('MeshNetwork (web): Initialized with mock implementation');

    // Create some mock peers for testing
    this.mockPeers = [
      {
        id: 'peer-1',
        name: 'Nearby Device 1',
        address: '192.168.49.2',
        isConnected: false,
        lastSeen: new Date().toISOString(),
        signalStrength: 85,
      },
      {
        id: 'peer-2',
        name: 'Nearby Device 2',
        address: '192.168.49.3',
        isConnected: false,
        lastSeen: new Date().toISOString(),
        signalStrength: 72,
      },
    ];

    return { initialized: true };
  }

  async startWiFiDirectDiscovery(): Promise<{ started: boolean }> {
    console.log('MeshNetwork (web): WiFi Direct discovery started (mock)');
    return { started: true };
  }

  async stopWiFiDirectDiscovery(): Promise<{ stopped: boolean }> {
    console.log('MeshNetwork (web): WiFi Direct discovery stopped (mock)');
    return { stopped: true };
  }

  async getDiscoveredPeers(): Promise<{ peers: MeshPeer[] }> {
    return { peers: this.mockPeers };
  }

  async connectToPeer(options: { peerId: string }): Promise<{ connected: boolean }> {
    const peer = this.mockPeers.find(p => p.id === options.peerId);
    if (peer) {
      peer.isConnected = true;
      console.log(`MeshNetwork (web): Connected to peer ${options.peerId} (mock)`);
    }
    return { connected: true };
  }

  async disconnectFromPeer(options: { peerId: string }): Promise<{ disconnected: boolean }> {
    const peer = this.mockPeers.find(p => p.id === options.peerId);
    if (peer) {
      peer.isConnected = false;
      console.log(`MeshNetwork (web): Disconnected from peer ${options.peerId} (mock)`);
    }
    return { disconnected: true };
  }

  async sendData(options: { peerId: string; data: string }): Promise<{ sent: boolean }> {
    console.log(`MeshNetwork (web): Sent data to peer ${options.peerId} (mock)`, options.data);
    return { sent: true };
  }

  async receiveData(): Promise<{ messages: MeshMessage[] }> {
    const messages = [...this.mockMessages];
    this.mockMessages = []; // Clear after reading
    return { messages };
  }

  async startBluetoothDiscovery(): Promise<{ started: boolean }> {
    console.log('MeshNetwork (web): Bluetooth discovery started (mock)');
    return { started: true };
  }

  async stopBluetoothDiscovery(): Promise<{ stopped: boolean }> {
    console.log('MeshNetwork (web): Bluetooth discovery stopped (mock)');
    return { stopped: true };
  }

  async getStatus(): Promise<MeshStatus> {
    const connectedCount = this.mockPeers.filter(p => p.isConnected).length;
    return {
      wifiDirectEnabled: true,
      bluetoothEnabled: true,
      connectedPeers: connectedCount,
      discoveredPeers: this.mockPeers.length,
      pendingMessages: this.mockMessages.length,
    };
  }
}
