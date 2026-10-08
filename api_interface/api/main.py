import json
import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api_interface.api.config import settings
from api_interface.api.errors import (
    APIError,
    api_error_handler,
    generic_exception_handler,
)
from api_interface.repositories.db import check_db_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Supply Chain API", version="1.0.0")

from api_interface.api.routers import dq, predictions, routes, shipments
from api_interface.services.prediction_service import (
    ModelUnavailableError,
    prediction_service,
)

app.include_router(shipments.router)
app.include_router(routes.router)
app.include_router(dq.router)
app.include_router(predictions.router)


@app.on_event("startup")
def load_ml_model():
    try:
        prediction_service.load_model()
        logger.info("ML model loaded successfully")
    except ModelUnavailableError as e:
        logger.warning(f"ML model not available at startup: {e}")


app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": str(exc),
                "request_id": request_id,
            }
        },
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
        except Exception:
            logger.exception("Unhandled exception in middleware")
            raise
        finally:
            latency_ms = (time.time() - start_time) * 1000
            status_code = response.status_code if "response" in locals() else 500

            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime()),
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "request_id": request_id,
            }
            logger.info(json.dumps(log_entry))

        return response


app.add_middleware(RequestLoggingMiddleware)


@app.get("/health")
async def health_check():
    db_ok = check_db_health()
    model_ok = Path(settings.model_path).exists()

    status_code = 200 if (db_ok and model_ok) else 503
    status = "healthy" if (db_ok and model_ok) else "unhealthy"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "version": "1.0.0",
            "checks": {
                "database": "ok" if db_ok else "error",
                "model": "ok" if model_ok else "error",
            },
        },
    )
