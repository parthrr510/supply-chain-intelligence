from unittest.mock import MagicMock, patch

import pytest

from api_interface.api.errors import APIError
from api_interface.services.prediction_service import (
    ModelUnavailableError,
    PredictionService,
)


def test_missing_artifact():
    service = PredictionService(model_path="nonexistent.joblib")
    with pytest.raises(ModelUnavailableError):
        service.predict_delay("SHIP123")


@patch("api_interface.services.prediction_service.shipment_service")
@patch("api_interface.services.prediction_service.joblib")
@patch("api_interface.services.prediction_service.get_db_connection")
@patch("pathlib.Path.exists")
def test_successful_prediction(
    mock_exists, mock_db, mock_joblib, mock_shipment_service
):
    mock_exists.return_value = True

    mock_model = MagicMock()
    mock_model.predict_proba.return_value = [[0.2, 0.8]]
    mock_joblib.load.return_value = mock_model

    # Mock shipment
    from datetime import datetime

    mock_shipment_service.get_shipment.return_value = {
        "shipment_id": "SHIP123",
        "origin_port": "USLAX",
        "destination_port": "CNSHA",
        "vessel_id": "VES001",
        "cargo_type": "FCL",
        "container_count": 5,
        "weight_tons": 100.0,
        "transit_days_planned": 14.5,
        "booking_date": datetime(2023, 1, 15),
    }

    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.execute.return_value.fetchone.return_value = [5.0]

    service = PredictionService()
    result = service.predict_delay("SHIP123", threshold=0.5)

    assert result["probability"] == 0.8
    assert result["prediction"] is True
    assert result["threshold"] == 0.5
    assert result["model_version"] == "1.0"

    # Verify extraction
    df = mock_model.predict_proba.call_args[0][0]
    assert df["origin_port"][0] == "USLAX"
    assert df["booking_month"][0] == 1

    # Verify no leakage features
    assert "actual_arrival" not in df.columns
    assert "actual_delay_hours" not in df.columns
    assert "on_time_flag" not in df.columns


@patch("api_interface.services.prediction_service.shipment_service")
@patch("pathlib.Path.exists")
def test_missing_shipment(mock_exists, mock_shipment_service):
    mock_exists.return_value = True
    mock_shipment_service.get_shipment.side_effect = APIError(
        "SHIPMENT_NOT_FOUND", "not found", 404
    )

    service = PredictionService()
    # model isn't loaded until needed but since get_shipment is after load_model
    # wait we need to mock load_model to not fail
    with patch.object(PredictionService, "load_model"):
        with pytest.raises(APIError) as exc_info:
            service.predict_delay("INVALID")
        assert exc_info.value.code == "SHIPMENT_NOT_FOUND"


@patch("api_interface.services.prediction_service.shipment_service")
@patch("api_interface.services.prediction_service.joblib")
@patch("api_interface.services.prediction_service.get_db_connection")
@patch("pathlib.Path.exists")
def test_threshold_behavior(mock_exists, mock_db, mock_joblib, mock_shipment_service):
    mock_exists.return_value = True

    mock_model = MagicMock()
    mock_model.predict_proba.return_value = [[0.6, 0.4]]
    mock_joblib.load.return_value = mock_model

    from datetime import datetime

    mock_shipment_service.get_shipment.return_value = {
        "shipment_id": "SHIP123",
        "booking_date": datetime(2023, 1, 15),
    }

    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.execute.return_value.fetchone.return_value = [5.0]

    service = PredictionService()

    # With threshold 0.5, 0.4 is False
    result1 = service.predict_delay("SHIP123", threshold=0.5)
    assert result1["prediction"] is False

    # With threshold 0.3, 0.4 is True
    result2 = service.predict_delay("SHIP123", threshold=0.3)
    assert result2["prediction"] is True
