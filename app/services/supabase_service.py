from supabase import create_client, Client
from app.config import settings
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

    def get_sensor_history(self, user_id: str, hours: int = 24):
        """Consulta el historial de sensores desde la tabla real en Supabase por usuario."""
        if not self.client:
            return "Error: Supabase no configurado correctamente."
        
        try:
            # Consultamos los últimos registros del usuario
            response = self.client.table("sensor_data") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(20) \
                .execute()
            
            if not response.data:
                return "No hay datos históricos registrados en Supabase aún."
            
            # Formatear un resumen para el LLM
            history_summary = "Historial reciente:\n"
            for row in response.data:
                history_summary += f"- {row['created_at']}: T={row.get('temperature')}°C, H={row.get('humidity')}%\n"
            return history_summary

        except Exception as e:
            logger.error(f"Error consultando Supabase: {e}")
            return f"Error técnico al consultar el historial: {str(e)}"

    def get_latest_sensors(self, user_id: str) -> dict:
        """Obtiene el último registro de sensores por usuario."""
        if not self.client:
            return {}
        try:
            response = self.client.table("sensor_data") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error obteniendo último sensor: {e}")
            return {}

    def insert_sensor_data(self, data: dict, user_id: str):
        """Inserta un nuevo registro de sensores asociado a un usuario."""
        if not self.client:
            return False
        
        try:
            # Añadir user_id a la data si no está
            data["user_id"] = user_id
            response = self.client.table("sensor_data").insert(data).execute()
            return True if response.data else False
        except Exception as e:
            logger.error(f"Error insertando en Supabase: {e}")
            return False

    def save_chat_message(self, user_id: str, role: str, message: str) -> None:
        """Guarda un mensaje en el historial del chat."""
        if not self.client:
            return
        try:
            self.client.table("chat_history").insert({
                "user_id": user_id,
                "role": role,
                "message": message
            }).execute()
        except Exception as e:
            logger.error(f"Error guardando mensaje de chat para {user_id}: {e}")

    def get_chat_history(self, user_id: str, limit: int = 6) -> str:
        """
        Recupera los últimos N mensajes del usuario y la IA formatados en texto.
        """
        if not self.client:
            return ""
        try:
            response = self.client.table("chat_history").select("*") \
                        .eq("user_id", user_id) \
                        .order("created_at", desc=True) \
                        .limit(limit) \
                        .execute()
            
            if not response.data:
                return ""
                
            # Los datos vienen más recientes primero, los invertimos cronológicamente
            history_lines = []
            for row in reversed(response.data):
                role_label = "USUARIO" if row["role"] == "user" else "AGRONEXUS"
                history_lines.append(f"{role_label}: {row['message']}")
                
            return "\n".join(history_lines)
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de chat para {user_id}: {e}")
            return ""

supabase_db = SupabaseService()
