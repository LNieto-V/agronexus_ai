from typing import Annotated
from fastapi import Depends
from app.core.security import get_current_user, verify_read_key, verify_write_key
from app.services.supabase_service import SupabaseService, supabase_db

def get_supabase_db() -> SupabaseService:
    return supabase_db

# Aliases de dependencias para mayor legibilidad
CurrentUser = Annotated[dict, Depends(get_current_user)]
ReadKey = Annotated[str, Depends(verify_read_key)]
WriteKey = Annotated[str, Depends(verify_write_key)]
DBService = Annotated[SupabaseService, Depends(get_supabase_db)]
