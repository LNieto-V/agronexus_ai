from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.core.security import generate_api_key, hash_key
from app.api.deps import CurrentUser, Identity
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# --- Esquemas de Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    metadata: Optional[Dict[str, Any]] = None

class APIKeyResponse(BaseModel):
    user_id: str
    key_type: str
    key_prefix: str
    zone_id: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None

class NewAPIKeyResponse(APIKeyResponse):
    api_key: str # Solo se muestra una vez

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None

router = APIRouter(prefix="/auth", tags=["auth"])

@router.patch("/profile")
async def update_profile(body: ProfileUpdate, user: CurrentUser, identity: Identity):
    """Actualiza el perfil del usuario."""
    # Filtrar solo campos enviados
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar.")
    
    updated_profile = await identity.update_profile(user["id"], update_data)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado o error en actualización.")
    
    return updated_profile

@router.post("/register")
async def register(body: RegisterRequest, identity: Identity):
    """Registro de usuario mediado por el backend."""
    try:
        # Supabase se encarga del hashing y validación
        res = identity.client.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": body.metadata or {}}
        })
        logger.info(f"Audit: Registro exitoso - {body.email}")
        return {"status": "success", "user": res.user}
    except Exception as e:
        logger.error(f"Audit: Fallo en registro - {body.email} - {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(body: LoginRequest, identity: Identity):
    """Login mediado por el backend (Punto de Auditoría)."""
    try:
        res = identity.client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })
        logger.info(f"Audit: Login exitoso - {body.email}")
        return {
            "access_token": res.session.access_token,
            "token_type": "bearer",
            "user": res.user,
            "expires_in": res.session.expires_in
        }
    except Exception as e:
        logger.warning(f"Audit: Intento de login fallido - {body.email} - {e}")
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")

@router.get("/me")
async def get_me(user: CurrentUser):
    """Devuelve el usuario actual basado en el JWT (Verificación de Backend)."""
    return user


@router.get("/keys", response_model=List[APIKeyResponse])
async def get_keys(user: CurrentUser, identity: Identity):
    """Lista las llaves (metadatos) del usuario autenticado."""
    try:
        return await identity.get_api_keys(user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener llaves: {str(e)}")

@router.post("/keys", response_model=NewAPIKeyResponse)
async def create_key(identity: Identity, key_type: str = Query(..., pattern="^(read|write)$"), zone_id: Optional[str] = Query(None), user: CurrentUser = None):
    """Genera una nueva API Key para el usuario."""
    # Validación de seguridad: Write keys SIEMPRE deben tener una zona
    if key_type == "write" and not zone_id:
        raise HTTPException(
            status_code=400, 
            detail="Security Policy Error: 'write' keys must be restricted to a specific zone."
        )
        
    prefix = "agnx_r_" if key_type == "read" else "agnx_w_"
    new_key = generate_api_key(prefix)
    hashed = hash_key(new_key)
    
    try:
        key_data = {
            "user_id": user["id"],
            "key_type": key_type,
            "key_hash": hashed,
            "key_prefix": prefix,
            "zone_id": zone_id,
            "created_at": datetime.now().isoformat()
        }
        
        result = await identity.upsert_api_key(key_data)
        if not result:
            raise HTTPException(status_code=500, detail="Error al guardar la llave.")
            
        result["api_key"] = new_key
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear llave: {str(e)}")

@router.delete("/keys/{key_type}")
async def delete_key(key_type: str, user: CurrentUser, identity: Identity):
    """Revoca una API Key específica."""
    if key_type not in ["read", "write"]:
        raise HTTPException(status_code=400, detail="Tipo de llave inválido.")
        
    try:
        await identity.delete_api_key(user["id"], key_type)
        return {"status": "success", "message": f"Llave '{key_type}' revocada."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar llave: {str(e)}")
