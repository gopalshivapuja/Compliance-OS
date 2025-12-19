#!/bin/bash
###############################################################################
# Health Check Script for Compliance OS
#
# This script checks the health of all application services
#
# Usage:
#   ./scripts/health_check.sh [environment]
#   ./scripts/health_check.sh production
#   ./scripts/health_check.sh staging
#   ./scripts/health_check.sh local
#
# Exit codes:
#   0 - All services healthy
#   1 - One or more services unhealthy
###############################################################################

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-local}"

# Environment-specific URLs
case "$ENVIRONMENT" in
    production)
        API_URL="https://api.complianceos.com"
        FRONTEND_URL="https://app.complianceos.com"
        ;;
    staging)
        API_URL="https://staging-api.complianceos.com"
        FRONTEND_URL="https://staging.complianceos.com"
        ;;
    local)
        API_URL="http://localhost:8000"
        FRONTEND_URL="http://localhost:3000"
        ;;
    *)
        echo "Invalid environment: $ENVIRONMENT"
        echo "Usage: $0 [production|staging|local]"
        exit 1
        ;;
esac

# Track overall health
ALL_HEALTHY=true

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ALL_HEALTHY=false
}

# Check API health endpoint
check_api_health() {
    echo "Checking API health..."

    HEALTH_URL="${API_URL}/api/v1/health"

    if RESPONSE=$(curl -sf "$HEALTH_URL" 2>&1); then
        STATUS=$(echo "$RESPONSE" | jq -r '.status' 2>/dev/null || echo "unknown")

        if [ "$STATUS" = "healthy" ]; then
            log_info "API is healthy"

            # Check individual services
            DB_STATUS=$(echo "$RESPONSE" | jq -r '.services.database.status' 2>/dev/null || echo "unknown")
            REDIS_STATUS=$(echo "$RESPONSE" | jq -r '.services.redis.status' 2>/dev/null || echo "unknown")
            CELERY_STATUS=$(echo "$RESPONSE" | jq -r '.services.celery.status' 2>/dev/null || echo "unknown")

            [ "$DB_STATUS" = "healthy" ] && log_info "  Database: healthy" || log_warn "  Database: $DB_STATUS"
            [ "$REDIS_STATUS" = "healthy" ] && log_info "  Redis: healthy" || log_warn "  Redis: $REDIS_STATUS"
            [ "$CELERY_STATUS" = "healthy" ] && log_info "  Celery: healthy" || log_warn "  Celery: $CELERY_STATUS"
        else
            log_error "API is unhealthy (status: $STATUS)"
        fi
    else
        log_error "API is not responding: $HEALTH_URL"
    fi
}

# Check liveness probe
check_liveness() {
    echo "Checking liveness probe..."

    LIVE_URL="${API_URL}/api/v1/health/live"

    if curl -sf "$LIVE_URL" > /dev/null 2>&1; then
        log_info "Liveness probe: OK"
    else
        log_error "Liveness probe: FAILED"
    fi
}

# Check readiness probe
check_readiness() {
    echo "Checking readiness probe..."

    READY_URL="${API_URL}/api/v1/health/ready"

    if curl -sf "$READY_URL" > /dev/null 2>&1; then
        log_info "Readiness probe: OK"
    else
        log_error "Readiness probe: FAILED"
    fi
}

# Check frontend
check_frontend() {
    echo "Checking frontend..."

    if curl -sf "$FRONTEND_URL" > /dev/null 2>&1; then
        log_info "Frontend is accessible"
    else
        log_error "Frontend is not accessible: $FRONTEND_URL"
    fi
}

# Check API response time
check_response_time() {
    echo "Checking API response time..."

    HEALTH_URL="${API_URL}/api/v1/health/live"

    if RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' "$HEALTH_URL" 2>&1); then
        RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

        if [ "$(echo "$RESPONSE_TIME_MS < 500" | bc)" -eq 1 ]; then
            log_info "Response time: ${RESPONSE_TIME_MS}ms (excellent)"
        elif [ "$(echo "$RESPONSE_TIME_MS < 1000" | bc)" -eq 1 ]; then
            log_warn "Response time: ${RESPONSE_TIME_MS}ms (acceptable)"
        else
            log_error "Response time: ${RESPONSE_TIME_MS}ms (slow)"
        fi
    else
        log_error "Could not measure response time"
    fi
}

# Check SSL certificate (production/staging only)
check_ssl_certificate() {
    if [ "$ENVIRONMENT" = "local" ]; then
        return 0
    fi

    echo "Checking SSL certificate..."

    DOMAIN=$(echo "$API_URL" | sed 's|https://||' | sed 's|/.*||')

    if EXPIRY=$(echo | openssl s_client -servername "$DOMAIN" -connect "${DOMAIN}:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null); then
        EXPIRY_DATE=$(echo "$EXPIRY" | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

        if [ "$DAYS_UNTIL_EXPIRY" -gt 30 ]; then
            log_info "SSL certificate: valid (expires in ${DAYS_UNTIL_EXPIRY} days)"
        elif [ "$DAYS_UNTIL_EXPIRY" -gt 7 ]; then
            log_warn "SSL certificate: expires soon (${DAYS_UNTIL_EXPIRY} days)"
        else
            log_error "SSL certificate: expires very soon (${DAYS_UNTIL_EXPIRY} days)"
        fi
    else
        log_error "Could not check SSL certificate"
    fi
}

# Main health check flow
main() {
    echo "=================================================="
    echo "Compliance OS Health Check - ${ENVIRONMENT^^} Environment"
    echo "=================================================="
    echo

    check_api_health
    echo
    check_liveness
    echo
    check_readiness
    echo
    check_frontend
    echo
    check_response_time
    echo
    check_ssl_certificate
    echo

    echo "=================================================="
    if [ "$ALL_HEALTHY" = true ]; then
        log_info "All health checks passed! ✓"
        exit 0
    else
        log_error "Some health checks failed! ✗"
        exit 1
    fi
}

# Run main function
main
