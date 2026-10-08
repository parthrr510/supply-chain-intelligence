from datetime import date

from fastapi import APIRouter, Query

from api_interface.api.schemas import Shipment, ShipmentListResponse
from api_interface.services import shipment_service

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", response_model=ShipmentListResponse)
def get_shipments(
    origin: str | None = None,
    destination: str | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = shipment_service.get_shipments(
        origin=origin,
        destination=destination,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return ShipmentListResponse(
        items=items, page=page, page_size=page_size, total=total
    )


@router.get("/{id}", response_model=Shipment)
def get_shipment(id: str):
    return shipment_service.get_shipment(id)
