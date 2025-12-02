# 🌿 Sistema IoT de Monitoreo de Plantas (Fog-to-Cloud)

Este proyecto implementa una arquitectura completa de IoT para el monitoreo de condiciones ambientales en plantas. Utiliza un enfoque de **Niebla a Nube (Fog to Cloud)**, integrando microcontroladores, contenedores Docker, servicios de mensajería y almacenamiento en la nube.

## 🚀 Arquitectura del Sistema

1. **Capa Física (Edge):** ESP32 simulando sensores de Humedad, Luz y Movimiento (PIR).
2. **Capa de Comunicaciones:** Protocolo MQTT sobre WiFi.
3. **Capa de Niebla/Servidor (Backend Dockerizado):**
   * **Broker:** Eclipse Mosquitto.
   * **Lógica de Negocio (Python):** Microservicio modular para procesamiento de datos.
   * **Notificaciones:** Servidor WebSocket para alertas en tiempo real.
4. **Capa de Nube:** InfluxDB Cloud para almacenamiento de series de tiempo.

---

## 📋 Requisitos Previos

Antes de arrancar, asegúrate de tener instalado:

* [Visual Studio Code](https://code.visualstudio.com/)
* **Extensión PlatformIO** (dentro de VS Code).
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (debe estar corriendo).
* [Python 3.9+](https://www.python.org/) (solo para ejecutar el test de cliente localmente).

---

## ⚙️ Configuración (Paso a Paso)

### 1. Configuración de Credenciales (Backend)

El proyecto utiliza variables de entorno para proteger las credenciales. Crea un archivo llamado `.env` en la raíz del proyecto (junto a `platformio.ini`) con el siguiente contenido:

**Archivo: `.env`**
```ini
# --- Configuración MQTT (Interna de Docker) ---
MQTT_BROKER_HOST=mosquitto
MQTT_PORT=1883

# --- Configuración InfluxDB (Nube) ---
INFLUXDB_URL=https://us-east-1-1.aws.cloud2.influxdata.com/
# IMPORTANTE: Usar el ID de Organización (Hexadecimal), NO el correo.
INFLUXDB_ORG=TU_ORG_ID_AQUI
INFLUXDB_BUCKET=humedad_data
# Token con permisos de ESCRITURA (Write)
INFLUXDB_TOKEN=TU_TOKEN_ALL_ACCESS==
```

### 2. Configuración del Hardware (ESP32)

Las credenciales de WiFi y la IP de tu computadora (donde corre el Broker) se inyectan al compilar. Edita el archivo `platformio.ini`:

**Archivo: `platformio.ini`**
```ini
[env:esp32doit-devkit-v1]
platform = espressif32
board = esp32doit-devkit-v1
framework = arduino
monitor_speed = 115200
lib_deps =
    knolleary/PubSubClient
    bblanchon/ArduinoJson
    adafruit/DHT sensor library
    adafruit/Adafruit Unified Sensor
build_flags =
    '-D WIFI_SSID="NOMBRE_DE_TU_RED_WIFI"'
    '-D WIFI_PASS="TU_CONTRASEÑA_WIFI"'
    '-D MQTT_SERVER="192.168.1.XX"'  ; <--- IMPORTANTE: Pon la IP local de tu PC (ipconfig/ifconfig)
```

### 3. 🐳 Arrancar el Servidor (Docker)

No necesitas instalar librerías de Python ni configurar Mosquitto manualmente en tu sistema operativo. Docker se encarga de todo el entorno.

1. Abre una terminal en la raíz del proyecto.
2. Ejecuta el siguiente comando para construir y levantar los servicios:
```bash
docker-compose up --build
```

Deberías ver en los logs:

* `mosquitto`: Iniciando en puerto 1883.
* `backend`: Conectado exitosamente al Broker y listo para recibir datos.

### 4. ⚡ Cargar Código al ESP32

1. Conecta tu ESP32 por USB a la computadora.
2. Asegúrate de que tu PC y el ESP32 estén conectados a la misma red WiFi.
3. En PlatformIO (VS Code), presiona el botón de **Upload** (Flecha Derecha) en la barra inferior.
4. Una vez cargado, abre el **Monitor Serie** (Enchufe) para verificar la conexión.

**Nota:** Actualmente el código en `src/main.cpp` tiene valores simulados ("hardcodeados") para probar las alertas sin sensores físicos.

### 5. 🧪 Pruebas de Integración (Simulación de Cliente)

Para verificar que las alertas en tiempo real funcionan sin tener un Frontend desarrollado:

1. Abre una nueva terminal (sin cerrar Docker).
2. Instala la librería de websockets localmente (si no la tienes):
```bash
pip install websockets
```

3. Ejecuta el cliente de prueba WebSocket:
```bash
python python_service/wsocketclient_test.py
```

Si el ESP32 envía un valor de humedad < 30%, verás la alerta llegar instantáneamente a esta terminal.

---

## 📂 Estructura del Proyecto
```
IoT_Plantas/
├── .env                    # Variables de entorno (NO SUBIR A GIT)
├── docker-compose.yml      # Orquestador de contenedores
├── platformio.ini          # Configuración del ESP32 y Librerías
├── mosquitto/
│   └── config/mosquitto.conf
├── python_service/         # Microservicio de Backend Modular
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             # Orquestador del servicio
│   ├── database.py         # Módulo de InfluxDB
│   ├── ws_manager.py       # Módulo de WebSockets
│   └── wsocketclient_test.py # Script de prueba (Cliente)
└── src/
    └── main.cpp            # Firmware C++ del ESP32
```

---

**Autores:** Equipo IoT Plantas  
**Curso:** Introducción al Internet de las Cosas