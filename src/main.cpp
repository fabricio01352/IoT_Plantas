#include <Arduino.h>
#include <WiFi.h> 
#include <PubSubClient.h> // libreria necesaria para publicar en el topic
#include <ArduinoJson.h>  
#include "DHT.h"


// -------------------------------------------------------------------------------------------
// WiFi, idealmente en un .env pero por ahora cada quien puede mover a su propia red aqui
const char *ssid = "Tlaneci24G";
const char *password = "Depas2025";


// -------------------------------------------------------------------------------------------
// -------------declaraion de variables, nos importa el servidor mqtt el cual se ejecuta localmente, el puerto por defecto 1883
//                 y los topics, solo leeremos 3 datos por ahora
// -------------------------------------------------------------------------------------------

WiFiClient espClient;
const char* mqtt_server = "192.168.10.142";
const int mqtt_port = 1883;
const char* mqtt_topic = "sensores/humedad";
const char* mqtt_topic2 = "sensores/luz";
const char* mqtt_topic3 = "sensores/pir";
PubSubClient client(espClient);

 int humedad;  // lee humedad
    int pir;         // deteca radiacion infrarroja
    int luminosidad;  // 

// Definición de pines de sensores
#define HUMEDAD_PIN 34  // Pin analógico para sensor de humedad del suelo
#define LDR_PIN 32  
#define PIR_PIN 27      // Pin digital para sensor de movimiento PIR









// -------------------------------------------------------------------------------------------
// ----------funcion para conectarse al servidor mqtt
// -------------------------------------------------------------------------------------------


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


// -------------------------------------------------------------------------------------------
// -------------------------------------------------------------------------------------------

void setup() {
  Serial.begin(9600);  

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

  reconnect();




  // Configuración de los pines
  pinMode(HUMEDAD_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);




  };



void loop() {

   if (!client.connected()) {
    reconnect();
  }
  client.loop(); 





  int valor = analogRead(HUMEDAD_PIN);
  Serial.print("raw: ");
  Serial.print(valor);
  int humedad = map(valor,2000,4095,100,0);
  pir = digitalRead(PIR_PIN);
  
  // ESTO es lo correcto pero por ahorita me ire por el de temperatura
  //luminosidad = analogRead(LDR_PIN);




  // -------------------------------------------------------------------------------------------
  // aqui es donde creamos los formatos en JSON para mandarlos a influx db y a cualquier suscriptor de Mosquitto
  // podemos agregar o quitar campos aqui, en este caso solo tiene VALOR y UNIDAD
  //  esta es la parte que estaremos modificando si queremos agregar o quitar campos o cosas que mandar a otro cliente

  StaticJsonDocument<100> humedadDoc;
  humedadDoc["valor"] = String(humedad).c_str();
  humedadDoc["unidad"] = "%";
  char humedadPayload [100];
  serializeJson(humedadDoc, humedadPayload); // formato json {valor: X unidad: Y}
   client.publish("sensores/humedad",humedadPayload); // publicamos al topic sensores/humedad el payload (cuerpo del mensaje)



 StaticJsonDocument<100> LuminosidadDoc;
  LuminosidadDoc["valor"] = String(luminosidad).c_str();
  LuminosidadDoc["unidad"] = "LX";
  char luzPayload [100];
  serializeJson(LuminosidadDoc, luzPayload);
   client.publish("sensores/luz",luzPayload);



   StaticJsonDocument<100> pirDoc;
  pirDoc["valor"] = String(pir).c_str();
  pirDoc["unidad"] = "";
  char pirPayload[100];
  serializeJson(pirDoc, pirPayload);
  client.publish("sensores/pir", pirPayload);


// -------------------------------------------------------------------------------------------
// -------------------------------------------------------------------------------------------

  // que espere 5 segundos, solo para no quemar mi pc
  delay(5000);



}
