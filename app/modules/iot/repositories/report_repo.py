import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReportRepository:
    def __init__(self, db_client):
        self.db = db_client

    async def save_report(self, user_id: str, zone_id: Optional[str], period_hours: int, focus: str, analysis: str, aggregated_data: Dict[str, Any]):
        """Guarda un reporte generado en la base de datos."""
        try:
            payload = {
                "user_id": user_id,
                "zone_id": zone_id,
                "period_hours": period_hours,
                "focus": focus,
                "analysis_text": analysis,
                "aggregated_data": aggregated_data
            }
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.db.table("ai_reports").insert(payload).execute())
            return True
        except Exception as e:
            logger.error(f"Error saving report to DB: {e}")
            return False

    async def get_latest_report(self, user_id: str, zone_id: Optional[str], period_hours: int, focus: str, max_age_hours: int = 4):
        """Busca el reporte más reciente que cumpla con los criterios."""
        try:
            since = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
            
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, 
                lambda: self.db.table("ai_reports")
                .select("*")
                .eq("user_id", user_id)
                .eq("zone_id", zone_id)
                .eq("period_hours", period_hours)
                .eq("focus", focus)
                .gte("created_at", since)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching latest report: {e}")
            return None
