#!/bin/bash
# Database restore script (GAP-58)
#
# This script:
# - Restores a backup to the database
# - Verifies integrity before and after
# - Creates a safety backup of current database
# - Optionally stops/starts the application
#
# Usage:
#   ./scripts/restore.sh <backup_file> [database_path]
#
# Environment variables:
#   DATABASE_PATH - Path to SQLite database (default: ./dtn_bundles.db)
#   RESTORE_STOP_SERVICE - Whether to stop service before restore (default: false)
#   SERVICE_NAME - Systemd service name (default: dtn-bundle-system)

set -euo pipefail

# Configuration
BACKUP_FILE="${1:-}"
DATABASE_PATH="${2:-${DATABASE_PATH:-./dtn_bundles.db}}"
STOP_SERVICE="${RESTORE_STOP_SERVICE:-false}"
SERVICE_NAME="${SERVICE_NAME:-dtn-bundle-system}"
SAFETY_BACKUP_DIR="./backups/pre-restore"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
if [ -z "$BACKUP_FILE" ]; then
    log_error "Usage: $0 <backup_file> [database_path]"
    return
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    return
fi

log_info "Starting restore process..."
log_info "Backup file: $BACKUP_FILE"
log_info "Target database: $DATABASE_PATH"

# Check if backup is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log_info "Backup is compressed, will decompress during restore"
    COMPRESSED=true
else
    COMPRESSED=false
fi

# Create temporary file for decompressed backup
TEMP_BACKUP=$(mktemp)
trap "rm -f $TEMP_BACKUP" EXIT

# Decompress backup if needed
if [ "$COMPRESSED" = true ]; then
    log_info "Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > "$TEMP_BACKUP"
else
    cp "$BACKUP_FILE" "$TEMP_BACKUP"
fi

# Verify backup integrity
log_info "Verifying backup integrity..."
INTEGRITY_CHECK=$(sqlite3 "$TEMP_BACKUP" "PRAGMA integrity_check")

if [ "$INTEGRITY_CHECK" != "ok" ]; then
    log_error "Backup integrity check failed: $INTEGRITY_CHECK"
    log_error "Cannot restore corrupted backup"
    return
fi

log_info "Backup integrity verified"

# Create safety backup of current database
if [ -f "$DATABASE_PATH" ]; then
    mkdir -p "$SAFETY_BACKUP_DIR"
    SAFETY_BACKUP_FILE="${SAFETY_BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).db"

    log_info "Creating safety backup of current database..."
    log_info "Safety backup: $SAFETY_BACKUP_FILE"

    sqlite3 "$DATABASE_PATH" ".backup $SAFETY_BACKUP_FILE"

    if [ $? -ne 0 ]; then
        log_error "Failed to create safety backup"
        return
    fi

    log_info "Safety backup created successfully"
else
    log_warn "No existing database found, skipping safety backup"
fi

# Stop service if requested
SERVICE_STOPPED=false
if [ "$STOP_SERVICE" = "true" ]; then
    if command -v systemctl &> /dev/null; then
        log_info "Stopping service: $SERVICE_NAME"
        sudo systemctl stop "$SERVICE_NAME" || {
            log_warn "Failed to stop service (may not be running)"
        }
        SERVICE_STOPPED=true
        # Give service time to shut down gracefully
        sleep 2
    else
        log_warn "systemctl not available, cannot stop service"
        log_warn "Make sure to stop the application manually before restore!"
    fi
fi

# Restore database
log_info "Restoring database from backup..."
cp "$TEMP_BACKUP" "$DATABASE_PATH"

if [ $? -ne 0 ]; then
    log_error "Restore failed"

    # Attempt to restore safety backup
    if [ -f "$SAFETY_BACKUP_FILE" ]; then
        log_info "Attempting to restore safety backup..."
        cp "$SAFETY_BACKUP_FILE" "$DATABASE_PATH"
    fi

    return
fi

# Verify restored database
log_info "Verifying restored database..."
RESTORE_INTEGRITY=$(sqlite3 "$DATABASE_PATH" "PRAGMA integrity_check")

if [ "$RESTORE_INTEGRITY" != "ok" ]; then
    log_error "Restored database integrity check failed: $RESTORE_INTEGRITY"

    # Attempt to restore safety backup
    if [ -f "$SAFETY_BACKUP_FILE" ]; then
        log_info "Attempting to restore safety backup..."
        cp "$SAFETY_BACKUP_FILE" "$DATABASE_PATH"
    fi

    return
fi

log_info "Restored database integrity verified"

# Start service if we stopped it
if [ "$SERVICE_STOPPED" = "true" ]; then
    log_info "Starting service: $SERVICE_NAME"
    sudo systemctl start "$SERVICE_NAME"

    # Wait a moment and check status
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Service started successfully"
    else
        log_error "Service failed to start"
        log_error "Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
        return
    fi
fi

# Get database info
DB_SIZE=$(du -h "$DATABASE_PATH" | cut -f1)
TABLE_COUNT=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")

log_info "Restore complete!"
log_info "Database size: $DB_SIZE"
log_info "Table count: $TABLE_COUNT"

# Output restore info as JSON for monitoring
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"backup_file\":\"$BACKUP_FILE\",\"database\":\"$DATABASE_PATH\",\"db_size\":\"$DB_SIZE\",\"table_count\":$TABLE_COUNT,\"status\":\"success\"}"
