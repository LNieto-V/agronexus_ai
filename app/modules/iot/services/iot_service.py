import asyncio
import logging
from app.core.database import supabase_client
from app.modules.iot.repositories.sensor_repo import SensorRepository
from app.modules.iot.repositories.actuator_repo import ActuatorRepository

logger = logging.getLogger(__name__)

class IoTService:
    def __init__(self):
        self._client = None
        self._sensor_repo = None
        self._actuator_repo = None

    @property
    def db(self):
        if not self._client:
            from app.core.database import get_supabase_client
            self._client = get_supabase_client()
        return self._client

    @property
    def sensor_repo(self):
        if not self._sensor_repo:
            from app.modules.iot.repositories.sensor_repo import SensorRepository
            self._sensor_repo = SensorRepository(self.db)
        return self._sensor_repo

    @property
    def actuator_repo(self):
        if not self._actuator_repo:
            from app.modules.iot.repositories.actuator_repo import ActuatorRepository
            self._actuator_repo = ActuatorRepository(self.db)
        return self._actuator_repo

    async def get_sensor_history(self, user_id: str, limit: int = 20, zone_id: str = None) -> str:
        return await self.sensor_repo.get_sensor_history(user_id, limit, zone_id)

    async def get_latest_sensors(self, user_id: str, zone_id: str = None) -> dict:
        return await self.sensor_repo.get_latest_sensors(user_id, zone_id)

    async def insert_sensor_data(self, data: dict, user_id: str) -> bool:
        return await self.sensor_repo.insert_sensor_data(data, user_id)

    async def get_sensor_history_raw(self, user_id: str, limit: int = 50, offset: int = 0, zone_id: str = None) -> list:
        return await self.sensor_repo.get_sensor_history_raw(user_id, limit, offset, zone_id)

    async def log_actuator_action(self, user_id: str, device: str, action: str, reason: str = None, triggered_by: str = "AI", zone_id: str = None):
        return await self.actuator_repo.log_action(user_id, device, action, reason, triggered_by, zone_id)

    async def get_actuator_logs(self, user_id: str, limit: int = 50, offset: int = 0, zone_id: str = None):
        return await self.actuator_repo.get_logs(user_id, limit, offset, zone_id)

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
        if not self.db:
            logger.error(f"Cannot get zones: DB client is None for user {user_id}")
            return []
        try:
            target_id = user_id.strip() if isinstance(user_id, str) else user_id
            logger.info(f"FETCHING ZONES for user_id: '{target_id}'")
            
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, 
                lambda: self.db.table("zones")
                .select("*")
                .eq("user_id", target_id)
                .order("created_at", desc=False)
                .execute()
            )
            
            data = res.data or []
            logger.info(f"RETRIEVED {len(data)} zones for user {target_id}")
            
            if len(data) == 0:
                # Debug: check if table even has data
                count_res = await loop.run_in_executor(None, lambda: self.db.table("zones").select("id", count="exact").limit(1).execute())
                logger.debug(f"Total rows in zones table (audit): {getattr(count_res, 'count', 'unknown')}")
                
            return data
        except Exception as e:
            logger.error(f"Error fetching zones for {user_id}: {e}", exc_info=True)
            return []

    async def create_zone(self, user_id: str, name: str, crop_type: str = None):
        if not self.db:
            logger.error("Cannot create zone: DB client is None")
            return None
        try:
            loop = asyncio.get_event_loop()
            payload = {"user_id": user_id, "name": name, "crop_type": crop_type}
            res = await loop.run_in_executor(None, lambda: self.db.table("zones").insert(payload).execute())
            
            if res.data and len(res.data) > 0:
                logger.info(f"Zone created successfully in DB: {res.data[0]['id']}")
                return res.data[0]
            
            logger.error(f"Create zone returned no data. Possible RLS or DB constraint issue. Response: {res}")
            return None
        except Exception as e:
            logger.error(f"Exception in create_zone: {e}", exc_info=True)
            return None

    async def update_zone_heartbeat(self, zone_id: str):
        if not self.db:
            return
        try:
            loop = asyncio.get_event_loop()
            # Usar await en lugar de create_task para asegurar persistencia antes de que el proceso pueda morir o fallar
            await loop.run_in_executor(None, lambda: self.db.table("zones").update({"status": "ONLINE", "last_seen": "now()"}).eq("id", zone_id).execute())
        except Exception as e:
            logger.warning(f"Failed to update heartbeat for zone {zone_id}: {e}")

    async def delete_zone(self, user_id: str, zone_id: str) -> bool:
        if not self.db:
            return False
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: self.db.table("zones").delete().eq("user_id", user_id).eq("id", zone_id).execute())
            return len(res.data) > 0 if res.data else False
        except Exception as e:
            logger.error(f"Error deleting zone: {e}")
            return False

    async def update_zone(self, user_id: str, zone_id: str, name: str, crop_type: str = None):
        if not self.db:
            return None
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, 
                lambda: self.db.table("zones")
                .update({"name": name, "crop_type": crop_type})
                .eq("user_id", user_id)
                .eq("id", zone_id)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Exception in update_zone: {e}")
            return None

iot_service = IoTService()

