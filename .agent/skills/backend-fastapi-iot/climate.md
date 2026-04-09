# Contexto Climático y Métricas de Salud (VPD)

Para la agricultura de precisión en zonas tropicales y costeras, el clima se gestiona mediante el **Déficit de Presión de Vapor (VPD)**, que integra temperatura y humedad en un solo indicador de transpiración.

## Rangos Estándar de VPD (Agronomía)
- **Bajo (0.0 - 0.5 kPa)**: Humedad excesiva o frío extremo. Las plantas no transpiran, riesgo alto de hongos (mildiu, botrytis). 
  - *Acción*: Activar FAN o HEATER.
- **Óptimo (0.8 - 1.2 kPa)**: Intercambio gaseoso ideal. Máxima absorción de nutrientes y crecimiento.
  - *Acción*: Mantener estado actual.
- **Alto (> 1.6 kPa)**: Aire muy seco o calor excesivo. La planta cierra estomas para no deshidratarse (estrés hídrico). 
  - *Acción*: Activar IRRIGATION o HUMIDIFIER.

## Consideraciones de la Costa
- **Humedad Salina**: La humedad relativa suele ser alta (>70%). El reto es evitar el estancamiento de aire que baja el VPD a niveles peligrosos (<0.4 kPa).
- **Inercia Térmica**: Las temperaturas nocturnas rara vez bajan de 24°C, lo que mantiene una tasa metabólica alta que requiere monitoreo constante del sustrato.

## Reactividad del Sistema
Cualquier fluctuación crítica detectada por los sensores se informa vía **SSE (Server-Sent Events)** al usuario y permite a la IA (tú) sugerir cambios proactivos en los actuadores de la zona afectada.

