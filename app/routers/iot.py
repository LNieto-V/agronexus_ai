from fastapi import APIRouter, HTTPException
import logging
from app.schemas import IOTTelemetryRequest, IOTTelemetryResponse
from app.services.iot_service import process_automated_telemetry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/iot", tags=["iot"])

@router.post("/telemetry", response_model=IOTTelemetryResponse)
async def telemetry(request: IOTTelemetryRequest) -> IOTTelemetryResponse:
    """
    Endpoint para telemetría de hardware (ESP32).
    Recibe datos de sensores, los guarda en Supabase y devuelve acciones si es necesario.
    """
    try:
        sensor_data = request.sensor_data.model_dump()
        actions, alerts = await process_automated_telemetry(sensor_data)
        
        return IOTTelemetryResponse(
            actions=actions,
            alerts=alerts
        )
    except Exception as e:
        if "CUOTA_AGOTADA" in str(e):
            raise HTTPException(
                status_code=429,
                detail="Límite de IA alcanzado. Por favor, reintenta más tarde."
            )
        logger.error(f"Error procesando telemetría IoT: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Error procesando telemetría del hardware."
        )
