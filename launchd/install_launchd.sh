#!/bin/bash
# Install Solarpunk services as launchd agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"

echo "========================================="
echo "Installing Solarpunk LaunchAgents"
echo "========================================="

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCHAGENTS_DIR"

# Copy plist files
echo "Copying plist files to $LAUNCHAGENTS_DIR..."
cp "$SCRIPT_DIR/com.solarpunk.backend.plist" "$LAUNCHAGENTS_DIR/"
cp "$SCRIPT_DIR/com.solarpunk.frontend.plist" "$LAUNCHAGENTS_DIR/"

# Load the services
echo ""
echo "Loading backend service..."
launchctl load "$LAUNCHAGENTS_DIR/com.solarpunk.backend.plist"

echo "Loading frontend service..."
launchctl load "$LAUNCHAGENTS_DIR/com.solarpunk.frontend.plist"

echo ""
echo "========================================="
echo "✓ Installation complete!"
echo "========================================="
echo ""
echo "Services are now running and will start automatically at login."
echo ""
echo "Useful commands:"
echo "  Check status:    launchctl list | grep solarpunk"
echo "  View logs:       tail -f $PROJECT_DIR/logs/launchd-*.log"
echo "  Stop backend:    launchctl stop com.solarpunk.backend"
echo "  Stop frontend:   launchctl stop com.solarpunk.frontend"
echo "  Uninstall:       ./launchd/uninstall_launchd.sh"
echo ""
