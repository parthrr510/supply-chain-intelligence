from unittest.mock import patch

from fastapi.testclient import TestClient

from api_interface.api.main import app

client = TestClient(app)


@patch("api_interface.repositories.route_repository.get_route_stats")
def test_get_route_stats_existing(mock_get_stats):
    mock_get_stats.return_value = {
        "origin_port": "USLAX",
        "destination_port": "JPTYO",
        "shipment_count": 50,
        "average_delay_hours": 12.5,
        "on_time_rate": 0.8,
    }

    response = client.get("/routes/USLAX/JPTYO/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "USLAX"
    assert data["destination"] == "JPTYO"
    assert data["shipment_count"] == 50
    assert data["average_delay_hours"] == 12.5
    assert data["on_time_rate"] == 0.8


@patch("api_interface.repositories.route_repository.get_route_stats")
def test_get_route_stats_empty(mock_get_stats):
    mock_get_stats.return_value = None

    response = client.get("/routes/UNKNOWN/ROUTE/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "UNKNOWN"
    assert data["destination"] == "ROUTE"
    assert data["shipment_count"] == 0
    assert data["average_delay_hours"] is None
    assert data["on_time_rate"] is None
