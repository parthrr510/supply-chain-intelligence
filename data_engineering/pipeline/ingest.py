from pathlib import Path

import duckdb
import pandas as pd

from data_engineering.dq.clean import process_and_clean_data


def init_schema(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS ports (
        port_code VARCHAR PRIMARY KEY,
        name VARCHAR,
        country VARCHAR,
        region VARCHAR,
        timezone VARCHAR,
        average_congestion_score DOUBLE
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id VARCHAR PRIMARY KEY,
        customer_id VARCHAR,
        origin_port VARCHAR,
        destination_port VARCHAR,
        vessel_id VARCHAR,
        booking_date TIMESTAMP,
        planned_departure TIMESTAMP,
        actual_departure TIMESTAMP,
        planned_arrival TIMESTAMP,
        actual_arrival TIMESTAMP,
        container_count DOUBLE,
        cargo_type VARCHAR,
        weight_tons DOUBLE,
        status VARCHAR,
        actual_delay_hours DOUBLE,
        on_time_flag BOOLEAN,
        route_key VARCHAR,
        transit_days_planned DOUBLE,
        transit_days_actual DOUBLE
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS port_events (
        event_id VARCHAR PRIMARY KEY,
        port_code VARCHAR,
        event_type VARCHAR,
        event_timestamp TIMESTAMP,
        vessel_id VARCHAR
    );
    """)

    conn.execute("""
    CREATE OR REPLACE VIEW route_statistics AS
    SELECT 
        route_key,
        origin_port,
        destination_port,
        COUNT(*) as shipment_count,
        AVG(actual_delay_hours) as average_delay_hours,
        SUM(CASE WHEN on_time_flag THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0) as on_time_rate
    FROM shipments
    GROUP BY route_key, origin_port, destination_port;
    """)


def ingest_data(db_path: Path, raw_dir: Path, quarantine_dir: Path):
    # 1. Read Raw
    ports_path = raw_dir / "ports.csv"
    if not ports_path.exists():
        ports_path = raw_dir / "ports 2.csv"

    shipments_path = raw_dir / "shipments.csv"
    if not shipments_path.exists():
        shipments_path = raw_dir / "shipments 2.csv"

    events_path = raw_dir / "port_events.csv"
    if not events_path.exists():
        events_path = raw_dir / "port_events 2.csv"

    ports_df = pd.read_csv(ports_path)
    shipments_df = pd.read_csv(shipments_path)
    events_df = pd.read_csv(events_path)

    # 2. Clean Data
    clean_p, clean_s, clean_e = process_and_clean_data(
        ports_df, shipments_df, events_df, quarantine_dir
    )

    # 3. Connect to DuckDB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))

    # 4. Initialize Schema and clear existing data for idempotency
    init_schema(conn)
    conn.execute("DELETE FROM port_events")
    conn.execute("DELETE FROM shipments")
    conn.execute("DELETE FROM ports")

    # 5. Load and calculate derived fields using DuckDB
    # Ports
    conn.register("df_ports", clean_p)
    conn.execute("""
    INSERT INTO ports (port_code, name, country, region, timezone, average_congestion_score)
    SELECT port_code, port_name, country, region, timezone, CAST(avg_congestion_score AS DOUBLE)
    FROM df_ports
    """)

    # Shipments
    conn.register("df_shipments", clean_s)
    conn.execute("""
    INSERT INTO shipments
    SELECT 
        shipment_id, customer_id, origin_port, destination_port, vessel_id,
        TRY_CAST(booking_date AS TIMESTAMP), 
        TRY_CAST(planned_departure AS TIMESTAMP), 
        TRY_CAST(actual_departure AS TIMESTAMP), 
        TRY_CAST(planned_arrival AS TIMESTAMP), 
        TRY_CAST(actual_arrival AS TIMESTAMP),
        CAST(container_count AS DOUBLE), cargo_type, CAST(weight_tons AS DOUBLE), status,
        DATE_DIFF('hour', TRY_CAST(planned_arrival AS TIMESTAMP), TRY_CAST(actual_arrival AS TIMESTAMP)) as actual_delay_hours,
        CASE WHEN DATE_DIFF('hour', TRY_CAST(planned_arrival AS TIMESTAMP), TRY_CAST(actual_arrival AS TIMESTAMP)) <= 24 THEN true ELSE false END as on_time_flag,
        origin_port || '-' || destination_port as route_key,
        DATE_DIFF('day', TRY_CAST(planned_departure AS TIMESTAMP), TRY_CAST(planned_arrival AS TIMESTAMP)) as transit_days_planned,
        DATE_DIFF('day', TRY_CAST(actual_departure AS TIMESTAMP), TRY_CAST(actual_arrival AS TIMESTAMP)) as transit_days_actual
    FROM df_shipments
    """)

    # Events
    conn.register("df_events", clean_e)
    conn.execute("""
    INSERT INTO port_events (event_id, port_code, event_type, event_timestamp, vessel_id)
    SELECT 
        event_id, port_code, event_type, TRY_CAST(event_timestamp AS TIMESTAMP), vessel_id
    FROM df_events
    """)

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the DuckDB ingestion pipeline")
    parser.add_argument(
        "--db-path", default="data_engineering/data/curated/supply_chain.db"
    )
    parser.add_argument("--raw-dir", default="data_engineering/data-files")
    parser.add_argument("--quarantine-dir", default="data_engineering/data/quarantine")
    args = parser.parse_args()

    ingest_data(Path(args.db_path), Path(args.raw_dir), Path(args.quarantine_dir))
    print("Ingestion complete.")
