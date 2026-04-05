from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DeviceAction(BaseModel):
    device: str = Field(..., description="Nombre del dispositivo (FAN, LIGHT, etc.)")
    action: str = Field(..., description="Acción a realizar (ON, OFF, AUTO)")
    reason: Optional[str] = Field(None, description="Motivo de la acción")

class SensorData(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None
    ph: Optional[float] = None
    ec: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Si es None, usa contexto global (sin sesión)

class ChatResponse(BaseModel):
    response: str
    actions: List[DeviceAction] = []
    alerts: List[str] = []

class IOTTelemetryRequest(BaseModel):
    sensor_data: SensorData

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
