#!/bin/bash
###############################################################################
# Database Restore Script for Compliance OS
#
# This script restores a PostgreSQL database from a backup file
#
# Usage:
#   ./scripts/restore_db.sh <backup_file>
#   ./scripts/restore_db.sh  # Interactive mode - lists available backups
#
# Prerequisites:
#   - psql and gunzip installed
#   - DATABASE_URL environment variable set
###############################################################################

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATABASE_URL="${DATABASE_URL:-}"
BACKUP_FILE="${1:-}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."

    # Check if psql is installed
    if ! command -v psql &> /dev/null; then
        log_error "psql is not installed. Please install PostgreSQL client tools."
        exit 1
    fi

    # Check if gunzip is installed
    if ! command -v gunzip &> /dev/null; then
        log_error "gunzip is not installed."
        exit 1
    fi

    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable is not set."
        exit 1
    fi

    log_info "Prerequisites validated."
}

# List available backups
list_backups() {
    log_info "Available backups in ${BACKUP_DIR}:"
    echo "=================================================="

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.sql.gz 2>/dev/null)" ]; then
        log_warn "No backup files found in ${BACKUP_DIR}."
        return 1
    fi

    ls -lh "$BACKUP_DIR"/*.sql.gz | awk '{print NR". "$9" ("$5")"}'
    echo "=================================================="
    return 0
}

# Select backup file interactively
select_backup() {
    if ! list_backups; then
        log_error "No backups available for restore."
        exit 1
    fi

    read -p "Enter the number of the backup to restore (or 'q' to quit): " SELECTION

    if [ "$SELECTION" = "q" ]; then
        log_info "Restore cancelled."
        exit 0
    fi

    BACKUP_FILE=$(ls "$BACKUP_DIR"/*.sql.gz | sed -n "${SELECTION}p")

    if [ -z "$BACKUP_FILE" ]; then
        log_error "Invalid selection."
        exit 1
    fi

    log_info "Selected backup: ${BACKUP_FILE}"
}

# Verify backup file
verify_backup_file() {
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: ${BACKUP_FILE}"
        exit 1
    fi

    log_info "Verifying backup file integrity..."
    if ! gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        log_error "Backup file is corrupted: ${BACKUP_FILE}"
        exit 1
    fi

    log_info "Backup file verified."
}

# Restore database
restore_database() {
    log_warn "WARNING: This will overwrite the current database!"
    log_warn "Database: ${DATABASE_URL}"
    log_warn "Backup: ${BACKUP_FILE}"

    read -p "Are you absolutely sure you want to continue? (yes/no) " -r
    echo
    if [[ ! $REPLY =~ ^(yes|YES)$ ]]; then
        log_info "Restore cancelled."
        exit 0
    fi

    log_info "Restoring database from backup..."

    # Drop existing connections
    log_info "Terminating existing database connections..."
    psql "$DATABASE_URL" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();" || true

    # Restore database
    if gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"; then
        log_info "Database restored successfully."
        return 0
    else
        log_error "Database restore failed."
        return 1
    fi
}

# Verify restore
verify_restore() {
    log_info "Verifying database restore..."

    # Check if database is accessible
    if psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM tenants;" &>/dev/null; then
        log_info "Database restore verified."
        return 0
    else
        log_error "Database restore verification failed."
        return 1
    fi
}

# Main restore flow
main() {
    log_info "Starting database restore for Compliance OS..."
    echo "=================================================="

    validate_prerequisites

    # If no backup file specified, show interactive selection
    if [ -z "$BACKUP_FILE" ]; then
        select_backup
    fi

    verify_backup_file

    if ! restore_database; then
        log_error "Restore failed."
        exit 1
    fi

    if ! verify_restore; then
        log_error "Restore verification failed."
        exit 1
    fi

    log_info "=================================================="
    log_info "Database restore completed successfully! ✓"
}

# Run main function
main
