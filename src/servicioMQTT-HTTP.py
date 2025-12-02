import asyncio # maneja tareas asincronas, clave para que pueda trabajare l servidor websocket y el cliente mqtt al mismo tiempo
import json # convierte datos entre json y objetos python
import websockets # para crear servidores y clientes websocket
import paho.mqtt.client as mqtt #cliente oficial de mqtt de eciplse , para suscribirse a topics y recibir mensajes desde el brotker
from influxdb_client import InfluxDBClient, Point, WritePrecision # cliente influx db
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


#  ESTE SERVICIO SIMULA UN BACKEND QUE IDEALMENTE SE TENDRIA EN OTRA COMPUTADORA, EL SERVICIO SE SUSCRIBE AL BROKER DE MOSQUITTO EN LOS TOPICS MENCIONADOS MAS ABAJO
#  Y UNA VEZ QUE LOS RECIBE, MANEJA DOS HILOS DIFERENTES PARA HACER ESTAS DOS COSAS: MANDAR DATOS A UN WEBSOCKET (ESTA ES LA PARTE DE NOTIFICACIONES) DONDE SE DEFINE UNA REGLA
#  QUE DICE CUANDO MANDAR ESA NOTIFICACION AL WEBSOCKET CLIENTE, Y POR OTRO LADO GUARDA LOS DATOS EN LA BD DE INFLUX DB EN LA NUBE



#  ------------------------------------------------------------------------------------------------------------
#  ------------------------------------------------------------------------------------------------------------
#  --------------------------------Definimos los datos de influxdb, todo es serverless y se sacan del cloud--------------------------------------------

org = "iotteam"
bucket = "humedad_data"
token = "oI2F4t12rZStmHnh8RMj89COxeEUcOv0p_JjCSc4m_PPVvOLVqTpRwfKFeRA9KvC25bz_nWPRyU6gH5hidQlfQ=="
client = InfluxDBClient(url="https://us-east-1-1.aws.cloud2.influxdata.com/", token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

ultimo_valor_humedad = None
ultimo_valor_luz = None

# el broker mosquitto esta en la computadora local
#  y los topics que se suscribe son humedad, luz y pir
#  los datos que manda los define el esp32, en formato JSON, por ahora solo manda valor y unidad, mas abajo se define el timestamp
mqtt_broker = "localhost"
# mqtt_topics = ["sensores/humedad", "sensores/luz", "sensores/pir"]
mqtt_topics = ["sensores/humedad", "sensores/luz", "sensores/pir"]


# lista de clientes conectadso al websocket
clients = set()
main_loop = None
#  ------------------------------------------------------------------------------------------------------------
#  ------------------------------------------------------------------------------------------------------------








#  ------------------------------------------------------------------------------------------------------------
#  ----------------------------------Funcion para guardar los datos en influxdb
#  ------------------------------------------------------------------------------------------------------------

#  esta funcion recibe el topic (humedad, luz o pir) y un payload que es el cuerp odel mensaje
def guardar_en_influx(topic, payload):
    global ultimo_valor_humedad, ultimo_valor_luz
    try:
        data = json.loads(payload)
        valor = float(data.get("valor", 0))
        unidad = data.get("unidad", "")
        sensor = topic.split("/")[-1]

        # AQUI ES DONDE AGREGAREMOS LIMPIEZAS DE DATOS Y CALIDAD DE DATOS
        # POR AHORA SOLO BUSCAMOS QUE NO EXISTAN DATOS ATIPICOS

        if sensor == "humedad":
            if not(0 <= valor <= 4095):
                print(f"valor de humedad fuera del rango: {valor}")
                return
            # salto brusco de 200 unidades, deberia estar en 0 a 1023 con analog read, pero si entre lecturas 
            # hace un salto de mas de 200 unidades es muy probable que seaerror electrico
        if ultimo_valor_humedad is not None and abs(valor - ultimo_valor_humedad) >200:
                print(f" vambio brusco en humedad ({ultimo_valor_humedad} → {valor}), descartado")
                return
        elif sensor == "luz":
            if not (0 <= valor <= 1023):
                print(f" Valor de luz fuera de rango: {valor}")
                return
                # cambio de 300 unidades, probable error electronico
            if ultimo_valor_luz is not None and abs(valor - ultimo_valor_luz) > 300:
                print(f" Cambio brusco en luz ({ultimo_valor_luz} → {valor}), descartado")
                return       
      
# Esta es la parte que crea la serie de datos que se guarda en la base de datos
# la estructura que se creo por ahora es el campo VALOR y el campo UNIDAD, ejemplo '23.5' 'Farhenheit"
#  y el timestamp es la hora actual
        p = (
            Point(topic.split("/")[-1])
            .tag("sensor", "esp32")
            .field("valor", valor)
            .field("unidad", unidad)
            .time(datetime.utcnow(), WritePrecision.NS)
        )

# Aqui es donde se guarda lo que se recibio en parametros, se manda a la interfaz de influxdb
        write_api.write(bucket=bucket, org=org, record=p)
        print(f" Guardado en InfluxDB: {topic} → {valor}{unidad}")

    except Exception as e:
        print(f" Error al guardar: {e}")









#  ------------------------------------------------------------------------------------------------------------
#  --------------------ESTA FUNCION ENVIA DATOS/NOTIFICACIONES AL CLIENTE MEDIANTE WEBSOCKET

#  ------------------------------------------------------------------------------------------------------------

async def enviar_a_clientes(msg):
    if clients:

        await asyncio.gather(*[c.send(msg) for c in clients])










#  ------------------------------------------------------------------------------------------------------------
#  -------ESTA FUNCION MANEJA LA LOGICA DEL WEBSOCKET, AGREGA Y REMUEVE CLIENTES
#  ------------------------------------------------------------------------------------------------------------

async def ws_handler(websocket):
    print(" Cliente WebSocket conectado")
    clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        clients.remove(websocket)
        print(" Cliente WebSocket desconectado")







#  ------------------------------------------------------------------------------------------------------------
#  ---------------ESTA FUNCION GUARDA LOS DATOS E INFLUX Y MANDA LOS DATOS AL WEBSOCKET
#  ------------------------------------------------------------------------------------------------------------

        # AQUI ES DONDE PODEMOS AGREGAR LOGICA DE NOTIFICACIONES, EJEMPLO, SI EL ATRIBUTO "VALOR" DEL TOPIC
        #  HUMEDAD ES MAYOR A 50%, ENVIA NOTIFICACION
 
def on_message(client, userdata, msg):
    global main_loop
    #  OBTENEMOS el cuerpo del mensaje lo que realmente nos interesa
    payload = msg.payload.decode()
    print(f" Mensaje MQTT : {payload}")

# guardamos
    guardar_en_influx(msg.topic, payload)

#  EN ESTE CASO, AGREGARE UNA CONDICION PARA QUE SE MANDE ALGO AL WEB SOCKET SOLAMENTE SI LA HUMEDAD ALCANZA CIERTO VALOR
#  PERO SE PUEDE AGREGAR CUALQUIER CONDICION
    try:
        # convertimos el payload a json para extraer el valor que nos interese
        data = json.loads(payload)
        valor = float(data.get("valor",0))
        unidad = data.get("unidad", "")

        if "humedad" in msg.topic and valor < 30:
            alerta = f" la humedad esta en valores criticos: {valor}{unidad}"
            asyncio.run_coroutine_threadsafe(enviar_a_clientes(alerta),main_loop)

    except Exception as e:
        print(f" Error procesando mensaje: {e}")










#  ------------------------------------------------------------------------------------------------------------
#  --------FUNCION MAIN
#  ------------------------------------------------------------------------------------------------------------


# Crea dos hilos separados, inicia el loop para que servir el web socket y para conectarse al broker mqtt
async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()

    #  inicia websocket puerto 8765
    ws_server = await websockets.serve(ws_handler, "0.0.0.0", 8765)

    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(mqtt_broker)

    # suscribe a los topics
    for t in mqtt_topics:
        mqtt_client.subscribe(t)

    main_loop.run_in_executor(None, mqtt_client.loop_forever)

    print(" Servidor WebSocket y MQTT iniciado")
    await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())
