import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("api")


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


async def api_error_handler(request: Request, exc: APIError):
    request_id = (
        request.state.request_id if hasattr(request.state, "request_id") else "unknown"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    request_id = (
        request.state.request_id if hasattr(request.state, "request_id") else "unknown"
    )
    logger.exception("Internal error")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "request_id": request_id,
            }
        },
    )
