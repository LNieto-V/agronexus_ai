from fastapi import APIRouter, HTTPException
import logging
from typing import List, Dict, Any
from app.schemas import SystemModeUpdate
from app.services.supabase_service import supabase_db
from app.services.state_service import backend_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/latest", response_model=Dict[str, Any])
async def get_latest_data():
    """Obtiene los últimos datos de sensores para el dashboard principal."""
    try:
        latest = supabase_db.get_latest_sensors()
        return latest
    except Exception as e:
        logger.error(f"Error en dashboard latest: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo últimos sensores.")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history_data():
    """Obtiene el historial reciente para gráficas de Ionic."""
    try:
        # Reutilizamos la lógica de Supabase pero devolvemos los datos crudos para el frontend
        if not supabase_db.client:
            return []
        response = supabase_db.client.table("sensor_data") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error en dashboard history: {e}")
        return []

@router.get("/state")
async def get_system_state():
    """Obtiene el estado interno del sistema (Modo, Bomba, Alertas)."""
    return backend_state.get_state()

@router.post("/mode")
async def update_system_mode(update: SystemModeUpdate):
    """Cambia el modo de operación (AUTO/MANUAL) desde la App."""
    success = backend_state.update_mode(update.mode)
    if not success:
        raise HTTPException(status_code=400, detail="Modo inválido. Use AUTO o MANUAL.")
    return {"status": "success", "new_mode": backend_state.system_mode}
