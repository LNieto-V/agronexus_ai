import json
import re
import logging
from typing import Tuple, List, Dict, Any
from app.services.supabase_service import supabase_db
from app.services.state_service import backend_state
from app.llm import generate_raw_response
from app.prompts import build_prompt

logger = logging.getLogger(__name__)

async def process_chatbot_request(message: str) -> Tuple[str, List[dict], List[str]]:
    """
    Orquesta el flujo completo de una solicitud del usuario humano:
    1. Obtiene contexto histórico, de estado y LOS ÚLTIMOS DATOS DE SENSORES.
    2. Construye el prompt enriquecido.
    3. Llama al LLM.
    4. Extrae y formatea la respuesta IoT.
    """
    # 1. Obtener contexto externo (incluyendo los últimos sensores registrados)
    history = supabase_db.get_sensor_history()
    current_state = backend_state.get_state()
    latest_sensors = supabase_db.get_latest_sensors()
    
    # 2. Construir prompt usando los últimos datos automáticos
    full_prompt = build_prompt(
        message=message, 
        sensor_data=latest_sensors,
        history=history,
        backend_state=current_state
    )

    # 3. Obtener respuesta del LLM
    raw_text = await generate_raw_response(full_prompt)
    
    # 4. Extraer datos estructurados
    return extract_iot_data(raw_text)

async def process_automated_telemetry(sensor_data: Dict[str, Any]) -> Tuple[List[dict], List[str]]:
    """
    Procesa telemetría de hardware (ESP32):
    1. Guarda los datos en Supabase automáticamente.
    2. FILTRO: Solo consulta a la IA si hay anomalías importantes.
    3. Retorna acciones solo cuando es crítico (Ahorra Cuota API).
    """
    # 1. Persistencia automática (Siempre ocurre)
    supabase_db.insert_sensor_data(sensor_data)
    
    # 2. Verificar anomalías (Umbrales de seguridad)
    if not is_anomaly(sensor_data):
        logger.info("Datos recibidos: OK. Saltando IA para ahorrar cuota.")
        return [], [] # Todo normal, no hay acciones ni alertas requeridas

    # 3. Datos anómalos encontrados -> Activar IA
    logger.warning("Anomalía detectada. Consultando a la IA...")
    
    # Obtener contexto
    history = supabase_db.get_sensor_history()
    current_state = backend_state.get_state()
    
    # Prompt de monitoreo técnico
    full_prompt = build_prompt(
        message="SISTEMA: Monitoreo automatizado. Analiza los datos y emite acciones SOLO si hay desviaciones críticas.", 
        sensor_data=sensor_data,
        history=history,
        backend_state=current_state
    )

    # Llamada al LLM (Solo ocurre en anomalías)
    raw_text = await generate_raw_response(full_prompt)
    
    # Extraer acciones de emergencia
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
    
    # Extraer bloque JSON usando regex (formato markdown)
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not json_match:
        # Intentar buscar sin los delimitadores de markdown
        json_match = re.search(r"(\{.*\"actions\".*\})", text, re.DOTALL)
        
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            actions = data.get("actions", [])
            alerts = data.get("alerts", [])
            
            # Remover el bloque JSON del texto original para dejar solo el mensaje humano
            # Esto es más seguro que un split si la IA escribe algo después
            clean_text = text.replace(json_match.group(0), "").strip()
        except Exception as e:
            logger.warning(f"Error parseando JSON de respuesta: {e}")
            clean_text = text
    else:
        clean_text = text

    return clean_text, actions, alerts
