# 🚜 AgroNexus AI: Backend de Agricultura de Precisión IoT

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-DB%20%26%20Auth-3ecf8e?logo=supabase)](https://supabase.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.1--Flash-4285F4?logo=google-gemini)](https://ai.google.dev/)

AgroNexus AI es un asistente agrícola inteligente diseñado específicamente para zonas de transición costera (como Santa Marta, Colombia). Este backend gestiona telemetría en tiempo real desde dispositivos IoT (ESP32), orquesta decisiones proactivas para el control de invernaderos y ofrece una interfaz conversacional impulsada por la IA de Google Gemini con memoria persistente.

---

## ⚡ Características Principales

- **Orquestación IoT**: Recepción de telemetría y control de actuadores (Ventiladores, Luces, Riego) mediante lógica de anomalías.
- **Seguridad Dual**:
  - **JWT (Supabase)**: Para usuarios finales en aplicaciones Web/Móviles.
  - **API Keys (SHA-256)**: Para dispositivos embebidos con permisos `read` y `write`.
- **IA Proactiva**: Integración asíncrona con Gemini con detección inteligente de anomalías para optimizar el consumo de la cuota de API.
- **RAG Simplificado**: Inyección de conocimiento agrícola costero y estado del sistema en tiempo real en los prompts.
- **Persistencia Completa**: Cada mensaje de chat y lectura de sensor se almacena en Supabase para análisis histórico.

---

## 🛠️ Instalación y Configuración

### 1. Requisitos Previos
- **Python 3.12+**
- El gestor de paquetes `uv` (recomendado) para mejor rendimiento.

### 2. Clonar y despliegue local
```bash
# Clonar el repo
git clone https://github.com/LNieto-V/agronexus_ai
cd agronexus_ai

# Instalar dependencias con uv
uv sync

# Ejecutar servidor de desarrollo
uv run uvicorn app.main:app --reload
```

### 3. Configuración de Variables de Entorno `.env`
Crea un archivo `.env` basado en el `.env.example`:
```env
GEMINI_API_KEY=tu_api_key
SUPABASE_URL=tu_url_proyecto
SUPABASE_KEY=tu_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
SUPABASE_JWT_SECRET=tu_jwt_secret
```

---

## 📡 Documentación de Endpoints (API)

Accede a la documentación interactiva en:
- `http://localhost:8000/docs` (Swagger UI)
- `https://agronexus-ai.vercel.app/docs` (Producción)

### Endpoints Críticos
- `POST /chat`: Interfaz conversacional con el asistente (Requiere JWT).
- `POST /iot/telemetry`: Consumo de datos desde ESP32 (Requiere API Key `write`).
- `GET /dashboard/latest`: Últimos valores de sensores (Requiere JWT).
- `POST /auth/keys`: Gestión de API Keys para dispositivos (Requiere JWT).

---

## 🗄️ Estructura de la Base de Datos

Para desplegar este backend necesitas crear las siguientes tablas en tu instancia de Supabase:

1.  `sensor_data`: Registra la telemetría histórica.
2.  `chat_history`: Almacena la memoria conversacional.
3.  `api_keys`: Gestiona las llaves de acceso para hardware IoT.

> [!TIP]
> Consulta el archivo `supabase_schema.sql` para ver la definición exacta de las tablas e índices.

---

## 🧪 Pruebas
El proyecto incluye una suite de pruebas para validar la conexión con Gemini, el procesamiento de telemetría y la seguridad:
```bash
uv run python test_connection.py
uv run python test_iot_telemetry.py
```

---

## 🛡️ Estándares del Proyecto
Este backend sigue el estándar de la Universidad del Magdalena para el curso de Herramientas de Desarrollo con IA, implementando la estructura de **Skills** definida en `.agent/skills/`.
