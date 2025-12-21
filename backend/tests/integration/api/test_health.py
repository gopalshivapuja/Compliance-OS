"""
Integration tests for health check endpoint
"""


def test_health_check(client):
    """Test that health check endpoint returns 200 OK."""
    # Health check is now at /api/v1/health/health with real service checks
    response = client.get("/api/v1/health/health")

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"


def test_health_check_structure(client):
    """Test health check response structure."""
    response = client.get("/api/v1/health/health")

    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str)
    assert data["status"] == "healthy"
    # Verify service status is included
    assert "services" in data
    assert "database" in data["services"]


def test_root_endpoint(client):
    """Test that root endpoint returns basic status."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "name" in data
    assert "version" in data


def test_liveness_probe(client):
    """Test Kubernetes liveness probe endpoint."""
    response = client.get("/api/v1/health/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_readiness_probe(client):
    """Test Kubernetes readiness probe endpoint."""
    response = client.get("/api/v1/health/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
