from fastapi import APIRouter, HTTPException
import logging
from app.schemas import ChatRequest, ChatResponse
from app.services.iot_service import process_chatbot_request, process_test_chat_request
from app.services.supabase_service import supabase_db
from app.api.deps import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: CurrentUser) -> ChatResponse:
    """Endpoint principal de chat agrícola."""
    try:
        text, actions, alerts = await process_chatbot_request(request.message, user["id"])
        return ChatResponse(response=text, actions=actions, alerts=alerts)
    except Exception as e:
        if "CUOTA_AGOTADA" in str(e):
            raise HTTPException(
                status_code=429,
                detail="Límite de la IA alcanzado. Por favor, reintenta en unos instantes."
            )
        logger.error(f"Error en chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error procesando la solicitud.")

@router.get("/chat/history")
async def get_history(user: CurrentUser):
    """Recupera el historial de chat para la interfaz."""
    try:
        history = await supabase_db.get_chat_history_raw(user["id"])
        return {"history": history}
    except Exception as e:
        logger.error(f"Error en historial: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial.")

@router.post("/chat/test", response_model=ChatResponse)
async def chat_test(request: ChatRequest) -> ChatResponse:
    """Endpoint de prueba sin autenticación para evaluadores."""
    try:
        text, actions, alerts = await process_test_chat_request(request.message)
        return ChatResponse(response=text, actions=actions, alerts=alerts)
    except Exception as e:
        logger.error(f"Error en chat test: {e}")
        raise HTTPException(status_code=500, detail="Error en el nodo de prueba.")

