import { defineConfig, devices } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/user.json');

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:4444',
    trace: 'on-first-retry',
  },

  projects: [
    // Setup project - runs first to create authenticated state
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    // Test projects - use the authenticated state
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: authFile,
      },
      dependencies: ['setup'],
    },
    // No-auth project for basic tests
    {
      name: 'chromium-no-auth',
      testMatch: /test_basic_navigation\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],

  webServer: {
    command: 'cd frontend && npm run dev -- --port 4444',
    url: 'http://localhost:4444',
    reuseExistingServer: !process.env.CI,
  },
});
