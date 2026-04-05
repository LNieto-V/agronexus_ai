# Ejemplos de Uso de la Skill Backend-FastAPI-IoT

Esta skill permite al agente interactuar con el ecosistema AgroNexus. A continuación se detallan ejemplos prácticos de cómo utilizar los flujos del sistema:

## 1. Simulación de Envío de Telemetría (IoT a Backend)

Cuando el ESP32 envía datos de sensores, FastApi intercepta, valida API Keys y llama al orquestador.
```json
// POST /iot/telemetry
{
  "temperature": 29.5,
  "humidity": 65.0,
  "light": 850,
  "ph": 6.3,
  "ec": 1.6
}
```

## 2. Invocación de la IA (Frontend a Backend)

El usuario consulta el estado del cultivo mediante el chat.
```json
// POST /chat
{
  "message": "¿Mi tomate requiere más agua dadas las condiciones actuales?"
}
```
**Flujo Interno:**
1. Autentica JWT.
2. Recupera últimos datos de `sensor_data` (Supabase).
3. Recupera memoria de `chat_history`.
4. Inyecta RAG (Ej: `crops.md` para "tomate").
5. Gemini analiza y devuelve texto + alertas.
