from pydantic import BaseModel, Field
from typing import List, Optional

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
