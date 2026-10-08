from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Shipment(BaseModel):
    shipment_id: str
    customer_id: str | None = None
    origin_port: str | None = None
    destination_port: str | None = None
    vessel_id: str | None = None
    booking_date: datetime | None = None
    planned_departure: datetime | None = None
    actual_departure: datetime | None = None
    planned_arrival: datetime | None = None
    actual_arrival: datetime | None = None
    container_count: float | None = None
    cargo_type: str | None = None
    weight_tons: float | None = None
    status: str | None = None
    actual_delay_hours: float | None = None
    on_time_flag: bool | None = None
    route_key: str | None = None
    transit_days_planned: float | None = None
    transit_days_actual: float | None = None

    model_config = ConfigDict(from_attributes=True)


class ShipmentListResponse(BaseModel):
    items: list[Shipment]
    page: int
    page_size: int
    total: int


class RouteStats(BaseModel):
    origin: str
    destination: str
    shipment_count: int
    average_delay_hours: float | None = None
    on_time_rate: float | None = None


class DelayPredictionRequest(BaseModel):
    shipment_id: str


class DelayPredictionResponse(BaseModel):
    probability: float
    prediction: bool
    threshold: float
    model_version: str
