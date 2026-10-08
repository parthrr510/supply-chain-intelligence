import pandas as pd

from data_engineering.dq.clean import process_and_clean_data


def test_clean_pipeline(tmp_path):
    quarantine_dir = tmp_path / "quarantine"

    ports_df = pd.DataFrame(
        {
            "port_code": ["P1", "P2", "P2", "P3", "P3"],
            "name": ["Port 1", "Port 2", "Port 2", "Port 3", "Port 3_Diff"],
        }
    )

    shipments_df = pd.DataFrame(
        {
            "shipment_id": ["S1", "S1", "S2", "S2", "S3", "S4", "S5"],
            "origin_port": [
                "P1",
                "P1",
                "P1",
                "P2",
                "P9",
                "P1",
                "P1",
            ],  # S2 is conflicting, S3 has invalid port P9
            "destination_port": ["P2", "P2", "P2", "P1", "P2", "P2", "P2"],
            "status": [
                " COMPLETED ",
                "COMPLETED",
                "In Transit",
                "In Transit",
                "Delivered",
                "complete",
                "Pending",
            ],
            "actual_arrival": [
                "2023-01-01",
                "2023-01-01",
                "2023-01-02",
                "2023-01-02",
                None,
                None,
                None,
            ],
        }
    )

    events_df = pd.DataFrame(
        {
            "event_id": ["E1", "E1", "E2", "E3", "E4"],
            "port": [
                "P1",
                "P1",
                "P9",
                "P2",
                "P1",
            ],  # E2 has invalid port, E3 missing type (below)
            "event_type": ["DEPARTURE", "DEPARTURE", "ARRIVAL", None, "ARRIVAL"],
        }
    )

    # Run once
    clean_p, clean_s, clean_e = process_and_clean_data(
        ports_df, shipments_df, events_df, quarantine_dir
    )

    # 1. Normalization behavior
    assert clean_p.iloc[0]["port_code"] == "P1"
    # Status should be normalized
    s4_status = clean_s[clean_s["shipment_id"] == "S4"]["status"].iloc[0]
    assert s4_status == "DELIVERED"

    # 2. Duplicate handling (exact)
    # S1 was exact duplicate, should be 1
    assert len(clean_s[clean_s["shipment_id"] == "S1"]) == 1

    # 3. Conflicting duplicate handling
    # P3 was conflicting
    assert "P3" not in clean_p["port_code"].values
    # S2 was conflicting
    assert "S2" not in clean_s["shipment_id"].values

    # 4. Invalid references
    # S3 had P9
    assert "S3" not in clean_s["shipment_id"].values
    # E2 had P9
    assert "E2" not in clean_e["event_id"].values

    # 5. Missing event type
    # E3 had None
    assert "E3" not in clean_e["event_id"].values

    # 6. Valid missing actual timestamps
    # S4 has None actual_arrival but should still be in clean_s
    assert "S4" in clean_s["shipment_id"].values

    # Check quarantine files are created (from first run)
    assert (quarantine_dir / "ports_quarantined.csv").exists()
    assert (quarantine_dir / "shipments_quarantined.csv").exists()
    assert (quarantine_dir / "port_events_quarantined.csv").exists()

    # 7. Deterministic repeated execution
    # Run again on the already clean data
    clean_p2, clean_s2, clean_e2 = process_and_clean_data(
        clean_p, clean_s, clean_e, quarantine_dir
    )
    assert len(clean_p) == len(clean_p2)
    assert len(clean_s) == len(clean_s2)
    assert len(clean_e) == len(clean_e2)
