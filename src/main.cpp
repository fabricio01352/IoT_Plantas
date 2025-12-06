#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "DHT.h"
#include <SPIFFS.h>
#include <WebServer.h>

// -------------------------------------------------------------------------------------------
// CONFIGURACIÓN DE CREDENCIALES (platformio.ini)
// -------------------------------------------------------------------------------------------

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASS;
const char *mqtt_server = MQTT_SERVER;

// -------------------------------------------------------------------------------------------
// CLIENTES
// -------------------------------------------------------------------------------------------

WiFiClient espClient;
PubSubClient client(espClient);
WebServer server(80);

const int mqtt_port = 1883;

// -------------------------------------------------------------------------------------------
// VARIABLES GLOBALES (Para almacenar lecturas)
// -------------------------------------------------------------------------------------------

int humedadSuelo = 0;   // Humedad del suelo en %
int luminosidad = 0;    // Luz en %
int pir = 0;            // 0 o 1
float temperatura = 0.0; 
float humedadAire = 0.0; // Extra: Humedad del ambiente (DHT11)

// -------------------------------------------------------------------------------------------
// DEFINICIÓN DE PINES (HARDWARE REAL)
// -------------------------------------------------------------------------------------------
#define LDR_PIN 32      // Módulo LDR
#define DHTPIN 33       // DHT11 Data
#define HUMEDAD_PIN 34  // Sensor Suelo (AO)
#define PIR_PIN 35      // Sensor PIR

#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE); 

// -------------------------------------------------------------------------------------------
// SERVIDOR WEB – Archivos SPIFFS
// -------------------------------------------------------------------------------------------

void handleRoot() {
    File file = SPIFFS.open("/index.html", "r");
    if (!file) {
        server.send(404, "text/plain", "index.html no encontrado");
        return;
    }
    server.streamFile(file, "text/html");
    file.close();
}

void handleCSS() {
    File file = SPIFFS.open("/styles.css", "r");
    if (!file) {
        server.send(404, "text/plain", "styles.css no encontrado");
        return;
    }
    server.streamFile(file, "text/css");
    file.close();
}

void handleImages() {
    String path = server.uri();
    if (SPIFFS.exists(path)) {
        File file = SPIFFS.open(path, "r");
        if (path.endsWith(".svg")) server.streamFile(file, "image/svg+xml");
        else if (path.endsWith(".png")) server.streamFile(file, "image/png");
        else if (path.endsWith(".jpg")) server.streamFile(file, "image/jpeg");
        else server.streamFile(file, "application/octet-stream");
        file.close();
    } else {
        server.send(404, "text/plain", "Imagen no encontrada");
    }
}

// -------------------------------------------------------------------------------------------
// ENDPOINT /e PARA EL FRONTEND (AJAX/FETCH)
// -------------------------------------------------------------------------------------------

void handleData() {
    // Construimos el string con los datos REALES
    // Nota: enviamos 'humedad' como la del suelo, que es lo critico para la planta
    String data = "humedad:" + String(humedadSuelo) +
                  ",pir:" + String(pir) +
                  ",luminosidad:" + String(luminosidad) +
                  ",temperatura:" + String(temperatura) + 
                  ",led:0,zumbador:0";

    server.send(200, "text/plain", data);
}

// -------------------------------------------------------------------------------------------
// MQTT RECONNECT
// -------------------------------------------------------------------------------------------

void reconnect() {
    while (!client.connected()) {
        Serial.print("Intentando conectar a MQTT...");
        if (client.connect("ESP32_Plantas_Client")) {
            Serial.println("Conectado.");
        } else {
            Serial.print("Fallo, rc=");
            Serial.print(client.state());
            Serial.println(" Reintentando en 2s...");
            delay(2000);
        }
    }
}

// -------------------------------------------------------------------------------------------
// SETUP
// -------------------------------------------------------------------------------------------

void setup() {
    Serial.begin(115200);

    // 1. SPIFFS
    if (!SPIFFS.begin(true)) {
        Serial.println("❌ Error montando SPIFFS");
    } else {
        Serial.println("✅ SPIFFS montado correctamente");
    }

    // 2. WIFI
    WiFi.begin(ssid, password);
    Serial.print("Conectando a WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ WiFi conectado. IP: " + WiFi.localIP().toString());

    // 3. SERVER
    server.on("/", HTTP_GET, handleRoot);
    server.on("/styles.css", HTTP_GET, handleCSS);
    server.on("/e", HTTP_GET, handleData);
    server.onNotFound(handleImages); // Maneja cualquier otra ruta como archivo (imágenes)
    server.begin();
    Serial.println("🌐 Servidor web iniciado");

    // 4. MQTT
    client.setServer(mqtt_server, mqtt_port);

    // 5. HARDWARE PINES
    // Nota: Pines 34 y 35 son solo entrada (Input Only) en ESP32
    pinMode(HUMEDAD_PIN, INPUT);
    pinMode(LDR_PIN, INPUT);
    pinMode(PIR_PIN, INPUT);
    
    dht.begin();
}

// -------------------------------------------------------------------------------------------
// LOOP PRINCIPAL (CON DIAGNÓSTICO DE ERRORES)
// -------------------------------------------------------------------------------------------

void loop() {
    server.handleClient(); 

    if (!client.connected()) reconnect();
    client.loop(); 

    Serial.println("\n--- 🔍 DIAGNÓSTICO DE SENSORES ---");

    // ==========================================
    // 1. TEMPERATURA (DHT11)
    // ==========================================
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    
    if (!isnan(t) && !isnan(h)) {
        temperatura = t;
        humedadAire = h; // Guardamos dato aunque no se envíe por MQTT aun
        Serial.printf("✅ DHT11: %.1f °C | %.1f %% Humedad\n", t, h);
    } else {
        Serial.println("⚠️ FALLO DHT11: No responde. Revisa cable azul (Pin 33) y alimentación.");
    }

    // ==========================================
    // 2. HUMEDAD DE SUELO (Analógico AO - Pin 34)
    // ==========================================
    int lecturaSueloRaw = analogRead(HUMEDAD_PIN);
    
    // LOGICA DE DETECCION DE ERROR:
    // Rango normal en agua: ~1500-2000. Rango en aire (seco): ~4095.
    // Si marca 0 absoluto, suele ser cortocircuito a GND o falla del módulo.
    
    if (lecturaSueloRaw < 50) {
        Serial.printf("⚠️ FALLO SUELO (Raw: %d): Lectura demasiado baja. Posible corto o cable suelto.\n", lecturaSueloRaw);
        humedadSuelo = 0; // Asumimos 0 por error
    } else if (lecturaSueloRaw >= 4090) {
        Serial.printf("⚠️ ALERTA SUELO (Raw: %d): Sensor en aire o desconectado (Muy Seco).\n", lecturaSueloRaw);
        humedadSuelo = 0; // Seco
    } else {
        // Mapeo normal
        humedadSuelo = map(lecturaSueloRaw, 4095, 1500, 0, 100); 
        humedadSuelo = constrain(humedadSuelo, 0, 100);
        Serial.printf("✅ SUELO: %d %% (Raw: %d)\n", humedadSuelo, lecturaSueloRaw);
    }

    // ==========================================
    // 3. LUZ (LDR - Pin 32)
    // ==========================================
    int lecturaLuzRaw = analogRead(LDR_PIN);

    // Si la lectura es 0 absoluto o 4095 absoluto, suele ser sospechoso en un LDR
    // (a menos que estés en oscuridad total o apuntando al sol).
    if (lecturaLuzRaw == 0) {
        Serial.println("⚠️ ALERTA LUZ (Raw: 0): Oscuridad total o cable de señal desconectado.");
        luminosidad = 0;
    } else if (lecturaLuzRaw == 4095) {
        Serial.println("⚠️ ALERTA LUZ (Raw: 4095): Luz saturada o cable VCC desconectado.");
        luminosidad = 100;
    } else {
        luminosidad = map(lecturaLuzRaw, 0, 4095, 0, 100);
        Serial.printf("✅ LUZ: %d %% (Raw: %d)\n", luminosidad, lecturaLuzRaw);
    }

    // ==========================================
    // 4. PIR (Movimiento - Pin 35)
    // ==========================================
    // El PIR es digital (0 o 1). No podemos saber si está roto por software, 
    // pero podemos mostrar su estado claramente.
    pir = digitalRead(PIR_PIN);
    
    if (pir == HIGH) {
        Serial.println("🏃 PIR: ¡MOVIMIENTO DETECTADO! (Estado: 1)");
    } else {
        Serial.println("💤 PIR: Sin movimiento (Estado: 0)");
    }

    Serial.println("--------------------------------");

    // ==========================================
    // ENVÍO POR MQTT
    // ==========================================
    JsonDocument doc;
    char buffer[100];

    // Envio Humedad
    doc["valor"] = humedadSuelo;
    doc["unidad"] = "%";
    serializeJson(doc, buffer);
    client.publish("sensores/humedad", buffer);

    // Envio Temperatura
    doc.clear();
    doc["valor"] = temperatura;
    doc["unidad"] = "C";
    serializeJson(doc, buffer);
    client.publish("sensores/temperatura", buffer);

    // Envio Luz
    doc.clear();
    doc["valor"] = luminosidad;
    doc["unidad"] = "%";
    serializeJson(doc, buffer);
    client.publish("sensores/luz", buffer);

    // Envio PIR
    doc.clear();
    doc["valor"] = pir;
    doc["unidad"] = "";
    serializeJson(doc, buffer);
    client.publish("sensores/pir", buffer);

    delay(3000); 
}