/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          🌿 AgroNexus AI — Firmware ESP32-C6                ║
 * ║          Telemetría IoT + Control de Actuadores             ║
 * ╚══════════════════════════════════════════════════════════════╝
 * 
 * Envía datos de sensores simulados al backend FastAPI y ejecuta
 * acciones de actuadores dictadas por la IA de AgroNexus.
 * 
 * Board:  ESP32-C6 DevKit
 * SDK:    Arduino ESP32 Core 3.x+
 * Libs:   ArduinoJson 7.x, WiFi (built-in)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────
// 🔧 CONFIGURACIÓN — Edita estos valores
// ─────────────────────────────────────────────
const char* WIFI_SSID     = "TU_RED_WIFI";
const char* WIFI_PASSWORD = "TU_PASSWORD_WIFI";

// Backend AgroNexus (IP local o dominio Vercel)
const char* API_BASE_URL  = "http://192.168.1.100:8000";
const char* API_KEY       = "agnx_w_TU_WRITE_KEY_AQUI";
const char* ZONE_ID       = "TU_ZONE_UUID_AQUI";

// ─────────────────────────────────────────────
// ⚡ PINES DE ACTUADORES (Relés / MOSFET)
// ─────────────────────────────────────────────
const int PIN_FAN   = 2;   // Ventilador
const int PIN_PUMP  = 3;   // Bomba de riego
const int PIN_LIGHT = 4;   // Iluminación suplementaria
const int PIN_LED   = 8;   // LED onboard (status)

// ─────────────────────────────────────────────
// ⏱️ INTERVALOS
// ─────────────────────────────────────────────
const unsigned long TELEMETRY_INTERVAL_MS = 30000;  // 30 segundos
const int HTTP_TIMEOUT_MS = 20000;                   // 20s (tiempo para que la IA razone)

// ─────────────────────────────────────────────
// 📊 ESTADO GLOBAL
// ─────────────────────────────────────────────
unsigned long lastSendTime = 0;
int telemetryCount = 0;
bool wifiConnected = false;

// ═════════════════════════════════════════════
// 🖨️ SISTEMA DE LOGS BONITOS
// ═════════════════════════════════════════════

void logHeader() {
  Serial.println();
  Serial.println("╔══════════════════════════════════════════════════════════╗");
  Serial.println("║          🌿 AgroNexus AI — ESP32-C6 Node               ║");
  Serial.println("╚══════════════════════════════════════════════════════════╝");
  Serial.println();
}

void logSection(const char* title) {
  Serial.println();
  Serial.print("┌─── ");
  Serial.print(title);
  Serial.println(" ───────────────────────────────");
}

void logSectionEnd() {
  Serial.println("└────────────────────────────────────────────────────────");
}

void logInfo(const char* key, const char* value) {
  Serial.print("│  ✦ ");
  Serial.print(key);
  Serial.print(": ");
  Serial.println(value);
}

void logInfo(const char* key, float value, const char* unit) {
  Serial.print("│  ✦ ");
  Serial.print(key);
  Serial.print(": ");
  Serial.print(value, 1);
  Serial.print(" ");
  Serial.println(unit);
}

void logInfo(const char* key, int value) {
  Serial.print("│  ✦ ");
  Serial.print(key);
  Serial.print(": ");
  Serial.println(value);
}

void logOk(const char* msg) {
  Serial.print("│  ✅ ");
  Serial.println(msg);
}

void logWarn(const char* msg) {
  Serial.print("│  ⚠️  ");
  Serial.println(msg);
}

void logError(const char* msg) {
  Serial.print("│  ❌ ");
  Serial.println(msg);
}

void logAction(const char* device, const char* action, const char* reason) {
  Serial.print("│  🤖 IA → ");
  Serial.print(device);
  Serial.print(" = ");
  Serial.print(action);
  Serial.print("  (");
  Serial.print(reason);
  Serial.println(")");
}

void logDivider() {
  Serial.println("│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─");
}

// ═════════════════════════════════════════════
// 📡 WIFI
// ═════════════════════════════════════════════

void connectWiFi() {
  logSection("📡 CONEXIÓN WiFi");
  logInfo("SSID", WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  Serial.print("│  Conectando");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    logOk("Conectado a la red WiFi");
    logInfo("IP Local", WiFi.localIP().toString().c_str());
    logInfo("RSSI", WiFi.RSSI());
  } else {
    wifiConnected = false;
    logError("No se pudo conectar al WiFi");
  }
  logSectionEnd();
}

// ═════════════════════════════════════════════
// 🌡️ LECTURA DE SENSORES (Simulados)
// ═════════════════════════════════════════════
// Reemplaza estas funciones con lecturas reales de tus sensores.
// Ejemplo: DHT22, DS18B20, sensor capacitivo, pH-4502C, etc.

float readTemperature()   { return 22.0 + random(-30, 80) / 10.0; }   // 19.0 – 30.0 °C
float readHumidity()      { return 60.0 + random(-150, 200) / 10.0; } // 45.0 – 80.0 %
float readSoilMoisture()  { return 40.0 + random(-100, 300) / 10.0; } // 30.0 – 70.0 %
float readSoilTemp()      { return 18.0 + random(-20, 50) / 10.0; }   // 16.0 – 23.0 °C
float readPH()            { return 6.0 + random(-5, 10) / 10.0; }     // 5.5 – 7.0
float readEC()            { return 1.2 + random(-3, 8) / 10.0; }      // 0.9 – 2.0 mS/cm
float readLight()         { return 400.0 + random(0, 600); }          // 400 – 1000 lux
float readVPD()           { return 0.8 + random(-2, 5) / 10.0; }     // 0.6 – 1.3 kPa

// ═════════════════════════════════════════════
// ⚙️ CONTROL DE ACTUADORES
// ═════════════════════════════════════════════

void executeAction(const char* device, const char* action) {
  int pin = -1;
  
  if (strcmp(device, "FAN") == 0)   pin = PIN_FAN;
  if (strcmp(device, "PUMP") == 0)  pin = PIN_PUMP;
  if (strcmp(device, "LIGHT") == 0) pin = PIN_LIGHT;
  
  if (pin >= 0) {
    bool state = (strcmp(action, "ON") == 0);
    digitalWrite(pin, state ? HIGH : LOW);
  }
}

// ═════════════════════════════════════════════
// 🚀 ENVÍO DE TELEMETRÍA
// ═════════════════════════════════════════════

void sendTelemetry() {
  if (WiFi.status() != WL_CONNECTED) {
    logSection("⚠️  RECONEXIÓN");
    logWarn("WiFi desconectado, reconectando...");
    logSectionEnd();
    connectWiFi();
    if (!wifiConnected) return;
  }

  telemetryCount++;

  // ── Leer sensores ──
  float temp          = readTemperature();
  float humidity      = readHumidity();
  float soilMoisture  = readSoilMoisture();
  float soilTemp      = readSoilTemp();
  float ph            = readPH();
  float ec            = readEC();
  float light         = readLight();
  float vpd           = readVPD();

  logSection("📊 TELEMETRÍA");
  char countBuf[32];
  snprintf(countBuf, sizeof(countBuf), "#%d", telemetryCount);
  logInfo("Lectura", countBuf);
  logDivider();
  logInfo("🌡️  Temperatura", temp, "°C");
  logInfo("💧 Humedad Aire", humidity, "%");
  logInfo("🌱 Humedad Suelo", soilMoisture, "%");
  logInfo("🪴 Temp. Suelo", soilTemp, "°C");
  logInfo("🧪 pH", ph, "");
  logInfo("⚡ EC", ec, "mS/cm");
  logInfo("☀️  Luz", light, "lux");
  logInfo("💨 VPD", vpd, "kPa");
  logSectionEnd();

  // ── Construir JSON ──
  JsonDocument doc;
  doc["zone_id"] = ZONE_ID;

  JsonObject sensors = doc["sensor_data"].to<JsonObject>();
  sensors["temperature"]    = round(temp * 10) / 10.0;
  sensors["humidity"]       = round(humidity * 10) / 10.0;
  sensors["soil_moisture"]  = round(soilMoisture * 10) / 10.0;
  sensors["soil_temperature"] = round(soilTemp * 10) / 10.0;
  sensors["ph"]             = round(ph * 100) / 100.0;
  sensors["ec"]             = round(ec * 100) / 100.0;
  sensors["light"]          = round(light);
  sensors["vpd"]            = round(vpd * 100) / 100.0;

  String body;
  serializeJson(doc, body);

  // ── Enviar HTTP POST ──
  logSection("🚀 ENVÍO AL BACKEND");
  
  String url = String(API_BASE_URL) + "/api/iot/telemetry";
  logInfo("URL", url.c_str());

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  http.setTimeout(HTTP_TIMEOUT_MS);

  unsigned long startMs = millis();
  int httpCode = http.POST(body);
  unsigned long elapsed = millis() - startMs;

  char timeBuf[32];
  snprintf(timeBuf, sizeof(timeBuf), "%lu ms", elapsed);
  logInfo("Latencia", timeBuf);

  if (httpCode == 200) {
    logOk("Respuesta 200 OK");
    
    String response = http.getString();
    
    // ── Parsear respuesta ──
    JsonDocument resDoc;
    DeserializationError err = deserializeJson(resDoc, response);

    if (!err) {
      // Procesar acciones de la IA
      JsonArray actions = resDoc["actions"];
      JsonArray alerts  = resDoc["alerts"];

      if (actions.size() > 0) {
        logDivider();
        char actionBuf[16];
        snprintf(actionBuf, sizeof(actionBuf), "%d", actions.size());
        logInfo("Acciones IA", actionBuf);
        
        for (JsonObject a : actions) {
          const char* device = a["device"] | "???";
          const char* action = a["action"] | "???";
          const char* reason = a["reason"] | "Sin motivo";
          
          logAction(device, action, reason);
          executeAction(device, action);
        }
      } else {
        logOk("Sin acciones requeridas (todo normal)");
      }

      if (alerts.size() > 0) {
        logDivider();
        for (JsonVariant alert : alerts) {
          logWarn(alert.as<const char*>());
        }
      }
    } else {
      logWarn("No se pudo parsear la respuesta JSON");
    }
  } else if (httpCode == 429) {
    logWarn("⏳ Backend en límite de cuota (429). Esperando...");
  } else if (httpCode < 0) {
    char errBuf[64];
    snprintf(errBuf, sizeof(errBuf), "Error de conexión: %s", http.errorToString(httpCode).c_str());
    logError(errBuf);
  } else {
    char errBuf[64];
    snprintf(errBuf, sizeof(errBuf), "HTTP %d inesperado", httpCode);
    logError(errBuf);
  }

  logSectionEnd();
  http.end();
}

// ═════════════════════════════════════════════
// 🏁 SETUP & LOOP
// ═════════════════════════════════════════════

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Pines de actuadores
  pinMode(PIN_FAN,   OUTPUT);
  pinMode(PIN_PUMP,  OUTPUT);
  pinMode(PIN_LIGHT, OUTPUT);
  pinMode(PIN_LED,   OUTPUT);
  
  digitalWrite(PIN_FAN,   LOW);
  digitalWrite(PIN_PUMP,  LOW);
  digitalWrite(PIN_LIGHT, LOW);
  digitalWrite(PIN_LED,   LOW);

  logHeader();
  
  logSection("⚙️  CONFIGURACIÓN");
  logInfo("Board", "ESP32-C6 DevKit");
  logInfo("Backend", API_BASE_URL);
  logInfo("Zona", ZONE_ID);
  
  char intervalBuf[16];
  snprintf(intervalBuf, sizeof(intervalBuf), "%ds", TELEMETRY_INTERVAL_MS / 1000);
  logInfo("Intervalo", intervalBuf);
  logSectionEnd();

  connectWiFi();

  // Primera lectura inmediata
  if (wifiConnected) {
    sendTelemetry();
  }
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastSendTime >= TELEMETRY_INTERVAL_MS) {
    lastSendTime = now;
    
    // Parpadeo del LED status
    digitalWrite(PIN_LED, HIGH);
    sendTelemetry();
    digitalWrite(PIN_LED, LOW);
  }
}
