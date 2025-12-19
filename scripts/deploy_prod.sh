#!/bin/bash
###############################################################################
# Production Deployment Script for Compliance OS
#
# This script deploys the application to production via Render.com
#
# Usage:
#   ./scripts/deploy_prod.sh
#
# Prerequisites:
#   - Git repository on main branch
#   - All tests passing
#   - RENDER_PRODUCTION_DEPLOY_HOOK environment variable set
###############################################################################

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_HOOK="${RENDER_PRODUCTION_DEPLOY_HOOK:-}"
HEALTH_CHECK_URL="https://api.complianceos.com/api/v1/health"
MAX_WAIT_TIME=300  # 5 minutes
CHECK_INTERVAL=10  # 10 seconds

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if on main branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        log_error "Not on main branch (current: $CURRENT_BRANCH). Aborting deployment."
        exit 1
    fi

    # Check if working directory is clean
    if [ -n "$(git status --porcelain)" ]; then
        log_warn "Working directory is not clean. Uncommitted changes detected."
        read -p "Continue with deployment? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment aborted."
            exit 1
        fi
    fi

    # Check if DEPLOY_HOOK is set
    if [ -z "$DEPLOY_HOOK" ]; then
        log_error "RENDER_PRODUCTION_DEPLOY_HOOK environment variable not set."
        exit 1
    fi

    log_info "Pre-deployment checks passed."
}

# Create database backup before deployment
create_backup() {
    log_info "Creating database backup before deployment..."

    if [ -f "./scripts/backup_db.sh" ]; then
        ./scripts/backup_db.sh
        log_info "Backup created successfully."
    else
        log_warn "Backup script not found. Skipping backup."
    fi
}

# Trigger deployment
trigger_deployment() {
    log_info "Triggering production deployment via Render..."

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$DEPLOY_HOOK")

    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
        log_info "Deployment triggered successfully (HTTP $HTTP_CODE)."
        return 0
    else
        log_error "Deployment trigger failed (HTTP $HTTP_CODE)."
        return 1
    fi
}

# Wait for deployment to complete
wait_for_deployment() {
    log_info "Waiting for deployment to complete..."

    ELAPSED=0
    while [ $ELAPSED -lt $MAX_WAIT_TIME ]; do
        sleep $CHECK_INTERVAL
        ELAPSED=$((ELAPSED + CHECK_INTERVAL))

        # Check health endpoint
        if curl -sf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log_info "Deployment completed successfully in ${ELAPSED}s!"
            return 0
        fi

        log_info "Waiting... (${ELAPSED}s / ${MAX_WAIT_TIME}s)"
    done

    log_error "Deployment timed out after ${MAX_WAIT_TIME}s."
    return 1
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment health..."

    HEALTH_RESPONSE=$(curl -sf "$HEALTH_CHECK_URL")

    if [ $? -eq 0 ]; then
        log_info "Health check passed."
        echo "$HEALTH_RESPONSE" | jq '.' || echo "$HEALTH_RESPONSE"
        return 0
    else
        log_error "Health check failed."
        return 1
    fi
}

# Rollback function
rollback() {
    log_error "Deployment failed! Initiating rollback..."

    # In Render, rollback is typically done via dashboard
    # This is a placeholder for manual rollback instructions
    log_warn "Manual rollback required:"
    log_warn "1. Go to Render dashboard: https://dashboard.render.com"
    log_warn "2. Select the Compliance OS service"
    log_warn "3. Click 'Rollback' to previous deployment"
    log_warn "4. Run database restore if needed: ./scripts/restore_db.sh"
}

# Main deployment flow
main() {
    log_info "Starting production deployment for Compliance OS..."
    echo "=================================================="

    # Confirmation prompt
    log_warn "You are about to deploy to PRODUCTION."
    read -p "Are you sure you want to continue? (yes/no) " -r
    echo
    if [[ ! $REPLY =~ ^(yes|YES)$ ]]; then
        log_info "Deployment cancelled."
        exit 0
    fi

    # Run deployment steps
    pre_deployment_checks
    create_backup

    if ! trigger_deployment; then
        log_error "Deployment failed at trigger stage."
        exit 1
    fi

    if ! wait_for_deployment; then
        rollback
        exit 1
    fi

    if ! verify_deployment; then
        rollback
        exit 1
    fi

    log_info "=================================================="
    log_info "Production deployment completed successfully! 🚀"
    log_info "Application URL: https://app.complianceos.com"
}

# Run main function
main
