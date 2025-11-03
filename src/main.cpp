#include <Arduino.h>
#include <WiFi.h> 
#include <PubSubClient.h>         

// WiFi
const char *ssid = "Mega_2.4G_C091";
const char *password = "heTdTPE4";

WiFiClient espClient;
const char* mqtt_server = "192.168.1.6";
const int mqtt_port = 1883;
const char* mqtt_topic = "sensores/humedad";
const char* mqtt_topic2 = "sensores/luz";
const char* mqtt_topic3 = "sensores/pir";
PubSubClient client(espClient);

 int humedad;  // Valor entre 0 y 4095
    int pir;         // Valor 0 o 1 (detección de movimiento)
    int luminosidad; 








// Definición de pines de sensores
#define HUMEDAD_PIN 34  // Pin analógico para sensor de humedad del suelo
#define LDR_PIN 35  
    // Pin analógico para sensor de luz (LDR)
#define PIR_PIN 13      // Pin digital para sensor de movimiento PIR









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
  Serial.begin(9600);  // Inicializa la comunicación serial

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

  reconnect();
  // Configuración de los pines
  pinMode(HUMEDAD_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);













    // Lectura de sensores
    int humedad = analogRead(HUMEDAD_PIN);  // Valor entre 0 y 4095
    int pir = digitalRead(PIR_PIN);         // Valor 0 o 1 (detección de movimiento)
    int luminosidad = analogRead(LDR_PIN);  // Valor entre 0 y 4095


  };



void loop() {

   if (!client.connected()) {
    reconnect();
  }
  client.loop(); 

  humedad = analogRead(HUMEDAD_PIN);
  pir = digitalRead(PIR_PIN);
  luminosidad = analogRead(LDR_PIN);

  //  client.publish("sensores/humedad", "{\"valor\":25.4,\"unidad\":\"C\"}");
  client.publish("sensores/luz", String(luminosidad).c_str());
  client.publish("sensores/humedad", String(humedad).c_str());
  client.publish("sensores/pir", String(pir).c_str());
  delay(5000);



}
