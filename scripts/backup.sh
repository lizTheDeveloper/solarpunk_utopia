#!/bin/bash
# Automated SQLite backup script (GAP-58)
#
# This script:
# - Creates timestamped backups of the database
# - Compresses backups to save space
# - Optionally uploads to S3 if configured
# - Enforces retention policy (7 days)
# - Verifies backup integrity
#
# Usage:
#   ./scripts/backup.sh [database_path] [backup_dir]
#
# Environment variables:
#   DATABASE_PATH - Path to SQLite database (default: ./dtn_bundles.db)
#   BACKUP_DIR - Backup storage directory (default: ./backups)
#   BACKUP_RETENTION_DAYS - How many days to keep backups (default: 7)
#   BACKUP_S3_BUCKET - S3 bucket for remote backup (optional)
#   BACKUP_S3_PATH - S3 path prefix (default: backups/)

set -euo pipefail

# Configuration
DATABASE_PATH="${1:-${DATABASE_PATH:-./dtn_bundles.db}}"
BACKUP_DIR="${2:-${BACKUP_DIR:-./backups}}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
S3_PATH="${BACKUP_S3_PATH:-backups/}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="dtn_backup_${DATE}.db"
BACKUP_COMPRESSED="${BACKUP_FILE}.gz"

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

# Check if database exists
if [ ! -f "$DATABASE_PATH" ]; then
    log_error "Database not found: $DATABASE_PATH"
    return
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log_info "Starting backup of $DATABASE_PATH..."
log_info "Backup directory: $BACKUP_DIR"

# Perform SQLite hot backup using .backup command
# This is safer than copying the file directly as it handles locking
log_info "Creating backup: ${BACKUP_FILE}"
sqlite3 "$DATABASE_PATH" ".backup ${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -ne 0 ]; then
    log_error "Backup failed"
    return
fi

# Verify backup integrity
log_info "Verifying backup integrity..."
INTEGRITY_CHECK=$(sqlite3 "${BACKUP_DIR}/${BACKUP_FILE}" "PRAGMA integrity_check")

if [ "$INTEGRITY_CHECK" != "ok" ]; then
    log_error "Backup integrity check failed: $INTEGRITY_CHECK"
    rm -f "${BACKUP_DIR}/${BACKUP_FILE}"
    return
fi

log_info "Backup integrity verified"

# Compress backup
log_info "Compressing backup..."
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -ne 0 ]; then
    log_error "Compression failed"
    return
fi

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_COMPRESSED}" | cut -f1)
log_info "Compressed backup size: ${BACKUP_SIZE}"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    log_info "Uploading to S3: s3://${S3_BUCKET}/${S3_PATH}${BACKUP_COMPRESSED}"

    # Check if aws CLI is available
    if ! command -v aws &> /dev/null; then
        log_warn "AWS CLI not found, skipping S3 upload"
    else
        aws s3 cp "${BACKUP_DIR}/${BACKUP_COMPRESSED}" "s3://${S3_BUCKET}/${S3_PATH}${BACKUP_COMPRESSED}"

        if [ $? -eq 0 ]; then
            log_info "S3 upload successful"
        else
            log_warn "S3 upload failed (backup still saved locally)"
        fi
    fi
fi

# Enforce retention policy
log_info "Enforcing retention policy (${RETENTION_DAYS} days)..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "dtn_backup_*.db.gz" -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)

if [ "$DELETED_COUNT" -gt 0 ]; then
    log_info "Deleted $DELETED_COUNT old backup(s)"
else
    log_info "No old backups to delete"
fi

# List current backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "dtn_backup_*.db.gz" | wc -l)
log_info "Current backup count: $BACKUP_COUNT"

log_info "Backup complete: ${BACKUP_DIR}/${BACKUP_COMPRESSED}"

# Output backup info as JSON for monitoring systems
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"backup_file\":\"${BACKUP_COMPRESSED}\",\"backup_size\":\"${BACKUP_SIZE}\",\"database\":\"${DATABASE_PATH}\",\"status\":\"success\"}"
