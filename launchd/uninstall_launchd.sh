#!/bin/bash
# Uninstall Solarpunk launchd agents

set -e

LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"

echo "========================================="
echo "Uninstalling Solarpunk LaunchAgents"
echo "========================================="

# Unload the services
echo "Unloading backend service..."
launchctl unload "$LAUNCHAGENTS_DIR/com.solarpunk.backend.plist" 2>/dev/null || echo "Backend service not loaded"

echo "Unloading frontend service..."
launchctl unload "$LAUNCHAGENTS_DIR/com.solarpunk.frontend.plist" 2>/dev/null || echo "Frontend service not loaded"

# Remove plist files
echo ""
echo "Removing plist files..."
rm -f "$LAUNCHAGENTS_DIR/com.solarpunk.backend.plist"
rm -f "$LAUNCHAGENTS_DIR/com.solarpunk.frontend.plist"

echo ""
echo "========================================="
echo "✓ Uninstallation complete!"
echo "========================================="
echo ""
echo "Services have been stopped and removed from auto-start."
echo "You can manually start services using ./run_all_services.sh"
echo ""
