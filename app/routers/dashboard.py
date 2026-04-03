from fastapi import APIRouter, HTTPException, Depends
import logging
from typing import List, Dict, Any
from app.schemas import SystemModeUpdate
from app.services.supabase_service import supabase_db
from app.services.state_service import backend_state
from app.services.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/latest", response_model=Dict[str, Any])
async def get_latest_data(user = Depends(get_current_user)):
    """Obtiene los últimos datos de sensores filtrados por usuario."""
    try:
        latest = supabase_db.get_latest_sensors(user["id"])
        return latest
    except Exception as e:
        logger.error(f"Error en dashboard latest: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo últimos sensores.")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history_data(user = Depends(get_current_user)):
    """Obtiene el historial reciente filtrado por usuario."""
    try:
        if not supabase_db.client:
            return []
        response = supabase_db.client.table("sensor_data") \
            .select("*") \
            .eq("user_id", user["id"]) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error en dashboard history: {e}")
        return []

@router.get("/state")
async def get_system_state(user = Depends(get_current_user)):
    """Obtiene el estado interno del sistema."""
    return backend_state.get_state()

@router.post("/mode")
async def update_system_mode(update: SystemModeUpdate, user = Depends(get_current_user)):
    """Cambia el modo de operación (AUTO/MANUAL)."""
    success = backend_state.update_mode(update.mode)
    if not success:
        raise HTTPException(status_code=400, detail="Modo inválido. Use AUTO o MANUAL.")
    return {"status": "success", "new_mode": backend_state.system_mode}
