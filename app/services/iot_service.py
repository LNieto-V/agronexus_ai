import asyncio
import logging
from typing import Tuple, List, Dict, Any
from app.services.supabase_service import supabase_db
from app.services.state_service import backend_state
from app.core.ai.llm import generate_raw_response
from app.core.ai.prompts import build_prompt
from app.services.parser_service import extract_iot_data, is_anomaly

logger = logging.getLogger(__name__)

async def process_chatbot_request(message: str, user_id: str) -> Tuple[str, List[dict], List[str]]:
    """
    Orquesta el flujo completo con procesamiento paralelo (asyncio.gather).
    """
    # 1. Obtener contexto externo en PARALELO
    chat_history_task = supabase_db.get_chat_history(user_id)
    history_task = supabase_db.get_sensor_history(user_id)
    state_task = backend_state.get_state(user_id)
    latest_sensors_task = supabase_db.get_latest_sensors(user_id)

    chat_history, history, current_state, latest_sensors = await asyncio.gather(
        chat_history_task, history_task, state_task, latest_sensors_task
    )
    
    # 2. Construir prompt enriquecido
    full_prompt = build_prompt(
        message=message, 
        sensor_data=latest_sensors,
        history=history,
        backend_state=current_state,
        chat_history=chat_history
    )

    # 3. Obtener respuesta del LLM
    raw_text = await generate_raw_response(full_prompt)
    
    # 4. Extraer datos estructurados
    clean_text, actions, alerts = extract_iot_data(raw_text)
    
    # 5. Guardar Memoria Conversacional (En paralelo)
    asyncio.create_task(supabase_db.save_chat_message(user_id, "user", message))
    asyncio.create_task(supabase_db.save_chat_message(user_id, "ai", clean_text))
    
    return clean_text, actions, alerts

async def process_automated_telemetry(sensor_data: Dict[str, Any], user_id: str) -> Tuple[List[dict], List[str]]:
    """
    Procesa telemetría de hardware con paralelismo y verificaciones asíncronas.
    """
    # 1. Persistencia automática
    await supabase_db.insert_sensor_data(sensor_data, user_id)
    
    if not is_anomaly(sensor_data):
        return [], []

    # 2. Consulta de contexto en paralelo si hay anomalía
    history_task = supabase_db.get_sensor_history(user_id)
    state_task = backend_state.get_state(user_id)
    
    history, current_state = await asyncio.gather(history_task, state_task)
    
    # 3. Prompt de monitoreo técnico con IA
    full_prompt = build_prompt(
        message="SISTEMA: Monitoreo automatizado. Analiza los datos y emite acciones SOLO si hay desviaciones críticas.", 
        sensor_data=sensor_data,
        history=history,
        backend_state=current_state
    )

    raw_text = await generate_raw_response(full_prompt)
    _, actions, alerts = extract_iot_data(raw_text)
    return actions, alerts

async def process_test_chat_request(message: str) -> Tuple[str, List[dict], List[str]]:
    """
    Lógica para el endpoint de prueba sin autenticación.
    """
    test_user_id = "00000000-0000-0000-0000-000000000000"
    current_state = await backend_state.get_state(test_user_id)
    
    sensor_data = {"temperature": 30.5, "humidity": 75.2, "ph": 6.5}
    try:
        if supabase_db.client:
            # Usar directamente el helper asíncrono que ya maneja el run_in_executor
            db_data = await supabase_db.get_latest_sensors(test_user_id)
            if db_data:
                sensor_data = {
                    "temperature": db_data.get("temperature", 30.5),
                    "humidity": db_data.get("humidity", 75.2),
                    "ph": db_data.get("ph", 6.5)
                }
    except Exception:
        pass

    full_prompt = build_prompt(
        message=message,
        sensor_data=sensor_data,
        history="[MODO EVALUACIÓN: Datos Históricos Simulados]",
        backend_state=current_state,
        chat_history="ENTORNO: Nodo de prueba público (Evaluación de Proyecto)."
    )
    
    raw_text = await generate_raw_response(full_prompt)
    return extract_iot_data(raw_text)
