# 🚜 AgroNexus AI: Backend de Agricultura de Precisión IoT

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-DB%20%26%20Auth-3ecf8e?logo=supabase)](https://supabase.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5--Flash-4285F4?logo=google-gemini)](https://ai.google.dev/)

**AgroNexus AI** es un ecosistema backend de alto rendimiento diseñado para la gestión inteligente de invernaderos. Basado en una arquitectura **DDD-Lite (Domain-Driven Design Lite)**, desacopla la lógica de negocio del hardware y la infraestructura, permitiendo una orquestación asíncrona entre telemetría IoT, inteligencia artificial (Google Gemini) y persistencia en la nube (Supabase).

---

## 🏗️ Arquitectura Modular (DDD-Lite)

El sistema está organizado en dominios independientes bajo una estructura de **Capas Desacopladas**, lo que permite una escalabilidad granular.

---

### 1️⃣ Capa de Entrada y Seguridad
Gestiona el tráfico entrante, valida la identidad (JWT vs API Key) y enruta las solicitudes.

```mermaid
graph TB
    subgraph Clients["🖥️ Clientes"]
        direction LR
        UI["📱 Ionic + Vue 3"]
        ESP["🔌 ESP32 (IoT)"]
        CRON["⏰ Vercel Cron"]
    end

    subgraph Gateway["⚡ API Gateway (FastAPI)"]
        direction TB
        CORS["CORS Middleware"]
        
        subgraph Auth["🔐 Autenticación"]
            JWT["JWT Validator<br/>(Supabase)"]
            APIKEY["API Key Validator<br/>(SHA-256)"]
        end

        subgraph Routes["📡 Routers"]
            R_AUTH["/auth"]
            R_IOT["/iot"]
            R_DASH["/dashboard"]
            R_CHAT["/chat"]
            R_ZONES["/zones"]
            R_CRON["/cron"]
        end
    end

    UI -->|"JWT Token"| CORS
    ESP -->|"API Key"| CORS
    CRON -->|"Bearer Secret"| R_CRON

    CORS --> Auth
    JWT --> R_AUTH & R_DASH & R_CHAT & R_ZONES
    APIKEY --> R_IOT

    classDef client fill:#1a1a2e,stroke:#e94560,color:#fff
    classDef gateway fill:#16213e,stroke:#0f3460,color:#fff
    class UI,ESP,CRON client
    class CORS,JWT,APIKEY,R_AUTH,R_IOT,R_DASH,R_CHAT,R_ZONES,R_CRON gateway
```

---

### 2️⃣ Capa de Dominio (Lógica de Negocio)
Contiene la inteligencia del sistema dividida por responsabilidades agrícolas.

```mermaid
graph LR
    subgraph Routes["📡 Routers"]
        R_IOT["/api/iot"]
        R_DASH["/api/dashboard"]
        R_CHAT["/api/chat"]
        R_AUTH["/api/auth"]
    end

    subgraph Domains["🧩 Módulos de Dominio"]
        subgraph MOD_IOT["📡 IoT & Invernadero"]
            IOT_SVC["IoT Service"]
            SSE["SSE Bus (Real-Time)"]
            STATE["State Control"]
            ANOMALY["Anomaly Detector"]
        end

        subgraph MOD_CHAT["💬 Asesoría IA"]
            ORCH["AI Orchestrator"]
            CHAT_SVC["Chat Service"]
        end

        subgraph MOD_ID["🪪 Identidad"]
            ID_SVC["Identity Service"]
        end
    end

    R_IOT --> IOT_SVC
    R_DASH --> IOT_SVC & STATE
    R_CHAT --> ORCH
    R_AUTH --> ID_SVC
    
    IOT_SVC --> SSE & ANOMALY
    ORCH --> CHAT_SVC
    ANOMALY --> ORCH

    classDef gateway fill:#16213e,stroke:#0f3460,color:#fff
    classDef domain fill:#0f3460,stroke:#533483,color:#fff
    class R_IOT,R_DASH,R_CHAT,R_AUTH gateway
    class IOT_SVC,SSE,STATE,ANOMALY,ORCH,CHAT_SVC,ID_SVC domain
```

---

### 3️⃣ Capa de Núcleo e Infraestructura
Orquestación con Inteligencia Artificial y persistencia de datos segura.

```mermaid
graph TB
    subgraph Domains["🧩 Servicios de Dominio"]
        direction LR
        IOT_REPO["IoT Repository"]
        CHAT_REPO["Chat Repository"]
        ID_REPO["Identity Repository"]
        ORCH["AI Orchestrator"]
    end

    subgraph Core["🧠 Inteligencia Artificial"]
        GEMINI["Google Gemini 2.5"]
        PROMPTS["Prompt Engine"]
    end

    subgraph Infra["☁️ Infraestructura (Supabase)"]
        direction LR
        SB_AUTH["Supabase Auth"]
        SB_DB["PostgreSQL (RLS)"]
    end

    ORCH --> PROMPTS --> GEMINI
    IOT_REPO & CHAT_REPO & ID_REPO --> SB_DB
    
    classDef domain fill:#0f3460,stroke:#533483,color:#fff
    classDef core fill:#533483,stroke:#e94560,color:#fff
    classDef infra fill:#2d6a4f,stroke:#40916c,color:#fff

    class IOT_REPO,CHAT_REPO,ID_REPO,ORCH domain
    class GEMINI,PROMPTS core
    class SB_AUTH,SB_DB infra
```

---

### 📂 Estructura del Proyecto
```text
agronexus_ai/
├── app/
│   ├── api/            # Capa de Entrada: Routers y Dependencias (Auth/DI)
│   │   └── routes/     # Endpoints de cada dominio
│   ├── core/           # Shared Kernel: AI (Prompts), Database, Security
│   ├── modules/        # Capa de Dominio: Servicios y Repositorios (Lógica pura)
│   │   ├── iot/        # Gestión de telemetría y actuadores
│   │   ├── chat/       # Orquestación de IA y sesiones RAG
│   │   └── identity/   # Gestión de perfiles, roles y llaves de seguridad
│   ├── schemas/        # DTOs: Modelos Pydantic para validación de datos
│   └── main.py         # Punto de entrada y configuración de FastAPI
└── database/           # Migraciones y scripts SQL (Supabase)
```

---

## 🚀 Instalación y Despliegue

### 1. Requisitos Previos
*   **Python 3.12+**
*   **UV** (Gestor de paquetes recomendado)
*   Cuentas en **Google AI Studio** y **Supabase**.

### 2. Configuración Inicial
```bash
# Sincronizar el entorno de desarrollo
uv sync

# Configurar variables de entorno
cp .env.example .env
```

| Variable | Responsabilidad |
|----------|-----------------|
| `SUPABASE_JWT_SECRET` | Validación de tokens de usuario (Auth). |
| `SUPABASE_SERVICE_ROLE_KEY` | Bypass de RLS para operaciones administrativas. |
| `GEMINI_API_KEY` | Llave primaria de la IA (Orquestador). |
| `GEMINI_API_KEYS` | *(Opcional)* Lista de llaves separadas por coma para rotación inteligente con balanceo de carga. |

### 3. Base de Datos (Replicable)

El esquema completo de la base de datos es **idempotente** y se puede replicar en cualquier instancia de Supabase ejecutando un único archivo SQL:

```bash
# Ejecutar en el SQL Editor de Supabase (Dashboard → SQL Editor → New Query)
database/migrations/schema_v1.sql
```

Este script crea automáticamente:

| # | Tabla | Propósito |
|---|-------|-----------|
| 1 | `sensor_data` | Telemetría IoT (ESP32). |
| 2 | `conversations` | Sesiones del sistema multi-chat. |
| 3 | `chat_history` | Mensajes persistentes (usuario ↔ IA). |
| 4 | `api_keys` | Autenticación de hardware (SHA-256). |
| 5 | `system_state` | Estado y modo de operación por usuario. |
| 6 | `profiles` | Perfiles con roles (owner, agronomist, viewer). |
| 7 | `actuator_log` | Historial de acciones de actuadores. |
| 8 | `alert_thresholds` | Umbrales personalizados de alerta. |
| 9 | `zones` | Invernaderos y áreas de cultivo. |
| 10 | `maintenance_log` | Registro de mantenimiento. |
| 11 | `ai_reports` | Persistencia de diagnósticos agronómicos (Caché IA). |

Además configura:
- 🔒 **Row Level Security (RLS)** en todas las tablas.
- ⚡ **Trigger automático** que inicializa perfil, estado y umbrales al registrar un usuario.
- 📇 **Índices optimizados** para consultas por `user_id` y `created_at`.

> [!TIP]
> El script usa `CREATE TABLE IF NOT EXISTS`, `DROP POLICY IF EXISTS` y bloques `DO $$` condicionales, por lo que puede ejecutarse múltiples veces sin errores.

---

## 🔐 Seguridad y Control de Acceso

Implementamos un modelo de **Confianza Cero** distribuido en tres capas:

1.  **Autenticación Humana (JWT)**: Acceso a la App mediante tokens de Supabase Auth.
2.  **Autenticación de Hardware (API Keys)**: Los dispositivos usan llaves cifradas (SHA-256).
    *   **Política Crítica**: Las llaves con permisos de **escritura** (`write`) deben estar vinculadas permanentemente a un `zone_id` específico.
3.  **Row Level Security (RLS)**: Cada dato en la base de datos pertenece estrictamente a un `user_id`, garantizando aislamiento total.

---

## 🔄 Resiliencia y Persistencia de Zonas

Para garantizar que el sistema sea robusto frente a reinicios del servidor o micro-cortes de red (comunes en despliegues Serverless o entornos de desarrollo):

1.  **Cliente Autocurativo**: El backend utiliza un patrón de *Lazy-Loading* para el cliente de Supabase. Si la conexión se pierde, el sistema intenta re-instanciar el cliente automáticamente en la siguiente petición.
2.  **Persistencia Garantizada de Zonas**: Las zonas de cultivo se guardan en Supabase de forma síncrona durante su creación y las actualizaciones de estado (*heartbeats*) se verifican antes de retornar la respuesta al hardware.
3.  **Inicialización Frontend (v2.6)**: El frontend utiliza un patrón de montaje centralizado en `TabsPage.vue` que garantiza que las zonas se recuperen de la base de datos en cada recarga de página, evitando estados vacíos en el selector superior.
4.  **Auditabilidad**: Se han incluido logs detallados que permiten rastrear el flujo de datos desde el ESP32 hasta la base de datos sin exponer secretos.

### 📡 Ejemplo de Integración Hardware (ESP32)

Para conectar un dispositivo físico o simulado sin exponer llaves reales:

**Solicitud de Telemetría (JSON):**
```json
// POST /api/iot/telemetry
// Header: X-API-Key: agnx_w_TU_LLAVE_AQUI (Hash SHA-256 en DB)
{
  "zone_id": "88b18d49-07bb-497a-bb35-be497058265c", // UUID de tu zona
  "sensor_data": {
    "temperature": 24.5,
    "humidity": 65.0,
    "light": 850,
    "ph": 6.2,
    "ec": 1.5
  }
}
```

**Respuesta del Backend:**
```json
{
  "actions": [
    {
      "device": "PUMP",
      "action": "ON",
      "reason": "La IA detectó humedad baja en la zona 1"
    }
  ],
  "alerts": ["Humedad crítica detectada"]
}
```
> [!IMPORTANT]
> Nunca incluyas el `SUPABASE_SERVICE_ROLE_KEY` ni llaves `agnx_w_` en el código fuente público. Usa `X-API-Key` únicamente en los headers de conexión segura (HTTPS).

#### 🛠️ Firmware de Referencia (ESP32-C6 / Arduino C++)

El firmware de AgroNexus para ESP32-C6 está optimizado para procesar respuestas de IA de baja latencia (soporta timeouts de 20s para el razonamiento de Gemini):

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Pines de Actuadores (Relés)
const int PIN_FAN = 2; 

void sendTelemetry() {
  HTTPClient http;
  http.begin("http://TU_IP_LOCAL:8000/api/iot/telemetry");
  http.addHeader("X-API-Key", "TU_WRITE_KEY");
  http.setTimeout(20000); // Tiempo para que la IA razone

  StaticJsonDocument<512> doc;
  JsonObject sensors = doc.createNestedObject("sensor_data");
  sensors["temperature"] = readTemp(); // Lectura real
  doc["zone_id"] = "TU_ZONE_UUID";

  String body;
  serializeJson(doc, body);
  int code = http.POST(body);

  if (code == 200) {
    String res = http.getString();
    StaticJsonDocument<1024> result;
    deserializeJson(result, res);
    
    // Ejecución de acciones físicas
    JsonArray actions = result["actions"];
    for (JsonObject a : actions) {
      if (a["device"] == "FAN") {
        digitalWrite(PIN_FAN, a["action"] == "ON" ? HIGH : LOW);
        Serial.printf("[IA] %s -> %s\n", (const char*)a["device"], (const char*)a["action"]);
      }
    }
  }
  http.end();
}
```

---

```

---

## 📊 Sistema de Reportes Agronómicos (IA + Fallback Estadístico)

AgroNexus AI genera reportes técnicos directamente en el chat, en formato **Markdown**, eliminando la dependencia de librerías PDF del lado del servidor.

### 🧠 Arquitectura de Resiliencia IA
Para optimizar el uso de cuotas y garantizar la entrega **siempre**, el sistema utiliza:
- **Agregación Inteligente**: Comprime miles de registros en resúmenes horarios (Promedio, Min, Max, Tendencia) para un análisis de IA más contextual y eficiente.
- **Rotación Inteligente de API Keys**: Soporta múltiples llaves (`GEMINI_API_KEYS`) con balanceo Round Robin, cooldown de 30s por llave fallida y backoff exponencial con jitter para errores 503.
- **Diferenciación de Errores**: Los errores `503` (servicio ocupado) aplican backoff y reintentan con la misma llave; los errores `429` (cuota agotada) rotan inmediatamente a la siguiente llave disponible.
- **Fallback Estadístico**: Si **todas** las llaves fallan, el sistema genera automáticamente un reporte Markdown con tablas de KPIs crudos (promedios, tendencias, valores actuales) usando los datos agregados de la base de datos. El usuario **siempre** recibe sus métricas.

### 📈 Contenido del Reporte
El reporte IA incluye automáticamente:
- **KPIs Tabulados**: Comparación de promedios históricos vs valores actuales con tendencia.
- **Análisis de Micro-Clima**: Temperatura, humedad y VPD (Déficit de Presión de Vapor).
- **Estado de Suelo y Nutrición**: pH, EC, humedad de suelo y disponibilidad de nutrientes.
- **Evaluación de Riesgos**: Detección de anomalías, plagas, enfermedades fúngicas.
- **Recomendaciones Accionables**: Pasos concretos y data-driven para el agricultor.

---

## 💬 Inteligencia Artificial y RAG Dinámico

El agrónomo virtual de AgroNexus no es un simple chat. Es un orquestador que:
*   **Consume Contexto IoT**: Lee el estado actual del invernadero antes de responder.
*   **Toma Acciones**: Puede emitir comandos a actuadores (Bomba, Luces) en formato JSON.
*   **Historial Aislado**: Cada sesión de chat (`session_id`) mantiene su propio hilo de pensamiento para evitar interferencias entre diferentes cultivos o consultas.

---

### 🔄 Ciclo de Telemetría e Intervención IA

```mermaid
sequenceDiagram
    participant ESP as 🔌 ESP32 (Hardware)
    participant API as 🚀 FastAPI Backend
    participant DB as ☁️ Supabase (DB/Auth)
    participant AI as 🧠 Gemini AI Engine
    participant UI as 📱 Mobile App (SSE)

    ESP->>API: POST /telemetry (Sensor Data + API Key)
    API->>DB: Validar API Key & Permisos de Zona
    DB-->>API: Key Válida (Owner: Luis)
    
    par Paralelo: Persistencia y Notificación
        API->>DB: INSERT sensor_data
        API->>UI: Broadcast via SSE (Real-time graph update)
    end

    API->>AI: ¿Anomalía detectada? (Contexto: Humedad 25%, Temp 30°)
    Note over AI: El Agente analiza umbrales<br/>y estado histórico (RAG)
    
    AI-->>API: JSON: { "action": "ACTIVATE_PUMP", "reason": "Low soil moisture" }
    
    alt Acción Requerida
        API->>DB: INSERT actuator_log (Bomba activada por AI)
        API-->>ESP: Response: { "actions": ["PUMP_ON"] }
    end
```

---

## 🖥️ Ejecución Local

```bash
# Iniciar el servidor de desarrollo expuesto a la red local (para ESP32)
uv run uvicorn app.main:app --reload --host 0.0.0.0
```

Una vez corriendo, la documentación interactiva está disponible en:

| Recurso | URL (Local) | URL (IP Red) |
|---------|-------------|--------------|
| **Swagger UI** | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | [http://192.168.x.x:8000/api/docs](http://192.168.x.x:8000/api/docs) |
| **ReDoc** | [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc) | - |
| **OpenAPI JSON** | [http://localhost:8000/api/openapi.json](http://localhost:8000/api/openapi.json) | - |

> [!NOTE]
> Las URLs de documentación están bajo el prefijo `/api` para mantener consistencia con el resto de los endpoints.

---

## 📡 Endpoints de la API (v1)

### ⚙️ Sistema
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/health` | Health check del servidor. |

### 📡 IoT y Telemetría
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/api/iot/telemetry` | API Key (write) | Recepción de datos de hardware (ESP32). |
| `GET` | `/api/iot/stream` | JWT | Stream SSE para actualización en tiempo real. |

### 📊 Dashboard
| Método | Ruta | Auth / Rol | Descripción |
|--------|------|------------|-------------|
| `GET` | `/api/dashboard/latest` | JWT | Últimos datos de sensores (soporta `?zone_id=`). |
| `GET` | `/api/dashboard/history` | JWT | Historial reciente de telemetría. |
| `GET` | `/api/dashboard/state` | JWT | Estado interno del sistema (modo, actuadores). |
| `POST` | `/api/dashboard/mode` | owner, agronomist | Cambia el modo de operación (AUTO/MANUAL). |
| `GET` | `/api/dashboard/actuator-log` | owner, agronomist | Historial de acciones de actuadores (paginado). |
| `GET` | `/api/dashboard/stats` | JWT | Estadísticas agregadas (min/max/avg). |
| `GET` | `/api/dashboard/export` | owner, agronomist | Exporta historial de sensores a CSV. |
| `GET` | `/api/dashboard/maintenance` | JWT | Historial de mantenimiento. |
| `GET` | `/api/dashboard/thresholds` | JWT | Obtiene umbrales de alerta. |
| `PUT` | `/api/dashboard/thresholds` | owner | Configura umbrales de alerta. |

### 🌱 Zonas de Cultivo
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/api/zones/` | JWT | Lista todos los invernaderos/zonas del usuario. |
| `POST` | `/api/zones/` | JWT | Crea un nuevo invernadero o zona. |
| `PATCH` | `/api/zones/{zone_id}` | JWT | Actualiza una zona existente. |
| `DELETE` | `/api/zones/{zone_id}` | JWT | Elimina una zona de cultivo. |

### 💬 Chat e IA
| Método | Ruta | Auth / Rol | Descripción |
|--------|------|------------|-------------|
| `POST` | `/api/chat` | owner, agronomist | Interacción con el agrónomo IA (soporta `session_id`). |
| `GET` | `/api/chat/history` | JWT | Historial de mensajes (paginado, filtrable por sesión). |
| `POST` | `/api/chat/test` | *Ninguna* | Endpoint de prueba sin auth para evaluación/QA. |
| `POST` | `/api/chat/report` | owner, agronomist | Genera un reporte agronómico detallado en Markdown. |
| `GET` | `/api/conversations` | JWT | Lista todas las conversaciones del usuario. |
| `POST` | `/api/conversations` | owner, agronomist | Crea una nueva sesión de chat. |
| `PATCH` | `/api/conversations/{session_id}` | owner, agronomist | Renombra una conversación. |
| `DELETE` | `/api/conversations/{session_id}` | owner, agronomist | Elimina una conversación y sus mensajes. |

### 🔐 Identidad y Acceso
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | *Ninguna* | Registro de nuevo usuario. |
| `POST` | `/api/auth/login` | *Ninguna* | Login (devuelve `access_token`). |
| `GET` | `/api/auth/me` | JWT | Devuelve el usuario autenticado actual. |
| `PATCH` | `/api/auth/profile` | JWT | Actualiza perfil (nombre, rol). |
| `GET` | `/api/auth/keys` | JWT | Lista las API Keys del usuario (metadatos). |
| `POST` | `/api/auth/keys` | JWT | Genera una nueva API Key (`?key_type=read\|write`). |
| `DELETE` | `/api/auth/keys/{key_type}` | JWT | Revoca una API Key específica. |

### 🕐 Cron (Interno)
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/cron/daily-summary` | Genera resumen proactivo de salud agrícola (Vercel Cron). |

---

## 🧪 Validación del Sistema
El proyecto incluye una suite de pruebas para simular tráfico real sin hardware físico:
```bash
# Simulación de telemetría masiva
python tests/test_iot_bulk.py

# Validación completa de integración (End-to-End)
python tests/test_transmission.py
```

---
*Desarrollado para la agricultura inteligente por el equipo de **AgroNexus AI**.*
