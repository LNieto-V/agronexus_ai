from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

# Servidor FastMCP optimizado para Prefect Horizon
mcp = FastMCP("AgroNexusMCP")

class TelemetryData(BaseModel):
    timestamp: str = Field(description="Fecha y hora de la lectura en formato ISO 8601")
    temperature: float = Field(description="Temperatura ambiente en grados Celsius")
    humidity: float = Field(description="Humedad relativa ambiental en porcentaje")
    soil_moisture: float = Field(description="Humedad del suelo en porcentaje")
    nitrogen: float = Field(description="Nivel de Nitrógeno (mg/kg aproximado)")

class AnomalyReport(BaseModel):
    zone_id: str = Field(description="Identificador de la zona analizada")
    status: str = Field(description="Estado general (Normal, Cuidado, Crítico)")
    anomalies_detected: List[str] = Field(description="Lista detallada de advertencias o umbrales rotos")

@mcp.tool()
def get_zone_telemetry(zone_id: str, days: int = 7) -> List[TelemetryData]:
    """
    Obtiene los datos históricos de telemetría de humedad, temperatura y nutrientes
    para una zona de cultivo específica a lo largo del número de días especificado.
    Útil para el análisis de tendencias.
    
    Args:
        zone_id: Identificador único de la zona agrícola (ej. 'ZONA-A', 'ZONA-B')
        days: Rango de días hacia atrás a consultar (default: 7)
    """
    # En un entorno real se extraería de Supabase (from database.client import async_get...)
    # Para el MCP, mockeamos el flujo de datos siguiendo el principio de aislamiento o usando direct-DB hits
    data = []
    end_date = datetime.now()
    for i in range(days):
        current_date = end_date - timedelta(days=days - 1 - i)
        data.append(TelemetryData(
            timestamp=current_date.isoformat(),
            temperature=round(random.uniform(20.0, 35.0), 1),
            humidity=round(random.uniform(40.0, 80.0), 1),
            soil_moisture=round(random.uniform(30.0, 70.0), 1),
            nitrogen=round(random.uniform(20.0, 100.0), 1)
        ))
    return data

@mcp.tool()
def analyze_anomalies(zone_id: str) -> AnomalyReport:
    """
    Analiza la telemetría reciente de una zona para detectar anomalías o valores 
    que superan los umbrales de seguridad agronómica pre-establecidos (ej. alta temperatura).

    Args:
        zone_id: Identificador único de la zona agrícola
    """
    # Lógica de detección simulada
    anomalies = []
    
    temp = random.uniform(25.0, 42.0)
    if temp > 35.0:
        anomalies.append(f"ALERTA: Alta temperatura crítica detectada: {temp:.1f}°C (> 35.0°C)")
    
    moisture = random.uniform(10.0, 60.0)
    if moisture < 25.0:
        anomalies.append(f"ADVERTENCIA: Baja humedad en el suelo: {moisture:.1f}% (< 25.0%)")

    status = "Normal"
    if len(anomalies) > 0:
        status = "Crítico" if len(anomalies) > 1 else "Cuidado"

    return AnomalyReport(
        zone_id=zone_id,
        status=status,
        anomalies_detected=anomalies
    )

@mcp.tool()
def generate_agronomic_summary(zone_id: str) -> str:
    """
    Genera un resumen analítico accionable en lenguaje natural basado en los datos 
    recientes de los sensores.

    Args:
        zone_id: Identificador único de la zona agrícola
    """
    report = f"RESUMEN AGRONÓMICO PARA {zone_id}:\n"
    report += "--------------------------------------\n"
    report += "- CLIMA: Las temperaturas se han mantenido estables en las últimas 48h con un pico inusual a mediodía.\n"
    report += "- SUELO: Se requiere aumentar el riego. La humedad del suelo ha bajado del umbral óptimo (tendencia a la baja).\n"
    report += "- ACCIÓN RECOMENDADA: Programar ciclo de bomba de irrigación al 100% durante 15 minutos en el próximo horario de madrugada para equilibrar la hidratación.\n"
    
    return report

if __name__ == "__main__":
    mcp.run()
