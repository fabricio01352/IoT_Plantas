import json
from influxdb import InfluxDBClient

class DatabaseManager:
    def __init__(self):
        # Conexión directa al servicio 'influxdb' definido en Docker
        # No necesitamos tokens ni orgs complicados para la versión 1.8
        self.client = InfluxDBClient(host='influxdb', port=8086)
        
        # Aseguramos que la base de datos exista y la seleccionamos
        self.client.create_database('iot_data')
        self.client.switch_database('iot_data')
        
        # TUS VARIABLES DE CONTROL (Las mantuve intactas)
        self.ultimo_valor_humedad = None
        self.ultimo_valor_luz = None

    def validar_datos(self, sensor, valor):
        # --- TU LÓGICA ORIGINAL DE VALIDACIÓN ---
        if sensor == "humedad":
            # Si el sensor da valores locos fuera de rango
            if not(0 <= valor <= 4095): return False
            
            # Filtro de "saltos bruscos" (ruido)
            if self.ultimo_valor_humedad is not None and abs(valor - self.ultimo_valor_humedad) > 200:
                print(f"[FILTRO] Salto brusco en humedad descartado: {valor}")
                return False
            self.ultimo_valor_humedad = valor
            
        elif sensor == "luz":
            if not (0 <= valor <= 4095): return False
            if self.ultimo_valor_luz is not None and abs(valor - self.ultimo_valor_luz) > 300:
                print(f"[FILTRO] Salto brusco en luz descartado: {valor}")
                return False
            self.ultimo_valor_luz = valor
            
        return True

    def guardar(self, topic, payload):
        try:
            data = json.loads(payload)
            valor = float(data.get("valor", 0))
            # Identificamos el sensor por el tópico (ej: sensores/humedad -> humedad)
            sensor_name = topic.split("/")[-1]

            # 1. VALIDAMOS ANTES DE GUARDAR
            # (Si tu función dice False, no guardamos nada)
            if not self.validar_datos(sensor_name, valor):
                return

            # 2. PREPARAMOS EL DATO PARA INFLUXDB v1
            json_body = [
                {
                    "measurement": sensor_name,
                    "tags": {
                        "origen": "esp32_lab"
                    },
                    "fields": {
                        "value": valor
                    }
                }
            ]

            # 3. GUARDAMOS
            self.client.write_points(json_body)
            print(f"[DB] Guardado: {sensor_name} -> {valor}")

        except Exception as e:
            print(f"[DB] Error: {e}")