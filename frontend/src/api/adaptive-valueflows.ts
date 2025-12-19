// Adaptive ValueFlows API
// Automatically switches between remote API (when online) and local SQLite (when offline)

import { valueflowsApi } from './valueflows';
import { localValueflowsApi } from '../storage/local-api';
import { localDb } from '../storage/sqlite';
import { Capacitor } from '@capacitor/core';

// Network status
let isOnline = navigator.onLine;
let useLocalFirst = false;

// Initialize local database when app starts
export async function initializeStorage() {
  try {
    await localDb.initialize();
    console.log('Local storage initialized');

    // On native platforms, always use local-first
    const platform = Capacitor.getPlatform();
    if (platform === 'android' || platform === 'ios') {
      useLocalFirst = true;
      console.log('Running on native platform - using local-first mode');
    }
  } catch (error) {
    console.error('Failed to initialize local storage:', error);
  }
}

// Listen for network status changes
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    isOnline = true;
    console.log('Network: Online');
  });

  window.addEventListener('offline', () => {
    isOnline = false;
    console.log('Network: Offline');
  });
}

// Wrapper that chooses the right API based on network status
function createAdaptiveApi<T extends Record<string, Function>>(
  remoteApi: T,
  localApi: T
): T {
  const adaptiveApi = {} as T;

  for (const key in remoteApi) {
    adaptiveApi[key] = async (...args: any[]) => {
      // Always use local API if we're in local-first mode (native platforms)
      if (useLocalFirst) {
        return await localApi[key](...args);
      }

      // Try remote first, fall back to local
      if (isOnline) {
        try {
          const result = await remoteApi[key](...args);
          // TODO: Update local cache with result
          return result;
        } catch (error) {
          console.warn(`Remote API call failed, falling back to local: ${key}`, error);
          return await localApi[key](...args);
        }
      } else {
        // Offline - use local only
        return await localApi[key](...args);
      }
    };
  }

  return adaptiveApi;
}

// Export the adaptive API that automatically switches
export const adaptiveValueflowsApi = createAdaptiveApi(
  valueflowsApi,
  localValueflowsApi
);

// Export helpers
export function isLocalMode(): boolean {
  return useLocalFirst || !isOnline;
}

export function setLocalFirst(enabled: boolean): void {
  useLocalFirst = enabled;
}

export function getNetworkStatus(): { online: boolean; localFirst: boolean } {
  return {
    online: isOnline,
    localFirst: useLocalFirst,
  };
}
