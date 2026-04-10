import asyncio
import logging
from typing import Tuple, List, Dict, Any
from app.modules.iot.services.iot_service import iot_service as iot
from app.modules.chat.services.chat_service import chat_service as chat
from app.modules.identity.services.identity_service import identity_service as idsvc
from app.modules.iot.services.state_service import backend_state
from app.core.ai.llm import generate_raw_response
from app.core.ai.prompts import build_prompt
from app.core.ai.tools import IOT_TOOLS
from app.core.utils.parser import extract_iot_data, is_anomaly, predict_danger
from app.core.utils.aggregators import aggregate_sensor_data

logger = logging.getLogger(__name__)

async def process_tool_calls(response: Any, user_id: str) -> Tuple[List[dict], List[str]]:
    """Procesa llamadas a funciones devueltas por el LLM."""
    actions = []
    alerts = []
    
    # Si la respuesta es un mensaje con tool_calls (GenAI SDK format)
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate.content, "parts"):
            for part in candidate.content.parts:
                if hasattr(part, "call"):
                    call = part.call
                    name = call.name
                    args = call.args
                    
                    if name == "control_actuador":
                        actions.append({
                            "device": args.get("device"),
                            "action": args.get("action"),
                            "reason": args.get("reason")
                        })
                    elif name == "configurar_umbrales":
                        # Acción inmediata en DB a través de Identity Service
                        await idsvc.update_alert_threshold(
                            user_id, 
                            args.get("sensor_type"), 
                            args.get("min_value"), 
                            args.get("max_value")
                        )
                        alerts.append(f"Umbrales para {args.get('sensor_type')} actualizados.")
                    elif name == "registrar_mantenimiento":
                        # El mantenimiento es una preocupación de IoT/Hardware
                        # TODO: Mover log_maintenance a iot_service if missing
                        # Por ahora usamos el cliente directo si no está en iot
                        await iot.client.table("maintenance_log").insert({
                            "user_id": user_id, "task": args.get("task"), "notes": args.get("notes")
                        }).execute()
                        alerts.append(f"MANTENIMIENTO REGISTRADO: {args.get('task')}")
    
    return actions, alerts

async def process_chatbot_request(message: str, user_id: str, session_id: str | None = None) -> Tuple[str, List[dict], List[str]]:
    """
    Orquesta el flujo completo con procesamiento paralelo.
    """
    # 1. Obtener datos externos en PARALELO usando servicios por dominio
    raw_history_task = chat.get_chat_history_raw(user_id, limit=15, session_id=session_id)
    history_task = iot.get_sensor_history_raw(user_id, limit=20) # RAW para ML/Análisis
    state_task = backend_state.get_state(user_id)
    latest_sensors_task = iot.get_latest_sensors(user_id)
    thresholds_task = idsvc.get_alert_thresholds(user_id)

    raw_history, history_raw, current_state, latest_sensors, thresholds = await asyncio.gather(
        raw_history_task, history_task, state_task, latest_sensors_task, thresholds_task
    )
    
    # Formatear historial para el prompt (LLM)
    history_text = "\n".join([
        f"- {h.get('created_at', '')}: T={h.get('temperature')}°C, H={h.get('humidity')}%" 
        for h in history_raw
    ]) if history_raw else "No hay datos históricos."
    
    # 2. Smart Sliding Window & Memory Compression
    chat_context = ""
    if raw_history and len(raw_history) > 6:
        older = raw_history[:-4]
        recent = raw_history[-4:]
        older_text = "\n".join([f"{r['role']}: {r['message']}" for r in older])
        # Memory Compression via LLM
        summary_prompt = f"Resume los puntos clave de esta charla previa en 2 líneas. Omite saludos. Charla:\n{older_text}"
        long_term_summary = await generate_raw_response(summary_prompt)
        chat_context = f"[Resumen Memoria a Largo Plazo]:\n{long_term_summary}\n\n[Memoria a Corto Plazo]:\n"
        for r in recent:
            chat_context += f"{'USUARIO' if r['role']=='user' else 'AgroNexus'}: {r['message']}\n"
    elif raw_history:
        for r in raw_history:
            chat_context += f"{'USUARIO' if r['role']=='user' else 'AgroNexus'}: {r['message']}\n"
            
    # 3. Construir prompt enriquecido
    full_prompt = build_prompt(
        message=message, 
        sensor_data=latest_sensors,
        history=history_text,
        backend_state=current_state,
        chat_history=chat_context
    )

    # 4. Obtener respuesta del LLM con TOOLS habilitadas
    response = await generate_raw_response(full_prompt, tools=IOT_TOOLS)
    
    # 5. Extraer datos estructurados (Dual mode: Tool calls + Regex fallback)
    tool_actions, tool_alerts = await process_tool_calls(response, user_id)
    
    # Fallback a texto plano si no hubo tool calls o para extraer texto de respuesta
    raw_text = response.text if hasattr(response, "text") and response.text else str(response)
    clean_text, regex_actions, regex_alerts = extract_iot_data(raw_text)
    
    actions = tool_actions or regex_actions
    alerts = tool_alerts + regex_alerts
    
    # 6. Guardar Memoria Conversacional
    await chat.save_chat_message(user_id, "user", message, session_id)
    await chat.save_chat_message(user_id, "ai", clean_text, session_id)
    
    # 7. Log Actuador Actions (Si existen)
    if actions:
        await asyncio.gather(*[
            iot.log_actuator_action(user_id, a.get("device"), a.get("action"), a.get("reason"), triggered_by="AI")
            for a in actions
        ])
    
    return clean_text, actions, alerts

async def process_automated_telemetry(sensor_data: Dict[str, Any], user_id: str) -> Tuple[List[dict], List[str]]:
    """
    Procesa telemetría de hardware con paralelismo total y corrección de tipos.
    """
    # 1. Obtener todo el contexto en paralelo para evitar latencia y advertencias de "never awaited"
    history_task = iot.get_sensor_history_raw(user_id, limit=20)
    state_task = backend_state.get_state(user_id)
    thresholds_task = idsvc.get_alert_thresholds(user_id)
    
    history_raw, current_state, thresholds = await asyncio.gather(
        history_task, state_task, thresholds_task
    )
    
    # 2. Análisis de Anomalías y Predicción
    anomaly = is_anomaly(sensor_data, thresholds)
    predictive_alerts = predict_danger(sensor_data, history_raw)
    
    if not anomaly and not predictive_alerts:
        return [], []

    # 3. Formatear historial para el Prompt (solo si hay algo que reportar)
    history_text = "\n".join([
        f"- {h.get('created_at', '')}: T={h.get('temperature')}°C, H={h.get('humidity')}%" 
        for h in history_raw
    ]) if history_raw else "No hay datos históricos."
    
    # 4. Generar respuesta de la IA con autoridad de control
    full_prompt = build_prompt(
        message="SISTEMA DE CONTROL AGRO-NEXUS: Monitoreo crítico detectado. Los sensores muestran valores fuera de rango. Debes emitir acciones CORRECTIVAS inmediatas (ej. FAN ON, PUMP ON) si los niveles de temperatura, humedad o pH ponen en riesgo el cultivo.", 
        sensor_data=sensor_data,
        history=history_text,
        backend_state=current_state
    )

    response = await generate_raw_response(full_prompt, tools=IOT_TOOLS)
    tool_actions, tool_alerts = await process_tool_calls(response, user_id)
    
    actions = tool_actions
    alerts = predictive_alerts + tool_alerts
    
    # Fallback mejorado: Si no hubo tool calls, procesar el texto plano como string
    if not actions:
        # Si 'response' ya es un string (de llm.py), lo usamos directamente. 
        # Si es un objeto de respuesta, sacamos el .text.
        raw_output = response.text if hasattr(response, "text") else str(response)
        _, regex_actions, regex_alerts = extract_iot_data(raw_output)
        actions = regex_actions
        alerts += regex_alerts

    # 5. Log e Inyección de metadatos de zona
    if actions:
        zone_id = sensor_data.get("zone_id")
        for a in actions:
            if not a.get("zone_id"):
                a["zone_id"] = zone_id
        
        await asyncio.gather(*[
            iot.log_actuator_action(
                user_id, 
                a.get("device"), 
                a.get("action"), 
                a.get("reason"), 
                triggered_by="AI",
                zone_id=a.get("zone_id")
            )
            for a in actions
        ])

    return actions, alerts

async def process_test_chat_request(message: str) -> Tuple[str, List[dict], List[str]]:
    """
    Lógica para el endpoint de prueba sin autenticación.
    """
    test_user_id = "00000000-0000-0000-0000-000000000000"
    current_state = await backend_state.get_state(test_user_id)
    
    sensor_data = {"temperature": 30.5, "humidity": 75.2, "ph": 6.5}
    try:
        # Usar directamente el helper asíncrono
        db_data = await iot.get_latest_sensors(test_user_id)
        if db_data:
            sensor_data = {
                "temperature": db_data.get("temperature", 30.5),
                "humidity": db_data.get("humidity", 75.2),
                "ph": db_data.get("ph", 6.5)
            }
    except Exception:
        pass

    full_prompt = build_prompt(
        message=message,
        sensor_data=sensor_data,
        history="[MODO EVALUACIÓN: Datos Históricos Simulados]",
        backend_state=current_state,
        chat_history="ENTORNO: Nodo de prueba público (Evaluación de Proyecto)."
    )
    
    raw_text = await generate_raw_response(full_prompt)
    return extract_iot_data(raw_text)

def _build_fallback_report(aggregated_data: dict, latest: dict, zone_name: str, hours: int, focus: str) -> str:
    """
    Genera un reporte estadístico en Markdown si el LLM falla o está ocupado.
    """
    focus_title = focus.upper()
    return f"""# REPORTE TÉCNICO AGRONÓMICO: {zone_name} (FALLBACK)

> [!WARNING]
> **Modo Fallback Activo**: El motor de Análisis de IA se encuentra bajo alta demanda temporal. Se presenta el reporte estadístico de métricas crudas.

## 1. RESUMEN TÉCNICO DE KPIs ({hours}h)

| Métrica | Promedio Histórico | Valor Actual | Tendencia |
|---------|------------------|--------------|-----------|
| **Temperatura** | {aggregated_data.get('avg_temp', 'N/A')}°C | {latest.get('temperature', 'N/A')}°C | {aggregated_data.get('trend_temp', 'ESTABLE')} |
| **Humedad** | {aggregated_data.get('avg_humidity', 'N/A')}% | {latest.get('humidity', 'N/A')}% | {aggregated_data.get('trend_humidity', 'ESTABLE')} |
| **pH** | {aggregated_data.get('avg_ph', 'N/A')} | {latest.get('ph', 'N/A')} | {aggregated_data.get('trend_ph', 'ESTABLE')} |
| **EC** | {aggregated_data.get('avg_ec', 'N/A')} mS/cm | {latest.get('ec', 'N/A')} mS/cm | {aggregated_data.get('trend_ec', 'ESTABLE')} |

## 2. ANÁLISIS DE ESTADO BÁSICO
* **Enfoque solicitado:** {focus_title}
* **Última actualización:** {latest.get('created_at', 'Desconocido')}

*Nota: Para obtener recomendaciones avanzadas de un agrónomo experto, por favor solicita un nuevo reporte en unos minutos una vez que la capacidad del modelo se normalice.*
"""

async def process_report_request(user_id: str, zone_id: str = None, hours: int = 24, focus: str = "general", session_id: str | None = None) -> str:
    """
    Genera un reporte agronómico detallado en formato Markdown para el chat.
    """
    # 1. Obtener datos técnicos
    try:
        limit = min(60 * hours, 1440) 
        history_raw = await iot.get_sensor_history_raw(user_id, zone_id=zone_id, limit=limit)
    except Exception as e:
        logger.error(f"Error obteniendo datos técnicos para reporte: {e}")
        return "Hubo un error al obtener los datos de los sensores de la base de datos. Por favor, reintenta más tarde."

    if not history_raw:
        return "No hay datos suficientes para generar un reporte detallado en este momento."
        
    latest = history_raw[0]
    aggregated_data = aggregate_sensor_data(history_raw)
    zone_name = latest.get("zone_name", "Zona Alpha")
    
    # 2. Generar Diagnóstico IA de Alto Nivel con Prompt Enriquecido
    prompt = f"""
    ACTÚA COMO UN AGRÓNOMO EXPERTO SENIOR CON ESPECIALIDAD EN AGRICULTURA DE PRECISIÓN Y DATOS IOT.
    TU OBJETIVO ES ENTREGAR UN DIAGNÓSTICO TÉCNICO PROFESIONAL, ANALÍTICO Y ACCIONABLE.

    CONTEXTO DEL REPORTE:
    - ENFOQUE: {focus.upper()} 
    - ZONA: {zone_name} 
    - PERIODO DE ANÁLISIS: Últimas {hours} horas.

    ---
    1. DATOS ACTUALES DE SENSORES (TIEMPO REAL):
    {latest}

    2. RESUMEN ESTADÍSTICO AGREGADO DEL PERIODO:
    {aggregated_data}
    ---

    TAREA:
    Escribe un REPORTE TÉCNICO detallado utilizando el siguiente formato exacto en MARKDOWN:

    # REPORTE TÉCNICO AGRONÓMICO: {zone_name}

    ## 1. RESUMEN TÉCNICO DE KPIs
    (Crea una tabla de Markdown que compare los promedios del periodo vs valores actuales y su tendencia (ASC/DESC/ESTABLE). Explica brevemente si los valores están dentro del rango óptimo para cultivos estándar).

    ## 2. ANÁLISIS DEL MICRO-CLIMA Y ENTORNO
    (Analiza la temperatura y humedad. Explica la relación entre ambos y, de ser posible, comenta sobre el VPD (Déficit de Presión de Vapor) observado y su impacto en la transpiración).

    ## 3. ESTADO DE SUELO Y NUTRICIÓN
    (Analiza pH, EC, humedad y temperatura de suelo. Comenta cómo estas condiciones afectan la disponibilidad de nutrientes para la planta según las tendencias observadas).

    ## 4. EVALUACIÓN DE RIESGOS Y ALERTAS
    (Identifica anomalías o desviaciones críticas. Evalúa el riesgo de plagas, enfermedades fúngicas o estrés abiótico basado en el historial reciente).

    ## 5. RECOMENDACIONES ACCIONABLES (ENFOQUE: {focus.upper()})
    (Proporciona al menos 3 pasos concretos que el usuario deba realizar (ej: ajustar riego, ventilar, verificar sensores ph, etc). Sé específico y data-driven).

    ## 6. CONCLUSIÓN Y VERIFICACIÓN EN CAMPO
    (Cierra con un juicio experto sobre la salud global del invernadero).

    REGLAS DE ESTILO:
    - Tono: Sobrio, técnico, empoderador.
    - Evita generalidades como "tus plantas están bien". Usa: "Los niveles de humedad del 85% indican un riesgo latente de Botrytis".
    - Extensión: Sé exhaustivo pero directo al grano.
    """
    
    try:
        report_text = await generate_raw_response(prompt)
    except Exception as e:
        logger.error(f"LLM falló para reporte: {e}")
        report_text = _build_fallback_report(aggregated_data, latest, zone_name, hours, focus)
        
    # 3. Persistencia en Chat (Opcional pero recomendado)
    try:
        if session_id:
            user_msg = f"Solicitud de reporte: {focus} ({hours}h)"
            await chat.save_chat_message(user_id, "user", user_msg, session_id)
            await chat.save_chat_message(user_id, "ai", report_text, session_id)
    except Exception as e:
        logger.error(f"Error guardando contexto del reporte en DB: {e}")
            
    return report_text
