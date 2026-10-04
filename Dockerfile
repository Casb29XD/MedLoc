# Usar una imagen base oficial y ligera de Python
FROM python:3.13-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python (incluyendo gunicorn para servir la app)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn==21.2.0

# Copiar el resto del código del backend
COPY . .

# Exponer el puerto en el que correrá la aplicación
EXPOSE 5000

# Comando por defecto para ejecutar la aplicación en producción
# Se enlaza a 0.0.0.0:5000 y apunta al objeto 'app' dentro de 'run.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
