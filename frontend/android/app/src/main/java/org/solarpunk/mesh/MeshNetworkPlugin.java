package org.solarpunk.mesh;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.net.wifi.p2p.WifiP2pConfig;
import android.net.wifi.p2p.WifiP2pDevice;
import android.net.wifi.p2p.WifiP2pDeviceList;
import android.net.wifi.p2p.WifiP2pInfo;
import android.net.wifi.p2p.WifiP2pManager;
import android.os.Build;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;

import java.util.ArrayList;
import java.util.List;

/**
 * Mesh Network Plugin for WiFi Direct peer discovery and data sync
 * Enables offline mesh networking for Solarpunk gift economy
 */
@CapacitorPlugin(
    name = "MeshNetwork",
    permissions = {
        @Permission(
            strings = {
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_WIFI_STATE,
                Manifest.permission.CHANGE_WIFI_STATE,
                Manifest.permission.NEARBY_WIFI_DEVICES
            },
            alias = "mesh"
        )
    }
)
public class MeshNetworkPlugin extends Plugin {

    private WifiP2pManager wifiP2pManager;
    private WifiP2pManager.Channel channel;
    private BroadcastReceiver receiver;
    private IntentFilter intentFilter;
    private List<WifiP2pDevice> peers = new ArrayList<>();
    private boolean isWiFiDirectEnabled = false;

    @Override
    public void load() {
        // Initialize WiFi Direct
        wifiP2pManager = (WifiP2pManager) getContext().getSystemService(Context.WIFI_P2P_SERVICE);
        channel = wifiP2pManager.initialize(getContext(), getContext().getMainLooper(), null);

        // Setup broadcast receiver for WiFi P2P events
        intentFilter = new IntentFilter();
        intentFilter.addAction(WifiP2pManager.WIFI_P2P_STATE_CHANGED_ACTION);
        intentFilter.addAction(WifiP2pManager.WIFI_P2P_PEERS_CHANGED_ACTION);
        intentFilter.addAction(WifiP2pManager.WIFI_P2P_CONNECTION_CHANGED_ACTION);
        intentFilter.addAction(WifiP2pManager.WIFI_P2P_THIS_DEVICE_CHANGED_ACTION);

        receiver = new WiFiDirectBroadcastReceiver(wifiP2pManager, channel, this);
    }

    @PluginMethod
    public void initialize(PluginCall call) {
        // Check permissions
        if (!hasRequiredPermissions()) {
            requestAllPermissions(call, "mesh");
            return;
        }

        JSObject result = new JSObject();
        result.put("initialized", true);
        call.resolve(result);
    }

    @PluginMethod
    public void startWiFiDirectDiscovery(PluginCall call) {
        if (!hasRequiredPermissions()) {
            call.reject("Missing required permissions");
            return;
        }

        // Register broadcast receiver
        getContext().registerReceiver(receiver, intentFilter);

        // Start peer discovery
        if (ActivityCompat.checkSelfPermission(getContext(), Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            call.reject("Location permission not granted");
            return;
        }

        wifiP2pManager.discoverPeers(channel, new WifiP2pManager.ActionListener() {
            @Override
            public void onSuccess() {
                JSObject result = new JSObject();
                result.put("started", true);
                call.resolve(result);
            }

            @Override
            public void onFailure(int reason) {
                call.reject("Discovery failed: " + getFailureReason(reason));
            }
        });
    }

    @PluginMethod
    public void stopWiFiDirectDiscovery(PluginCall call) {
        try {
            getContext().unregisterReceiver(receiver);
        } catch (IllegalArgumentException e) {
            // Receiver not registered, ignore
        }

        JSObject result = new JSObject();
        result.put("stopped", true);
        call.resolve(result);
    }

    @PluginMethod
    public void getDiscoveredPeers(PluginCall call) {
        JSArray peersArray = new JSArray();

        for (WifiP2pDevice device : peers) {
            JSObject peer = new JSObject();
            peer.put("id", device.deviceAddress);
            peer.put("name", device.deviceName);
            peer.put("address", device.deviceAddress);
            peer.put("isConnected", device.status == WifiP2pDevice.CONNECTED);
            peer.put("lastSeen", System.currentTimeMillis());
            peersArray.put(peer);
        }

        JSObject result = new JSObject();
        result.put("peers", peersArray);
        call.resolve(result);
    }

    @PluginMethod
    public void connectToPeer(PluginCall call) {
        String peerId = call.getString("peerId");
        if (peerId == null) {
            call.reject("peerId required");
            return;
        }

        WifiP2pDevice targetDevice = null;
        for (WifiP2pDevice device : peers) {
            if (device.deviceAddress.equals(peerId)) {
                targetDevice = device;
                break;
            }
        }

        if (targetDevice == null) {
            call.reject("Peer not found");
            return;
        }

        WifiP2pConfig config = new WifiP2pConfig();
        config.deviceAddress = targetDevice.deviceAddress;

        if (ActivityCompat.checkSelfPermission(getContext(), Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            call.reject("Location permission not granted");
            return;
        }

        wifiP2pManager.connect(channel, config, new WifiP2pManager.ActionListener() {
            @Override
            public void onSuccess() {
                JSObject result = new JSObject();
                result.put("connected", true);
                call.resolve(result);
            }

            @Override
            public void onFailure(int reason) {
                call.reject("Connection failed: " + getFailureReason(reason));
            }
        });
    }

    @PluginMethod
    public void disconnectFromPeer(PluginCall call) {
        wifiP2pManager.removeGroup(channel, new WifiP2pManager.ActionListener() {
            @Override
            public void onSuccess() {
                JSObject result = new JSObject();
                result.put("disconnected", true);
                call.resolve(result);
            }

            @Override
            public void onFailure(int reason) {
                call.reject("Disconnect failed: " + getFailureReason(reason));
            }
        });
    }

    @PluginMethod
    public void sendData(PluginCall call) {
        // TODO: Implement data transfer using sockets
        // For now, return success
        JSObject result = new JSObject();
        result.put("sent", true);
        call.resolve(result);
    }

    @PluginMethod
    public void receiveData(PluginCall call) {
        // TODO: Implement data reception
        JSObject result = new JSObject();
        result.put("messages", new JSArray());
        call.resolve(result);
    }

    @PluginMethod
    public void startBluetoothDiscovery(PluginCall call) {
        // TODO: Implement Bluetooth fallback
        JSObject result = new JSObject();
        result.put("started", true);
        call.resolve(result);
    }

    @PluginMethod
    public void stopBluetoothDiscovery(PluginCall call) {
        JSObject result = new JSObject();
        result.put("stopped", true);
        call.resolve(result);
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject result = new JSObject();
        result.put("wifiDirectEnabled", isWiFiDirectEnabled);
        result.put("bluetoothEnabled", false); // TODO: Check BT status
        result.put("connectedPeers", countConnectedPeers());
        result.put("discoveredPeers", peers.size());
        result.put("pendingMessages", 0); // TODO: Track pending messages
        call.resolve(result);
    }

    // Update peers list when discovered
    public void updatePeersList(WifiP2pDeviceList peerList) {
        peers.clear();
        peers.addAll(peerList.getDeviceList());
    }

    // Update WiFi Direct enabled status
    public void setWiFiDirectEnabled(boolean enabled) {
        isWiFiDirectEnabled = enabled;
    }

    private int countConnectedPeers() {
        int count = 0;
        for (WifiP2pDevice device : peers) {
            if (device.status == WifiP2pDevice.CONNECTED) {
                count++;
            }
        }
        return count;
    }

    private boolean hasRequiredPermissions() {
        Context context = getContext();
        boolean hasLocation = ContextCompat.checkSelfPermission(context,
                Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;

        // Android 13+ requires NEARBY_WIFI_DEVICES
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            boolean hasNearby = ContextCompat.checkSelfPermission(context,
                    Manifest.permission.NEARBY_WIFI_DEVICES) == PackageManager.PERMISSION_GRANTED;
            return hasLocation && hasNearby;
        }

        return hasLocation;
    }

    private String getFailureReason(int reason) {
        switch (reason) {
            case WifiP2pManager.P2P_UNSUPPORTED:
                return "P2P unsupported";
            case WifiP2pManager.ERROR:
                return "Internal error";
            case WifiP2pManager.BUSY:
                return "Device busy";
            default:
                return "Unknown error";
        }
    }

    @Override
    protected void handleOnDestroy() {
        try {
            getContext().unregisterReceiver(receiver);
        } catch (IllegalArgumentException e) {
            // Receiver not registered, ignore
        }
    }
}
