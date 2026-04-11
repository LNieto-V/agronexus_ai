# 🔌 Guía de Hardware: Nodo ESP32-C6 (AgroNexus AI)

Esta guía detalla cómo configurar y desplegar el nodo de telemetría y control basado en el **ESP32-C6 DevKit**.

## 📋 Requisitos Técnicos

### Hardware
- **ESP32-C6 DevKit** (Soporta WiFi 6, Bluetooth 5.3 y Zigbee/Thread).
- **Actuadores**: Relés de 5V o MOSFETs para el control de carga.
- **Sensores**: Sensores de temperatura/humedad (DHT22), pH, EC y humedad de suelo.

### Software (Arduino IDE)
1. **Board Manager**: Instalar el core de `esp32` por Espressif Systems (versión 3.0.0 o superior).
2. **Librerías**:
   - `ArduinoJson` (v7.0+)
   - `WiFi` (integrada)
   - `HTTPClient` (integrada)

---

## 🛠️ Configuración de Pines

El firmware utiliza los siguientes pines por defecto para el control de actuadores:

| Dispositivo | Pin GPIO | Tipo | Descripción |
|-------------|:---:|:---:|-------------|
| **Ventilador (FAN)** | 2 | Salida | Control de ventilación/extracción. |
| **Bomba (PUMP)** | 3 | Salida | Control de riego/fertirrigación. |
| **Luz (LIGHT)** | 4 | Salida | Iluminación suplementaria. |
| **LED Status** | 8 | Salida | Indicador visual de actividad (Onboard). |

---

## 🚀 Despliegue Paso a Paso

1. **Abrir el archivo**: Localiza `firmware/agronexus_esp32c6.ino`.
2. **Configurar Conectividad**:
   ```cpp
   const char* WIFI_SSID     = "TU_RED_WIFI";
   const char* WIFI_PASSWORD = "TU_PASSWORD_WIFI";
   const char* API_BASE_URL  = "http://TU_IP_O_DOMINIO:8000";
   ```
3. **Identidad del Dispositivo**: Obtén tu `ZONE_ID` y `API_KEY` desde el panel de **Seguridad** en la App de AgroNexus.
   ```cpp
   const char* API_KEY       = "agnx_w_xxx"; // Tu Write Key
   const char* ZONE_ID       = "uuid-de-tu-zona";
   ```
4. **Cargar**: Selecciona "ESP32C6 Dev Module" en el Arduino IDE y pulsa Upload.

---

## 🚦 Diagnóstico Visual (LED Onboard)
- **Parpadeo lento**: Iniciando conexión WiFi.
- **Parpadeo rápido (100ms)**: Enviando telemetría al backend.
- **Apagado prolongado**: Modo espera (intervalo entre lecturas).

---

## ⚠️ Notas de Seguridad
- El ESP32-C6 opera a **3.3V**. Cuidado al conectar sensores de 5V sin un divisor de tensión.
- Las **API Keys de escritura** (`write`) están vinculadas a una zona específica por seguridad. Si intentas enviar datos a una zona diferente, el servidor responderá con error.

---
*Para soporte técnico adicional, consulta el [FRONTEND_SYNC_PLAN.md](file:///home/tensei/agronexus_ai/docs/FRONTEND_SYNC_PLAN.md).*
