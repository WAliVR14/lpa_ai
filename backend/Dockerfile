# ==============================================================================
# Dockerfile Backend - Sistema IA de Análisis LPA Aumovio (FastAPI)
# ==============================================================================
FROM python:3.11-slim

# Variables de entorno para optimización de Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

# Instalar dependencias esenciales del sistema para PyTorch CPU, OpenMP y Scikit-Learn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar la memoria caché de capas de Docker
COPY requirements.txt .

# Instalar dependencias de Python con el índice de PyTorch CPU sin almacenar caché de pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del backend
COPY app/ ./app

# Exponer el puerto del servidor ASGI
EXPOSE 8000

# Comando de ejecución con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

