from datetime import date
from unittest.mock import patch

import duckdb
import pytest

from api_interface.repositories.route_repository import get_route_stats
from api_interface.repositories.shipment_repository import (
    get_shipment_by_id,
    get_shipments,
)
from data_engineering.pipeline.ingest import init_schema


@pytest.fixture
def mock_db_conn():
    conn = duckdb.connect(":memory:")
    init_schema(conn)

    # insert mock data
    conn.execute("""
    INSERT INTO shipments (shipment_id, customer_id, origin_port, destination_port, vessel_id, 
                           booking_date, planned_departure, status, actual_delay_hours, on_time_flag)
    VALUES 
    ('SHP-1', 'CUST-1', 'USLAX', 'JPTYO', 'VSL-1', '2023-01-01', '2023-01-05', 'COMPLETED', 5.0, true),
    ('SHP-2', 'CUST-1', 'USLAX', 'JPTYO', 'VSL-1', '2023-01-02', '2023-01-06', 'PENDING', 5.0, true)
    """)

    with (
        patch("api_interface.repositories.shipment_repository.get_db_connection", return_value=conn),
        patch("api_interface.repositories.route_repository.get_db_connection", return_value=conn),
    ):
        yield conn


def test_get_route_stats_found(mock_db_conn):
    stats = get_route_stats("USLAX", "JPTYO")
    assert stats is not None
    assert stats["shipment_count"] == 2
    assert stats["average_delay_hours"] == 5.0


def test_get_route_stats_not_found(mock_db_conn):
    stats = get_route_stats("UNKNOWN", "UNKNOWN")
    assert stats is None


def test_get_shipment_by_id_found(mock_db_conn):
    shipment = get_shipment_by_id("SHP-1")
    assert shipment is not None
    assert shipment["shipment_id"] == "SHP-1"


def test_get_shipment_by_id_not_found(mock_db_conn):
    shipment = get_shipment_by_id("UNKNOWN")
    assert shipment is None


def test_get_shipments_no_filters(mock_db_conn):
    rows, total = get_shipments()
    assert total == 2
    assert len(rows) == 2


def test_get_shipments_with_filters(mock_db_conn):
    rows, total = get_shipments(
        origin="USLAX",
        destination="JPTYO",
        status="COMPLETED",
        start_date=date(2023, 1, 4),
        end_date=date(2023, 1, 5),
    )
    assert total == 1
    assert len(rows) == 1
    assert rows[0]["shipment_id"] == "SHP-1"
