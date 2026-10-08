import duckdb
import pandas as pd


def get_training_data(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Constructs the ML dataset.
    Target: 1 if actual_delay_hours > 24 else 0.
    Only rows where target is determinable (actual_arrival and planned_arrival are not null) are included.
    """

    query = """
    SELECT
        s.origin_port,
        s.destination_port,
        s.vessel_id,
        s.cargo_type,
        s.container_count,
        s.weight_tons,
        s.transit_days_planned as planned_transit_days,
        op.average_congestion_score as origin_congestion_score,
        dp.average_congestion_score as destination_congestion_score,
        EXTRACT(MONTH FROM s.booking_date) as booking_month,
        EXTRACT(ISODOW FROM s.booking_date) as booking_day_of_week,
        CASE WHEN s.actual_delay_hours > 24 THEN 1 ELSE 0 END as target
    FROM shipments s
    LEFT JOIN ports op ON s.origin_port = op.port_code
    LEFT JOIN ports dp ON s.destination_port = dp.port_code
    WHERE s.actual_arrival IS NOT NULL AND s.planned_arrival IS NOT NULL
    ORDER BY s.booking_date ASC
    """

    df = conn.execute(query).df()

    # Ensure no leakage columns are returned
    leakage_columns = [
        "actual_departure",
        "actual_arrival",
        "actual_delay_hours",
        "on_time_flag",
    ]
    for col in leakage_columns:
        if col in df.columns:
            df = df.drop(columns=[col])

    return df
