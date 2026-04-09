from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.api.deps import CurrentUser, IoT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zones", tags=["zones"])

class ZoneCreate(BaseModel):
    name: str
    crop_type: Optional[str] = None

@router.get("/")
async def list_zones(user: CurrentUser, iot: IoT):
    """Lista todos los invernaderos/zonas del usuario."""
    return await iot.get_zones(user["id"])

@router.post("/", status_code=201)
async def create_zone(body: ZoneCreate, user: CurrentUser, iot: IoT):
    """Crea un nuevo invernadero o zona de cultivo."""
    logger.info(f"CREATE ZONE REQUEST: {body.name} for user {user['id']}")
    zone = await iot.create_zone(user["id"], body.name, body.crop_type)
    if not zone:
        raise HTTPException(status_code=500, detail="Error al crear zona.")
    return zone

@router.delete("/{zone_id}", status_code=204)
async def delete_zone(zone_id: str, user: CurrentUser, iot: IoT):
    """Elimina una zona de cultivo."""
    success = await iot.delete_zone(user["id"], zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zona no encontrada.")

@router.patch("/{zone_id}")
async def update_zone(zone_id: str, body: ZoneCreate, user: CurrentUser, iot: IoT):
    """Actualiza una zona de cultivo."""
    zone = await iot.update_zone(user["id"], zone_id, body.name, body.crop_type)
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada o error crítico.")
    return zone
