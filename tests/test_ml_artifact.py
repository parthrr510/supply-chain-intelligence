from pathlib import Path

import joblib
import pandas as pd
import pytest


def test_model_artifact_reload():
    model_path = Path("machine_learning/artifacts/delay_model.joblib")
    if not model_path.exists():
        pytest.skip("Model artifact not found, run training first")

    pipeline = joblib.load(model_path)

    # Dummy row with expected features
    dummy_data = pd.DataFrame(
        [
            {
                "origin_port": "PORT_A",
                "destination_port": "PORT_B",
                "vessel_id": "V1",
                "cargo_type": "Electronics",
                "container_count": 10.0,
                "weight_tons": 50.0,
                "planned_transit_days": 5.0,
                "origin_congestion_score": 0.5,
                "destination_congestion_score": 0.8,
                "booking_month": 1,
                "booking_day_of_week": 1,
            }
        ]
    )

    # Should predict without error
    proba = pipeline.predict_proba(dummy_data)
    assert proba.shape == (1, 2)

    pred = pipeline.predict(dummy_data)
    assert pred.shape == (1,)
    assert pred[0] in [0, 1]
