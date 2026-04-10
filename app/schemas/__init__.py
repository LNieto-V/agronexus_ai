from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DeviceAction(BaseModel):
    device: str = Field(..., description="Nombre del dispositivo (FAN, LIGHT, etc.)")
    action: str = Field(..., description="Acción a realizar (ON, OFF, AUTO)")
    reason: Optional[str] = Field(None, description="Motivo de la acción")

class SensorData(BaseModel):
    # Ambientales
    temperature: Optional[float] = None       # Temperatura del aire (°C)
    humidity: Optional[float] = None          # Humedad relativa del aire (%)
    vpd: Optional[float] = None               # Déficit de Presión de Vapor (kPa)
    co2: Optional[float] = None               # Dióxido de carbono (ppm)

    # Suelo / Sustrato
    soil_temperature: Optional[float] = None  # Temperatura de raíz/sustrato (°C)
    soil_moisture: Optional[float] = None     # Contenido volumétrico de agua VWC (%)
    
    # Calidad de nutrición 
    light: Optional[float] = None
    ph: Optional[float] = None
    ec: Optional[float] = None

    # Recursos
    tank_level: Optional[float] = None        # Nivel de tanque (%)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Si es None, usa contexto global (sin sesión)

class ChatResponse(BaseModel):
    response: str
    actions: List[DeviceAction] = []
    alerts: List[str] = []

class IOTTelemetryRequest(BaseModel):
    sensor_data: SensorData
    zone_id: Optional[str] = None

class IOTTelemetryResponse(BaseModel):
    actions: List[DeviceAction] = []
    alerts: List[str] = []

class SystemModeUpdate(BaseModel):
    mode: str # AUTO or MANUAL

class DashboardSummary(BaseModel):
    latest_sensors: SensorData
    system_state: dict
    active_alerts: List[str]

# --- Sesiones / Conversaciones ---
class ConversationCreate(BaseModel):
    title: str = "Nueva conversación"

class ConversationRename(BaseModel):
    title: str

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class ChatMessageOut(BaseModel):
    id: str
    role: str
    message: str
    created_at: datetime
    session_id: Optional[str] = None

class ChatHistoryOut(BaseModel):
    history: List[ChatMessageOut]
