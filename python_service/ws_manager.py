import asyncio
import websockets

class WebSocketManager:
    def __init__(self):
        self.clients = set()

    async def handler(self, websocket):
        print("[WS] Cliente conectado")
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print("[WS] Cliente desconectado")

    async def enviar_alerta(self, mensaje):
        if self.clients:
            # Envia el mensaje a todos los clientes conectados
            await asyncio.gather(*[client.send(mensaje) for client in self.clients])
            print(f"[WS] Alerta enviada: {mensaje}")

    async def start_server(self):
        # Inicia el servidor en el puerto 8765
        print("[WS] Servidor escuchando en puerto 8765...")
        async with websockets.serve(self.handler, "0.0.0.0", 8765):
            await asyncio.Future() # Mantiene el servidor corriendo