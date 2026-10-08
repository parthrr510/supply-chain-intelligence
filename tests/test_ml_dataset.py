import duckdb
import pytest

from machine_learning.ml.dataset import get_training_data


@pytest.fixture
def test_conn():
    conn = duckdb.connect(":memory:")

    # Create ports table
    conn.execute("""
    CREATE TABLE ports (
        port_code VARCHAR,
        average_congestion_score DOUBLE
    )
    """)
    conn.execute("INSERT INTO ports VALUES ('PORT_A', 0.5), ('PORT_B', 0.8)")

    # Create shipments table
    conn.execute("""
    CREATE TABLE shipments (
        shipment_id VARCHAR,
        origin_port VARCHAR,
        destination_port VARCHAR,
        vessel_id VARCHAR,
        cargo_type VARCHAR,
        container_count DOUBLE,
        weight_tons DOUBLE,
        transit_days_planned DOUBLE,
        booking_date TIMESTAMP,
        actual_arrival TIMESTAMP,
        planned_arrival TIMESTAMP,
        actual_departure TIMESTAMP,
        actual_delay_hours DOUBLE,
        on_time_flag BOOLEAN
    )
    """)

    # Insert a valid row
    conn.execute("""
    INSERT INTO shipments VALUES (
        'SH1', 'PORT_A', 'PORT_B', 'V1', 'Electronics', 10.0, 50.0, 5.0, 
        '2023-01-01 10:00:00', '2023-01-07 10:00:00', '2023-01-06 05:00:00', 
        '2023-01-02 10:00:00', 29.0, false
    )
    """)

    # Insert a row missing actual_arrival (should be excluded)
    conn.execute("""
    INSERT INTO shipments VALUES (
        'SH2', 'PORT_B', 'PORT_A', 'V2', 'Apparel', 5.0, 20.0, 4.0, 
        '2023-01-02 10:00:00', NULL, '2023-01-07 10:00:00', 
        '2023-01-03 10:00:00', NULL, NULL
    )
    """)

    return conn


def test_get_training_data_excludes_leakage(test_conn):
    df = get_training_data(test_conn)

    leakage_cols = [
        "actual_departure",
        "actual_arrival",
        "actual_delay_hours",
        "on_time_flag",
    ]

    for col in leakage_cols:
        assert col not in df.columns, f"Leakage column {col} found in training data!"


def test_get_training_data_filters_null_arrival(test_conn):
    df = get_training_data(test_conn)
    # SH2 has NULL actual_arrival, so it should be filtered out
    assert len(df) == 1


def test_get_training_data_target_calculation(test_conn):
    df = get_training_data(test_conn)
    # actual_delay_hours is 29.0, which is > 24, so target should be 1
    assert df["target"].iloc[0] == 1


def test_get_training_data_features_present(test_conn):
    df = get_training_data(test_conn)

    expected_features = [
        "origin_port",
        "destination_port",
        "vessel_id",
        "cargo_type",
        "container_count",
        "weight_tons",
        "planned_transit_days",
        "origin_congestion_score",
        "destination_congestion_score",
        "booking_month",
        "booking_day_of_week",
    ]

    for feature in expected_features:
        assert feature in df.columns, (
            f"Expected feature {feature} missing from training data"
        )
