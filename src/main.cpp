#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "DHT.h"

// -------------------------------------------------------------------------------------------
// CONFIGURACIÓN DE CREDENCIALES
// Estas variables toman los valores que definimos en el platformio.ini
// -------------------------------------------------------------------------------------------

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASS;
const char *mqtt_server = MQTT_SERVER;

// -------------------------------------------------------------------------------------------
// DECLARACIÓN DE VARIABLES Y CLIENTES
// -------------------------------------------------------------------------------------------

WiFiClient espClient;
const int mqtt_port = 1883;
PubSubClient client(espClient);

// Variables para datos (Hardcodeadas para pruebas sin sensores)
int humedad = 25;    
int pir = 0;        
int luminosidad = 500; 

// Definición de pines (Se mantienen por si conectas algo despues)
#define HUMEDAD_PIN 34 
#define LDR_PIN 32
#define PIR_PIN 27 

// -------------------------------------------------------------------------------------------
// FUNCIÓN PARA CONECTARSE AL MQTT
// -------------------------------------------------------------------------------------------
void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conectar a MQTT en ");
    Serial.print(mqtt_server);
    Serial.print("...");
    
    // Intentamos conectar con un ID único
    if (client.connect("ESP32_Plantas_Client")) {
      Serial.println("¡Conectado!");
    } else {
      Serial.print("Fallo, rc=");
      Serial.print(client.state());
      Serial.println(" intentando de nuevo en 2 segundos");
      delay(2000);
    }
  }
}

// -------------------------------------------------------------------------------------------
// SETUP
  // -------------------------------------------------------------------------------------------
void setup() {
  Serial.begin(115200); // 9600 es muy lento, mejor 115200 hoy en dia

  // Conexión WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi: ");
  Serial.println(ssid);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi Conectado");
  Serial.print("IP asignada: ");
  Serial.println(WiFi.localIP());

  // Configurar servidor MQTT
  client.setServer(mqtt_server, mqtt_port);

  // Configuración de pines
  pinMode(HUMEDAD_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);
}

// -------------------------------------------------------------------------------------------
// LOOP PRINCIPAL
// -------------------------------------------------------------------------------------------
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // --- SECCION DE LECTURA DE SENSORES ---
  // COMENTADO PARA PRUEBAS: Si no tienes sensores, esto lee ruido electrico.
  // Descomenta las siguientes lineas cuando ya tengas los sensores fisicos.
  
  /*
  int valor = analogRead(HUMEDAD_PIN);
  humedad = map(valor, 2000, 4095, 100, 0); // Actualiza la variable global
  pir = digitalRead(PIR_PIN);
  luminosidad = analogRead(LDR_PIN);
  */

  // --- SIMULACION DE DATOS (HARDCODING) ---
  // Cambia estos valores manuales para probar tus alertas
  humedad = 25;  // < 30 para probar la alerta
  pir = 1;       // 1 detectó movimiento
  luminosidad = 800; 

  Serial.print("Enviando -> Humedad: ");
  Serial.print(humedad);
  Serial.print("% | PIR: ");
  Serial.println(pir);

  // -------------------------------------------------------------------------------------------
  // ENVIO DE DATOS JSON (ArduinoJson v7)
  // En la version 7 ya no se usa StaticJsonDocument<Tamano>, solo JsonDocument.
  // La memoria se gestiona sola.
  // -------------------------------------------------------------------------------------------

  // 1. Humedad
  JsonDocument humedadDoc;
  humedadDoc["valor"] = humedad; // No necesitas convertir a String, ArduinoJson lo maneja
  humedadDoc["unidad"] = "%";
  char humedadPayload[100];
  serializeJson(humedadDoc, humedadPayload);
  client.publish("sensores/humedad", humedadPayload);

  // 2. Luminosidad
  JsonDocument LuminosidadDoc;
  LuminosidadDoc["valor"] = luminosidad;
  LuminosidadDoc["unidad"] = "LX";
  char luzPayload[100];
  serializeJson(LuminosidadDoc, luzPayload);
  client.publish("sensores/luz", luzPayload);

  // 3. PIR (Movimiento)
  JsonDocument pirDoc;
  pirDoc["valor"] = pir;
  pirDoc["unidad"] = "";
  char pirPayload[100];
  serializeJson(pirDoc, pirPayload);
  client.publish("sensores/pir", pirPayload);

  // Esperar 5 segundos antes de la siguiente lectura
  delay(5000);
}