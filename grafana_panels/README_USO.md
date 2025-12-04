# Configuraciones de Grafana - Paneles que no se veían

Este directorio contiene las configuraciones JSON para los paneles de Grafana que no se estaban mostrando en el frontend.

## Archivos creados

1. **Tasa_Secado_Tendencia.json** - 💨 Tendencia de Tasa de Secado
2. **Historial_Conexion.json** - 📡 Historial de Conexión
3. **Historial_Alertas.json** - 🔔 Historial de Alertas
4. **Grafica_Humedad.json** - 💧 Gráfica Humedad
5. **Tendencia_Temperatura.json** - 🌡️ Tendencia de Temperatura (Histórico)
6. **Correlacion_Humedad_Temperatura.json** - 📊 Análisis de Correlación (Humedad vs Temperatura)
7. **Ciclo_Iluminacion.json** - ☀️ Ciclo de Iluminación (Día/Noche)
8. **Registro_Seguridad_PIR.json** - 🛡️ Registro de Seguridad (Últimos Movimientos)

## Cómo usar

### Paso 1: Crear los dashboards en Grafana

Para cada panel que no se ve:

1. Ve a Grafana → Dashboards → New Dashboard
2. Haz clic en "Add visualization" o "Add panel"
3. Selecciona "Import panel" o pega el JSON directamente
4. Copia el contenido completo del archivo JSON correspondiente
5. Pégalo en el editor de Grafana
6. Guarda el panel

### Paso 2: Obtener el UID del dashboard

Después de crear cada panel:

1. Ve al dashboard donde está el panel
2. Haz clic en el título del dashboard → Settings
3. Copia el **UID** del dashboard (aparece en la URL o en la configuración)

### Paso 3: Actualizar los iframes en index.html

Una vez que tengas los UIDs de los dashboards, actualiza las URLs en `data/index.html`:

**Formato de URL:**
```
http://192.168.1.72:3000/d-solo/[UID_DASHBOARD]/[nombre-dashboard]?orgId=1&from=now-24h&to=now&timezone=browser&theme=dark&panelId=[ID_PANEL]
```

**Ejemplo:**
Si el dashboard de "Tasa de Secado" tiene UID `abc123` y el panel tiene ID `2`:
```
http://192.168.1.72:3000/d-solo/abc123/tasa-secado?orgId=1&from=now-24h&to=now&timezone=browser&theme=dark&panelId=2
```

## Configuración importante

Todos los paneles están configurados con:
- **Datasource UID**: `df616a1a2251cb` (ajusta si es diferente)
- **Queries**: Usan `rawQuery: true` y `time > now() - 24h` (formato que funciona)
- **Result Format**: `time_series`

## Queries usadas

### Tasa de Secado
```sql
SELECT derivative(mean("value"), 1d) as "Tasa de Secado" FROM "humedad" WHERE time > now() - 24h GROUP BY time(1h) fill(null)
```

### Historial de Conexión
```sql
SELECT COUNT("value") as "Mensajes recibidos" FROM "humedad" WHERE time > now() - 24h GROUP BY time(5m) fill(0)
```

### Historial de Alertas
```sql
SELECT COUNT("value") as "Alertas Humedad" FROM "humedad" WHERE time > now() - 7d AND "value" < 30 GROUP BY time(1h) fill(0)
SELECT COUNT("value") as "Detecciones PIR" FROM "pir" WHERE time > now() - 24h AND "value" = 1 GROUP BY time(1h) fill(0)
```

### Gráfica Humedad
```sql
SELECT mean("value") as "Humedad" FROM "humedad" WHERE time > now() - 24h GROUP BY time(5m) fill(null)
```

### Tendencia de Temperatura
```sql
SELECT mean("value") as "Temperatura" FROM "temperatura" WHERE time > now() - 24h GROUP BY time(5m) fill(null)
```

### Correlación Humedad vs Temperatura
```sql
SELECT mean("value") as "Humedad" FROM "humedad" WHERE time > now() - 24h GROUP BY time(5m) fill(null)
SELECT mean("value") as "Temperatura" FROM "temperatura" WHERE time > now() - 24h GROUP BY time(5m) fill(null)
```

### Ciclo de Iluminación
```sql
SELECT mean("value") as "Luminosidad" FROM "luz" WHERE time > now() - 24h GROUP BY time(5m) fill(null)
```

### Registro de Seguridad PIR
```sql
SELECT "value" as "Detecciones de Movimiento" FROM "pir" WHERE time > now() - 24h AND "value" = 1
```

## Notas

- Todos los paneles usan el formato de query que funciona en tu instalación
- Los intervalos de tiempo son configurables (actualmente 24h para la mayoría)
- Asegúrate de que el datasource UID coincida con el tuyo
- Después de crear los dashboards, actualiza las URLs en `index.html` con los UIDs correctos

