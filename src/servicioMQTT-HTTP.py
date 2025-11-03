import asyncio
import json
import websockets
import paho.mqtt.client as mqtt

clients = set()

MQTT_BROKER = "192.168.1.6"
MQTT_TOPIC = "sensores/humedad"

loop = asyncio.get_event_loop() 

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print(f"mensaje de mqtt: {data}")
    asyncio.run_coroutine_threadsafe(send_to_clients(data), loop)

async def send_to_clients(message):
    if clients:
        await asyncio.wait([c.send(message) for c in clients])

async def ws_handler(websocket, path):
    clients.add(websocket)
    print("cliente conectado")
    try:
        async for message in websocket:
            pass
    finally:
        clients.remove(websocket)
        print("cliente desconectado")

async def main():
    server = await websockets.serve(ws_handler, "0.0.0.0", 8765)
    print("Servidor WebSocket corriendo en ws://0.0.0.0:8765")
    
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.subscribe(MQTT_TOPIC)
    mqtt_client.loop_start()

    await server.wait_closed()

asyncio.run(main())
