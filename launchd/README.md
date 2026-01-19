# Solarpunk LaunchAgents Setup

This directory contains launchd configuration files to automatically start and keep the Solarpunk Mesh Network services running on macOS.

## What is launchd?

launchd is macOS's built-in service management system. It's like systemd on Linux - it can:
- Start services automatically when you log in
- Restart services if they crash
- Manage service logs
- Run services in the background

## Quick Start

### Install and Start Services

```bash
./launchd/install_launchd.sh
```

This will:
1. Copy the plist files to `~/Library/LaunchAgents/`
2. Load both backend and frontend services
3. Start the services immediately
4. Configure them to start automatically at login

### Uninstall Services

```bash
./launchd/uninstall_launchd.sh
```

This will:
1. Stop all running services
2. Remove them from auto-start
3. Delete the plist files from LaunchAgents

## Services Managed

### 1. Backend Services (`com.solarpunk.backend`)
- DTN Bundle System (port 8000)
- ValueFlows Node (port 8001)
- Discovery & Search
- File Chunking
- Bridge Management (port 8002)
- AI Inference Node (port 8005)

### 2. Frontend Service (`com.solarpunk.frontend`)
- Vite dev server (port 4444)

## Useful Commands

### Check Service Status
```bash
# List all solarpunk services
launchctl list | grep solarpunk

# Check specific service
launchctl list com.solarpunk.backend
launchctl list com.solarpunk.frontend
```

### View Logs
```bash
# View all launchd logs
tail -f logs/launchd-*.log

# View specific logs
tail -f logs/launchd-backend.log
tail -f logs/launchd-backend-error.log
tail -f logs/launchd-frontend.log
tail -f logs/launchd-frontend-error.log
```

### Manual Control

```bash
# Stop a service (will restart automatically due to KeepAlive)
launchctl stop com.solarpunk.backend
launchctl stop com.solarpunk.frontend

# Start a service
launchctl start com.solarpunk.backend
launchctl start com.solarpunk.frontend

# Restart a service (unload + load)
launchctl unload ~/Library/LaunchAgents/com.solarpunk.backend.plist
launchctl load ~/Library/LaunchAgents/com.solarpunk.backend.plist
```

### Temporarily Disable Auto-Start

```bash
# Unload without removing files
launchctl unload ~/Library/LaunchAgents/com.solarpunk.backend.plist
launchctl unload ~/Library/LaunchAgents/com.solarpunk.frontend.plist

# Re-enable
launchctl load ~/Library/LaunchAgents/com.solarpunk.backend.plist
launchctl load ~/Library/LaunchAgents/com.solarpunk.frontend.plist
```

## How It Works

### Auto-Restart on Crash
The `KeepAlive` setting ensures services automatically restart if they crash:
```xml
<key>KeepAlive</key>
<dict>
    <key>SuccessfulExit</key>
    <false/>
</dict>
```

This means:
- If a service exits with an error, it will restart immediately
- If a service exits cleanly (exit 0), it will NOT restart
- Throttling prevents rapid restart loops (10 second delay)

### Startup Behavior
The `RunAtLoad` setting starts services when you log in:
```xml
<key>RunAtLoad</key>
<true/>
```

### Environment Variables
Both services have proper PATH and working directory configured to find Python, npm, and node.

## Troubleshooting

### Services Won't Start

1. Check the error logs:
   ```bash
   cat logs/launchd-backend-error.log
   cat logs/launchd-frontend-error.log
   ```

2. Verify the scripts work manually:
   ```bash
   ./run_all_services.sh
   cd frontend && npm run dev -- --port 4444
   ```

3. Check launchd status:
   ```bash
   launchctl list | grep solarpunk
   ```

### Services Crash Loop

If you see rapid restarts in the logs:

1. Unload the problematic service:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.solarpunk.backend.plist
   ```

2. Fix the underlying issue

3. Reload:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.solarpunk.backend.plist
   ```

### Port Already in Use

If you get "Address already in use" errors:

1. Check what's using the port:
   ```bash
   lsof -ti:8000,8001,8002,4444
   ```

2. Stop existing processes:
   ```bash
   ./stop_all_services.sh
   ```

3. Restart the launchd services:
   ```bash
   launchctl stop com.solarpunk.backend
   launchctl stop com.solarpunk.frontend
   ```

## Files

- `com.solarpunk.backend.plist` - Backend services configuration
- `com.solarpunk.frontend.plist` - Frontend service configuration
- `install_launchd.sh` - Installation script
- `uninstall_launchd.sh` - Uninstallation script
- `README.md` - This file

## Notes

- These are **user-level** LaunchAgents (run as your user, not root)
- Services run in the background (ProcessType: Background)
- Logs are written to the project's `logs/` directory
- Services will NOT start if you're not logged in
- For system-wide services (start at boot), use LaunchDaemons instead

## See Also

- [launchd man page](https://ss64.com/osx/launchd.html)
- [launchctl man page](https://ss64.com/osx/launchctl.html)
- [LaunchAgent vs LaunchDaemon](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
