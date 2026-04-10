import json
import re
import math
from typing import Tuple, List, Dict, Any

def predict_danger(current_data: Dict[str, Any], history: List[Dict[str, Any]]) -> List[str]:
    """
    Analiza tendencias para predecir peligros inminentes.
    ML Simple (Regresión Lineal Básica / Derivada).
    """
    predictions = []
    if not history or len(history) < 3:
        return []

    # Ordenar historial por tiempo (más reciente primero en nuestro Repo usualmente)
    # pero aquí necesitamos cronológico
    sorted_history = sorted(history, key=lambda x: x.get('created_at', ''))
    
    # 1. Tendencia de Temperatura (Subida rápida)
    recent_temps = [h.get('temperature') for h in sorted_history[-5:] if h.get('temperature')]
    if len(recent_temps) >= 3:
        # Calcular delta promedio
        deltas = [recent_temps[i] - recent_temps[i-1] for i in range(1, len(recent_temps))]
        avg_delta = sum(deltas) / len(deltas)
        
        # Si la temperatura sube > 0.5°C por cada registro (asuncion de tiempo breve entre registros)
        if avg_delta > 0.8:
            predictions.append("ALERTA PREDICTIVA: La temperatura sube peligrosamente rápido (+0.8°C/step).posible fallo en ventilación.")

    # 2. Tendencia de pH
    recent_ph = [h.get('ph') for h in sorted_history[-5:] if h.get('ph')]
    if len(recent_ph) >= 3:
        deltas_ph = [recent_ph[i] - recent_ph[i-1] for i in range(1, len(recent_ph))]
        avg_delta_ph = sum(deltas_ph) / len(deltas_ph)
        if abs(avg_delta_ph) > 0.3:
            predictions.append(f"TENDENCIA CRÍTICA: El pH está {'subiendo' if avg_delta_ph > 0 else 'bajando'} bruscamente (+/-0.3/step).")

    return predictions

def calculate_vpd(temp: float, humidity: float) -> float:
    """
    Calcula el Déficit de Presión de Vapor (VPD) en kPa.
    VPD = VPsat - VPair
    """
    if temp is None or humidity is None:
        return 0.0
    # Saturation Vapor Pressure (VPsat) en kPa usando Tetens formula
    vpsat = 0.61078 * math.exp((17.27 * temp) / (temp + 237.3))
    # Actual Vapor Pressure (VPair)
    vpair = vpsat * (humidity / 100.0)
    # VPD
    return round(vpsat - vpair, 2)

def is_anomaly(data: Dict[str, Any], thresholds: List[Dict[str, Any]] = None) -> bool:
    """
    Verifica si los datos de los sensores están fuera del rango de seguridad.
    Si se pasan thresholds (desde la DB), se usan esos rangos.
    """
    if thresholds:
        for t in thresholds:
            sensor = t.get("sensor_type")
            val = data.get(sensor)
            if val is not None:
                if (t.get("min_value") is not None and val < t["min_value"]) or \
                   (t.get("max_value") is not None and val > t["max_value"]):
                    return True
        return False

    # Fallback a rangos estáticos si no hay configuración en DB
    temp = data.get("temperature")
    hum = data.get("humidity")
    ph = data.get("ph")
    soil_temp = data.get("soil_temperature")
    soil_hum = data.get("soil_moisture")
    co2 = data.get("co2")
    tank = data.get("tank_level")
    vpd = data.get("vpd")

    # Clima ambiente
    if temp is not None and (temp < 10 or temp > 38): return True
    if hum is not None and (hum < 30 or hum > 95): return True
    
    # Suelo
    if soil_temp is not None and (soil_temp < 10 or soil_temp > 35): return True
    if soil_hum is not None and (soil_hum < 10 or soil_hum > 90): return True
    
    # Nutrición
    if ph is not None and (ph < 4.5 or ph > 8.5): return True
    
    # Premium / Recursos
    if co2 is not None and (co2 < 300 or co2 > 2000): return True
    if tank is not None and tank < 15: return True # Tanque bajo
    if vpd is not None and (vpd < 0.3 or vpd > 2.0): return True # Estrés hídrico
    
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
