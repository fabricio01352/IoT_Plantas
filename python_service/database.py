import os
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

class DatabaseManager:
    def __init__(self):
        # Carga de variables
        self.url = os.getenv('INFLUXDB_URL', "")
        self.token = os.getenv('INFLUXDB_TOKEN', "")
        self.org = os.getenv('INFLUXDB_ORG', "")
        self.bucket = os.getenv('INFLUXDB_BUCKET', "")
        
        # Inicializacion del cliente
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        # Variables para control de calidad (cache)
        self.ultimo_valor_humedad = None
        self.ultimo_valor_luz = None

    def validar_datos(self, sensor, valor):
        # Logica de validacion y limpieza
        if sensor == "humedad":
            if not(0 <= valor <= 4095): return False
            if self.ultimo_valor_humedad is not None and abs(valor - self.ultimo_valor_humedad) > 200:
                print(f"Salto brusco en humedad descartado: {valor}")
                return False
            self.ultimo_valor_humedad = valor
            
        elif sensor == "luz":
            if not (0 <= valor <= 4095): return False
            if self.ultimo_valor_luz is not None and abs(valor - self.ultimo_valor_luz) > 300:
                print(f"Salto brusco en luz descartado: {valor}")
                return False
            self.ultimo_valor_luz = valor
            
        return True

    def guardar(self, topic, payload):
        try:
            data = json.loads(payload)
            valor = float(data.get("valor", 0))
            unidad = data.get("unidad", "")
            sensor = topic.split("/")[-1]

            if not self.validar_datos(sensor, valor):
                return

            p = (
                Point(sensor)
                .tag("sensor", "esp32")
                .field("valor", valor)
                .field("unidad", unidad)
                .time(datetime.utcnow(), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, org=self.org, record=p)
            print(f"[DB] Guardado: {sensor} -> {valor}{unidad}")

        except Exception as e:
            print(f"[DB] Error: {e}")