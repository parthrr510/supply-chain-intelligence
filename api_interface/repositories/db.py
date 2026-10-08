import duckdb

from api_interface.api.config import settings

_conn = None


def get_db_connection() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        _conn = duckdb.connect(settings.database_path, read_only=True)
    return _conn


def check_db_health() -> bool:
    try:
        conn = duckdb.connect(settings.database_path, read_only=True)
        conn.execute("SELECT 1").fetchall()
        conn.close()
        return True
    except Exception:
        return False
