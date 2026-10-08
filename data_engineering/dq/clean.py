from pathlib import Path

import pandas as pd


def _save_quarantine(df: pd.DataFrame, reason: str, output_path: Path):
    if df.empty:
        return
    q_df = df.copy()
    q_df["quarantine_reason"] = reason

    # Append if exists
    if output_path.exists():
        q_df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        q_df.to_csv(output_path, index=False)


def normalize_status(status: pd.Series) -> pd.Series:
    # Known aliases: COMPLETED, Complete -> DELIVERED
    # and normalize whitespace/case
    s = status.astype(str).str.strip().str.upper()
    mapping = {
        "COMPLETED": "DELIVERED",
        "COMPLETE": "DELIVERED",
        "DELIVERED": "DELIVERED",
        "IN_TRANSIT": "IN_TRANSIT",
        "IN TRANSIT": "IN_TRANSIT",
        "PENDING": "PENDING",
        "CANCELLED": "CANCELLED",
    }
    return s.map(lambda x: mapping.get(x, x)).replace("NAN", pd.NA)


def normalize_dataframe_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(["object"]).columns:
        df[col] = (
            df[col].astype(str).str.strip().replace("nan", pd.NA).replace("None", pd.NA)
        )
    return df


def clean_ports(ports_df: pd.DataFrame, quarantine_dir: Path) -> pd.DataFrame:
    df = ports_df.copy()
    df = normalize_dataframe_strings(df)

    # 1. Exact duplicates removal
    df = df.drop_duplicates()

    # 2. Conflicting duplicates (Duplicate port_code but different other fields)
    dup_ports = df.duplicated(subset=["port_code"], keep=False)
    if dup_ports.any():
        _save_quarantine(
            df[dup_ports],
            "PORTS_CONFLICTING_DUPLICATES",
            quarantine_dir / "ports_quarantined.csv",
        )
        df = df[~dup_ports]

    return df


def clean_shipments(
    shipments_df: pd.DataFrame, valid_ports: set, quarantine_dir: Path
) -> pd.DataFrame:
    df = shipments_df.copy()
    df = normalize_dataframe_strings(df)

    if "status" in df.columns:
        df["status"] = normalize_status(df["status"])

    # 1. Exact duplicates removal
    df = df.drop_duplicates()

    # 2. Conflicting duplicates
    dup_ids = df.duplicated(subset=["shipment_id"], keep=False)
    if dup_ids.any():
        _save_quarantine(
            df[dup_ids],
            "SHIPMENTS_CONFLICTING_DUPLICATES",
            quarantine_dir / "shipments_quarantined.csv",
        )
        df = df[~dup_ids]

    # 3. Invalid Port References
    invalid_origin = ~df["origin_port"].isin(valid_ports)
    if invalid_origin.any():
        _save_quarantine(
            df[invalid_origin],
            "SHIPMENTS_INVALID_ORIGIN_PORT",
            quarantine_dir / "shipments_quarantined.csv",
        )
        df = df[~invalid_origin]

    invalid_dest = ~df["destination_port"].isin(valid_ports)
    if invalid_dest.any():
        _save_quarantine(
            df[invalid_dest],
            "SHIPMENTS_INVALID_DESTINATION_PORT",
            quarantine_dir / "shipments_quarantined.csv",
        )
        df = df[~invalid_dest]

    # 4. Negative Weight (Warning -> Fix)
    if "weight_tons" in df.columns:
        # Convert to numeric first
        df["weight_tons"] = pd.to_numeric(df["weight_tons"], errors="coerce")
        negative_weight = df["weight_tons"] < 0
        if negative_weight.any():
            _save_quarantine(
                df[negative_weight],
                "SHIPMENTS_NEGATIVE_WEIGHT_FIXED",
                quarantine_dir / "shipments_quarantined.csv",
            )
            df.loc[negative_weight, "weight_tons"] = df.loc[
                negative_weight, "weight_tons"
            ].abs()

    # Note: Missing actual dates are valid. High weight is info, so no quarantine.

    return df


def clean_events(
    events_df: pd.DataFrame, valid_ports: set, quarantine_dir: Path
) -> pd.DataFrame:
    df = events_df.copy()

    # Standardize column name if needed
    if "port" in df.columns and "port_code" not in df.columns:
        df = df.rename(columns={"port": "port_code"})

    df = normalize_dataframe_strings(df)

    # 1. Exact duplicates removal
    df = df.drop_duplicates()

    # 2. Conflicting duplicates
    dup_ids = df.duplicated(subset=["event_id"], keep=False)
    if dup_ids.any():
        _save_quarantine(
            df[dup_ids],
            "EVENTS_CONFLICTING_DUPLICATES",
            quarantine_dir / "port_events_quarantined.csv",
        )
        df = df[~dup_ids]

    # 3. Missing event_type
    missing_type = df["event_type"].isnull()
    if missing_type.any():
        _save_quarantine(
            df[missing_type],
            "EVENTS_MISSING_TYPE",
            quarantine_dir / "port_events_quarantined.csv",
        )
        df = df[~missing_type]

    # 4. Invalid port reference
    invalid_port = ~df["port_code"].isin(valid_ports)
    if invalid_port.any():
        _save_quarantine(
            df[invalid_port],
            "EVENTS_INVALID_PORT",
            quarantine_dir / "port_events_quarantined.csv",
        )
        df = df[~invalid_port]

    return df


def process_and_clean_data(
    ports_df: pd.DataFrame,
    shipments_df: pd.DataFrame,
    events_df: pd.DataFrame,
    quarantine_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Ensure quarantine dir exists and clear previous files for determinism
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    for f in quarantine_dir.glob("*_quarantined.csv"):
        f.unlink()

    clean_p = clean_ports(ports_df, quarantine_dir)

    valid_ports = set(clean_p["port_code"].dropna())

    clean_s = clean_shipments(shipments_df, valid_ports, quarantine_dir)
    clean_e = clean_events(events_df, valid_ports, quarantine_dir)

    return clean_p, clean_s, clean_e
