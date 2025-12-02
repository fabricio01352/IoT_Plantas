import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:8765"
    print(f" Conectando a {uri} ...")

    try:
        async with websockets.connect(uri) as ws:
            print(" Conectado al WebSocket")

            while True:
                msg = await ws.recv()
                print(f" Mensaje recibido: {msg}")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f" Conexión cerrada inesperadamente: {e}")
    except Exception as e:
        print(f" Error: {e}")

asyncio.run(test_ws())
