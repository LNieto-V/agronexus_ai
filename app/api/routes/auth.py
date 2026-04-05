from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.core.security import generate_api_key, hash_key
from app.services.supabase_service import supabase_db
from app.api.deps import CurrentUser
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

class APIKeyResponse(BaseModel):
    user_id: str
    key_type: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

class NewAPIKeyResponse(APIKeyResponse):
    api_key: str # Solo se muestra una vez

@router.get("/keys", response_model=List[APIKeyResponse])
async def get_keys(user: CurrentUser):
    """Lista las llaves (metadatos) del usuario autenticado."""
    try:
        return await supabase_db.get_api_keys(user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener llaves: {str(e)}")

@router.post("/keys", response_model=NewAPIKeyResponse)
async def create_key(key_type: str = Query(..., pattern="^(read|write)$"), user: CurrentUser = None):
    """Genera una nueva API Key para el usuario."""
    prefix = "agnx_r_" if key_type == "read" else "agnx_w_"
    new_key = generate_api_key(prefix)
    hashed = hash_key(new_key)
    
    try:
        key_data = {
            "user_id": user["id"],
            "key_type": key_type,
            "key_hash": hashed,
            "key_prefix": prefix,
            "created_at": datetime.now().isoformat()
        }
        
        result = await supabase_db.upsert_api_key(key_data)
        if not result:
            raise HTTPException(status_code=500, detail="Error al guardar la llave.")
            
        result["api_key"] = new_key
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear llave: {str(e)}")

@router.delete("/keys/{key_type}")
async def delete_key(key_type: str, user: CurrentUser):
    """Revoca una API Key específica."""
    if key_type not in ["read", "write"]:
        raise HTTPException(status_code=400, detail="Tipo de llave inválido.")
        
    try:
        await supabase_db.delete_api_key(user["id"], key_type)
        return {"status": "success", "message": f"Llave '{key_type}' revocada."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar llave: {str(e)}")
