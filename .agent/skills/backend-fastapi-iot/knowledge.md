# Conocimiento Agrícola: Costal Tropical

## Cultivos Comunes en la Costa
*   **Tomate Tropical**: Rango ideal 24°C - 30°C. Sufre mucho arriba de 34°C.
*   **Ají / Pimentón**: Rango ideal 25°C - 31°C. No soportan humedad arriba del 85% (riesgo de hongos).
*   **Pepino Tropical**: Sensible a la falta de agua con el calor directo.
*   **Berenjena**: Es la que más aguanta el calor (hasta 35°C sin problema).
*   **Albahaca**: Ciclo corto pero el sol directo de mediodía la quema; se aconseja malla sombra.

## ADN Técnico de AgroNexus
Este es tu stack de nacimiento, diseñado para el alto rendimiento (SaaS AgTech):
*   **Backend**: Desarrollado con **FastAPI (Python 3.12)**. Es asíncrono, lo que permite manejar múltiples dispositivos IoT sin bloqueos.
*   **Base de Datos y Auth**: Utilizamos **Supabase** (PostgreSQL). Gestiona la persistencia de sensores, el historial de chat y la seguridad de los usuarios.
*   **Cerebro (IA)**: Estás impulsado por **Google Gemini** (vía Gemini API), especializado en razonamiento proactivo para agricultura.
*   **Conectividad IoT**: Integración directa con hardware (ESP32) mediante una capa de seguridad de **API Keys con Hash SHA-256**.
*   **Infraestructura**: Desplegado en **Vercel** (Serverless), optimizado para baja latencia global.

## Temperaturas Críticas Generales
*   **Más de 33°C**: Peligro de calor térmico. Sugiere ventilación inmediata (FAN ON).
*   **Humedad más de 85%**: Riesgo de hongos. Sugiere ventilación (FAN ON).
*   **Humedad menos de 40%**: Peligro de deshidratación. Sugiere riego o humidificador.

