import asyncio
import logging
from app.core.database import supabase_client
from app.modules.iot.repositories.sensor_repo import SensorRepository
from app.modules.iot.repositories.actuator_repo import ActuatorRepository

logger = logging.getLogger(__name__)

class IoTService:
    def __init__(self):
        self.sensor_repo = SensorRepository(supabase_client)
        self.actuator_repo = ActuatorRepository(supabase_client)
        self.client = supabase_client

    async def get_sensor_history(self, user_id: str, limit: int = 20) -> str:
        return await self.sensor_repo.get_sensor_history(user_id, limit)

    async def get_latest_sensors(self, user_id: str) -> dict:
        return await self.sensor_repo.get_latest_sensors(user_id)

    async def insert_sensor_data(self, data: dict, user_id: str) -> bool:
        return await self.sensor_repo.insert_sensor_data(data, user_id)

    async def get_sensor_history_raw(self, user_id: str, limit: int = 50, offset: int = 0) -> list:
        return await self.sensor_repo.get_sensor_history_raw(user_id, limit, offset)

    async def log_actuator_action(self, user_id: str, device: str, action: str, reason: str = None, triggered_by: str = "AI"):
        return await self.actuator_repo.log_action(user_id, device, action, reason, triggered_by)

    async def get_actuator_logs(self, user_id: str, limit: int = 50, offset: int = 0):
        return await self.actuator_repo.get_logs(user_id, limit) # TODO: Add offset to actuator_repo if needed

    async def get_stats(self, user_id: str, period_hours: int = 24):
        data = await self.get_sensor_history_raw(user_id, limit=200)
        if not data:
            return {}
        temps = [d['temperature'] for d in data if d.get('temperature') is not None]
        hums = [d['humidity'] for d in data if d.get('humidity') is not None]
        return {
            "temperature": {"avg": sum(temps)/len(temps), "min": min(temps), "max": max(temps)} if temps else {},
            "humidity": {"avg": sum(hums)/len(hums), "min": min(hums), "max": max(hums)} if hums else {},
            "count": len(data)
        }

    async def get_zones(self, user_id: str):
        if not self.client:
            return []
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: self.client.table("zones").select("*").eq("user_id", user_id).execute())
        return res.data or []

    async def create_zone(self, user_id: str, name: str, crop_type: str = None):
        if not self.client:
            return None
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: self.client.table("zones").insert({"user_id": user_id, "name": name, "crop_type": crop_type}).execute())
        return res.data[0] if res.data else None

    async def update_zone_heartbeat(self, zone_id: str):
        if not self.client:
            return
        loop = asyncio.get_event_loop()
        asyncio.create_task(loop.run_in_executor(None, lambda: self.client.table("zones").update({"status": "ONLINE", "last_seen": "now()"}).eq("id", zone_id).execute()))

iot_service = IoTService()
