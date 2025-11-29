import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.v1.routers import productos, categorias, menu

# ----------------------------
# Configuración de Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(
    title="Cafetería API",
    version="1.0.0",
    description="API REST para gestión de menú de cafetería con FastAPI."
)

# ----------------------------
# CORS (permite conexión desde el frontend)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Rutas de la API
# ----------------------------
API_PREFIX = "/api/v1"

app.include_router(menu.router, prefix=API_PREFIX)
app.include_router(categorias.router, prefix=API_PREFIX)
app.include_router(productos.router, prefix=API_PREFIX)


# Servir interfaz gráfica 

# Esto permite abrir: http://127.0.0.1:8000/ui
app.mount(
    "/ui",
    StaticFiles(directory="frontend", html=True),
    name="frontend",
)


@app.get("/")
def root():
    return {
        "status": "OK",
        "message": "Bienvenido a la API de Cafetería",
        "ui": "/ui",
        "docs": "/docs"
    }
