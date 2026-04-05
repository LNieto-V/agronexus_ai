from supabase import create_client, Client
from app.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        try:
            # Usar service_role_key para bypass de RLS en el backend
            key = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY != "your_service_role_key" else settings.SUPABASE_KEY
            self.client: Client = create_client(settings.SUPABASE_URL, key)
        except Exception as e:
            logger.warning(f"No se pudo inicializar el cliente de Supabase (URL/KEY inválidos): {e}")
            self.client = None

    async def get_sensor_history(self, user_id: str, limit: int = 20):
        """Consulta el historial de sensores asíncronamente."""
        if not self.client:
            return "Error: Supabase no configurado."
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.table("sensor_data") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .order("created_at", desc=True) \
                    .limit(limit) \
                    .execute()
            )
            
            if not response.data:
                return "No hay datos históricos disponibles."
            
            summary = "Historial reciente:\n"
            for row in response.data:
                summary += f"- {row['created_at']}: T={row.get('temperature')}°C, H={row.get('humidity')}%\n"
            return summary
        except Exception as e:
            logger.error(f"Error en sensor history: {e}")
            return f"Error técnico: {str(e)}"

    async def get_latest_sensors(self, user_id: str) -> dict:
        """Obtiene el último sensor de forma asíncrona."""
        if not self.client: 
            return {}
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.table("sensor_data") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
            )
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error en latest sensors: {e}")
            return {}

    async def insert_sensor_data(self, data: dict, user_id: str):
        """Inserta telemetría asíncronamente."""
        if not self.client: 
            return False
        try:
            data["user_id"] = user_id
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.client.table("sensor_data").insert(data).execute()
            )
            return True
        except Exception as e:
            logger.error(f"Error insertando sensor: {e}")
            return False

    async def save_chat_message(self, user_id: str, role: str, message: str) -> None:
        """Guarda mensaje de chat asíncronamente."""
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
        except Exception as e:
            logger.error(f"Error guardando chat: {e}")

    async def get_chat_history(self, user_id: str, limit: int = 6) -> str:
        """Recupera el contexto del chat asíncronamente."""
        if not self.client: 
            return ""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.table("chat_history") \
                            .select("*") \
                            .eq("user_id", user_id) \
                            .order("created_at", desc=True) \
                            .limit(limit) \
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
            logger.error(f"Error en chat history: {e}")
            return ""

supabase_db = SupabaseService()
