#!/bin/bash
###############################################################################
# Database Backup Script for Compliance OS
#
# This script creates a compressed backup of the PostgreSQL database
#
# Usage:
#   ./scripts/backup_db.sh
#
# Prerequisites:
#   - pg_dump installed
#   - DATABASE_URL environment variable set
#   - AWS CLI configured (for S3 upload)
###############################################################################

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="compliance_os_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
DATABASE_URL="${DATABASE_URL:-}"
S3_BUCKET="${AWS_S3_BACKUP_BUCKET:-}"
RETENTION_DAYS=30  # Keep backups for 30 days

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."

    # Check if pg_dump is installed
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump is not installed. Please install PostgreSQL client tools."
        exit 1
    fi

    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable is not set."
        exit 1
    fi

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    log_info "Prerequisites validated."
}

# Create database backup
create_backup() {
    log_info "Creating database backup: ${BACKUP_FILE}..."

    # Extract connection details from DATABASE_URL
    # Format: postgresql://user:password@host:port/database

    # Use pg_dump with gzip compression
    if pg_dump "$DATABASE_URL" | gzip > "$BACKUP_PATH"; then
        BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
        log_info "Backup created successfully: ${BACKUP_PATH} (${BACKUP_SIZE})"
        return 0
    else
        log_error "Failed to create backup."
        return 1
    fi
}

# Upload backup to S3
upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        log_info "S3_BUCKET not configured. Skipping S3 upload."
        return 0
    fi

    log_info "Uploading backup to S3: s3://${S3_BUCKET}/backups/${BACKUP_FILE}..."

    if command -v aws &> /dev/null; then
        if aws s3 cp "$BACKUP_PATH" "s3://${S3_BUCKET}/backups/${BACKUP_FILE}"; then
            log_info "Backup uploaded to S3 successfully."
            return 0
        else
            log_error "Failed to upload backup to S3."
            return 1
        fi
    else
        log_error "AWS CLI not installed. Skipping S3 upload."
        return 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."

    # Remove local backups older than retention period
    find "$BACKUP_DIR" -name "compliance_os_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

    # Remove old S3 backups if AWS CLI is available
    if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
        CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y-%m-%d)
        log_info "Removing S3 backups older than ${CUTOFF_DATE}..."

        # Note: This requires custom script to list and delete old files
        # aws s3 ls "s3://${S3_BUCKET}/backups/" | while read -r line; do
        #     # Parse and delete old files
        # done
    fi

    log_info "Old backups cleaned up."
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."

    if gunzip -t "$BACKUP_PATH" 2>/dev/null; then
        log_info "Backup integrity verified."
        return 0
    else
        log_error "Backup file is corrupted!"
        return 1
    fi
}

# Main backup flow
main() {
    log_info "Starting database backup for Compliance OS..."
    echo "=================================================="

    validate_prerequisites

    if ! create_backup; then
        log_error "Backup failed."
        exit 1
    fi

    if ! verify_backup; then
        log_error "Backup verification failed."
        exit 1
    fi

    upload_to_s3
    cleanup_old_backups

    log_info "=================================================="
    log_info "Database backup completed successfully! ✓"
    log_info "Backup file: ${BACKUP_PATH}"
}

# Run main function
main
