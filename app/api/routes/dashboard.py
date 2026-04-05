from fastapi import APIRouter, HTTPException
import logging
from typing import List, Dict, Any
from app.schemas import SystemModeUpdate
from app.services.state_service import backend_state
from app.api.deps import CurrentUser, DBService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/latest", response_model=Dict[str, Any])
async def get_latest_data(user: CurrentUser, db: DBService):
    """Obtiene los últimos datos de sensores filtrados por usuario."""
    try:
        return await db.get_latest_sensors(user["id"])
    except Exception as e:
        logger.error(f"Error en dashboard latest: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo últimos sensores.")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history_data(user: CurrentUser, db: DBService):
    """Obtiene el historial reciente filtrado por usuario."""
    try:
        return await db.get_sensor_history_raw(user["id"])
    except Exception as e:
        logger.error(f"Error en dashboard history: {e}")
        return []

@router.get("/state")
async def get_system_state(user: CurrentUser):
    """Obtiene el estado interno del sistema."""
    return await backend_state.get_state(user["id"])

@router.post("/mode")
async def update_system_mode(update: SystemModeUpdate, user: CurrentUser):
    """Cambia el modo de operación de forma persistente."""
    success = await backend_state.update_mode(user["id"], update.mode)
    if not success:
        raise HTTPException(status_code=400, detail="Modo inválido.")
    return {"status": "success", "new_mode": update.mode.upper()}
