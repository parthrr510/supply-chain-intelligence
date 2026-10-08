from datetime import date
from typing import Any

from api_interface.repositories.db import get_db_connection


def _fetch_dicts(query: str, params: list | None = None) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.execute(query, params or [])
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_shipment_by_id(shipment_id: str) -> dict[str, Any] | None:
    rows = _fetch_dicts("SELECT * FROM shipments WHERE shipment_id = ?", [shipment_id])
    if not rows:
        return None
    return rows[0]


def get_shipments(
    origin: str | None = None,
    destination: str | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    conn = get_db_connection()

    query = "SELECT * FROM shipments WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM shipments WHERE 1=1"
    params = []

    if origin:
        query += " AND origin_port = ?"
        count_query += " AND origin_port = ?"
        params.append(origin)
    if destination:
        query += " AND destination_port = ?"
        count_query += " AND destination_port = ?"
        params.append(destination)
    if status:
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)
    if start_date:
        query += " AND CAST(planned_departure AS DATE) >= ?"
        count_query += " AND CAST(planned_departure AS DATE) >= ?"
        params.append(start_date.isoformat())
    if end_date:
        query += " AND CAST(planned_departure AS DATE) <= ?"
        count_query += " AND CAST(planned_departure AS DATE) <= ?"
        params.append(end_date.isoformat())

    total_count = conn.execute(count_query, params).fetchone()[0]

    offset = (page - 1) * page_size
    query += " ORDER BY planned_departure DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    rows = _fetch_dicts(query, params)

    return rows, total_count
