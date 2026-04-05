import asyncio
from .base import BaseRepository, logger

class ChatRepository(BaseRepository):
    async def save_chat_message(self, user_id: str, role: str, message: str) -> None:
        if not self.client: 
            return
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.client.table("chat_history").insert({
                    "user_id": user_id, "role": role, "message": message
                }).execute()
            )
            logger.info(f"Chat message saved via Repo for role: {role}")
        except Exception as e:
            logger.error(f"Error en ChatRepository.save_chat_message: {e}")

    async def get_chat_history(self, user_id: str, limit: int = 6) -> str:
        if not self.client: 
            return ""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.table("chat_history")
                            .select("*")
                            .eq("user_id", user_id)
                            .order("created_at", desc=True)
                            .limit(limit)
                            .execute()
            )
            if not response.data: 
                return ""
            history_lines = []
            for row in reversed(response.data):
                role_label = "USUARIO" if row["role"] == "user" else "AGRONEXUS"
                history_lines.append(f"{role_label}: {row['message']}")
            return "\n".join(history_lines)
        except Exception as e:
            logger.error(f"Error en ChatRepository.get_chat_history: {e}")
            return ""

    async def get_chat_history_raw(self, user_id: str, limit: int = 50) -> list:
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.table("chat_history")
                            .select("*")
                            .eq("user_id", user_id)
                            .order("created_at", desc=False) # raw is ASC to get oldest first usually, keeping it ASC
                            .limit(limit)
                            .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error en ChatRepository.get_chat_history_raw: {e}")
            return []
