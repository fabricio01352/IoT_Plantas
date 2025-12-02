import os
import asyncio
import json
import paho.mqtt.client as mqtt
from database import DatabaseManager
from ws_manager import WebSocketManager

# Instancias de nuestros modulos
db_manager = DatabaseManager()
ws_manager = WebSocketManager()
main_loop = None

# -------------------------------------------------------------------------
# CALLBACKS MQTT
# -------------------------------------------------------------------------

def on_connect(client, userdata, flags, rc):
    topics = ["sensores/humedad", "sensores/luz", "sensores/pir"]
    if rc == 0:
        print("[MQTT] Conectado exitosamente")
        for t in topics:
            client.subscribe(t)
            print(f"[MQTT] Suscrito a: {t}")
    else:
        print(f"[MQTT] Fallo conexion, codigo: {rc}")

def on_message(client, userdata, msg):
    global main_loop
    payload = msg.payload.decode()
    topic = msg.topic
    
    # 1. Guardar en Base de Datos (Delegamos a db_manager)
    db_manager.guardar(topic, payload)

    # 2. Logica de Alertas (Delegamos el envio a ws_manager)
    try:
        data = json.loads(payload)
        valor = float(data.get("valor", 0))
        unidad = data.get("unidad", "")

        # Regla de Negocio: Humedad Critica
        if "humedad" in topic and valor < 30:
            mensaje = f"ALERTA: Humedad critica detectada: {valor}{unidad}"
            
            # Usamos el loop principal de asyncio para enviar el mensaje asincrono
            # desde este hilo sincrono de MQTT
            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.enviar_alerta(mensaje), 
                    main_loop
                )

    except Exception as e:
        print(f"[MAIN] Error procesando reglas: {e}")

# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()

    # Configuracion MQTT
    mqtt_broker = os.getenv('MQTT_BROKER_HOST', 'localhost')
    mqtt_port = int(os.getenv('MQTT_PORT', 1883))
    
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect

    print(f"[MAIN] Conectando a Broker {mqtt_broker}:{mqtt_port}...")
    
    try:
        mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        mqtt_client.loop_start() # Usamos loop_start para que corra en su propio hilo background
    except Exception as e:
        print(f"[MQTT] Error de conexion: {e}")

    # Iniciamos el servidor WebSocket (esto bloqueara la ejecucion aqui, manteniendo el script vivo)
    await ws_manager.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Apagando servicios...")