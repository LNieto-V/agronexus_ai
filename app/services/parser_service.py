import json
import re
from typing import Tuple, List, Dict, Any

def is_anomaly(data: Dict[str, Any]) -> bool:
    """Verifica si los datos de los sensores están fuera del rango de seguridad."""
    temp = data.get("temperature", 25)
    hum = data.get("humidity", 60)
    ph = data.get("ph", 6)
    
    if temp < 10 or temp > 38:
        return True
    if hum < 30 or hum > 95:
        return True
    if ph < 4.5 or ph > 8.0:
        return True
    
    return False

def extract_iot_data(text: str) -> Tuple[str, List[dict], List[str]]:
    """
    Extrae acciones JSON y alertas del texto de respuesta del LLM.
    Retorna: (clean_text, actions, alerts)
    """
    actions = []
    alerts = []
    clean_text = text
    
    json_patterns = [
        r"```json\s*(\{.*?\})\s*```",
        r"```\s*(\{.*?\})\s*```",
        r"(\{.*\"actions\".*?\})" 
    ]
    
    found_json = None
    full_match_text = None

    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
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
        clean_text = text.replace(full_match_text, "").strip()
        
    return clean_text, actions, alerts
