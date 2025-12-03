# 🌿 Sistema IoT de Monitoreo de Plantas (Full Stack Local)

Este proyecto implementa una solución completa de IoT para el monitoreo de condiciones ambientales en plantas. A diferencia de soluciones básicas, este proyecto integra un **Servidor Web embebido en el ESP32** con un Dashboard profesional, backend en **Python**, base de datos de series temporales **InfluxDB** y visualización histórica con **Grafana**, todo orquestado mediante **Docker**.

---

## 🚀 Arquitectura del Sistema

### 1. Capa Física (Edge - ESP32)
- Lectura de sensores: Humedad (YL-69), Temperatura (DHT11), Luz (LDR), Movimiento (PIR)
- **Hosting Web:** El ESP32 aloja el Frontend (`index.html`, `styles.css`) en su memoria SPIFFS
- **Comunicación:** Envía datos por MQTT y recibe actualizaciones en tiempo real por WebSockets

### 2. Capa de Comunicaciones
- Protocolo MQTT (Eclipse Mosquitto)

### 3. Capa de Procesamiento (Backend)
- Servicio en Python que procesa mensajes MQTT
- Guarda datos históricos en InfluxDB
- Gestiona alertas y las envía al Dashboard vía WebSockets

### 4. Capa de Datos y Visualización
- **InfluxDB (v1.8):** Almacenamiento local de datos
- **Grafana:** Generación de gráficos históricos incrustados en el Dashboard principal

---

## 📋 Requisitos Previos

- [Visual Studio Code](https://code.visualstudio.com/) + Extensión **PlatformIO**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (debe estar corriendo)
- Hardware ESP32 y sensores (DHT11, LDR, PIR, YL-69)

---

## ⚙️ Instalación y Configuración (Paso a Paso)

### 1️⃣ Preparar el Entorno (Docker)

Toda la infraestructura de servidores corre en contenedores. No necesitas instalar Python ni bases de datos en tu PC.

1. Abre una terminal en la carpeta del proyecto
2. Construye y levanta los servicios:
   ```bash
   docker-compose up -d --build
   ```
3. Verifica que los 4 servicios estén corriendo (`mosquitto`, `backend`, `influxdb`, `grafana`)

---

### 2️⃣ Configurar Grafana (Visualización Histórica)

Este paso es manual y se hace una sola vez para generar la gráfica:

1. Entra a `http://localhost:3000` (Usuario/Pass: `admin`/`admin`)
2. Ve a **Connections → Data Sources** y agrega **InfluxDB**
   - **URL:** `http://influxdb:8086`
   - **Database:** `iot_data`
   - Click en "Save & Test"
3. Crea un nuevo **Dashboard**, agrega un panel y selecciona la métrica (ej. `humedad`)
4. Haz click en el título del panel → **Share → Embed**
5. **⚠️ IMPORTANTE:** Copia la URL del `src` y cambia `localhost` por la IP de tu computadora (ej. `192.168.1.212`)
6. Pega esa URL en el archivo `data/index.html` (línea del `iframe`)

---

### 3️⃣ Configurar Firmware (ESP32)

Edita el archivo `platformio.ini` para configurar tu red y particiones:

```ini
[env:esp32doit-devkit-v1]
platform = espressif32
board = esp32doit-devkit-v1
framework = arduino
monitor_speed = 115200
board_build.partitions = min_spiffs.csv  ; ⚠️ CRÍTICO PARA EL HTML

build_flags =
    '-D WIFI_SSID="TU_WIFI"'
    '-D WIFI_PASS="TU_CONTRASEÑA"'
    '-D MQTT_SERVER="IP_DE_TU_PC"'      ; Ej: 192.168.1.212
```

---

### 4️⃣ Cargar Código y Archivos al ESP32

Este proyecto requiere dos subidas distintas: una para el código (C++) y otra para la página web (HTML/CSS).

#### Paso A: Subir el Firmware (Código)

1. Conecta el ESP32
2. En PlatformIO, presiona **Upload** (Flecha derecha →)

#### Paso B: Subir el Dashboard (HTML/CSS)

Este paso guarda la carpeta `data/` en la memoria del ESP32.

1. Abre la terminal de PlatformIO en VS Code
2. Ejecuta el comando:
   ```bash
   pio run -t uploadfs
   ```
   *(Si falla por puerto ocupado, agrega `--upload-port COMx`)*

---

## 🖥️ Uso del Dashboard

1. Abre el **Monitor Serie** en VS Code y resetea el ESP32
2. Copia la dirección IP que aparece (ej. `IP del ESP32: 192.168.1.89`)
3. Abre esa IP en tu navegador web
4. **¡Listo!** Verás los valores en tiempo real y la gráfica histórica de Grafana

---

## 📂 Estructura del Proyecto

```
IoT_Plantas/
├── docker-compose.yml          # Orquestador (MQTT, Python, InfluxDB, Grafana)
├── platformio.ini              # Configuración ESP32
├── data/                       # Archivos Web (Se suben al ESP32)
│   ├── index.html              # Dashboard Principal
│   └── styles.css              # Estilos Dark Mode
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
├── python_service/             # Backend Lógico
│   ├── Dockerfile
│   ├── main.py                 # Procesa MQTT y envía WebSockets
│   ├── database.py             # Conector a InfluxDB
│   ├── ws_manager.py           # Gestor de conexiones WS
│   └── requirements.txt
└── src/
    └── main.cpp                # Código C++ del ESP32
```

---

## 🛠️ Solución de Problemas Comunes

| Problema | Solución |
|----------|----------|
| **Pantalla blanca en el navegador** | Olvidaste subir el sistema de archivos. Ejecuta `pio run -t uploadfs` |
| **Valores en "--" o "Desconectado"** | Verifica que el servicio de Python esté corriendo y que la IP en `index.html` (`wsUrl`) sea la correcta de tu PC |
| **Gráfica con icono roto** | Asegúrate de haber cambiado `localhost` por tu IP real en el `src` del `iframe` dentro de `index.html` |

---

## 👥 Autores

- Diego Alcantar
- Fabricio Aldaco
- Pablo Galán
- Manuel Perez
- Raul Verduzco

---