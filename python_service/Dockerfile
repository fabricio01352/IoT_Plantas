# Usamos una imagen de Python 3.9
FROM python:3.9-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos los requerimientos y los instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código fuente de la carpeta actual al contenedor
COPY . .

# Comando para arrancar tu script principal
# El "-u" es para ver los prints en la consola de Docker en tiempo real
CMD ["python", "-u", "main.py"]