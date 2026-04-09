import asyncio
from app.core.repositories.base_repo import BaseRepository, logger

class SensorRepository(BaseRepository):
    async def get_sensor_history(self, user_id: str, limit: int = 20, zone_id: str = None) -> str:
        if not self.client:
            return "Error: Supabase no configurado."
        try:
            loop = asyncio.get_event_loop()
            
            def query_builder():
                q = self.client.table("sensor_data").select("*").eq("user_id", user_id)
                if zone_id:
                    q = q.eq("zone_id", zone_id)
                return q.order("created_at", desc=True).limit(limit).execute()

            response = await loop.run_in_executor(None, query_builder)
            
            if not response.data:
                return "No hay datos históricos disponibles."
            summary = "Historial reciente:\n"
            for row in response.data:
                summary += f"- {row['created_at']}: T={row.get('temperature')}°C, H={row.get('humidity')}%\n"
            return summary
        except Exception as e:
            logger.error(f"Error en SensorRepository.get_sensor_history: {e}")
            return f"Error técnico: {str(e)}"

    async def get_latest_sensors(self, user_id: str, zone_id: str = None) -> dict:
        if not self.client: 
            return {}
        try:
            loop = asyncio.get_event_loop()
            
            def query_builder():
                q = self.client.table("sensor_data").select("*").eq("user_id", user_id)
                if zone_id:
                    q = q.eq("zone_id", zone_id)
                return q.order("created_at", desc=True).limit(1).execute()

            response = await loop.run_in_executor(None, query_builder)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error en SensorRepository.get_latest_sensors: {e}")
            return {}

    async def get_sensor_history_raw(self, user_id: str, limit: int = 50, offset: int = 0, zone_id: str = None) -> list:
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()
            
            def query_builder():
                q = self.client.table("sensor_data").select("*").eq("user_id", user_id)
                if zone_id:
                    q = q.eq("zone_id", zone_id)
                return q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

            response = await loop.run_in_executor(None, query_builder)
            return response.data
        except Exception as e:
            logger.error(f"Error en SensorRepository.get_sensor_history_raw: {e}")
            return []

    async def insert_sensor_data(self, data: dict, user_id: str) -> bool:
        if not self.client: 
            return False
        try:
            data["user_id"] = user_id
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.client.table("sensor_data").insert(data).execute()
            )
            logger.info("Sensor data inserted successfully via Repo.")
            return True
        except Exception as e:
            logger.error(f"Error en SensorRepository.insert_sensor_data: {e}")
            return False
