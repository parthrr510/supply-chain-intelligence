from datetime import date
from typing import Any

from langchain_core.tools import tool

from api_interface.services.prediction_service import prediction_service
from api_interface.services.route_service import (
    get_route_stats as _service_get_route_stats,
)
from api_interface.services.shipment_service import get_shipments


@tool
def query_shipments(
    origin: str | None = None,
    destination: str | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query shipments with bounded filters.

    Args:
        origin: Origin port code
        destination: Destination port code
        status: Shipment status
        start_date: Start date for planned departure (YYYY-MM-DD)
        end_date: End date for planned departure (YYYY-MM-DD)
        page_size: Maximum number of shipments to return (max 20)
    """
    page_size = min(page_size, 20)

    try:
        s_date = date.fromisoformat(start_date) if start_date else None
        e_date = date.fromisoformat(end_date) if end_date else None

        items, total = get_shipments(
            origin=origin,
            destination=destination,
            status=status,
            start_date=s_date,
            end_date=e_date,
            page=1,
            page_size=page_size,
        )
        return {
            "shipments": items,
            "total_matches": total,
            "returned_count": len(items),
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def get_route_stats(
    origin: str, destination: str, date_range: str | None = None
) -> dict[str, Any]:
    """Get statistics for a specific route.

    Args:
        origin: Origin port code
        destination: Destination port code
        date_range: Optional date range description (e.g. 'this quarter')
    """
    try:
        stats = _service_get_route_stats(origin=origin, destination=destination)
        return stats
    except Exception as e:
        return {"error": str(e)}


@tool
def predict_delay(shipment_id: str) -> dict[str, Any]:
    """Predict if a shipment will be delayed.

    Args:
        shipment_id: The ID of the shipment
    """
    try:
        result = prediction_service.predict_delay(shipment_id)
        return result
    except Exception as e:
        return {"error": str(e)}


import os

import duckdb


@tool
def search_ports(query: str) -> dict[str, Any]:
    """Search for the exact UN/LOCODE port code for a given city or country name.

    Args:
        query: The name of the city or port (e.g. 'Shanghai', 'Rotterdam')
    """
    try:
        db_path = os.getenv(
            "DATABASE_PATH", "data_engineering/data/curated/supply_chain.db"
        )
        conn = duckdb.connect(db_path, read_only=True)
        # Search by name ignoring case
        df = conn.execute(
            "SELECT port_code, name, country FROM ports WHERE name ILIKE ?",
            [f"%{query}%"],
        ).df()
        conn.close()

        if df.empty:
            return {"error": f"No ports found matching '{query}'"}

        return {"ports": df.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}


def get_gemini_tools() -> list:
    """Return the list of tool functions for Langchain."""
    return [query_shipments, get_route_stats, predict_delay, search_ports]
