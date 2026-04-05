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

@router.post("/chat/test", response_model=ChatResponse)
async def chat_test(request: ChatRequest) -> ChatResponse:
    """
    Endpoint de PRUEBA SIN AUTENTICACIÓN.
    Permite a evaluadores probar la lógica del chatbot y el formato de respuesta 
    sin necesidad de un JWT de Supabase válido.
    """
    try:
        from app.llm import generate_raw_response
        from app.prompts import build_prompt
        from app.services.iot_service import extract_iot_data
        from app.services.supabase_service import supabase_db
        from app.services.state_service import backend_state
        
        # 1. Obtener contexto real si está disponible
        current_state = backend_state.get_state()
        
        # Intentar obtener los últimos datos globales de sensores (sin usuario específico) para realismo
        sensor_data = {"temperature": 30.5, "humidity": 75.2, "ph": 6.5}
        try:
            if supabase_db.client:
                res = supabase_db.client.table("sensor_data").select("*").order("created_at", desc=True).limit(1).execute()
                if res.data:
                    db_data = res.data[0]
                    sensor_data = {
                        "temperature": db_data.get("temperature", 30.5),
                        "humidity": db_data.get("humidity", 75.2),
                        "ph": db_data.get("ph", 6.5)
                    }
        except:
            pass # Usar mock si la DB falla

        # 2. Construir prompt completo
        full_prompt = build_prompt(
            message=request.message,
            sensor_data=sensor_data,
            history="[MODO EVALUACIÓN: Datos Históricos Simulados]",
            backend_state=current_state,
            chat_history="ENTORNO: Nodo de prueba público (Evaluación de Proyecto)."
        )
        
        # 3. Consultar IA y extraer datos
        raw_text = await generate_raw_response(full_prompt)
        text, actions, alerts = extract_iot_data(raw_text)
        
        return ChatResponse(
            response=text, # Eliminado prefijo [MODO TEST] para simetría con el real
            actions=actions,
            alerts=alerts
        )
    except Exception as e:
        logger.error(f"Error en chat test: {e}")
        raise HTTPException(status_code=500, detail="Error en el nodo de prueba de la IA.")

