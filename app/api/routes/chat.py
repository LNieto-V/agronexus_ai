from fastapi import APIRouter, HTTPException, Path, Depends
import logging
from app.schemas import (
    ChatRequest, ChatResponse, ReportChatRequest,
    ConversationCreate, ConversationRename, ConversationOut, ChatMessageOut, ChatHistoryOut
)
from app.api.deps import CurrentUser, Chat, require_role
from app.modules.chat.services.ai_orchestrator import (
    process_chatbot_request, process_test_chat_request, process_report_request
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


# =====================================================
# SESIONES / CONVERSACIONES
# =====================================================

@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(user: CurrentUser, chat_svc: Chat):
    """Lista todas las conversaciones del usuario, más recientes primero."""
    try:
        return await chat_svc.get_conversations(user["id"])
    except Exception as e:
        logger.error(f"Error listando conversaciones: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo conversaciones.")


@router.post("/conversations", response_model=ConversationOut, status_code=201, dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def create_conversation(body: ConversationCreate, user: CurrentUser, chat_svc: Chat):
    """Crea una nueva sesión de chat y la devuelve."""
    try:
        result = await chat_svc.create_conversation(user["id"], body.title)
        if not result:
            raise HTTPException(status_code=500, detail="No se pudo crear la conversación.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando conversación: {e}")
        raise HTTPException(status_code=500, detail="Error creando conversación.")


@router.patch("/conversations/{session_id}", dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def rename_conversation(
    body: ConversationRename,
    user: CurrentUser,
    chat_svc: Chat,
    session_id: str = Path(..., description="UUID de la conversación"),
):
    """Renombra el título de una conversación existente."""
    success = await chat_svc.rename_conversation(session_id, user["id"], body.title)
    if not success:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    return {"status": "ok", "session_id": session_id, "title": body.title}


@router.delete("/conversations/{session_id}", status_code=204, dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def delete_conversation(
    user: CurrentUser,
    chat_svc: Chat,
    session_id: str = Path(..., description="UUID de la conversación"),
):
    """Elimina una conversación y todos sus mensajes."""
    success = await chat_svc.delete_conversation(session_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")


# =====================================================
# MENSAJES (con soporte de sesión)
# =====================================================

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def chat(request: ChatRequest, user: CurrentUser, chat_svc: Chat) -> ChatResponse:
    """Endpoint principal de chat agrícola. Acepta session_id opcional para aislar el contexto."""
    try:
        text, actions, alerts = await process_chatbot_request(
            request.message, user["id"], request.session_id
        )
        return ChatResponse(response=text, actions=actions, alerts=alerts)
    except Exception as e:
        if "CUOTA_AGOTADA" in str(e):
            raise HTTPException(
                status_code=429,
                detail="Límite de la IA alcanzado. Por favor, reintenta en unos instantes."
            )
        logger.error(f"Error en chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error procesando la solicitud.")


@router.get("/chat/history", response_model=ChatHistoryOut)
async def get_history(user: CurrentUser, chat_svc: Chat, session_id: str | None = None, limit: int = 100, offset: int = 0):
    """Recupera el historial de chat para la interfaz."""
    try:
        history = await chat_svc.get_chat_history_raw(user["id"], limit=limit, session_id=session_id, offset=offset)
        return ChatHistoryOut(history=history)
    except Exception as e:
        logger.error(f"Error en historial: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial.")


@router.post(
    "/chat/test",
    response_model=ChatResponse,
    summary="[Evaluación] API Test Rápido sin Auth",
    description="Útil para probar el flujo completo del sistema RAG, prompts y personalidad del Agente AI en un entorno aislado sin requerir JWT. Ideal para corrección académica y SwaggerUI."
)
async def chat_test(request: ChatRequest) -> ChatResponse:
    """Endpoint de prueba sin autenticación para evaluadores y testing QA."""
    try:
        text, actions, alerts = await process_test_chat_request(request.message)
        return ChatResponse(response=text, actions=actions, alerts=alerts)
    except Exception as e:
        logger.error(f"Error en chat test: {e}")
        raise HTTPException(status_code=500, detail="Error en el nodo de prueba.")

@router.post("/chat/report", response_model=ChatResponse, dependencies=[Depends(require_role(["owner", "agronomist"]))])
async def generate_report(request: ReportChatRequest, user: CurrentUser, chat_svc: Chat) -> ChatResponse:
    """Endpoint dedicado a la generación de reportes agronómicos en formato chat."""
    try:
        report_text = await process_report_request(
            user_id=user["id"],
            zone_id=request.zone_id,
            hours=request.hours,
            focus=request.focus,
            session_id=request.session_id
        )
        return ChatResponse(response=report_text)
    except Exception as e:
        if "LIMITE_ALCANZADO" in str(e):
            raise HTTPException(
                status_code=429,
                detail="Límite de cuota o tasa de peticiones alcanzado. Por favor, reintenta más tarde."
            )
        logger.error(f"Error generando reporte: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generando el reporte agronómico.")
