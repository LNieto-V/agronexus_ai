import asyncio
from app.core.repositories.base_repo import BaseRepository, logger

class ActuatorRepository(BaseRepository):
    async def log_action(self, user_id: str, device: str, action: str, reason: str = None, triggered_by: str = "AI", zone_id: str = None) -> bool:
        """Registra una acción de actuador en la base de datos."""
        if not self.client:
            return False
        try:
            payload = {
                "user_id": user_id,
                "zone_id": zone_id,
                "device": device,
                "action": action,
                "reason": reason,
                "triggered_by": triggered_by
            }
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.table("actuator_log").insert(payload).execute()
            )
            return True
        except Exception as e:
            logger.error(f"Error en ActuatorRepository.log_action: {e}")
            return False

    async def get_logs(self, user_id: str, limit: int = 50, offset: int = 0, zone_id: str = None) -> list:
        """Obtiene historial de acciones de actuadores."""
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()
            
            def query_builder():
                q = self.client.table("actuator_log").select("*").eq("user_id", user_id)
                if zone_id:
                    q = q.eq("zone_id", zone_id)
                return q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

            response = await loop.run_in_executor(None, query_builder)
            return response.data or []
        except Exception as e:
            logger.error(f"Error en ActuatorRepository.get_logs: {e}")
            return []
