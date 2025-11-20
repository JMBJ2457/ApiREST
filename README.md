# Cafetería API

API REST construida con FastAPI siguiendo principios SOLID y arquitectura limpia.

## Estructura

```

app/
├── api/                     # Capa HTTP (FastAPI)
│   ├── routers/             # Endpoints / controladores
│   └── schemas/             # Esquemas Pydantic (entrada / salida)
│
├── core/                    # Configuración y wiring
│   ├── config.py            # Settings (pydantic-settings, variables .env)
│   └── dependencies.py      # Inyección de dependencias
│
├── domain/                  # Modelos de dominio (dataclasses, enums)
│
├── repositories/            # Contratos + persistencia (repo pattern)
│                           # Implementaciones según backend (SQLite / JSON)
│
├── services/                # Lógica de negocio (casos de uso)
│                           # Orquestan repositorios y modelos
│
├── data/                    # Datos JSON (modo archivo cuando REPO_BACKEND=file)
│
├── frontend/                # ***Nueva: Interfaz gráfica moderna***
│   ├── index.html           # Vista principal del menú
│   ├── admin.html           # Panel de administración (CRUD)
│   ├── styles.css           # Estilos modernos (dark UI)
│   ├── app.js               # Lógica del cliente (lista productos)
│   └── admin.js             # CRUD de productos (UI administrador)
│
├── main.py                  # Instancia FastAPI + routers + montaje de /ui
│
└── requirements.txt         # Dependencias del proyecto
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


## Acceso al frontend

La aplicación incluye una UI moderna que se monta automáticamente desde FastAPI.

- Menú principal (vista del cliente)
- http://127.0.0.1:8000/ui


- Permite:

- Ver el menú completo

- Buscar productos

- Filtrar por categoría

## Panel de Administración (CRUD de productos)
- http://127.0.0.1:8000/ui/admin.html


- Desde esta vista puedes:

- Crear productos

- Editar productos

- Eliminar productos

## Futuras extensiones

- `db/` + `models/` (SQLAlchemy) y `DatabaseRepository`.
- `core/logging.py`, `core/errors.py`, middlewares.
- Tests unitarios y de integración.
