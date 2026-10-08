from unittest.mock import patch

from fastapi.testclient import TestClient

from api_interface.api.main import app

client = TestClient(app)


@patch("api_interface.api.main.check_db_health")
@patch("api_interface.api.main.Path.exists")
def test_health_check_missing_deps(mock_exists, mock_db_health):
    mock_db_health.return_value = False
    mock_exists.return_value = False

    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["checks"]["database"] == "error"
    assert data["checks"]["model"] == "error"


@patch("api_interface.api.main.check_db_health")
@patch("api_interface.api.main.Path.exists")
def test_health_check_healthy(mock_exists, mock_db_health):
    mock_db_health.return_value = True
    mock_exists.return_value = True

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["model"] == "ok"


def test_request_id_in_response():
    response = client.get("/health", headers={"X-Request-ID": "test-id-123"})
    assert response.headers.get("X-Request-ID") == "test-id-123"
