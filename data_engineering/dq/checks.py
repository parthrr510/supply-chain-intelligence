import pandas as pd


def run_dq_checks(
    ports_df: pd.DataFrame, shipments_df: pd.DataFrame, events_df: pd.DataFrame
) -> list[dict]:
    results = []

    # 1. Ports Checks
    ports_len = len(ports_df)

    # Check: Duplicate port_codes
    dup_ports = ports_df.duplicated(subset=["port_code"], keep=False)
    if dup_ports.sum() > 0:
        results.append(
            {
                "check_id": "PORTS_DUPLICATE_CODE",
                "dataset": "ports",
                "check_name": "Duplicate Port Codes",
                "severity": "Critical",
                "rows_affected": int(dup_ports.sum()),
                "percentage_affected": float(dup_ports.sum() / ports_len),
                "action": "quarantine",
                "description": "Port codes must be unique",
                "sample_row_ids": ports_df[dup_ports]["port_code"].head().tolist(),
            }
        )

    # 2. Shipments Checks
    shipments_len = len(shipments_df)

    # Check: Exact Duplicates
    exact_dups = shipments_df.duplicated(keep=False)
    num_exact_dups = exact_dups.sum()
    if num_exact_dups > 0:
        results.append(
            {
                "check_id": "SHIPMENTS_EXACT_DUPLICATES",
                "dataset": "shipments",
                "check_name": "Exact Duplicate Shipments",
                "severity": "Warning",
                "rows_affected": int(num_exact_dups),
                "percentage_affected": float(num_exact_dups / shipments_len),
                "action": "clean",  # deduplicate
                "description": "Exact duplicate rows found in shipments",
                "sample_row_ids": shipments_df[exact_dups]["shipment_id"]
                .head()
                .tolist(),
            }
        )

    # Check: Conflicting Duplicates (Same ID, different data)
    # We find IDs that are duplicated but not exact duplicates
    dup_ids_all = shipments_df.duplicated(subset=["shipment_id"], keep=False)
    conflicting_dups = dup_ids_all & ~exact_dups
    num_conflicting = conflicting_dups.sum()
    if num_conflicting > 0:
        results.append(
            {
                "check_id": "SHIPMENTS_CONFLICTING_DUPLICATES",
                "dataset": "shipments",
                "check_name": "Conflicting Duplicate Shipments",
                "severity": "Critical",
                "rows_affected": int(num_conflicting),
                "percentage_affected": float(num_conflicting / shipments_len),
                "action": "quarantine",
                "description": "Multiple rows with same shipment_id but different data",
                "sample_row_ids": shipments_df[conflicting_dups]["shipment_id"]
                .head()
                .tolist(),
            }
        )

    # Check: Invalid Port References
    valid_ports = set(ports_df["port_code"].dropna())
    invalid_origin = ~shipments_df["origin_port"].isin(valid_ports)
    num_invalid_origin = invalid_origin.sum()
    if num_invalid_origin > 0:
        results.append(
            {
                "check_id": "SHIPMENTS_INVALID_ORIGIN_PORT",
                "dataset": "shipments",
                "check_name": "Invalid Origin Port",
                "severity": "Critical",
                "rows_affected": int(num_invalid_origin),
                "percentage_affected": float(num_invalid_origin / shipments_len),
                "action": "quarantine",
                "description": "Origin port not found in ports dataset",
                "sample_row_ids": shipments_df[invalid_origin]["shipment_id"]
                .head()
                .tolist(),
            }
        )

    invalid_dest = ~shipments_df["destination_port"].isin(valid_ports)
    num_invalid_dest = invalid_dest.sum()
    if num_invalid_dest > 0:
        results.append(
            {
                "check_id": "SHIPMENTS_INVALID_DESTINATION_PORT",
                "dataset": "shipments",
                "check_name": "Invalid Destination Port",
                "severity": "Critical",
                "rows_affected": int(num_invalid_dest),
                "percentage_affected": float(num_invalid_dest / shipments_len),
                "action": "quarantine",
                "description": "Destination port not found in ports dataset",
                "sample_row_ids": shipments_df[invalid_dest]["shipment_id"]
                .head()
                .tolist(),
            }
        )

    # Check: Negative Weight (Hard business rule)
    if "weight_tons" in shipments_df.columns:
        negative_weight = shipments_df["weight_tons"] < 0
        num_negative_weight = negative_weight.sum()
        if num_negative_weight > 0:
            results.append(
                {
                    "check_id": "SHIPMENTS_NEGATIVE_WEIGHT",
                    "dataset": "shipments",
                    "check_name": "Negative Shipment Weight",
                    "severity": "Warning",
                    "rows_affected": int(num_negative_weight),
                    "percentage_affected": float(num_negative_weight / shipments_len),
                    "action": "fix",
                    "description": "weight_tons cannot be negative, fixing by taking absolute value",
                    "sample_row_ids": shipments_df[negative_weight]["shipment_id"]
                    .head()
                    .tolist(),
                }
            )

    # Check: Suspiciously High Weight (Info/Warning)
    if "weight_tons" in shipments_df.columns:
        high_weight = shipments_df["weight_tons"] > 10000
        num_high_weight = high_weight.sum()
        if num_high_weight > 0:
            results.append(
                {
                    "check_id": "SHIPMENTS_HIGH_WEIGHT_OUTLIER",
                    "dataset": "shipments",
                    "check_name": "Suspiciously High Weight",
                    "severity": "Info",
                    "rows_affected": int(num_high_weight),
                    "percentage_affected": float(num_high_weight / shipments_len),
                    "action": "none",
                    "description": "weight_tons exceeds 10,000, which is highly unusual",
                    "sample_row_ids": shipments_df[high_weight]["shipment_id"]
                    .head()
                    .tolist(),
                }
            )

    # Check: Missing status (Warning - requires normalisation mapping, or Info)
    if "status" in shipments_df.columns:
        missing_status = shipments_df["status"].isnull()
        num_missing_status = missing_status.sum()
        if num_missing_status > 0:
            results.append(
                {
                    "check_id": "SHIPMENTS_MISSING_STATUS",
                    "dataset": "shipments",
                    "check_name": "Missing Status",
                    "severity": "Info",
                    "rows_affected": int(num_missing_status),
                    "percentage_affected": float(num_missing_status / shipments_len),
                    "action": "none",
                    "description": "Status field is missing",
                    "sample_row_ids": shipments_df[missing_status]["shipment_id"]
                    .head()
                    .tolist(),
                }
            )

    # 3. Events Checks
    events_len = len(events_df)

    # Check: Missing event_type
    missing_event_type = events_df["event_type"].isnull()
    num_missing_event = missing_event_type.sum()
    if num_missing_event > 0:
        results.append(
            {
                "check_id": "EVENTS_MISSING_TYPE",
                "dataset": "port_events",
                "check_name": "Missing Event Type",
                "severity": "Critical",
                "rows_affected": int(num_missing_event),
                "percentage_affected": float(num_missing_event / events_len),
                "action": "quarantine",
                "description": "event_type is required",
                "sample_row_ids": events_df[missing_event_type]["event_id"]
                .head()
                .tolist(),
            }
        )

    # Check: Invalid port reference in events
    event_port_col = "port_code" if "port_code" in events_df.columns else "port"
    invalid_event_port = ~events_df[event_port_col].isin(valid_ports)
    num_invalid_event_port = invalid_event_port.sum()
    if num_invalid_event_port > 0:
        results.append(
            {
                "check_id": "EVENTS_INVALID_PORT",
                "dataset": "port_events",
                "check_name": "Invalid Port Reference",
                "severity": "Critical",
                "rows_affected": int(num_invalid_event_port),
                "percentage_affected": float(num_invalid_event_port / events_len),
                "action": "quarantine",
                "description": "Event port not found in ports dataset",
                "sample_row_ids": events_df[invalid_event_port]["event_id"]
                .head()
                .tolist(),
            }
        )

    return results
