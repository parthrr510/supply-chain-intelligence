from fastapi import APIRouter

from api_interface.api.schemas import RouteStats
from api_interface.services import route_service

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/{origin}/{destination}/stats", response_model=RouteStats)
def get_route_stats(origin: str, destination: str):
    return route_service.get_route_stats(origin, destination)
