from datetime import date
from unittest.mock import patch

import pytest

from api_interface.api.errors import APIError
from api_interface.services.route_service import get_route_stats
from api_interface.services.shipment_service import get_shipment, get_shipments


@patch("api_interface.services.route_service.route_repository.get_route_stats")
def test_get_route_stats_service_found(mock_repo):
    mock_repo.return_value = {
        "shipment_count": 10,
        "average_delay_hours": 5.0,
        "on_time_rate": 0.9,
    }
    stats = get_route_stats("USLAX", "JPTYO")
    assert stats["origin"] == "USLAX"
    assert stats["shipment_count"] == 10


@patch("api_interface.services.route_service.route_repository.get_route_stats")
def test_get_route_stats_service_not_found(mock_repo):
    mock_repo.return_value = None
    stats = get_route_stats("UNKNOWN", "UNKNOWN")
    assert stats["shipment_count"] == 0
    assert stats["average_delay_hours"] is None


@patch("api_interface.services.shipment_service.shipment_repository.get_shipment_by_id")
def test_get_shipment_found(mock_repo):
    mock_repo.return_value = {"shipment_id": "SHP-1"}
    shipment = get_shipment("SHP-1")
    assert shipment["shipment_id"] == "SHP-1"


@patch("api_interface.services.shipment_service.shipment_repository.get_shipment_by_id")
def test_get_shipment_not_found(mock_repo):
    mock_repo.return_value = None
    with pytest.raises(APIError) as exc_info:
        get_shipment("UNKNOWN")
    assert exc_info.value.status_code == 404


@patch("api_interface.services.shipment_service.shipment_repository.get_shipments")
def test_get_shipments_valid(mock_repo):
    mock_repo.return_value = ([], 0)
    rows, total = get_shipments()
    assert total == 0
    assert rows == []


def test_get_shipments_invalid_dates():
    with pytest.raises(APIError) as exc_info:
        get_shipments(start_date=date(2023, 1, 5), end_date=date(2023, 1, 4))
    assert exc_info.value.status_code == 400


def test_get_shipments_invalid_page():
    with pytest.raises(APIError) as exc_info:
        get_shipments(page=0)
    assert exc_info.value.status_code == 400


def test_get_shipments_invalid_page_size():
    with pytest.raises(APIError) as exc_info:
        get_shipments(page_size=101)
    assert exc_info.value.status_code == 400
