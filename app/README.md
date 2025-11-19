# Cafetería API

API REST construida con FastAPI siguiendo principios SOLID y arquitectura limpia.

## Estructura

```
app/
├── api/                 # Capa HTTP
│   ├── routers/         # Endpoints (FastAPI Routers)
│   └── schemas/         # Esquemas Pydantic (I/O)
├── core/                # Configuración y wiring
│   ├── config.py        # Settings (pydantic-settings, .env)
│   └── dependencies.py  # Inyección de dependencias
├── domain/              # Modelos de dominio (dataclasses, enums)
├── repositories/        # Contratos e implementaciones de persistencia
├── services/            # Lógica de negocio / casos de uso
├── data/                # Datos JSON (cuando REPO_BACKEND=file)
├── main.py              # Instancia FastAPI + montaje de routers
└── requirements.txt     # Dependencias de la app
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

## Notas de diseño

- `/api` solo HTTP (routers, schemas). El core no depende de la API.
- `/services` depende de `/repositories` (interfaces), no de implementaciones concretas.
- Repositorio seleccionable por `REPO_BACKEND` sin cambiar código.
- Fácil de extender con un `repositories/database_repository.py`.

## Futuras extensiones

- `db/` + `models/` (SQLAlchemy) y `DatabaseRepository`.
- `core/logging.py`, `core/errors.py`, middlewares.
- Tests unitarios y de integración.
