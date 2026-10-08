import logging

from fastapi import APIRouter

from api_interface.api.errors import APIError
from api_interface.api.schemas import DelayPredictionRequest, DelayPredictionResponse
from api_interface.services.prediction_service import (
    ModelUnavailableError,
    prediction_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predictions"])


@router.post("/predict-delay", response_model=DelayPredictionResponse)
def predict_delay(request: DelayPredictionRequest):
    try:
        result = prediction_service.predict_delay(request.shipment_id)
        return DelayPredictionResponse(**result)
    except ModelUnavailableError as e:
        logger.error(f"Model unavailable: {e}")
        raise APIError(
            "MODEL_UNAVAILABLE", "Prediction model is currently unavailable", 503
        )
    except APIError:
        raise
    except Exception:
        logger.exception("Internal inference failure")
        raise APIError("INTERNAL_ERROR", "Internal inference failure", 500)
