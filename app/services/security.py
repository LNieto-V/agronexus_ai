import hashlib
import secrets
from datetime import datetime
from typing import Optional
from fastapi import Header, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
from app.services.supabase_service import supabase_db

# Security schemes
security_bearer = HTTPBearer()

def hash_key(key: str) -> str:
    """Hashea la API Key usando SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()

def generate_api_key(prefix: str = "agnx_") -> str:
    """Genera una nueva API Key con el prefijo indicado."""
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security_bearer)):
    """
    Verifica el JWT de Supabase y retorna la información del usuario.
    """
    try:
        payload = jwt.decode(
            auth.credentials, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            options={"verify_aud": False} # Supabase usa aud: authenticated
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido: No se encontró el sujet (sub).")
        return {"id": user_id, "email": payload.get("email")}
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido o expirado: {str(e)}")

async def verify_key(api_key: str = Header(..., alias="X-API-Key"), expected_type: Optional[str] = None):
    """
    Lógica base para verificar una API Key contra la base de datos.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header faltante.")
    
    hashed = hash_key(api_key)
    
    # Consultar la base de datos (Usamos el cliente de Supabase)
    # Nota: Requiere que el cliente de Supabase tenga permisos para leer api_keys
    try:
        query = supabase_db.client.table("api_keys").select("*").eq("key_hash", hashed)
        
        # Si se especifica un tipo, validamos que coincida 
        # (O que sea 'write' si se pide 'read', ya que write es superior)
        if expected_type:
            if expected_type == "read":
                # Aceptamos tanto 'read' como 'write' para endpoints de lectura
                query = query.in_("key_type", ["read", "write"])
            else:
                # Para escritura, solo aceptamos 'write'
                query = query.eq("key_type", "write")
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=401, detail="API Key inválida o sin permisos suficientes.")
        
        key_data = result.data[0]
        
        # Actualizar last_used_at de forma asíncrona (opcional, aquí lo hacemos simple)
        supabase_db.client.table("api_keys").update({"last_used_at": datetime.now().isoformat()}).eq("user_id", key_data["user_id"]).eq("key_type", key_data["key_type"]).execute()
        
        return key_data["user_id"]
        
    except Exception as e:
        if isinstance(e, HTTPException):
             raise e
        raise HTTPException(status_code=500, detail=f"Error verificando API Key: {str(e)}")

async def verify_read_key(api_key: str = Header(..., alias="X-API-Key")):
    """Dependency para endpoints de solo lectura."""
    return await verify_key(api_key, expected_type="read")

async def verify_write_key(api_key: str = Header(..., alias="X-API-Key")):
    """Dependency para endpoints de escritura (telemetría)."""
    return await verify_key(api_key, expected_type="write")
