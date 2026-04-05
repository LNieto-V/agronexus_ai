import json
import re
import asyncio
import logging
from typing import Tuple, List, Dict, Any
from app.services.supabase_service import supabase_db
from app.services.state_service import backend_state
from app.llm import generate_raw_response
from app.prompts import build_prompt

logger = logging.getLogger(__name__)

async def process_chatbot_request(message: str, user_id: str) -> Tuple[str, List[dict], List[str]]:
    """
    Orquesta el flujo completo con procesamiento paralelo (asyncio.gather).
    """
    # 1. Obtener contexto externo en PARALELO (Optimización Crítica de Rendimiento)
    chat_history_task = supabase_db.get_chat_history(user_id)
    history_task = supabase_db.get_sensor_history(user_id)
    state_task = backend_state.get_state(user_id)
    latest_sensors_task = supabase_db.get_latest_sensors(user_id)

    # Disparar todas las peticiones a la vez
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

    # 3. Obtener respuesta del LLM (Sigue siendo el cuello de botella, pero el resto es ahora instantáneo)
    raw_text = await generate_raw_response(full_prompt)
    
    # 4. Extraer datos estructurados
    clean_text, actions, alerts = extract_iot_data(raw_text)
    
    # 5. Guardar Memoria Conversacional (En paralelo con el retorno para no bloquear al usuario)
    asyncio.create_task(supabase_db.save_chat_message(user_id, "user", message))
    asyncio.create_task(supabase_db.save_chat_message(user_id, "ai", clean_text))
    
    return clean_text, actions, alerts

async def process_automated_telemetry(sensor_data: Dict[str, Any], user_id: str) -> Tuple[List[dict], List[str]]:
    """
    Procesa telemetría de hardware con paralelismo y verificaciones asíncronas.
    """
    # 1. Persistencia automática y verificación inicial
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

def is_anomaly(data: Dict[str, Any]) -> bool:
    """Verifica si los datos de los sensores están fuera del rango de seguridad."""
    # Umbrales sugeridos
    temp = data.get("temperature", 25)
    hum = data.get("humidity", 60)
    ph = data.get("ph", 6)
    
    # Lógica de anomalía: True si algo está mal
    if temp < 10 or temp > 38:
        return True
    if hum < 30 or hum > 95:
        return True
    if ph < 4.5 or ph > 8.0:
        return True
    
    return False

def extract_iot_data(text: str) -> Tuple[str, List[dict], List[str]]:
    """
    Extracts JSON actions and alerts from the LLM response text.
    Returns: (clean_text, actions, alerts)
    """
    actions = []
    alerts = []
    clean_text = text
    
    # 1. Buscar bloques de código JSON (```json ... ``` o ``` ...)
    # Buscamos el patrón JSON estructurado con alertas y acciones
    json_patterns = [
        r"```json\s*(\{.*?\})\s*```",
        r"```\s*(\{.*?\})\s*```",
        r"(\{.*\"actions\".*?\})" # Fallback para JSON plano sin bloques
    ]
    
    found_json = None
    full_match_text = None

    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # Intentar parsear el JSON capturado
            try:
                candidate = match.group(1)
                data = json.loads(candidate)
                if "actions" in data or "alerts" in data:
                    found_json = data
                    full_match_text = match.group(0)
                    break
            except json.JSONDecodeError:
                continue

    if found_json:
        actions = found_json.get("actions", [])
        alerts = found_json.get("alerts", [])
        # Limpiar el texto removiendo el bloque JSON
        clean_text = text.replace(full_match_text, "").strip()
        
    return clean_text, actions, alerts
