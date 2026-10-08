import pandas as pd

from data_engineering.dq.checks import run_dq_checks


def test_run_dq_checks():
    ports_df = pd.DataFrame(
        {"port_code": ["P1", "P2", "P1"], "name": ["Port 1", "Port 2", "Port 1"]}
    )

    shipments_df = pd.DataFrame(
        {
            "shipment_id": ["S1", "S2", "S2", "S1", "S3", "S4"],
            "origin_port": ["P1", "P1", "P1", "P1", "P3", "P1"],
            "destination_port": ["P2", "P2", "P2", "P2", "P2", "P4"],
            "weight_tons": [10.0, 15.0, 20.0, 10.0, 30.0, -5.0],
            "status": [
                "DELIVERED",
                "COMPLETED",
                "COMPLETED",
                "DELIVERED",
                None,
                "DELIVERED",
            ],
        }
    )

    events_df = pd.DataFrame(
        {
            "event_id": ["E1", "E2", "E3"],
            "port_code": ["P1", "P3", "P1"],
            "event_type": ["DEPARTURE", "ARRIVAL", None],
        }
    )

    results = run_dq_checks(ports_df, shipments_df, events_df)

    check_ids = {r["check_id"]: r for r in results}

    # Ports check
    assert "PORTS_DUPLICATE_CODE" in check_ids
    assert check_ids["PORTS_DUPLICATE_CODE"]["rows_affected"] == 2

    # Shipments checks
    assert "SHIPMENTS_EXACT_DUPLICATES" in check_ids
    assert check_ids["SHIPMENTS_EXACT_DUPLICATES"]["rows_affected"] == 2

    assert "SHIPMENTS_CONFLICTING_DUPLICATES" in check_ids
    assert check_ids["SHIPMENTS_CONFLICTING_DUPLICATES"]["rows_affected"] == 2

    assert "SHIPMENTS_INVALID_ORIGIN_PORT" in check_ids
    assert check_ids["SHIPMENTS_INVALID_ORIGIN_PORT"]["rows_affected"] == 1

    assert "SHIPMENTS_INVALID_DESTINATION_PORT" in check_ids
    assert check_ids["SHIPMENTS_INVALID_DESTINATION_PORT"]["rows_affected"] == 1

    assert "SHIPMENTS_NEGATIVE_WEIGHT" in check_ids
    assert check_ids["SHIPMENTS_NEGATIVE_WEIGHT"]["rows_affected"] == 1

    assert "SHIPMENTS_MISSING_STATUS" in check_ids
    assert check_ids["SHIPMENTS_MISSING_STATUS"]["rows_affected"] == 1

    # Events checks
    assert "EVENTS_MISSING_TYPE" in check_ids
    assert check_ids["EVENTS_MISSING_TYPE"]["rows_affected"] == 1

    assert "EVENTS_INVALID_PORT" in check_ids
    assert check_ids["EVENTS_INVALID_PORT"]["rows_affected"] == 1
