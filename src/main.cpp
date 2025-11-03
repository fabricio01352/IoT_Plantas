#include <Arduino.h>

#include <WiFi.h>                  
#include <ESPAsyncWebServer.h>    
#include <LittleFS.h>  
#include <PubSubClient.h>         

// WiFi
const char *ssid = "Totalplay-2.4G-c140";
const char *password = "FRUAGdku2RbN55sC";

WiFiClient espClient;
const char* mqtt_server = "";
const int mqtt_port = 1883;
const char* mqtt_topic = "sensores/humedad";
PubSubClient client(espClient);






// Definición de pines de sensores
#define HUMEDAD_PIN 34  // Pin analógico para sensor de humedad del suelo
#define LDR_PIN 35  
    // Pin analógico para sensor de luz (LDR)
#define PIR_PIN 13      // Pin digital para sensor de movimiento PIR

// Definición de pines de actuadores
#define LED_PIN 25       // Pin digital para LED
#define ZUMBADOR_PIN 27  // Pin digital para zumbador

// Instancia del servidor en el puerto 80
AsyncWebServer server(80);







void reconnect(){
  while(!client.connected()){
    Serial.print("Conectando a MQTT...");
    if(client.connect("ESP32Cliente")){
      Serial.println("Conectaod");
    } else{
      Serial.print("Error: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}



void setup() {
  Serial.begin(115200);  // Inicializa la comunicación serial


  



  // Conexión a WiFi
  WiFi.begin(ssid, password);







  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando a WiFi...");
  }
  Serial.println("Conectado a WiFi");
  Serial.print("Dirección IP del ESP32: ");
  Serial.println(WiFi.localIP());

  // configurar servidor mqtt
  client.setServer(mqtt_server, mqtt_port);


  // Configuración de los pines
  pinMode(HUMEDAD_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(ZUMBADOR_PIN, OUTPUT);

  // Inicializa actuadores apagados
  digitalWrite(LED_PIN, LOW);
  digitalWrite(ZUMBADOR_PIN, LOW);

  // Monta el sistema de archivos LittleFS
  if (!LittleFS.begin(true)) {
    Serial.println("Error al montar LittleFS");
    return;
  }

  // Ruta principal: carga index.html desde el sistema de archivos
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/index.html", "text/html");
  });

  // Carga de archivo CSS
  server.on("/styles.css", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/styles.css", "text/css");
  });

  // Carga de imágenes SVG usadas en la interfaz web
  server.on("/imgs/cloud.svg", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/imgs/cloud.svg", "image/svg+xml");
  });

  server.on("/imgs/cloud-sun.svg", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/imgs/cloud-sun.svg", "image/svg+xml");
  });

  server.on("/imgs/plant.svg", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/imgs/plant.svg", "image/svg+xml");
  });

  server.on("/imgs/plant-logo.svg", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/imgs/plant-logo.svg", "image/svg+xml");
  });








  // Endpoint de lectura de sensores y control de actuadores
  server.on("/e", HTTP_GET, [](AsyncWebServerRequest *request) {




    // Lectura de sensores
    int humedad = analogRead(HUMEDAD_PIN);  // Valor entre 0 y 4095
    int pir = digitalRead(PIR_PIN);         // Valor 0 o 1 (detección de movimiento)
    int luminosidad = analogRead(LDR_PIN);  // Valor entre 0 y 4095



    client.publish("sensores/humedad", "{\"valor\":25.4,\"unidad\":\"C\"}");





    // Lógica de control de actuadores:
    // Enciende LED si el suelo está seco
        //  int led = (humedad > 2000) ? 1 : 0;

    // Enciende zumbador si hay movimiento detectado por PIR
          // int zumbador = pir;

    // Activación de actuadores
          // digitalWrite(LED_PIN, led);
          // digitalWrite(ZUMBADOR_PIN, zumbador);








    // aqui metemos el mqtt

// librerias mqtt -> inicializar lo que se ocupe -> este main.cpp publica en una cola y el influxdb  o el backend se suscribe a la cola



    // Construcción de respuesta para el frontend
    // String response = "humedad:" + String(humedad) + 
    //                   ",pir:" + String(pir) + 
    //                   ",luminosidad:" + String(luminosidad) + 
    //                   ",led:" + String(led) + 
    //                   ",zumbador:" + String(zumbador);

    String response = "humedad:" + String(humedad) + 
                      ",pir:" + String(pir) + 
                      ",luminosidad:" + String(luminosidad);





    // Envío de respuesta al navegador
    //request->send(200, "text/plain", response);







  });

  // Inicio del servidor
  server.begin();
}

















void loop() {









}
