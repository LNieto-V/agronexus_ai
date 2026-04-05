from fastapi import APIRouter, HTTPException
import logging
from app.schemas import IOTTelemetryRequest, IOTTelemetryResponse
from app.services.iot_service import process_automated_telemetry
from app.api.deps import WriteKey

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/iot", tags=["iot"])

@router.post("/telemetry", response_model=IOTTelemetryResponse)
async def telemetry(request: IOTTelemetryRequest, user_id: WriteKey) -> IOTTelemetryResponse:
    """Endpoint para telemetría de hardware (ESP32)."""
    try:
        sensor_data = request.sensor_data.model_dump()
        actions, alerts = await process_automated_telemetry(sensor_data, user_id)
        return IOTTelemetryResponse(actions=actions, alerts=alerts)
    except Exception as e:
        if "CUOTA_AGOTADA" in str(e):
            raise HTTPException(status_code=429, detail="Límite alcanzado.")
        logger.error(f"Error en telemetría IoT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error de hardware.")
