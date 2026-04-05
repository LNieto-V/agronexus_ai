---
name: gemini-ai-agent
description: >
  Skill para la orquestación del agente de IA con Google Gemini, incluyendo 
  ingeniería de prompts modulares, inyección de contexto RAG en tiempo real 
  y gestión de memoria conversacional para agricultura de precisión.
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 🤖 AgroNexus AI — Gemini Agent Skill

Este skill define cómo el agente de IA comprende, construye y optimiza las 
interacciones con el modelo Google Gemini dentro del ecosistema AgroNexus.

## Capacidades

### 1. Ingeniería de Prompts Modulares
- Sistema de prompts basado en archivos Markdown independientes (`prompt.md`, `rules.md`, `knowledge.md`, `devices.md`).
- Cada archivo se carga con `@lru_cache` para evitar lecturas redundantes al disco.
- La función `build_prompt()` en `app/prompts.py` ensambla el prompt final concatenando:
  1. **Persona** (prompt.md): Rol, tono y personalidad del agente agrícola.
  2. **Conocimiento** (knowledge.md): Base de datos de cultivos costeros tropicales.
  3. **Dispositivos** (devices.md): Inventario y protocolos de actuadores IoT.
  4. **Reglas** (rules.md): Restricciones de formato JSON y seguridad.
  5. **Contexto dinámico**: Sensores, historial, estado del sistema e historial del chat.

### 2. Inyección de Contexto RAG (Retrieval-Augmented Generation)
- **Datos de sensores en tiempo real**: Últimos valores de `sensor_data` del usuario.
- **Historial de 24h**: Tendencias de temperatura y humedad (hasta 20 registros).
- **Estado interno del backend**: Modo del sistema (AUTO/MANUAL), salud de la bomba, alertas activas.
- **Memoria conversacional**: Últimos 6 mensajes del chat para continuidad del diálogo.

### 3. Gestión del Modelo LLM
- **Modelo**: `gemini-2.0-flash` (configurado en `app/llm.py`).
- **Generación asíncrona**: `generate_raw_response()` utiliza `asyncio` para no bloquear el event loop de FastAPI.
- **Manejo de cuota**: Detección de errores `429 (ResourceExhausted)` con mensaje amigable al usuario.
- **Reintentos**: El servicio propaga la excepción `CUOTA_AGOTADA` al router para respuesta HTTP adecuada.

### 4. Extracción de Datos Estructurados
- La respuesta del LLM incluye un bloque ```` ```json ```` con `actions` y `alerts`.
- `extract_iot_data()` usa regex para separar el texto humano del JSON de control.
- Las acciones (`FAN ON`, `IRRIGATION OFF`) se envían de vuelta al hardware ESP32.

## Flujo de Prompt (Diagrama)

```
┌───────────────────────────────────────┐
│          build_prompt()               │
├───────────────────────────────────────┤
│  1. prompt.md     → Persona           │
│  2. knowledge.md  → Cultivos          │
│  3. devices.md    → Actuadores        │
│  4. rules.md      → Formato/Seguridad │
│  5. sensor_data   → Tiempo Real       │
│  6. history       → Tendencias 24h    │
│  7. backend_state → Estado Interno    │
│  8. chat_history  → Memoria (6 msgs) │
│  9. message       → Input del Usuario │
└───────────────────────────────────────┘
              │
              ▼
    ┌──────────────────┐
    │  Gemini 2.0 Flash │
    └──────────────────┘
              │
              ▼
    ┌──────────────────┐
    │ extract_iot_data()│
    │  → text, actions, │
    │    alerts          │
    └──────────────────┘
```

## Archivos Clave
- `app/prompts.py`: Constructor modular de prompts.
- `app/llm.py`: Cliente asíncrono de Google Gemini.
- `app/services/iot_service.py`: Orquestador que conecta prompt → LLM → extracción.

## Buenas Prácticas
1. **Nunca hardcodear prompts** en los routers. Siempre usar `build_prompt()`.
2. **Mantener knowledge.md actualizado** con datos agronómicos relevantes a la zona.
3. **Evitar llamadas innecesarias a Gemini** — el filtro de anomalías reduce el consumo de cuota en ~70%.
4. **Siempre incluir chat_history** en solicitudes humanas para mantener coherencia conversacional.
