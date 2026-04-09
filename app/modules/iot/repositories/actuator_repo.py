import asyncio
from app.core.repositories.base_repo import BaseRepository, logger

class ActuatorRepository(BaseRepository):
    async def log_action(self, user_id: str, device: str, action: str, reason: str = None, triggered_by: str = "AI") -> bool:
        """Registra una acción de actuador en la base de datos."""
        if not self.client:
            return False
        try:
            payload = {
                "user_id": user_id,
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

    async def get_logs(self, user_id: str, limit: int = 50) -> list:
        """Obtiene historial de acciones de actuadores."""
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.table("actuator_log")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error en ActuatorRepository.get_logs: {e}")
            return []
