from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        try:
            self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.warning(f"No se pudo inicializar el cliente de Supabase (URL/KEY inválidos): {e}")
            self.client = None

    def get_sensor_history(self, hours: int = 24):
        """Consulta el historial de sensores desde la tabla real en Supabase."""
        if not self.client:
            return "Error: Supabase no configurado correctamente."
        
        try:
            # Consultamos los últimos registros ordenados por tiempo
            response = self.client.table("sensor_data") \
                .select("*") \
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

    def get_latest_sensors(self) -> dict:
        """Obtiene el último registro de sensores para usar como contexto real."""
        if not self.client:
            return {}
        try:
            response = self.client.table("sensor_data") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error obteniendo último sensor: {e}")
            return {}

    def insert_sensor_data(self, data: dict):
        """Inserta un nuevo registro de sensores en Supabase."""
        if not self.client:
            return False
        
        try:
            response = self.client.table("sensor_data").insert(data).execute()
            return True if response.data else False
        except Exception as e:
            logger.error(f"Error insertando en Supabase: {e}")
            return False

supabase_db = SupabaseService()
