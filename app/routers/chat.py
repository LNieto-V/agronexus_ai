from fastapi import APIRouter, HTTPException, Depends
import logging
from app.schemas import ChatRequest, ChatResponse
from app.services.iot_service import process_chatbot_request
from app.services.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user = Depends(get_current_user)) -> ChatResponse:
    """Endpoint principal delegado al servicio de orquestación IoT."""
    try:
        # El chatbot humano ya no envía datos de sensores; los obtenemos de la DB filtrando por usuario
        text, actions, alerts = await process_chatbot_request(request.message, user["id"])
        
        return ChatResponse(
            response=text,
            actions=actions,
            alerts=alerts
        )
    except Exception as e:
        if "CUOTA_AGOTADA" in str(e):
            raise HTTPException(
                status_code=429,
                detail="Límite de la IA alcanzado por hoy. Por favor, reintenta en unos instantes o mañana."
            )
        logger.error(f"Error procesando chat: {e}", exc_info=True)
        # El router se encarga solo del manejo de errores HTTP
        raise HTTPException(
            status_code=500, 
            detail="Error interno procesando la solicitud agrícola."
        )

@router.get("/chat/history")
async def get_history(user = Depends(get_current_user)):
    """
    Recupera el historial de chat para mostrarlo en la interfaz.
    """
    from app.services.supabase_service import supabase_db
    
    if not supabase_db.client:
        raise HTTPException(status_code=500, detail="Base de datos no disponible.")
        
    try:
        response = supabase_db.client.table("chat_history").select("*") \
                    .eq("user_id", user["id"]) \
                    .order("created_at", desc=False) \
                    .limit(50) \
                    .execute()
        return {"history": response.data}
    except Exception as e:
        logger.error(f"Error recuperando historial de chat: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial.")
