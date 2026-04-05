---
name: backend-fastapi-iot
description: >
  Skill para construir y gestionar un backend modular con FastAPI especializado en 
  agricultura de precisión (IoT), integración con Supabase (Auth/DB) y agentes 
  inteligentes de Google Gemini.
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 🚜 AgroNexus AI Backend Skill

Este skill permite al agente entender y operar sobre el corazón del ecosistema AgroNexus.

## Capacidades

### 1. Orquestación IoT y Anomalías
- Procesamiento de telemetría desde ESP32 (`/iot/telemetry`).
- Detección de desviaciones críticas (Umbrales de T, H, pH) para optimizar el uso de LLM.
- Control de actuadores (FAN, LIGHT, IRRIGATION) mediante respuestas JSON estructuradas.

### 2. Seguridad Multi-Capa
- Validación de JWT (Supabase) para usuarios finales.
- Gestión de API Keys (SHA-256) con permisos `read`/`write` para dispositivos embebidos.
- Rotación y revocación dinámica de llaves.

### 3. Memoria Conversacional y Reranking
- Persistencia de chats en Supabase para evitar pérdida de contexto.
- Inyección de contexto dinámico (sensores actuales + historial 24h + estado del sistema) en el prompt del agente.

## Estructura del Skill
- `app/routers/`: Endpoints modulares.
- `app/services/`: Lógica de negocio (IoT, Security, Supabase).
- `Context Files (Prompting)`: Archivos integrados en este directorio:
    - `prompt.md`: Definición del rol y tono.
    - `rules.md`: Reglas de seguridad y formato JSON.
    - `knowledge.md`: Base de conocimientos agrícolas.
    - `devices.md`: Protocolos de dispositivos IoT.
