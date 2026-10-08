from typing import Any

from api_interface.repositories.db import get_db_connection


def get_route_stats(origin: str, destination: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM route_statistics WHERE origin_port = ? AND destination_port = ?",
        [origin, destination],
    )
    rows = cursor.fetchall()
    if not rows:
        return None

    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, rows[0]))
