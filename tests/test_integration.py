import json
import os
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

# Override env vars before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_PATH"] = "data_engineering/data/test_integration.duckdb"
os.environ["MODEL_PATH"] = "machine_learning/artifacts/delay_model.joblib"
# Create dummy model for the integration test
dummy_model_path = Path(os.environ["MODEL_PATH"])
if not dummy_model_path.exists():
    dummy_model_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_model_path.touch()
    # We will mock the prediction service inner call to avoid needing a real model artifact

from unittest.mock import patch

from api_interface.api.main import app
from data_engineering.pipeline.ingest import init_schema


@pytest.fixture(scope="module")
def test_db():
    db_path = Path("data_engineering/data/test_integration.duckdb")
    if db_path.exists():
        db_path.unlink()

    conn = duckdb.connect(str(db_path))
    init_schema(conn)

    # insert fixtures
    conn.execute("""
    INSERT INTO shipments (shipment_id, customer_id, origin_port, destination_port, vessel_id, 
                           booking_date, planned_departure, status, actual_delay_hours, on_time_flag)
    VALUES 
    ('SHP-INT-1', 'CUST-1', 'USLAX', 'JPTYO', 'VSL-1', '2023-01-01', '2023-01-05', 'DELIVERED', 5.0, true),
    ('SHP-INT-2', 'CUST-1', 'USLAX', 'JPTYO', 'VSL-1', '2023-01-02', '2023-01-06', 'PENDING', 10.0, true)
    """)

    conn.execute("""
    INSERT INTO ports (port_code, name, country, region, timezone, average_congestion_score)
    VALUES ('USLAX', 'Los Angeles', 'USA', 'North America', 'PST', 0.5)
    """)

    # route_statistics view uses shipments

    conn.close()

    yield

    # teardown
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="module")
def client(test_db, tmp_path_factory):
    db_path = Path("data_engineering/data/test_integration.duckdb")
    # connect to test db for the client (not read_only so we can use same file concurrently or just read_only=True)
    conn = duckdb.connect(str(db_path), read_only=True)

    tmp_dir = tmp_path_factory.mktemp("reports")
    tmp_dq_path = tmp_dir / "dq_report.json"
    with open(tmp_dq_path, "w") as f:
        json.dump({"report_version": "1.0", "findings": []}, f)

    with (
        patch(
            "api_interface.services.prediction_service.prediction_service.predict_delay"
        ) as mock_predict,
        patch(
            "api_interface.repositories.shipment_repository.get_db_connection",
            return_value=conn,
        ),
        patch(
            "api_interface.repositories.route_repository.get_db_connection",
            return_value=conn,
        ),
        patch("api_interface.api.routers.dq.settings.dq_report_path", str(tmp_dq_path)),
    ):
        mock_predict.return_value = {
            "probability": 0.9,
            "prediction": True,
            "threshold": 0.5,
            "model_version": "1.0",
        }
        with TestClient(app) as c:
            yield c

    conn.close()


def test_integration_health(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_integration_shipment_lookup(client):
    response = client.get("/shipments/SHP-INT-1")
    assert response.status_code == 200
    assert response.json()["shipment_id"] == "SHP-INT-1"


def test_integration_unknown_shipment(client):
    response = client.get("/shipments/UNKNOWN_ID")
    assert response.status_code == 404


def test_integration_dq_report(client):
    response = client.get("/data-quality/report")
    assert response.status_code == 200


def test_integration_predict_delay(client):
    response = client.post("/predict-delay", json={"shipment_id": "SHP-INT-1"})
    assert response.status_code == 200
    assert response.json()["prediction"] is True


def test_integration_shipment_filters_and_pagination(client):
    response = client.get("/shipments?origin=USLAX&page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1


def test_integration_route_stats(client):
    response = client.get("/routes/USLAX/JPTYO/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["shipment_count"] == 2
    assert data["origin"] == "USLAX"


def test_integration_invalid_request(client):
    response = client.post("/predict-delay", json={})
    assert response.status_code == 422
