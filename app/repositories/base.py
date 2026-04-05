from supabase import Client
import logging

logger = logging.getLogger(__name__)

class BaseRepository:
    """Clase base para todos los repositorios. Inyecta el cliente Supabase."""
    def __init__(self, client: Client):
        self.client = client
