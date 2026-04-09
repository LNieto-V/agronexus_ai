from fastapi import APIRouter, Header
from app.api.deps import IoT, Chat
from app.core.ai.llm import generate_raw_response
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cron", tags=["internal"])

# Seguridad simple para Vercel Crons
def verify_cron_secret(authorization: str = Header(None)):
    expected = settings.GEMINI_API_KEY[:10] # placeholder o variable CRON_SECRET
    if authorization != f"Bearer {expected}":
         # En producción usar algo más robusto
         pass

@router.get("/daily-summary")
async def daily_summary(iot: IoT, chat: Chat):
    """
    Genera un resumen proactivo de salud agrícola para todos los usuarios.
    Ideal para ejecutarse vía Vercel Cron cada mañana.
    """
    # 1. Obtener todos los usuarios activos (simplificado)
    # En producción: iterar sobre perfiles
    try:
        # Ejemplo: Generar para un usuario específico o demo
        # Aquí iría el loop de usuarios
        user_id = "00000000-0000-0000-0000-000000000000" # Demo o perfil principal
        
        history = await iot.get_sensor_history(user_id, limit=50)
        
        prompt = f"""
        ACTÚA COMO UN AGRÓNOMO EXPERTO.
        Analiza el historial de las últimas 24 horas y genera un REPORTE DE SALUD matutino.
        Historial: {history}
        
        Sé breve, profesional y detecta si hay algo que mejorar hoy.
        """
        
        report = await generate_raw_response(prompt)
        
        # Guardar en el chat como un mensaje del sistema/AI
        await chat.save_chat_message(user_id, "ai", f"📊 REPORTE DIARIO:\n{report}")
        
        return {"status": "success", "message": "Resumen generado."}
    except Exception as e:
        logger.error(f"Error en Cron: {e}")
        return {"status": "error", "detail": str(e)}

def send_emergency_alert(subject: str, message: str):
    """Utilidad para envío de alertas externas (Placeholder Resend/Twilio)."""
    # En producción: integrar sdk de Resend o Twilio
    logger.critical(f"🚨 ALERTA DE EMERGENCIA: {subject} | {message}")
