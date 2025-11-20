# Cafetería API

API REST construida con FastAPI siguiendo principios SOLID y arquitectura limpia.

## Estructura

```

app/
├── api/                          # Capa HTTP (FastAPI)
│   ├── routers/                  # Endpoints / controladores
│   └── schemas/                  # Esquemas Pydantic (I/O)
│
├── core/                         # Configuración, Circuit Breaker y wiring
│   ├── config.py                 # Config global (pydantic-settings, .env)
│   ├── circuit_breaker.py        # Implementación de Circuit Breaker
│   └── dependencies.py           # Inyección de dependencias (DB, repos, servicios)
│
├── domain/                       # Modelos del dominio (dataclasses, enums)
│
├── repositories/                 # Contratos + implementaciones (Repository Pattern)
│   ├── base_repository.py        # Clase base
│   ├── sqlite_repository.py      # Persistencia en SQLite
│   └── json_repository.py        # Persistencia en archivos JSON (modo alterno)
│
├── services/                     # Lógica de negocio y casos de uso
│   ├── productos_service.py      # Reglas para productos
│   ├── categorias_service.py     # Reglas para categorías
│   └── menu_service.py           # Ensamblaje del menú
│
├── data/                         # Archivos JSON cuando REPO_BACKEND=file
│   └── menu.json
│
├── frontend/                     # Interfaz gráfica moderna integrada al backend
│   ├── index.html                # Vista principal del menú
│   ├── admin.html                # Panel de administrador (CRUD)
│   ├── styles.css                # Estilos (dark mode, diseño moderno)
│   ├── app.js                    # Lógica del frontend (consulta menú)
│   └── admin.js                  # CRUD de productos desde la UI
│
├── main.py                       # Inicialización FastAPI + CORS + montaje de /ui
│
├── database.db                   # Archivo SQLite generado en runtime
│
└── requirements.txt              # Dependencias del proyecto
```

## Configuración

Variables de entorno (via `.env` o entorno):

- `REPO_BACKEND`: `memory` (por defecto) o `file`.

Ejemplo `.env`:

```

REPO_BACKEND=file

```

## Ejecutar localmente

1. Instalar dependencias

```

pip install -r requirements.txt

```

2. Levantar servidor (backend en memoria)

```

uvicorn main:app --reload

```

3. Levantar servidor (backend de archivos JSON)

```

REPO_BACKEND=file uvicorn main:app --reload

```

4. Documentación interactiva

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Endpoints principales

- `GET /api/v1/menu`
- `GET /api/v1/estadisticas`
- `GET /api/v1/productos/`, `GET /api/v1/productos/{id}`
- `POST /api/v1/productos/`, `PUT /api/v1/productos/{id}`, `DELETE /api/v1/productos/{id}`
- `GET /api/v1/productos/search?q=...`, `GET /api/v1/productos/por-categoria/{categoria_id}`
- `GET /api/v1/productos/por-tipo?tipo=bebidas_calientes|postres|...`
- `GET /api/v1/categorias/`, `GET /api/v1/categorias/{id}`
- `POST /api/v1/categorias/`, `PUT /api/v1/categorias/{id}`, `DELETE /api/v1/categorias/{id}`

## Docker

### Archivos

- `app/Dockerfile`: imagen de la API (FastAPI + Uvicorn).
- `app/docker-compose.yml`: orquestación del servicio.
- `app/.dockerignore`: optimiza el contexto de build.
- `app/.env`: variables (ej. `REPO_BACKEND=file`).

### Construir y ejecutar

Desde la carpeta `app/`:

```
docker compose build
docker compose up
```

Por defecto usa `REPO_BACKEND=memory`. Para usar JSON:

1) Crear/editar `app/.env`:

```
REPO_BACKEND=file
```

2) Levantar:

```
docker compose up --build
```

La API quedará en `http://localhost:8000` y los endpoints bajo `/api/v1`.

## Notas de diseño

- `/api` solo HTTP (routers, schemas). El core no depende de la API.
- `/services` depende de `/repositories` (interfaces), no de implementaciones concretas.
- Repositorio seleccionable por `REPO_BACKEND` sin cambiar código.
- Fácil de extender con un `repositories/database_repository.py`.

## Futuras extensiones

- `db/` + `models/` (SQLAlchemy) y `DatabaseRepository`.
- `core/logging.py`, `core/errors.py`, middlewares.
- Tests unitarios y de integración.
