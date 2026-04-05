from supabase import create_client, Client
from app.core.config import settings
import logging
from app.repositories.sensor import SensorRepository
from app.repositories.chat import ChatRepository
from app.repositories.security import SecurityRepository

logger = logging.getLogger(__name__)

class SupabaseService:
    """Facade Pattern: Centraliza el acceso orquestando múltiples repositorios especializados."""
    def __init__(self):
        try:
            key = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY != "your_service_role_key" else settings.SUPABASE_KEY
            self.client: Client = create_client(settings.SUPABASE_URL, key)
            self.sensor_repo = SensorRepository(self.client)
            self.chat_repo = ChatRepository(self.client)
            self.security_repo = SecurityRepository(self.client)
        except Exception as e:
            logger.warning(f"No se pudo inicializar el cliente de Supabase (URL/KEY inválidos): {e}")
            self.client = None
            self.sensor_repo = SensorRepository(None)
            self.chat_repo = ChatRepository(None)
            self.security_repo = SecurityRepository(None)

    # ==========================================
    # DOMINIO: SENSORES (SensorRepository)
    # ==========================================
    async def get_sensor_history(self, user_id: str, limit: int = 20) -> str:
        return await self.sensor_repo.get_sensor_history(user_id, limit)

    async def get_latest_sensors(self, user_id: str) -> dict:
        return await self.sensor_repo.get_latest_sensors(user_id)

    async def insert_sensor_data(self, data: dict, user_id: str) -> bool:
        return await self.sensor_repo.insert_sensor_data(data, user_id)

    async def get_sensor_history_raw(self, user_id: str, limit: int = 50) -> list:
        return await self.sensor_repo.get_sensor_history_raw(user_id, limit)

    # ==========================================
    # DOMINIO: CHAT E IA (ChatRepository)
    # ==========================================

    # --- Sesiones / Conversaciones ---
    async def create_conversation(self, user_id: str, title: str = "Nueva conversación") -> dict:
        return await self.chat_repo.create_conversation(user_id, title)

    async def get_conversations(self, user_id: str) -> list:
        return await self.chat_repo.get_conversations(user_id)

    async def rename_conversation(self, session_id: str, user_id: str, title: str) -> bool:
        return await self.chat_repo.rename_conversation(session_id, user_id, title)

    async def delete_conversation(self, session_id: str, user_id: str) -> bool:
        return await self.chat_repo.delete_conversation(session_id, user_id)

    # --- Mensajes ---
    async def save_chat_message(self, user_id: str, role: str, message: str, session_id: str | None = None) -> None:
        return await self.chat_repo.save_chat_message(user_id, role, message, session_id)

    async def get_chat_history(self, user_id: str, limit: int = 6, session_id: str | None = None) -> str:
        return await self.chat_repo.get_chat_history(user_id, limit, session_id)

    async def get_chat_history_raw(self, user_id: str, limit: int = 50, session_id: str | None = None) -> list:
        return await self.chat_repo.get_chat_history_raw(user_id, limit, session_id)

    # ==========================================
    # DOMINIO: SEGURIDAD (SecurityRepository)
    # ==========================================
    async def get_api_keys(self, user_id: str) -> list:
        return await self.security_repo.get_api_keys(user_id)

    async def upsert_api_key(self, key_data: dict) -> dict:
        return await self.security_repo.upsert_api_key(key_data)

    async def delete_api_key(self, user_id: str, key_type: str) -> bool:
        return await self.security_repo.delete_api_key(user_id, key_type)

# Singleton global (Factory Default) - Compatible con Inyección de Dependencias
supabase_db = SupabaseService()
