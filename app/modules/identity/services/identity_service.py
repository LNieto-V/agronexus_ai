import asyncio
import logging
from typing import List, Dict, Any
from app.core.database import supabase_client
from app.modules.identity.repositories.identity_repo import SecurityRepository

logger = logging.getLogger(__name__)

class IdentityService:
    def __init__(self):
        self.security_repo = SecurityRepository(supabase_client)
        self.client = supabase_client

    async def get_api_keys(self, user_id: str) -> list:
        return await self.security_repo.get_api_keys(user_id)

    async def upsert_api_key(self, key_data: dict) -> dict:
        return await self.security_repo.upsert_api_key(key_data)

    async def delete_api_key(self, user_id: str, key_type: str) -> bool:
        return await self.security_repo.delete_api_key(user_id, key_type)

    async def get_alert_thresholds(self, user_id: str):
        if not self.client: return []
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: self.client.table("alert_thresholds").select("*").eq("user_id", user_id).execute())
        return res.data or []

    async def update_alert_threshold(self, user_id: str, sensor_type: str, min_val: float, max_val: float):
        if not self.client: return False
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.client.table("alert_thresholds").upsert({"user_id": user_id, "sensor_type": sensor_type, "min_value": min_val, "max_value": max_val}).execute())
        return True

    async def update_profile(self, user_id: str, profile_data: dict) -> dict:
        """Actualiza la información del perfil del usuario."""
        if not self.client:
            return {}
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None,
                lambda: self.client.table("profiles")
                .update(profile_data)
                .eq("id", user_id)
                .execute()
            )
            return res.data[0] if res.data else {}
        except Exception as e:
            logger.error(f"Error en IdentityService.update_profile: {e}")
            return {}

identity_service = IdentityService()
