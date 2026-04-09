import asyncio
from typing import Annotated
from fastapi import Depends, HTTPException
from app.core.security import get_current_user, verify_read_key, verify_write_key
from app.modules.iot.services.iot_service import iot_service, IoTService
from app.modules.chat.services.chat_service import chat_service, ChatService
from app.modules.identity.services.identity_service import identity_service, IdentityService

def get_iot_service() -> IoTService:
    return iot_service

def get_chat_service() -> ChatService:
    return chat_service

def get_identity_service() -> IdentityService:
    return identity_service

# Aliases de dependencias para mayor legibilidad
CurrentUser = Annotated[dict, Depends(get_current_user)]
ReadKey = Annotated[str, Depends(verify_read_key)]
WriteKey = Annotated[str, Depends(verify_write_key)]
IoT = Annotated[IoTService, Depends(get_iot_service)]
Chat = Annotated[ChatService, Depends(get_chat_service)]
Identity = Annotated[IdentityService, Depends(get_identity_service)]

async def get_current_profile(user: CurrentUser, identity: Identity):
    """Obtiene el perfil completo con rol del usuario."""
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: identity.client.table("profiles").select("*").eq("id", user["id"]).single().execute())
        if not res.data:
            raise HTTPException(status_code=404, detail="Perfil no encontrado.")
        return res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Error al recuperar perfil.")

def require_role(roles: list[str]):
    """Dependencia para restringir acceso por rol."""
    async def role_checker(profile: dict = Depends(get_current_profile)):
        if profile.get("role") not in roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Permisos insuficientes. Se requiere uno de los roles: {', '.join(roles)}"
            )
        return profile
    return role_checker
