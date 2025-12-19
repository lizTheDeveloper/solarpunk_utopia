/**
 * Security Manager - Auto-lock and security features (GAP-108)
 *
 * Features:
 * - Auto-lock after 2 minutes of inactivity
 * - PIN verification for sensitive actions
 * - Activity tracking
 */

const INACTIVITY_TIMEOUT_MS = 120_000; // 2 minutes
const ACTIVITY_CHECK_INTERVAL_MS = 10_000; // Check every 10 seconds

// Actions that require PIN verification
const SENSITIVE_ACTIONS = [
  "send_message",
  "create_offer",
  "create_need",
  "view_sanctuary",
  "vouch_for",
  "create_sanctuary",
  "broadcast_message",
  "revoke_vouch",
];

export class SecurityManager {
  private lastActivity: number;
  private locked: boolean;
  private lockTimeout: NodeJS.Timeout | null;
  private activityListeners: (() => void)[];

  constructor() {
    this.lastActivity = Date.now();
    this.locked = false;
    this.lockTimeout = null;
    this.activityListeners = [];
    this.initialize();
  }

  private initialize() {
    // Start inactivity timer
    this.startInactivityTimer();

    // Set up activity listeners
    this.setupEventListeners();
  }

  private startInactivityTimer() {
    this.lockTimeout = setInterval(() => {
      const inactiveDuration = Date.now() - this.lastActivity;

      if (inactiveDuration > INACTIVITY_TIMEOUT_MS && !this.locked) {
        this.lock();
      }
    }, ACTIVITY_CHECK_INTERVAL_MS);
  }

  private setupEventListeners() {
    // Track user activity
    const events = ["click", "keypress", "scroll", "touchstart", "mousemove"];

    events.forEach((event) => {
      document.addEventListener(event, () => this.recordActivity(), {
        passive: true,
      });
    });
  }

  /**
   * Record user activity to prevent auto-lock
   */
  recordActivity() {
    this.lastActivity = Date.now();
  }

  /**
   * Lock the app due to inactivity
   */
  async lock() {
    if (this.locked) return;

    this.locked = true;

    // Notify listeners
    this.activityListeners.forEach((listener) => listener());

    // Navigate to lock screen
    // In a real app, this would use the router
    console.log("[SecurityManager] App locked due to inactivity");

    // Emit custom event for UI components to listen to
    window.dispatchEvent(new CustomEvent("app-locked"));
  }

  /**
   * Unlock the app with PIN verification
   */
  async unlock(pin: string): Promise<boolean> {
    try {
      // Verify PIN with backend
      const response = await fetch("/api/auth/verify-pin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin }),
      });

      if (response.ok) {
        this.locked = false;
        this.recordActivity();
        window.dispatchEvent(new CustomEvent("app-unlocked"));
        return true;
      }

      return false;
    } catch (error) {
      console.error("[SecurityManager] PIN verification failed:", error);
      return false;
    }
  }

  /**
   * Check if action requires PIN verification and prompt if needed
   */
  async checkSensitiveAction(action: string): Promise<boolean> {
    if (!SENSITIVE_ACTIONS.includes(action)) {
      return true; // Action doesn't require verification
    }

    if (!this.locked) {
      return true; // App is unlocked, action allowed
    }

    // App is locked, require PIN
    return await this.promptForPIN();
  }

  /**
   * Prompt user for PIN entry
   */
  private async promptForPIN(): Promise<boolean> {
    // Emit event for UI to show PIN dialog
    return new Promise((resolve) => {
      const handler = (event: CustomEvent) => {
        window.removeEventListener("pin-verified", handler as EventListener);
        resolve(event.detail.verified);
      };

      window.addEventListener("pin-verified", handler as EventListener);
      window.dispatchEvent(new CustomEvent("pin-required"));
    });
  }

  /**
   * Check if app is currently locked
   */
  isLocked(): boolean {
    return this.locked;
  }

  /**
   * Get time until auto-lock (in milliseconds)
   */
  getTimeUntilLock(): number {
    const inactiveDuration = Date.now() - this.lastActivity;
    const remaining = INACTIVITY_TIMEOUT_MS - inactiveDuration;
    return Math.max(0, remaining);
  }

  /**
   * Add listener for lock state changes
   */
  onLockStateChange(callback: () => void) {
    this.activityListeners.push(callback);
  }

  /**
   * Clean up resources
   */
  destroy() {
    if (this.lockTimeout) {
      clearInterval(this.lockTimeout);
      this.lockTimeout = null;
    }
    this.activityListeners = [];
  }
}

// Export singleton instance
export const securityManager = new SecurityManager();
