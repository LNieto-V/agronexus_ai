import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Crea y devuelve un cliente de Supabase."""
    try:
        # Prioridad al Service Role Key para operaciones de backend bypass RLS
        key = settings.SUPABASE_SERVICE_ROLE_KEY
        if not key or key == "your_service_role_key":
            key = settings.SUPABASE_KEY
            
        if not settings.SUPABASE_URL or settings.SUPABASE_URL == "your_project_url":
            logger.error("SUPABASE_URL no configurada en .env")
            return None
            
        return create_client(settings.SUPABASE_URL, key)
    except Exception as e:
        logger.error(f"Fallo crítico al inicializar Supabase: {e}")
        return None

# Instancia compartida base
supabase_client = get_supabase_client()

