from typing import List, Dict, Any
import datetime

def aggregate_sensor_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrega datos de sensores para consumo de la IA.
    Calcula Promedio, Min, Max y tendencia para las métricas principales.
    """
    if not data:
        return {}

    metrics = ['temperature', 'humidity', 'ph', 'ec', 'soil_moisture', 'soil_temperature', 'vpd', 'co2']
    summary = {
        "period_start": data[-1].get('created_at'),
        "period_end": data[0].get('created_at'),
        "samples_count": len(data),
        "metrics": {}
    }

    for metric in metrics:
        values = [d[metric] for d in data if d.get(metric) is not None]
        if not values:
            continue
            
        summary["metrics"][metric] = {
            "avg": round(sum(values) / len(values), 2),
            "min": min(values),
            "max": max(values),
            "start_val": round(values[-1], 2),
            "end_val": round(values[0], 2),
            "trend": "ESTABLE"
        }
        
        # Simple trend calculation
        diff = values[0] - values[-1]
        threshold = 0.5 if metric == 'temperature' else 2.0
        if diff > threshold:
            summary["metrics"][metric]["trend"] = "ASCENDENTE"
        elif diff < -threshold:
            summary["metrics"][metric]["trend"] = "DESCENDENTE"

    # Determinar estado general simplificado
    summary["critical_alerts"] = []
    # Aquí podríamos añadir lógica de umbrales rápidos si quisiéramos
    
    return summary
