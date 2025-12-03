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
// VARIABLES DE PRUEBA (sensores simulados)
// -------------------------------------------------------------------------------------------

int humedad = 25;
int pir = 0;
int luminosidad = 500;
float temperatura = 24.0; // <--- NUEVA VARIABLE PARA TEMP

// -------------------------------------------------------------------------------------------
// PINES
// -------------------------------------------------------------------------------------------
#define HUMEDAD_PIN 34
#define LDR_PIN 32
#define PIR_PIN 27
#define DHTPIN 4      // Pin donde conectarás el DHT11 en el futuro
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE); // Inicializamos el objeto DHT

// -------------------------------------------------------------------------------------------
// SERVIDOR WEB – archivos desde SPIFFS
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
    File file = SPIFFS.open(path, "r");

    if (!file) {
        server.send(404, "text/plain", "Imagen no encontrada");
        return;
    }

    if (path.endsWith(".svg")) server.streamFile(file, "image/svg+xml");
    else if (path.endsWith(".png")) server.streamFile(file, "image/png");
    else if (path.endsWith(".jpg")) server.streamFile(file, "image/jpeg");
    else server.streamFile(file, "application/octet-stream");

    file.close();
}

// -------------------------------------------------------------------------------------------
// ENDPOINT /e PARA EL FRONTEND
// -------------------------------------------------------------------------------------------

void handleData() {
    // Actualizamos también aquí por si alguien consulta directo a la API del ESP
    String data = "humedad:" + String(humedad) +
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
            Serial.print("Error rc=");
            Serial.print(client.state());
            Serial.println(" | Reintentando en 2s...");
            delay(2000);
        }
    }
}

// -------------------------------------------------------------------------------------------
// SETUP
// -------------------------------------------------------------------------------------------

void setup() {
    Serial.begin(115200);

    // ----------------- MONTAR SPIFFS -----------------
    if (!SPIFFS.begin(true)) {
        Serial.println("❌ Error montando SPIFFS");
    } else {
        Serial.println("✅ SPIFFS montado correctamente");
    }

    // ----------------- WIFI -----------------
    WiFi.begin(ssid, password);
    Serial.print("Conectando a WiFi ");

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
    }

    Serial.println("\n✅ WiFi conectado");
    Serial.print("IP del ESP32: ");
    Serial.println(WiFi.localIP());

    // ----------------- SERVIDOR HTTP -----------------
    server.on("/", HTTP_GET, handleRoot);
    server.on("/styles.css", HTTP_GET, handleCSS);
    server.on("/e", HTTP_GET, handleData);

    server.begin();
    Serial.println("🌐 Servidor web iniciado en puerto 80");

    // ----------------- MQTT -----------------
    client.setServer(mqtt_server, mqtt_port);

    // ----------------- PINES & SENSORES -----------------
    pinMode(HUMEDAD_PIN, INPUT);
    pinMode(LDR_PIN, INPUT);
    pinMode(PIR_PIN, INPUT);
    dht.begin(); // Iniciamos el DHT aunque usaremos datos falsos por ahora
}

// -------------------------------------------------------------------------------------------
// LOOP
// -------------------------------------------------------------------------------------------

void loop() {
    // Servidor Web
    server.handleClient();

    // MQTT
    if (!client.connected()) reconnect();
    client.loop();

    // ----------------------------------------------------------
    // VALORES SIMULADOS (HARDCODED)
    // ----------------------------------------------------------
    humedad = 25;       // Simula suelo seco
    pir = 1;            // Simula movimiento detectado
    luminosidad = 800;  // Simula luz alta
    temperatura = 24.5; // <--- VALOR FIJO PARA TEMPERATURA

    /* NOTA: Cuando conectes el sensor real, descomenta esto:
       float t_real = dht.readTemperature();
       if (!isnan(t_real)) temperatura = t_real;
    */

    Serial.print("Enviando -> Humedad: ");
    Serial.print(humedad);
    Serial.print("% | Temp: ");
    Serial.print(temperatura);
    Serial.println("C");

    // ----------------------------------------------------------
    // ENVIAR POR MQTT
    // ----------------------------------------------------------
    JsonDocument doc;

    // 1. HUMEDAD
    doc["valor"] = humedad;
    doc["unidad"] = "%";
    char humPayload[90];
    serializeJson(doc, humPayload);
    client.publish("sensores/humedad", humPayload);

    // 2. TEMPERATURA (NUEVO)
    doc.clear();
    doc["valor"] = temperatura;
    doc["unidad"] = "C";
    char tempPayload[90];
    serializeJson(doc, tempPayload);
    client.publish("sensores/temperatura", tempPayload);

    // 3. LUZ
    doc.clear();
    doc["valor"] = luminosidad;
    doc["unidad"] = "LX";
    char luzPayload[90];
    serializeJson(doc, luzPayload);
    client.publish("sensores/luz", luzPayload);

    // 4. PIR
    doc.clear();
    doc["valor"] = pir;
    doc["unidad"] = "";
    char pirPayload[90];
    serializeJson(doc, pirPayload);
    client.publish("sensores/pir", pirPayload);

    delay(5000); // Espera 5 segundos entre envíos
}