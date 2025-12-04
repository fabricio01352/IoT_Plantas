# 📋 Guía Completa: Configuración de Grafana para el Proyecto Maceta Inteligente

Esta guía explica paso a paso cómo configurar todos los paneles de Grafana para que se muestren correctamente en el dashboard.

## ✅ Requisitos Previos

Antes de comenzar, asegúrate de que:

1. **Grafana esté instalado y funcionando** (accesible en `http://192.168.1.72:3000`)
2. **InfluxDB esté configurado** y guardando datos
3. **El datasource de InfluxDB esté configurado en Grafana** con:
   - Base de datos: `iot_data`
   - Mediciones: `humedad`, `temperatura`, `luz`, `pir`
   - UID del datasource: `df616a1a2251cb` (verifica que coincida con el tuyo)

## 📦 Archivos Necesarios

Los archivos JSON están en la carpeta `grafana_panels/`. Necesitarás:

1. **Extremos_Dia_Grafica.json** - Gráfica de extremos del día
2. **Tasa_Secado_Tendencia.json** - Tendencia de tasa de secado
3. **Historial_Conexion.json** - Historial de conexión
4. **Historial_Alertas.json** - Historial de alertas
5. **Grafica_Humedad.json** - Gráfica de humedad
6. **Tendencia_Temperatura.json** - Tendencia de temperatura
7. **Correlacion_Humedad_Temperatura.json** - Análisis de correlación
8. **Ciclo_Iluminacion.json** - Ciclo de iluminación
9. **Registro_Seguridad_PIR.json** - Registro de seguridad PIR

## 🚀 Proceso Paso a Paso

### Paso 1: Verificar el Datasource en Grafana

1. Abre Grafana → **Configuration** (⚙️) → **Data sources**
2. Haz clic en tu datasource de InfluxDB
3. **Copia el UID** del datasource (aparece en la URL o en la configuración)
4. Si el UID es diferente a `df616a1a2251cb`, necesitarás actualizar los JSONs (ver Paso 2.5)

### Paso 2: Crear los Dashboards y Paneles

Para cada archivo JSON:

#### 2.1 Crear un nuevo dashboard
1. Ve a **Dashboards** → **New** → **New Dashboard**
2. Haz clic en **Add visualization** o **Add panel**

#### 2.2 Importar el panel
1. Haz clic en el ícono de **"..."** (menú) → **Import panel**
2. O usa el atajo: presiona `Ctrl+V` después de copiar el JSON
3. Abre el archivo JSON correspondiente (ej: `Extremos_Dia_Grafica.json`)
4. **Copia TODO el contenido** del archivo
5. Pégalo en el campo de importación de Grafana
6. Haz clic en **Load** o **Import**

#### 2.3 Verificar la configuración
1. Verifica que el panel se haya cargado correctamente
2. Revisa que el **datasource** sea el correcto
3. Si el UID del datasource es diferente, edita el panel:
   - Ve a **Query** → Selecciona el datasource correcto
   - Guarda los cambios

#### 2.4 Guardar el dashboard
1. Haz clic en **Save dashboard** (💾)
2. Asigna un nombre descriptivo (ej: "Extremos del Día")
3. **Copia el UID del dashboard** (aparece en la URL después de guardar)
   - Formato: `http://192.168.1.72:3000/d/[UID]/...`
   - Ejemplo: Si la URL es `http://192.168.1.72:3000/d/2dd0701e-da16-4bbc-a83d-fe7f6128848a/...`
   - El UID es: `2dd0701e-da16-4bbc-a83d-fe7f6128848a`

#### 2.5 Obtener el ID del panel
1. Una vez guardado el dashboard, haz clic en el panel
2. En la URL verás algo como: `...&panelId=1` o `...&panelId=2`
3. **Anota el panelId** (puede ser 1, 2, 3, etc.)

#### 2.6 Repetir para cada panel
Repite los pasos 2.1 a 2.5 para cada archivo JSON.

### Paso 3: Actualizar las URLs en index.html

Una vez que tengas todos los UIDs de los dashboards y los panelIds:

1. Abre el archivo `data/index.html`
2. Busca cada iframe y actualiza la URL con el formato:

```
http://192.168.1.72:3000/d-solo/[UID_DASHBOARD]/[nombre-dashboard]?orgId=1&from=now-24h&to=now&timezone=browser&theme=dark&panelId=[ID_PANEL]
```

**Ejemplo:**
Si el dashboard de "Extremos del Día" tiene:
- UID: `2dd0701e-da16-4bbc-a83d-fe7f6128848a`
- Nombre: `extremos-del-dia-grafica`
- Panel ID: `1`

La URL sería:
```
http://192.168.1.72:3000/d-solo/2dd0701e-da16-4bbc-a83d-fe7f6128848a/extremos-del-dia-grafica?orgId=1&from=now-24h&to=now&timezone=browser&theme=dark&panelId=1
```

### Paso 4: Verificar que Funciona

1. Abre el dashboard en el navegador (`data/index.html`)
2. Verifica que todas las gráficas se muestren correctamente
3. Deben verse **solo las gráficas**, sin la interfaz de Grafana
4. Si alguna no se muestra:
   - Verifica que el UID del dashboard sea correcto
   - Verifica que el panelId sea correcto
   - Verifica que el datasource tenga datos
   - Revisa la consola del navegador (F12) para errores

## 📝 Checklist para tu Equipo

Usa esta lista para asegurarte de que todo esté configurado:

- [ ] Grafana está instalado y accesible
- [ ] InfluxDB está configurado y guardando datos
- [ ] El datasource de InfluxDB está configurado en Grafana
- [ ] El UID del datasource es conocido (o se actualizó en los JSONs)
- [ ] Se crearon todos los dashboards (9 en total)
- [ ] Se importaron todos los paneles JSON
- [ ] Se guardaron todos los dashboards
- [ ] Se anotaron todos los UIDs de los dashboards
- [ ] Se anotaron todos los panelIds
- [ ] Se actualizaron todas las URLs en `index.html`
- [ ] Se probó el dashboard y todas las gráficas se muestran

## 🔧 Solución de Problemas

### Problema: El panel no muestra datos

**Solución:**
1. Verifica que InfluxDB tenga datos: Ve a Grafana → Explore → Selecciona el datasource → Ejecuta una query simple como `SELECT * FROM "humedad" LIMIT 10`
2. Verifica que las mediciones existan: `humedad`, `temperatura`, `luz`, `pir`
3. Verifica que el rango de tiempo sea correcto (últimas 24h)

### Problema: El iframe muestra la interfaz completa de Grafana

**Solución:**
- Asegúrate de usar `/d-solo/` en lugar de `/d/` en las URLs
- Verifica que no tengas `editPanel=1` en la URL
- Asegúrate de tener `panelId=[número]` en la URL

### Problema: El panel muestra "No data"

**Solución:**
1. Verifica que haya datos en InfluxDB para el rango de tiempo seleccionado
2. Verifica que las queries sean correctas (deben usar `time > now() - 24h`)
3. Verifica que el datasource esté conectado correctamente

### Problema: El UID del datasource no coincide

**Solución:**
1. Obtén el UID correcto: Configuration → Data sources → InfluxDB → Copia el UID
2. Opción A: Edita cada JSON y reemplaza `"df616a1a2251cb"` con tu UID
3. Opción B: Después de importar, edita cada panel y cambia el datasource manualmente

## 📊 Mapeo de Paneles

| Archivo JSON | Panel en Dashboard | UID Dashboard | Panel ID |
|-------------|-------------------|---------------|---------|
| Extremos_Dia_Grafica.json | Extremos del Día | [Anotar] | [Anotar] |
| Tasa_Secado_Tendencia.json | Tasa de Secado | [Anotar] | [Anotar] |
| Historial_Conexion.json | Historial Conexión | [Anotar] | [Anotar] |
| Historial_Alertas.json | Historial Alertas | [Anotar] | [Anotar] |
| Grafica_Humedad.json | Gráfica Humedad | [Anotar] | [Anotar] |
| Tendencia_Temperatura.json | Tendencia Temperatura | [Anotar] | [Anotar] |
| Correlacion_Humedad_Temperatura.json | Correlación | [Anotar] | [Anotar] |
| Ciclo_Iluminacion.json | Ciclo Iluminación | [Anotar] | [Anotar] |
| Registro_Seguridad_PIR.json | Registro PIR | [Anotar] | [Anotar] |

**Usa esta tabla para anotar los UIDs y Panel IDs después de crear cada dashboard.**

## 💡 Tips Adicionales

1. **Organización**: Crea una carpeta en Grafana llamada "Maceta Inteligente" y guarda todos los dashboards ahí
2. **Nombres descriptivos**: Usa nombres claros para los dashboards (ej: "Extremos del Día", "Tasa de Secado")
3. **Permisos**: Si trabajas en equipo, asegúrate de que todos tengan permisos para ver los dashboards
4. **Backup**: Exporta los dashboards después de configurarlos (Dashboard → Settings → JSON Model → Save to file)

## 🎯 Resumen Rápido

1. **Importar JSONs** → Crear dashboards en Grafana
2. **Obtener UIDs** → Copiar UID de cada dashboard
3. **Obtener Panel IDs** → Anotar el ID de cada panel
4. **Actualizar HTML** → Cambiar URLs en `index.html` con formato `d-solo`
5. **Probar** → Verificar que todo funcione

---

**¿Necesitas ayuda?** Revisa la sección de "Solución de Problemas" o verifica los logs de Grafana e InfluxDB.

