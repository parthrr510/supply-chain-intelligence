from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from api_interface.repositories.db import get_db_connection
from api_interface.services import shipment_service


class ModelUnavailableError(Exception):
    pass


class PredictionService:
    def __init__(self, model_path: str | Path = "machine_learning/artifacts/delay_model.joblib"):
        self.model_path = Path(model_path)
        self.model = None
        self.model_version = "1.0"

    def load_model(self):
        if not self.model_path.exists():
            raise ModelUnavailableError(
                f"Model artifact not found at {self.model_path}"
            )
        self.model = joblib.load(self.model_path)

    def _get_port_congestion(self, port_code: str) -> float | None:
        if not port_code:
            return None
        conn = get_db_connection()
        row = conn.execute(
            "SELECT average_congestion_score FROM ports WHERE port_code = ?",
            [port_code],
        ).fetchone()
        return row[0] if row else None

    def predict_delay(self, shipment_id: str, threshold: float = 0.5) -> dict[str, Any]:
        if self.model is None:
            self.load_model()

        shipment = shipment_service.get_shipment(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")

        origin_port = shipment.get("origin_port")
        destination_port = shipment.get("destination_port")

        origin_congestion = self._get_port_congestion(origin_port)
        dest_congestion = self._get_port_congestion(destination_port)

        booking_date = shipment.get("booking_date")
        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date)

        if booking_date:
            booking_month = booking_date.month
            booking_day_of_week = booking_date.isoweekday()
        else:
            booking_month = None
            booking_day_of_week = None

        features = {
            "origin_port": [origin_port],
            "destination_port": [destination_port],
            "vessel_id": [shipment.get("vessel_id")],
            "cargo_type": [shipment.get("cargo_type")],
            "container_count": [shipment.get("container_count")],
            "weight_tons": [shipment.get("weight_tons")],
            "planned_transit_days": [shipment.get("transit_days_planned")],
            "origin_congestion_score": [origin_congestion],
            "destination_congestion_score": [dest_congestion],
            "booking_month": [booking_month],
            "booking_day_of_week": [booking_day_of_week],
        }

        df = pd.DataFrame(features)

        prob = self.model.predict_proba(df)[0][1]

        return {
            "probability": float(prob),
            "prediction": bool(prob >= threshold),
            "threshold": threshold,
            "model_version": self.model_version,
        }


prediction_service = PredictionService()
