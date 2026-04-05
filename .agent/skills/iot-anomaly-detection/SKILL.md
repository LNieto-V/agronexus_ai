---
name: iot-anomaly-detection
description: >
  Skill para la detección de anomalías en datos de sensores IoT, sistema de 
  umbrales de seguridad agrícola, y lógica proactiva de control automatizado 
  de actuadores para invernaderos de AgroNexus AI.
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 🚨 AgroNexus AI — IoT Anomaly Detection Skill

Este skill define la inteligencia de detección de anomalías y control proactivo
que permite a AgroNexus tomar decisiones automáticas sin intervención humana.

## Capacidades

### 1. Sistema de Umbrales de Seguridad

El motor de anomalías (`is_anomaly()` en `app/services/iot_service.py`) evalúa
cada lectura de telemetría contra umbrales calibrados para agricultura costera tropical:

| Sensor        | Rango Seguro  | Anomalía Baja    | Anomalía Alta   |
|---------------|---------------|-------------------|-----------------|
| Temperatura   | 10°C – 38°C   | < 10°C (Helada)  | > 38°C (Golpe de calor) |
| Humedad       | 30% – 95%     | < 30% (Sequedad) | > 95% (Inundación)     |
| pH            | 4.5 – 8.0     | < 4.5 (Ácido)    | > 8.0 (Alcalino)       |

### 2. Flujo de Decisión Proactiva

```
┌────────────────────────────────────────┐
│     ESP32 envía telemetría             │
│     POST /iot/telemetry                │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  1. Persistir datos en Supabase       │
│     (SIEMPRE ocurre)                  │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  2. ¿is_anomaly(data)?                │
│     Evaluar umbrales de seguridad     │
├────────────┬───────────────────────────┤
│  NO        │  SÍ                      │
│  → return  │  → Activar IA            │
│  [], []    │                           │
└────────────┴───────────┬───────────────┘
                         │
                         ▼
┌────────────────────────────────────────┐
│  3. Construir prompt de emergencia    │
│     con contexto: sensores + historial│
│     + estado del sistema              │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  4. Gemini analiza y genera:          │
│     - Acciones: [{device, action}]    │
│     - Alertas: ["mensaje1", ...]      │
└────────────────────────────────────────┘
```

### 3. Optimización de Cuota API (~70% Ahorro)
- **Sin anomalías**: Los datos se guardan pero NO se consulta a Gemini.
- **Con anomalías**: Se activa el pipeline completo de IA para generar acciones de control.
- **Resultado**: Solo las lecturas críticas consumen cuota del API de Gemini.

### 4. Formato de Respuesta IoT

El LLM responde con un bloque JSON embebido en su respuesta de texto:

```json
{
  "actions": [
    {"device": "FAN", "action": "ON"},
    {"device": "IRRIGATION", "action": "OFF"}
  ],
  "alerts": [
    "🌡️ Temperatura crítica: 39.2°C detectados. Ventilación activada.",
    "💧 Humedad alta: Riego desactivado preventivamente."
  ]
}
```

### 5. Dispositivos y Acciones Soportadas

| Dispositivo    | Acciones      | Caso de Uso                              |
|----------------|---------------|------------------------------------------|
| `FAN`          | ON / OFF / AUTO | Regulación de temperatura y circulación |
| `LIGHT`        | ON / OFF / AUTO | Control de fotoperiodo y lux           |
| `IRRIGATION`   | ON / OFF / AUTO | Hidratación del sustrato               |
| `HUMIDIFIER`   | ON / OFF / AUTO | Control de humedad relativa            |
| `HEATER`       | ON / OFF / AUTO | Protección contra heladas              |

### 6. Prioridades de Seguridad
1. **Seguridad**: Nunca activar riego si humedad > 95% (riesgo de inundación).
2. **Descanso vegetal**: Luces apagadas 6-8 horas/día para el ciclo circadiano.
3. **Eficiencia energética**: Preferir ventilación sobre calefacción cuando sea posible.

## Archivos Clave
- `app/services/iot_service.py`: Motor de anomalías y orquestación proactiva.
- `app/routers/iot.py`: Endpoint `POST /iot/telemetry` para recepción de datos ESP32.
- `.agent/skills/backend-fastapi-iot/devices.md`: Inventario de actuadores y protocolos.

## Extender los Umbrales

Para agregar nuevos sensores al sistema de anomalías, modificar `is_anomaly()`:

```python
def is_anomaly(data: Dict[str, Any]) -> bool:
    # Sensores existentes
    temp = data.get("temperature", 25)
    hum = data.get("humidity", 60)
    ph = data.get("ph", 6)
    
    # ── Nuevo sensor: Conductividad Eléctrica (EC) ──
    ec = data.get("ec", 1.5)
    if ec < 0.5 or ec > 3.5:  # Rango para hortalizas tropicales
        return True
    
    # ── Nuevo sensor: Luminosidad (Lux) ──
    light = data.get("light", 5000)
    if light > 80000:  # Estrés lumínico
        return True
    
    # Umbrales existentes...
    if temp < 10 or temp > 38: return True
    if hum < 30 or hum > 95: return True
    if ph < 4.5 or ph > 8.0: return True
    
    return False
```

## Buenas Prácticas
1. **Siempre persistir primero** — los datos deben guardarse antes de evaluar anomalías.
2. **Calibrar umbrales por zona** — los valores actuales son para costa tropical (Santa Marta).
3. **Log de anomalías** — registrar cada activación en logs para trazabilidad (`logger.warning`).
4. **Modo MANUAL** — si `system_mode == "MANUAL"`, ignorar acciones automáticas del LLM.
5. **Nunca confiar solo en la IA** — los umbrales duros son la primera línea de defensa.
