"""
Integration tests for health check endpoint
"""


def test_health_check(client):
    """Test that health check endpoint returns 200 OK."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_check_structure(client):
    """Test health check response structure."""
    response = client.get("/health")

    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str)
