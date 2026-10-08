import json
from pathlib import Path

from fastapi import APIRouter

from api_interface.api.config import settings
from api_interface.api.errors import APIError

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


@router.get("/report")
def get_dq_report():
    report_path = Path(settings.dq_report_path)
    if not report_path.exists():
        raise APIError(
            "DQ_REPORT_UNAVAILABLE",
            "Data Quality report is currently unavailable.",
            404,
        )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise APIError(
            "INTERNAL_ERROR", "Failed to read Data Quality report.", 500
        ) from e
