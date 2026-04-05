import asyncio
from .base import BaseRepository, logger

class SecurityRepository(BaseRepository):
    async def get_api_keys(self, user_id: str) -> list:
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None,
                lambda: self.client.table("api_keys").select("*").eq("user_id", user_id).execute()
            )
            return res.data
        except Exception as e:
            logger.error(f"Error en SecurityRepository.get_api_keys: {e}")
            return []

    async def upsert_api_key(self, key_data: dict) -> dict:
        if not self.client:
            return {}
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None,
                lambda: self.client.table("api_keys").upsert(key_data).execute()
            )
            logger.info("API Key upserted successfully via Repo.")
            return res.data[0] if res.data else {}
        except Exception as e:
            logger.error(f"Error en SecurityRepository.upsert_api_key: {e}")
            return {}

    async def delete_api_key(self, user_id: str, key_type: str) -> bool:
        if not self.client:
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.table("api_keys").delete().eq("user_id", user_id).eq("key_type", key_type).execute()
            )
            logger.info("API Key deleted successfully via Repo.")
            return True
        except Exception as e:
            logger.error(f"Error en SecurityRepository.delete_api_key: {e}")
            return False
