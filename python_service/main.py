import os
import asyncio
import json
import paho.mqtt.client as mqtt
from database import DatabaseManager
from ws_manager import WebSocketManager

# Instancias
db_manager = DatabaseManager()
ws_manager = WebSocketManager()
main_loop = None

# -------------------------------------------------------------------------
# CALLBACKS MQTT
# -------------------------------------------------------------------------

def on_connect(client, userdata, flags, rc):
    # Agregué sensores/temperatura por si decides enviarla después
    topics = ["sensores/humedad", "sensores/luz", "sensores/pir", "sensores/temperatura"]
    if rc == 0:
        print("[MQTT] Conectado exitosamente")
        for t in topics:
            client.subscribe(t)
            print(f"[MQTT] Suscrito a: {t}")
    else:
        print(f"[MQTT] Fallo conexion, codigo: {rc}")

def on_message(client, userdata, msg):
    global main_loop
    payload_str = msg.payload.decode()
    topic = msg.topic
    
    # 1. Guardar en Base de Datos (InfluxDB)
    # Esto sigue igual, guardamos todo el histórico
    db_manager.guardar(topic, payload_str)

    # 2. Procesar para WebSocket (Dashboard en Tiempo Real)
    try:
        data_in = json.loads(payload_str) # Lo que llega del ESP32
        valor = float(data_in.get("valor", 0))
        
        # Preparamos el JSON para el Frontend
        ws_payload = {}

        # Mapeamos el tópico MQTT a las claves que espera el HTML
        if "humedad" in topic:
            ws_payload["humedad"] = valor
            
            # REGLA DE ALERTA (Humedad Baja)
            if valor < 30:
                ws_payload["alerta"] = f"Humedad crítica: {valor}%"
            elif valor > 70:
                # Opcional: Limpiar alerta o avisar exceso
                pass 
            else:
                # Si todo está bien, enviamos alerta vacía para limpiar el mensaje rojo
                ws_payload["alerta"] = ""

        # KPI 4: LUMINOSIDAD
        elif "luz" in topic:
            ws_payload["luz"] = valor
            
            # Reglas de Negocio (Ajusta estos números según tu sensor real)
            # < 300: Muy oscuro (Alerta si es de día)
            # 300 - 2000: Luz Indirecta (Ideal)
            # > 2000: Luz Directa / Sol pleno
            
            if valor < 300:
                alerta_msg = "ALERTA: Poca luz para la planta"
            elif valor > 2000:
                alerta_msg = "ALERTA: Exceso de luz (Sol directo)"
            else:
                alerta_msg = "" # Luz óptima

        # KPI 5: MOVIMIENTO (PIR)
        elif "pir" in topic:
            ws_payload["pir"] = valor
            
            # Solo generamos alerta si detecta movimiento (valor 1)
            if valor == 1:
                alerta_msg = "ALERTA: ¡Movimiento detectado!"
            else:
                alerta_msg = "" # Silencio cuando no hay movimiento

        # KPI 2: TEMPERATURA
        elif "temperatura" in topic:
            ws_payload["temperatura"] = valor
            
            # Reglas de Negocio del KPI
            if valor < 15:
                alerta_msg = f"ALERTA: Temperatura Baja ({valor}°C)"
            elif valor > 28:
                alerta_msg = f"ALERTA: Calor Excesivo ({valor}°C)"
            else:
                # Si está en rango óptimo (15-28), no hay alerta
                alerta_msg = ""

        # 3. ENVIAR AL DASHBOARD
        # Convertimos el diccionario a String JSON
        mensaje_ws = json.dumps(ws_payload)

        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(mensaje_ws), 
                main_loop
            )

    except Exception as e:
        print(f"[MAIN] Error procesando mensaje: {e}")

# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------

async def calcular_y_enviar_kpis():
    """Tarea periódica que calcula y envía los KPIs 6-10 al frontend"""
    while True:
        try:
            await asyncio.sleep(30)  # Cada 30 segundos
            
            # KPI 6: Extremos del día
            extremos = db_manager.get_extremos_24h()
            
            # KPI 7: Horas en estrés
            horas_estres = db_manager.get_horas_estres_24h()
            
            # KPI 8: Tasa de secado
            tasa_secado = db_manager.get_tasa_secado()
            
            # KPI 9: Última conexión
            ultima_conexion = db_manager.get_ultima_conexion()
            
            # KPI 10: Frecuencia de alertas
            frecuencia_alertas = db_manager.get_frecuencia_alertas()
            
            # Combinamos todos los KPIs en un solo mensaje
            kpis_payload = {
                'kpi6': extremos,
                'kpi7': horas_estres,
                'kpi8': tasa_secado,
                'kpi9': ultima_conexion,
                'kpi10': frecuencia_alertas
            }
            
            mensaje_ws = json.dumps(kpis_payload)
            
            if main_loop and main_loop.is_running():
                await ws_manager.broadcast(mensaje_ws)
                print("[KPIs] Enviados KPIs 6-10 al dashboard")
                
        except Exception as e:
            print(f"[KPIs] Error calculando KPIs: {e}")

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
        mqtt_client.loop_start() 
    except Exception as e:
        print(f"[MQTT] Error de conexion: {e}")

    # Iniciamos la tarea periódica de KPIs
    asyncio.create_task(calcular_y_enviar_kpis())

    # Iniciamos el servidor WebSocket
    await ws_manager.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Apagando servicios...")