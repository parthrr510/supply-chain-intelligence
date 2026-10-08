from unittest.mock import patch

from fastapi.testclient import TestClient

from api_interface.api.errors import APIError
from api_interface.api.main import app
from api_interface.services.prediction_service import ModelUnavailableError

client = TestClient(app)


@patch("api_interface.api.routers.predictions.prediction_service")
def test_predict_delay_success(mock_prediction_service):
    mock_prediction_service.predict_delay.return_value = {
        "probability": 0.85,
        "prediction": True,
        "threshold": 0.5,
        "model_version": "1.0",
    }

    response = client.post("/predict-delay", json={"shipment_id": "SHIP123"})
    assert response.status_code == 200
    data = response.json()
    assert data["probability"] == 0.85
    assert data["prediction"] is True
    assert data["threshold"] == 0.5
    assert data["model_version"] == "1.0"


@patch("api_interface.api.routers.predictions.prediction_service")
def test_predict_delay_unknown_shipment(mock_prediction_service):
    mock_prediction_service.predict_delay.side_effect = APIError(
        "SHIPMENT_NOT_FOUND", "not found", 404
    )

    response = client.post("/predict-delay", json={"shipment_id": "INVALID"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SHIPMENT_NOT_FOUND"


@patch("api_interface.api.routers.predictions.prediction_service")
def test_predict_delay_model_unavailable(mock_prediction_service):
    mock_prediction_service.predict_delay.side_effect = ModelUnavailableError(
        "Not found"
    )

    response = client.post("/predict-delay", json={"shipment_id": "SHIP123"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_UNAVAILABLE"


def test_predict_delay_invalid_request():
    # Missing shipment_id
    response = client.post("/predict-delay", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@patch("api_interface.api.routers.predictions.prediction_service")
def test_predict_delay_internal_error(mock_prediction_service):
    mock_prediction_service.predict_delay.side_effect = Exception("Boom")

    response = client.post("/predict-delay", json={"shipment_id": "SHIP123"})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
