import tempfile
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from data_engineering.pipeline.ingest import ingest_data


@pytest.fixture
def temp_dirs():
    with (
        tempfile.TemporaryDirectory() as raw_dir,
        tempfile.TemporaryDirectory() as q_dir,
        tempfile.TemporaryDirectory() as db_dir,
    ):
        yield Path(raw_dir), Path(q_dir), Path(db_dir)


def create_dummy_data(raw_dir: Path):
    ports_df = pd.DataFrame(
        [
            {
                "port_code": "USLAX",
                "port_name": "Los Angeles",
                "country": "USA",
                "region": "North America",
                "timezone": "America/Los_Angeles",
                "avg_congestion_score": 5.0,
            },
            {
                "port_code": "CNSHA",
                "port_name": "Shanghai",
                "country": "China",
                "region": "Asia",
                "timezone": "Asia/Shanghai",
                "avg_congestion_score": 8.5,
            },
        ]
    )

    shipments_df = pd.DataFrame(
        [
            {
                "shipment_id": "SHP-1",
                "customer_id": "C-1",
                "origin_port": "CNSHA",
                "destination_port": "USLAX",
                "vessel_id": "V-1",
                "booking_date": "2023-01-01T00:00:00",
                "planned_departure": "2023-01-05T00:00:00",
                "actual_departure": "2023-01-05T12:00:00",
                "planned_arrival": "2023-01-20T00:00:00",
                "actual_arrival": "2023-01-21T02:00:00",
                "container_count": 2,
                "cargo_type": "Electronics",
                "weight_tons": 10.5,
                "status": "COMPLETED",
            },
            {
                "shipment_id": "SHP-2",
                "customer_id": "C-2",
                "origin_port": "CNSHA",
                "destination_port": "USLAX",
                "vessel_id": "V-2",
                "booking_date": "2023-02-01T00:00:00",
                "planned_departure": "2023-02-05T00:00:00",
                "actual_departure": "2023-02-05T00:00:00",
                "planned_arrival": "2023-02-20T00:00:00",
                "actual_arrival": "2023-02-19T00:00:00",
                "container_count": 1,
                "cargo_type": "Furniture",
                "weight_tons": 5.0,
                "status": "PENDING",
            },
        ]
    )

    events_df = pd.DataFrame(
        [
            {
                "event_id": "EV-1",
                "port": "CNSHA",
                "event_type": "DEPARTURE",
                "event_timestamp": "2023-01-05T12:00:00",
                "vessel_id": "V-1",
            }
        ]
    )

    ports_df.to_csv(raw_dir / "ports.csv", index=False)
    shipments_df.to_csv(raw_dir / "shipments.csv", index=False)
    events_df.to_csv(raw_dir / "port_events.csv", index=False)


def test_ingestion_pipeline(temp_dirs):
    raw_dir, q_dir, db_dir = temp_dirs
    db_path = db_dir / "test.db"

    create_dummy_data(raw_dir)

    ingest_data(db_path, raw_dir, q_dir)

    conn = duckdb.connect(str(db_path))

    # Check Shipments derived fields
    shipments = conn.execute(
        "SELECT shipment_id, actual_delay_hours, on_time_flag, route_key, transit_days_planned, transit_days_actual, status FROM shipments ORDER BY shipment_id"
    ).df()

    assert len(shipments) == 2

    shp1 = shipments[shipments["shipment_id"] == "SHP-1"].iloc[0]
    # planned: 01-20 00:00, actual: 01-21 02:00 => 26 hours
    assert shp1["actual_delay_hours"] == 26
    assert shp1["on_time_flag"] == False
    assert shp1["route_key"] == "CNSHA-USLAX"
    # transit planned: 01-05 to 01-20 => 15 days
    assert shp1["transit_days_planned"] == 15
    assert shp1["status"] == "DELIVERED"  # Normalized from COMPLETED

    shp2 = shipments[shipments["shipment_id"] == "SHP-2"].iloc[0]
    # planned: 02-20, actual: 02-19 => -24 hours
    assert shp2["actual_delay_hours"] == -24
    assert shp2["on_time_flag"] == True

    # Test route statistics view
    stats = conn.execute("SELECT * FROM route_statistics").df()
    assert len(stats) == 1
    assert stats.iloc[0]["shipment_count"] == 2
    assert stats.iloc[0]["average_delay_hours"] == 1.0  # (26 - 24) / 2 = 1.0
    assert stats.iloc[0]["on_time_rate"] == 0.5  # 1 out of 2 is on time

    # Test idempotency
    ingest_data(db_path, raw_dir, q_dir)
    shipments_count = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
    assert shipments_count == 2

    conn.close()
