import asyncio
import logging
from typing import List, Dict, Any
from app.core.database import supabase_client
from app.modules.chat.repositories.chat_repo import ChatRepository

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.chat_repo = ChatRepository(supabase_client)
        self.client = supabase_client

    async def create_conversation(self, user_id: str, title: str = "Nueva conversación") -> dict:
        return await self.chat_repo.create_conversation(user_id, title)

    async def get_conversations(self, user_id: str) -> list:
        return await self.chat_repo.get_conversations(user_id)

    async def rename_conversation(self, session_id: str, user_id: str, title: str) -> bool:
        return await self.chat_repo.rename_conversation(session_id, user_id, title)

    async def delete_conversation(self, session_id: str, user_id: str) -> bool:
        return await self.chat_repo.delete_conversation(session_id, user_id)

    async def save_chat_message(self, user_id: str, role: str, message: str, session_id: str | None = None) -> None:
        return await self.chat_repo.save_chat_message(user_id, role, message, session_id)

    async def get_chat_history(self, user_id: str, limit: int = 6, session_id: str | None = None) -> str:
        return await self.chat_repo.get_chat_history(user_id, limit, session_id)

    async def get_chat_history_raw(self, user_id: str, limit: int = 100, session_id: str | None = None, offset: int = 0) -> list:
        return await self.chat_repo.get_chat_history_raw(user_id, limit, session_id, offset)

chat_service = ChatService()
