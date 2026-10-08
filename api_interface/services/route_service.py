from typing import Any

from api_interface.repositories import route_repository


def get_route_stats(origin: str, destination: str) -> dict[str, Any]:
    stats = route_repository.get_route_stats(origin, destination)
    if stats:
        return {
            "origin": origin,
            "destination": destination,
            "shipment_count": stats.get("shipment_count", 0),
            "average_delay_hours": stats.get("average_delay_hours"),
            "on_time_rate": stats.get("on_time_rate"),
        }

    return {
        "origin": origin,
        "destination": destination,
        "shipment_count": 0,
        "average_delay_hours": None,
        "on_time_rate": None,
    }
