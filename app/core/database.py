import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Crea y devuelve un cliente de Supabase singleton-like."""
    try:
        key = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY != "your_service_role_key" else settings.SUPABASE_KEY
        return create_client(settings.SUPABASE_URL, key)
    except Exception as e:
        logger.error(f"Fallo al inicializar Supabase: {e}")
        return None

# Instancia compartida para los repositorios de los módulos
supabase_client = get_supabase_client()
