from fastapi import APIRouter, HTTPException
import logging
from app.schemas import IOTTelemetryRequest, IOTTelemetryResponse
from app.modules.chat.services.ai_orchestrator import process_automated_telemetry
from app.api.deps import WriteKey, IoT, CurrentUser
from fastapi.responses import StreamingResponse
import asyncio
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/iot", tags=["iot"])

# In-memory bus for SSE (Performance optimized for single-instance/dev)
# En producción usar Supabase Realtime o Redis
class TelemetryBus:
    def __init__(self):
        self.subscribers = []

    async def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self.subscribers.remove(queue)

    async def broadcast(self, data: dict):
        for queue in self.subscribers:
            await queue.put(data)

telemetry_bus = TelemetryBus()

@router.post("/telemetry", response_model=IOTTelemetryResponse)
async def telemetry(request: IOTTelemetryRequest, key_meta: WriteKey, iot: IoT) -> IOTTelemetryResponse:
    """Endpoint para telemetría de hardware (ESP32)."""
    user_id = key_meta["user_id"]
    key_zone_id = key_meta.get("zone_id")
    
    # Resolver la zona: Preferencia a la de la llave si esta restringida
    target_zone = request.zone_id
    if key_zone_id:
        if target_zone and target_zone != key_zone_id:
            logger.warning(f"Intento de posteo en zona cruzada: Key({key_zone_id}) -> Req({target_zone})")
            raise HTTPException(status_code=403, detail="Esta API Key solo tiene permisos para su zona asignada.")
        target_zone = key_zone_id

    try:
        sensor_data = request.sensor_data.model_dump()
        # Inyectar zone_id en los datos para el repositorio
        sensor_data["zone_id"] = target_zone
        
        # 1. Persistir en base de datos
        await iot.insert_sensor_data(sensor_data, user_id)
        
        # 2. Actualizar estado de la zona a ONLINE
        if target_zone:
            await iot.update_zone_heartbeat(target_zone)

        # 3. Broadcast para SSE (Real-Time) incluye info de zona
        asyncio.create_task(telemetry_bus.broadcast({
            "user_id": user_id, 
            "zone_id": target_zone,
            "data": sensor_data
        }))
        
        actions, alerts = await process_automated_telemetry(sensor_data, user_id)
        return IOTTelemetryResponse(actions=actions, alerts=alerts)
    except Exception as e:
        if "CUOTA_AGOTADA" in str(e):
            raise HTTPException(status_code=429, detail="Límite alcanzado.")
        logger.error(f"Error en telemetría IoT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error de hardware.")

@router.get("/stream")
async def stream_telemetry(user: CurrentUser):
    """Canal SSE para recibir telemetría en tiempo real."""
    async def event_generator():
        async for msg in telemetry_bus.subscribe():
            if msg["user_id"] == user["id"]:
                yield f"data: {json.dumps(msg['data'])}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
