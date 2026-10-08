from datetime import date
from typing import Any

from api_interface.api.errors import APIError
from api_interface.repositories import shipment_repository


def get_shipments(
    origin: str | None = None,
    destination: str | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    if start_date and end_date and start_date > end_date:
        raise APIError("INVALID_DATE_RANGE", "start_date cannot be after end_date", 400)

    if page < 1:
        raise APIError(
            "INVALID_REQUEST", "page must be greater than or equal to 1", 400
        )

    if page_size < 1 or page_size > 100:
        raise APIError("INVALID_REQUEST", "page_size must be between 1 and 100", 400)

    return shipment_repository.get_shipments(
        origin=origin,
        destination=destination,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


def get_shipment(shipment_id: str) -> dict[str, Any]:
    shipment = shipment_repository.get_shipment_by_id(shipment_id)
    if not shipment:
        raise APIError(
            "SHIPMENT_NOT_FOUND", f"Shipment {shipment_id} was not found", 404
        )
    return shipment
