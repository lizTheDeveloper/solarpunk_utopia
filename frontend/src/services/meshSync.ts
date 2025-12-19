/**
 * Mesh Sync Service
 *
 * Handles automatic DTN bundle synchronization over WiFi Direct mesh network.
 * Works offline - no internet required.
 */

import MeshNetwork from '../plugins/mesh-network';
import type { MeshPeer } from '../plugins/mesh-network';
import { dtnApi } from '../api/dtn';

interface SyncStats {
  lastSyncTime: number | null;
  bundlesSent: number;
  bundlesReceived: number;
  activePeers: number;
}

class MeshSyncService {
  private isRunning = false;
  private syncInterval: NodeJS.Timeout | null = null;
  private stats: SyncStats = {
    lastSyncTime: null,
    bundlesSent: 0,
    bundlesReceived: 0,
    activePeers: 0,
  };

  /**
   * Start mesh sync service
   * - Starts WiFi Direct discovery
   * - Polls for new peers
   * - Syncs bundles automatically
   */
  async start() {
    if (this.isRunning) {
      console.log('Mesh sync already running');
      return;
    }

    console.log('Starting mesh sync service...');

    try {
      // Initialize mesh network
      await MeshNetwork.initialize();

      // Start WiFi Direct discovery
      await MeshNetwork.startWiFiDirectDiscovery();

      this.isRunning = true;

      // Poll for peers and sync every 10 seconds
      this.syncInterval = setInterval(() => {
        this.syncWithPeers();
      }, 10000);

      console.log('Mesh sync service started');
    } catch (error) {
      console.error('Failed to start mesh sync:', error);
      throw error;
    }
  }

  /**
   * Stop mesh sync service
   */
  async stop() {
    if (!this.isRunning) {
      return;
    }

    console.log('Stopping mesh sync service...');

    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    try {
      await MeshNetwork.stopWiFiDirectDiscovery();
    } catch (error) {
      console.error('Error stopping discovery:', error);
    }

    this.isRunning = false;
    console.log('Mesh sync service stopped');
  }

  /**
   * Sync with all discovered peers
   */
  private async syncWithPeers() {
    try {
      // Get discovered peers
      const { peers } = await MeshNetwork.getDiscoveredPeers();
      this.stats.activePeers = peers.length;

      if (peers.length === 0) {
        return;
      }

      console.log(`Found ${peers.length} peers, syncing...`);

      // Sync with each peer
      for (const peer of peers) {
        await this.syncWithPeer(peer);
      }

      this.stats.lastSyncTime = Date.now();
    } catch (error) {
      console.error('Error syncing with peers:', error);
    }
  }

  /**
   * Sync DTN bundles with a specific peer
   */
  private async syncWithPeer(peer: MeshPeer) {
    try {
      // Connect to peer if not already connected
      if (!peer.isConnected) {
        await MeshNetwork.connectToPeer({ peerId: peer.id });
      }

      // Step 1: Get our bundles ready to forward
      const ourBundles = await dtnApi.getBundlesForForwarding();

      // Step 2: Send our bundles to peer
      if (ourBundles.length > 0) {
        const bundleData = JSON.stringify(ourBundles);
        await MeshNetwork.sendData({
          peerId: peer.id,
          data: bundleData,
        });
        this.stats.bundlesSent += ourBundles.length;
        console.log(`Sent ${ourBundles.length} bundles to ${peer.name}`);
      }

      // Step 3: Receive bundles from peer
      const { messages } = await MeshNetwork.receiveData();

      for (const message of messages) {
        try {
          const bundles = JSON.parse(message.data);
          if (Array.isArray(bundles)) {
            // Store received bundles locally
            await dtnApi.receiveBundles(bundles);
            this.stats.bundlesReceived += bundles.length;
            console.log(`Received ${bundles.length} bundles from peer`);
          }
        } catch (error) {
          console.error('Error processing received bundles:', error);
        }
      }
    } catch (error) {
      console.error(`Error syncing with peer ${peer.id}:`, error);
    }
  }

  /**
   * Get sync statistics
   */
  getStats(): SyncStats {
    return { ...this.stats };
  }

  /**
   * Get sync status
   */
  isActive(): boolean {
    return this.isRunning;
  }

  /**
   * Force immediate sync
   */
  async forceSync() {
    console.log('Forcing immediate sync...');
    await this.syncWithPeers();
  }
}

// Export singleton instance
export const meshSyncService = new MeshSyncService();
