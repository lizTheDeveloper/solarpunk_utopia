import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'org.solarpunk.mesh',
  appName: 'Solarpunk Network',
  webDir: 'dist',

  server: {
    // Allow clear text traffic for local mesh networking
    androidScheme: 'https',
    cleartext: true,
  },

  android: {
    // Allow all local network connections
    allowMixedContent: true,

    // Minimum Android version: 8.0 (API 26)
    minWebViewVersion: 55,
  },

  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: "#16a34a",
      androidScaleType: "CENTER_CROP",
      showSpinner: false,
    },

    // SQLite configuration
    CapacitorSQLite: {
      iosDatabaseLocation: 'Library/CapacitorDatabase',
      androidDatabaseLocation: 'default',
    },
  },
};

export default config;
