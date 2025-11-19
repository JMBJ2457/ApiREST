from fastapi import FastAPI

from api.v1.routers import productos, categorias, menu

app = FastAPI(title="Cafetería API", version="1.0.0")

# Prefijo de versión
API_PREFIX = "/api/v1"

app.include_router(menu.router, prefix=API_PREFIX)
app.include_router(categorias.router, prefix=API_PREFIX)
app.include_router(productos.router, prefix=API_PREFIX)
