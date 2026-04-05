---
name: testing-quality
description: >
  Skill para estrategias de testing, aseguramiento de calidad y validación 
  end-to-end del ecosistema AgroNexus AI: tests unitarios, de integración, 
  de endpoints y simulación de telemetría IoT.
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 🧪 AgroNexus AI — Testing & Quality Assurance Skill

Este skill define las estrategias, herramientas y patrones de testing utilizados
para validar la calidad del ecosistema AgroNexus AI.

## Capacidades

### 1. Suite de Tests Existente

| Archivo                  | Tipo          | Descripción                                        |
|--------------------------|---------------|----------------------------------------------------|
| `test_connection.py`     | Conectividad  | Valida la conexión con Google Gemini API            |
| `test_iot_telemetry.py`  | Integración   | Simula envío de telemetría desde ESP32              |
| `test_optimization.py`   | Rendimiento   | Valida la lógica de ahorro de cuota (anomalías)     |
| `test_proactivity.py`    | Funcional     | Verifica respuestas proactivas del agente           |
| `test_prompt.py`         | Unitario      | Valida la construcción modular de prompts           |
| `test_supabase.py`       | Integración   | Verifica operaciones CRUD en Supabase               |
| `verify_key.py`          | Seguridad     | Valida la generación y verificación de API Keys     |
| `seed_data.py`           | Setup         | Carga datos de ejemplo en la base de datos          |

### 2. Ejecución de Tests

```bash
# Test individual con uv
uv run python test_connection.py

# Test de telemetría IoT
uv run python test_iot_telemetry.py

# Test de optimización de cuota
uv run python test_optimization.py

# Test de proactividad del agente
uv run python test_proactivity.py

# Test de construcción de prompts
uv run python test_prompt.py

# Test de integración con Supabase
uv run python test_supabase.py
```

### 3. Estrategias de Testing por Capa

#### Capa 1 — Tests Unitarios (Sin Dependencias Externas)
Validan funciones puras sin conexiones a servicios externos.

```python
# Ejemplo: test_prompt.py
from app.prompts import build_prompt

def test_build_prompt_includes_message():
    result = build_prompt(message="¿Cómo están mis tomates?")
    assert "¿Cómo están mis tomates?" in result
    assert "MENSAJE NUEVO DEL USUARIO" in result

def test_build_prompt_includes_sensor_data():
    result = build_prompt(
        message="test",
        sensor_data={"temperature": 35.0, "humidity": 80.0}
    )
    assert "temperature: 35.0" in result
    assert "DATOS DE SENSORES ACTUALES" in result
```

```python
# Ejemplo: test_anomaly.py
from app.services.iot_service import is_anomaly

def test_normal_data_no_anomaly():
    assert is_anomaly({"temperature": 25, "humidity": 60, "ph": 6.5}) == False

def test_high_temp_anomaly():
    assert is_anomaly({"temperature": 40, "humidity": 60, "ph": 6.5}) == True

def test_low_humidity_anomaly():
    assert is_anomaly({"temperature": 25, "humidity": 20, "ph": 6.5}) == True

def test_extreme_ph_anomaly():
    assert is_anomaly({"temperature": 25, "humidity": 60, "ph": 3.0}) == True
```

#### Capa 2 — Tests de Integración (Con Servicios Reales)
Requieren `GEMINI_API_KEY` y/o `SUPABASE_URL` configurados en `.env`.

```python
# Ejemplo: test_iot_telemetry.py
import httpx
import asyncio

async def test_telemetry_with_anomaly():
    """Envía datos anómalos y verifica que la IA genera acciones."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/iot/telemetry",
            json={"temperature": 42.0, "humidity": 98.0, "ph": 3.0},
            headers={"X-API-Key": "tu_write_key_aqui"}
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data.get("actions", [])) > 0  # La IA debió generar acciones
```

#### Capa 3 — Tests de Endpoint (API Contract)
Validan el contrato HTTP de los endpoints sin verificar la lógica interna.

```python
# Ejemplo: test_chat_endpoint.py
async def test_chat_requires_auth():
    """El endpoint /chat debe retornar 401 sin JWT."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"message": "hola"}
        )
    assert response.status_code in [401, 403]

async def test_chat_test_no_auth():
    """El endpoint /chat/test funciona sin autenticación."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat/test",
            json={"message": "¿Cuál es la temperatura ideal para tomates?"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
```

### 4. Simulación de Telemetría IoT (Seed Data)

```python
# seed_data.py — Genera datos realistas para testing
import random
from datetime import datetime, timedelta

def generate_realistic_telemetry(hours: int = 24):
    """Genera N horas de datos simulados de invernadero tropical."""
    data = []
    base_time = datetime.now() - timedelta(hours=hours)
    
    for i in range(hours * 4):  # 4 lecturas por hora (cada 15 min)
        timestamp = base_time + timedelta(minutes=i * 15)
        # Simular ciclo diurno/nocturno
        hour = timestamp.hour
        is_day = 6 <= hour <= 18
        
        data.append({
            "temperature": random.uniform(28, 35) if is_day else random.uniform(22, 27),
            "humidity": random.uniform(55, 80) if is_day else random.uniform(70, 90),
            "ph": random.uniform(5.5, 7.0),
            "light": random.uniform(15000, 60000) if is_day else random.uniform(0, 50),
            "ec": random.uniform(1.0, 2.5),
            "created_at": timestamp.isoformat()
        })
    return data
```

### 5. Verificación del Deploy

```bash
# Verificar que el servidor de producción responde
curl -s https://agronexus-ai.vercel.app/docs | head -5

# Test rápido del endpoint público
curl -X POST https://agronexus-ai.vercel.app/chat/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿cómo están mis cultivos?"}'
```

## Buenas Prácticas
1. **Correr tests unitarios antes de cada commit** — son rápidos y no requieren servicios.
2. **Usar `/chat/test` para demos** — no requiere JWT y usa datos simulados.
3. **Nunca hardcodear API keys en tests** — usar `.env` y `python-dotenv`.
4. **Simular ciclos diurnos** — los datos de testing deben reflejar patrones reales.
5. **Verificar tanto status codes como response body** — no basta con un 200.
