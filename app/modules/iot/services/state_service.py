import asyncio
import logging
from app.core.database import supabase_client

logger = logging.getLogger(__name__)

class StateService:
    def __init__(self):
        # Default state fallback
        self._default_state = {
            "system_mode": "AUTO",
            "last_maintenance": "2026-03-25",
            "pump_health": 0.98,
            "alerts_active": [],
            "maintenance_required": False
        }

    async def get_state(self, user_id: str):
        """Obtiene el estado desde Supabase (Persistente en Serverless)."""
        if not supabase_client:
            return self._default_state
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: supabase_client.table("system_state") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute())
            
            if response.data:
                return response.data[0]
            
            # Si no existe, creamos el estado inicial para el usuario
            await self._initialize_state(user_id)
            return self._default_state
        except Exception as e:
            logger.error(f"Error obteniendo sistema state: {e}")
            return self._default_state

    async def _initialize_state(self, user_id: str):
        """Crea el registro inicial de estado para un nuevo usuario."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: supabase_client.table("system_state").insert({
                    "user_id": user_id,
                    "system_mode": "AUTO",
                    "pump_health": 1.0,
                    "alerts_active": []
                }).execute()
            )
        except Exception:
            pass

    async def update_mode(self, user_id: str, mode: str) -> bool:
        """Actualiza el modo en la DB."""
        if mode.upper() not in ["AUTO", "MANUAL"]: 
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: supabase_client.table("system_state") \
                    .update({"system_mode": mode.upper()}) \
                    .eq("user_id", user_id) \
                    .execute()
            )
            return True
        except Exception as e:
            logger.error(f"Error actualizando modo: {e}")
            return False

# Singleton
backend_state = StateService()
