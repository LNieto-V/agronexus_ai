from fastapi import APIRouter, HTTPException
import logging
from app.schemas import ChatRequest, ChatResponse
from app.services.iot_service import process_chatbot_request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Endpoint principal delegado al servicio de orquestación IoT."""
    try:
        # El chatbot humano ya no envía datos de sensores; los obtenemos de la DB
        text, actions, alerts = await process_chatbot_request(request.message)
        
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
