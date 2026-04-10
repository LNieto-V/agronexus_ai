from fastapi import APIRouter, HTTPException, Depends
import logging
from typing import List, Dict, Any
from app.schemas import SystemModeUpdate
from app.modules.iot.services.state_service import backend_state
from app.api.deps import CurrentUser, IoT, Identity, require_role
from fastapi.responses import StreamingResponse
import io
import csv
import asyncio
import datetime
from app.core.utils.aggregators import aggregate_sensor_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])



@router.get("/latest", response_model=Dict[str, Any])
async def get_latest_data(user: CurrentUser, iot: IoT, zone_id: str = None):
    """Obtiene los últimos datos de sensores filtrados por usuario."""
    try:
        return await iot.get_latest_sensors(user["id"], zone_id)
    except Exception as e:
        logger.error(f"Error en dashboard latest: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo últimos sensores.")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history_data(user: CurrentUser, iot: IoT, zone_id: str = None):
    """Obtiene el historial reciente filtrado por usuario."""
    try:
        return await iot.get_sensor_history_raw(user["id"], zone_id=zone_id)
    except Exception as e:
        logger.error(f"Error en dashboard history: {e}")
        return []

@router.get("/state")
async def get_system_state(user: CurrentUser):
    """Obtiene el estado interno del sistema."""
    state = await backend_state.get_state(user["id"])
    # Mapeo para compatibilidad con el frontend (system_mode -> mode)
    return {
        **state,
        "mode": state.get("system_mode", "AUTO")
    }

@router.post("/mode", dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def update_system_mode(update: SystemModeUpdate, user: CurrentUser):
    """Cambia el modo de operación de forma persistente."""
    success = await backend_state.update_mode(user["id"], update.mode)
    if not success:
        raise HTTPException(status_code=400, detail="Modo inválido.")
    return {"status": "success", "new_mode": update.mode.upper()}

@router.get("/actuator-log", dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def get_actuator_logs(user: CurrentUser, iot: IoT, limit: int = 50, offset: int = 0, zone_id: str = None):
    """Obtiene el historial de acciones de los actuadores."""
    return await iot.get_actuator_logs(user["id"], limit, offset, zone_id)

@router.get("/stats")
async def get_stats(user: CurrentUser, iot: IoT, period: int = 24):
    """Obtiene estadísticas agregadas (min/max/avg)."""
    return await iot.get_stats(user["id"], period)

@router.get("/export", dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def export_data(user: CurrentUser, iot: IoT, period: int = 30):
    """Exporta historial de sensores a CSV (High Performance Streaming)."""
    data = await iot.get_sensor_history_raw(user["id"], limit=1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "temperature", "humidity", "light", "ph", "ec", 
        "soil_temperature", "soil_moisture", "vpd", "co2", "tank_level", 
        "created_at"
    ])
    
    for row in data:
        writer.writerow([
            row.get("id"), 
            row.get("temperature"), 
            row.get("humidity"), 
            row.get("light"), 
            row.get("ph"), 
            row.get("ec"),
            row.get("soil_temperature"),
            row.get("soil_moisture"),
            row.get("vpd"),
            row.get("co2"),
            row.get("tank_level"),
            row.get("created_at")
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=agronexus_export_{user['id'][:8]}.csv"}
    )

@router.get("/maintenance")
async def get_maintenance_logs(user: CurrentUser, iot: IoT):
    """Obtiene el historial de mantenimiento."""
    if not iot.client:
        return []
    res = await asyncio.get_event_loop().run_in_executor(None, lambda: iot.client.table("maintenance_log").select("*").eq("user_id", user["id"]).order("performed_at", desc=True).execute())
    return res.data or []

@router.get("/thresholds")
async def get_thresholds(user: CurrentUser, identity: Identity):
    """Obtiene umbrales de alerta (Solo lectura para todos)."""
    return await identity.get_alert_thresholds(user["id"])

@router.put("/thresholds", dependencies=[Depends(require_role(["owner"]))])
async def update_threshold(sensor_type: str, min_val: float, max_val: float, user: CurrentUser, identity: Identity):
    """Configura umbrales de alerta (Solo el Owner)."""
    return await identity.update_alert_threshold(user["id"], sensor_type, min_val, max_val)
