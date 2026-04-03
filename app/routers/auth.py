from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.services.security import get_current_user, generate_api_key, hash_key
from app.services.supabase_service import supabase_db
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
async def get_keys(user = Depends(get_current_user)):
    """
    Lista las llaves (metadatos) del usuario autenticado.
    """
    try:
        res = supabase_db.client.table("api_keys").select("*").eq("user_id", user["id"]).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener llaves: {str(e)}")

@router.post("/keys", response_model=NewAPIKeyResponse)
async def create_key(key_type: str = Query(..., pattern="^(read|write)$"), user = Depends(get_current_user)):
    """
    Genera una nueva API Key para el usuario. 
    Si ya existe una de ese tipo, se sobrescribe (se rota).
    """
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
        
        # Insertamos o actualizamos usando upsert (requiere que user_id, key_type sea la PK)
        res = supabase_db.client.table("api_keys").upsert(key_data).execute()
        
        if not res.data:
            raise HTTPException(status_code=500, detail="Error al guardar la llave en la base de datos.")
            
        result = res.data[0]
        result["api_key"] = new_key # Añadimos la llave en texto plano para el usuario
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear llave: {str(e)}")

@router.delete("/keys/{key_type}")
async def delete_key(key_type: str, user = Depends(get_current_user)):
    """
    Revoca una API Key específica.
    """
    if key_type not in ["read", "write"]:
        raise HTTPException(status_code=400, detail="Tipo de llave inválido. Use 'read' o 'write'.")
        
    try:
        supabase_db.client.table("api_keys").delete().eq("user_id", user["id"]).eq("key_type", key_type).execute()
        return {"status": "success", "message": f"Llave de tipo '{key_type}' revocada."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar llave: {str(e)}")
