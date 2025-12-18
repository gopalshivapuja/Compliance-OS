#!/bin/bash
# Compliance OS - Health Check Script
# Verifies all services are running and healthy

set -e

echo "🏥 Compliance OS Health Check"
echo "=============================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    printf "%-30s " "$name:"

    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_code" ]; then
            echo -e "${GREEN}✓ Healthy${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}⚠ Warning${NC} (HTTP $response, expected $expected_code)"
            return 1
        fi
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local name=$1
    local container=$2

    printf "%-30s " "$name:"

    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")
        if [ "$status" = "healthy" ]; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        elif [ "$status" = "unknown" ]; then
            echo -e "${GREEN}✓ Running${NC} (no health check)"
            return 0
        else
            echo -e "${YELLOW}⚠ ${status}${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Not Running${NC}"
        return 1
    fi
}

# Check Docker containers
echo "Docker Containers:"
echo "------------------"
check_container "PostgreSQL" "compliance-os-postgres-1"
check_container "Redis" "compliance-os-redis-1"
check_container "Backend (FastAPI)" "compliance-os-backend-1"
check_container "Celery Worker" "compliance-os-celery-worker-1"
check_container "Celery Beat" "compliance-os-celery-beat-1"
check_container "Frontend (Next.js)" "compliance-os-frontend-1"
echo ""

# Check HTTP endpoints
echo "HTTP Endpoints:"
echo "---------------"
check_http "Backend Health" "http://localhost:8000/health"
check_http "Backend API Docs" "http://localhost:8000/docs"
check_http "Frontend" "http://localhost:3000" 200
echo ""

# Check database connection
echo "Database Connection:"
echo "-------------------"
printf "%-30s " "PostgreSQL:"
if docker exec compliance-os-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Ready${NC}"
else
    echo -e "${RED}✗ Not Ready${NC}"
fi
echo ""

# Check Redis connection
echo "Cache Connection:"
echo "----------------"
printf "%-30s " "Redis:"
if docker exec compliance-os-redis-1 redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Ready${NC}"
else
    echo -e "${RED}✗ Not Ready${NC}"
fi
echo ""

echo "=============================="
echo "Health check complete!"
echo ""
echo "💡 Tip: Run 'docker-compose logs <service>' to view logs for a specific service"
