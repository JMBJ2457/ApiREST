# Imagen base de Python ligera
FROM python:3.11-slim

# Config de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar (aprovecha cache de Docker)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar el código de la app
COPY . /app

# Backend por defecto (se puede sobrescribir con .env o compose)
ENV REPO_BACKEND=memory

# Puerto expuesto
EXPOSE 8000

# Comando por defecto de ejecución
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
