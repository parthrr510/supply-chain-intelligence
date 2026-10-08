import numpy as np
import pandas as pd

from machine_learning.ml.pipeline import get_preprocessing_pipeline, split_data


def test_split_boundaries():
    # Create dummy dataframe of 100 rows
    df = pd.DataFrame({"val": range(100)})
    train_df, val_df, test_df = split_data(df)

    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15


def test_chronological_ordering():
    df = pd.DataFrame({"val": range(100)})
    train_df, val_df, test_df = split_data(df)

    # Since we use .iloc, order must be strictly preserved
    assert train_df["val"].iloc[-1] < val_df["val"].iloc[0]
    assert val_df["val"].iloc[-1] < test_df["val"].iloc[0]


def test_preprocessing_missing_values():
    pipeline = get_preprocessing_pipeline()

    # Create test data with missing values
    df = pd.DataFrame(
        {
            "origin_port": ["PORT_A", None],
            "destination_port": ["PORT_B", "PORT_C"],
            "vessel_id": ["V1", "V2"],
            "cargo_type": ["E", "A"],
            "container_count": [10.0, np.nan],
            "weight_tons": [np.nan, 20.0],
            "planned_transit_days": [5.0, 5.0],
            "origin_congestion_score": [0.5, 0.5],
            "destination_congestion_score": [0.5, np.nan],
            "booking_month": [1, 2],
            "booking_day_of_week": [1, 2],
        }
    )
    y = pd.Series([0, 1])

    # Should fit without errors despite missing values
    pipeline.fit(df, y)

    # Should transform without errors
    X_trans = pipeline.named_steps["preprocessor"].transform(df)
    # The output should have no NaNs
    assert not np.isnan(
        X_trans.toarray() if hasattr(X_trans, "toarray") else X_trans
    ).any()


def test_no_target_leakage_in_features():
    pipeline = get_preprocessing_pipeline()
    preprocessor = pipeline.named_steps["preprocessor"]

    features = []
    for name, transformer, cols in preprocessor.transformers:
        if isinstance(cols, list):
            features.extend(cols)

    leakage_cols = [
        "actual_departure",
        "actual_arrival",
        "actual_delay_hours",
        "on_time_flag",
        "target",
    ]

    for col in leakage_cols:
        assert col not in features, f"Leakage column {col} found in pipeline features!"
