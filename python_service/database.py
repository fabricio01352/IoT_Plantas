import json
import time
from datetime import datetime, timedelta
from influxdb import InfluxDBClient

class DatabaseManager:
    def __init__(self):
        # TUS VARIABLES DE CONTROL (Las mantuve intactas)
        self.ultimo_valor_humedad = None
        self.ultimo_valor_luz = None
        self.ultimo_timestamp = None  # Para KPI 9
        self.client = None
        
        # Inicializamos la conexión con reintentos
        self._inicializar_conexion()
    
    def _inicializar_conexion(self):
        """Inicializa la conexión a InfluxDB con reintentos"""
        max_intentos = 10
        espera_segundos = 3
        
        for intento in range(max_intentos):
            try:
                # Conexión directa al servicio 'influxdb' definido en Docker
                # No necesitamos tokens ni orgs complicados para la versión 1.8
                self.client = InfluxDBClient(host='influxdb', port=8086, timeout=5)
                
                # Aseguramos que la base de datos exista y la seleccionamos
                self.client.create_database('iot_data')
                self.client.switch_database('iot_data')
                
                print(f"[DB] Conectado exitosamente a InfluxDB (intento {intento + 1})")
                return
                
            except Exception as e:
                if intento < max_intentos - 1:
                    print(f"[DB] Intento {intento + 1}/{max_intentos} fallido. Esperando {espera_segundos}s antes de reintentar...")
                    time.sleep(espera_segundos)
                else:
                    print(f"[DB] ERROR: No se pudo conectar a InfluxDB después de {max_intentos} intentos: {e}")
                    print("[DB] El servicio continuará pero no guardará datos históricos hasta que InfluxDB esté disponible")
                    self.client = None

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
        # Si no hay conexión, intentamos reconectar
        if self.client is None:
            self._inicializar_conexion()
            if self.client is None:
                return  # No podemos guardar sin conexión
        
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
            # Actualizamos el timestamp de última conexión (para KPI 9)
            self.ultimo_timestamp = datetime.utcnow()
            print(f"[DB] Guardado: {sensor_name} -> {valor}")

        except Exception as e:
            print(f"[DB] Error guardando: {e}")
            # Si falla la conexión, marcamos como desconectado para reintentar
            if "Connection" in str(e) or "refused" in str(e).lower():
                self.client = None
    
    # ===================================================================
    # MÉTODOS PARA KPIs 6-10
    # ===================================================================
    
    def get_extremos_24h(self):
        """KPI 6: Obtiene máximos y mínimos de humedad y temperatura en últimas 24h"""
        if self.client is None:
            return {'humedad_max': None, 'humedad_min': None, 'temperatura_max': None, 'temperatura_min': None}
        try:
            # InfluxDB v1.8 usa formato de tiempo relativo
            # Humedad: MAX y MIN
            query_hum_max = 'SELECT MAX(value) FROM humedad WHERE time >= now() - 24h'
            query_hum_min = 'SELECT MIN(value) FROM humedad WHERE time >= now() - 24h'
            
            result_hum_max = self.client.query(query_hum_max)
            result_hum_min = self.client.query(query_hum_min)
            
            hum_max = None
            hum_min = None
            if result_hum_max:
                points = list(result_hum_max.get_points())
                if points and 'max' in points[0]:
                    hum_max = points[0]['max']
            if result_hum_min:
                points = list(result_hum_min.get_points())
                if points and 'min' in points[0]:
                    hum_min = points[0]['min']
            
            # Temperatura: MAX y MIN
            query_temp_max = 'SELECT MAX(value) FROM temperatura WHERE time >= now() - 24h'
            query_temp_min = 'SELECT MIN(value) FROM temperatura WHERE time >= now() - 24h'
            
            result_temp_max = self.client.query(query_temp_max)
            result_temp_min = self.client.query(query_temp_min)
            
            temp_max = None
            temp_min = None
            if result_temp_max:
                points = list(result_temp_max.get_points())
                if points and 'max' in points[0]:
                    temp_max = points[0]['max']
            if result_temp_min:
                points = list(result_temp_min.get_points())
                if points and 'min' in points[0]:
                    temp_min = points[0]['min']
            
            return {
                'humedad_max': round(hum_max, 1) if hum_max is not None else None,
                'humedad_min': round(hum_min, 1) if hum_min is not None else None,
                'temperatura_max': round(temp_max, 1) if temp_max is not None else None,
                'temperatura_min': round(temp_min, 1) if temp_min is not None else None
            }
        except Exception as e:
            print(f"[DB] Error en get_extremos_24h: {e}")
            return {'humedad_max': None, 'humedad_min': None, 'temperatura_max': None, 'temperatura_min': None}
    
    def get_horas_estres_24h(self):
        """KPI 7: Calcula horas en condición de estrés (últimas 24h)"""
        if self.client is None:
            return {'horas_humedad_critica': 0, 'horas_temperatura_critica': 0, 'horas_poca_luz': 0}
        try:
            # Contar puntos con humedad < 30%
            query_hum_critica = 'SELECT COUNT(value) FROM humedad WHERE time >= now() - 24h AND value < 30'
            result_hum = self.client.query(query_hum_critica)
            count_hum = 0
            if result_hum:
                points = list(result_hum.get_points())
                if points and 'count' in points[0]:
                    count_hum = points[0]['count']
            
            # Contar puntos con temperatura > 28°C
            query_temp_critica = 'SELECT COUNT(value) FROM temperatura WHERE time >= now() - 24h AND value > 28'
            result_temp = self.client.query(query_temp_critica)
            count_temp = 0
            if result_temp:
                points = list(result_temp.get_points())
                if points and 'count' in points[0]:
                    count_temp = points[0]['count']
            
            # Contar puntos con luz < 300 (poca luz)
            query_luz_baja = 'SELECT COUNT(value) FROM luz WHERE time >= now() - 24h AND value < 300'
            result_luz = self.client.query(query_luz_baja)
            count_luz = 0
            if result_luz:
                points = list(result_luz.get_points())
                if points and 'count' in points[0]:
                    count_luz = points[0]['count']
            
            # Asumiendo que hay una lectura cada 5 minutos (12 por hora)
            # Convertimos a horas aproximadas
            horas_hum = round(count_hum / 12, 1) if count_hum > 0 else 0
            horas_temp = round(count_temp / 12, 1) if count_temp > 0 else 0
            horas_luz = round(count_luz / 12, 1) if count_luz > 0 else 0
            
            return {
                'horas_humedad_critica': horas_hum,
                'horas_temperatura_critica': horas_temp,
                'horas_poca_luz': horas_luz
            }
        except Exception as e:
            print(f"[DB] Error en get_horas_estres_24h: {e}")
            return {'horas_humedad_critica': 0, 'horas_temperatura_critica': 0, 'horas_poca_luz': 0}
    
    def get_tasa_secado(self):
        """KPI 8: Calcula la tasa promedio de secado (% por día)"""
        if self.client is None:
            return {'tasa_secado': 0}
        try:
            # Obtener primer y último valor de humedad en las últimas 24h
            query_first = 'SELECT FIRST(value) FROM humedad WHERE time >= now() - 24h'
            query_last = 'SELECT LAST(value) FROM humedad WHERE time >= now() - 24h'
            
            result_first = self.client.query(query_first)
            result_last = self.client.query(query_last)
            
            first_val = None
            last_val = None
            
            if result_first:
                points = list(result_first.get_points())
                if points and 'first' in points[0]:
                    first_val = points[0]['first']
            
            if result_last:
                points = list(result_last.get_points())
                if points and 'last' in points[0]:
                    last_val = points[0]['last']
            
            if first_val is not None and last_val is not None:
                # Diferencia en 24 horas
                diferencia = last_val - first_val
                # Tasa por día (ya está en 24h, así que es directo)
                tasa = round(diferencia, 2)
            else:
                tasa = 0
            
            return {'tasa_secado': tasa}
        except Exception as e:
            print(f"[DB] Error en get_tasa_secado: {e}")
            return {'tasa_secado': 0}
    
    def get_ultima_conexion(self):
        """KPI 9: Obtiene el timestamp del último mensaje recibido"""
        # Si tenemos un timestamp guardado en memoria, lo usamos
        if self.ultimo_timestamp:
            return {'ultima_conexion': self.ultimo_timestamp.isoformat()}
        
        if self.client is None:
            return {'ultima_conexion': None}
        
        try:
            # Si no, buscamos el último timestamp de cualquier sensor en la BD
            query = 'SELECT LAST(value), time FROM humedad'
            result = self.client.query(query)
            
            if result:
                point = list(result.get_points())[0]
                last_time_str = point.get('time')
                if last_time_str:
                    # Parsear el timestamp de InfluxDB
                    last_time = datetime.fromisoformat(last_time_str.replace('Z', '+00:00'))
                    if last_time.tzinfo:
                        last_time = last_time.replace(tzinfo=None)
                    self.ultimo_timestamp = last_time
                    return {'ultima_conexion': last_time.isoformat()}
            
            return {'ultima_conexion': None}
        except Exception as e:
            print(f"[DB] Error en get_ultima_conexion: {e}")
            return {'ultima_conexion': None}
    
    def get_frecuencia_alertas(self):
        """KPI 10: Cuenta alertas de humedad crítica (7 días) y PIR (24h)"""
        if self.client is None:
            return {'alertas_humedad_7d': 0, 'detecciones_pir_24h': 0}
        try:
            # Alertas de humedad crítica en últimos 7 días
            query_hum = 'SELECT COUNT(value) FROM humedad WHERE time >= now() - 7d AND value < 30'
            result_hum = self.client.query(query_hum)
            count_hum = 0
            if result_hum:
                points = list(result_hum.get_points())
                if points and 'count' in points[0]:
                    count_hum = points[0]['count']
            
            # Detecciones PIR en últimas 24h (valor = 1)
            query_pir = 'SELECT COUNT(value) FROM pir WHERE time >= now() - 24h AND value = 1'
            result_pir = self.client.query(query_pir)
            count_pir = 0
            if result_pir:
                points = list(result_pir.get_points())
                if points and 'count' in points[0]:
                    count_pir = points[0]['count']
            
            return {
                'alertas_humedad_7d': int(count_hum),
                'detecciones_pir_24h': int(count_pir)
            }
        except Exception as e:
            print(f"[DB] Error en get_frecuencia_alertas: {e}")
            return {'alertas_humedad_7d': 0, 'detecciones_pir_24h': 0}