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

    # Renombramos a 'broadcast' para que tenga sentido enviar datos y alertas
    async def broadcast(self, mensaje):
        if self.clients:
            # Envia el mensaje a todos los clientes conectados
            # mensaje debe ser un String (JSON.dumps)
            await asyncio.gather(*[client.send(mensaje) for client in self.clients])
            # print(f"[WS] Enviado a {len(self.clients)} clientes")

    async def start_server(self):
        # NOTA: Tu puerto en Python es 8765. 
        # Asegúrate de poner ese puerto en el index.html
        print("[WS] Servidor escuchando en 0.0.0.0:8765...")
        async with websockets.serve(self.handler, "0.0.0.0", 8765):
            await asyncio.Future()