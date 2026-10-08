from unittest.mock import patch

from fastapi.testclient import TestClient

from api_interface.api.main import app

client = TestClient(app)


@patch("api_interface.repositories.shipment_repository.get_shipments")
def test_get_shipments(mock_get_shipments):
    mock_get_shipments.return_value = (
        [{"shipment_id": "SHP-123", "status": "DELIVERED"}],
        1,
    )

    response = client.get("/shipments?status=DELIVERED&page=1&page_size=20")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["shipment_id"] == "SHP-123"

    mock_get_shipments.assert_called_once_with(
        origin=None,
        destination=None,
        status="DELIVERED",
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
    )


@patch("api_interface.repositories.shipment_repository.get_shipment_by_id")
def test_get_shipment_by_id_success(mock_get_shipment_by_id):
    mock_get_shipment_by_id.return_value = {
        "shipment_id": "SHP-456",
        "route_key": "SGSIN-NLRTM",
    }

    response = client.get("/shipments/SHP-456")

    assert response.status_code == 200
    data = response.json()
    assert data["shipment_id"] == "SHP-456"
    assert data["route_key"] == "SGSIN-NLRTM"


@patch("api_interface.repositories.shipment_repository.get_shipment_by_id")
def test_get_shipment_by_id_not_found(mock_get_shipment_by_id):
    mock_get_shipment_by_id.return_value = None

    response = client.get("/shipments/UNKNOWN")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SHIPMENT_NOT_FOUND"


def test_get_shipments_invalid_date_range():
    response = client.get("/shipments?start_date=2023-12-31&end_date=2023-01-01")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_DATE_RANGE"


def test_get_shipments_invalid_pagination():
    response = client.get("/shipments?page=0")
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "INVALID_REQUEST"
