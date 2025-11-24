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
│   ├── dependencies.py  # Inyección de dependencias
│   └── circuit_breaker.py  # Implementación del Circuit Breaker
├── db/                  # Base de datos
│   ├── models.py        # Modelos SQLAlchemy
│   └── session.py       # Configuración de sesión SQLite
├── domain/              # Modelos de dominio (dataclasses, enums)
├── repositories/        # Contratos e implementaciones de persistencia
├── services/            # Lógica de negocio / casos de uso
├── data/                # Datos JSON (cuando REPO_BACKEND=file) o SQLite (cuando REPO_BACKEND=database)
├── frontend/                # ***Nueva: Interfaz gráfica moderna***
│   ├── index.html           # Vista principal del menú
│   ├── admin.html           # Panel de administración (CRUD)
│   ├── styles.css           # Estilos modernos (dark UI)
│   ├── app.js               # Lógica del cliente (lista productos)
│   └── admin.js             # CRUD de productos (UI administrador)
├── main.py              # Instancia FastAPI + montaje de routers
└── requirements.txt     # Dependencias de la app
```

## Configuración

Variables de entorno (via `.env` o entorno):

- `REPO_BACKEND`: `memory` (por defecto), `file` o `database`.
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD`: Número de fallos antes de abrir el circuito (por defecto: 3).
- `CIRCUIT_BREAKER_RECOVERY_TIMEOUT`: Segundos antes de intentar recuperación (por defecto: 30.0).

Ejemplo `.env`:

```
REPO_BACKEND=database
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0
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

4. Levantar servidor (backend de base de datos SQLite)

```

REPO_BACKEND=database uvicorn main:app --reload

```

5. Documentación interactiva

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

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

Por defecto usa `REPO_BACKEND=memory`. Para usar archivos JSON o base de datos:

1) Crear/editar `app/.env`:

```
REPO_BACKEND=file
# o
REPO_BACKEND=database
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
- Base de datos SQLite implementada con SQLAlchemy en `db/models.py` y `repositories/database_repository.py`.
- Circuit Breaker protege automáticamente operaciones de archivo y base de datos.
- Arquitectura limpia: dominio independiente de infraestructura.

## Endpoints principales

- `GET /api/v1/menu`
- `GET /api/v1/estadisticas`
- `GET /api/v1/productos/`, `GET /api/v1/productos/{id}`
- `POST /api/v1/productos/`, `PUT /api/v1/productos/{id}`, `DELETE /api/v1/productos/{id}`
- `GET /api/v1/productos/search?q=...`, `GET /api/v1/productos/por-categoria/{categoria_id}`
- `GET /api/v1/productos/por-tipo?tipo=bebidas_calientes|postres|...`
- `GET /api/v1/categorias/`, `GET /api/v1/categorias/{id}`
- `POST /api/v1/categorias/`, `PUT /api/v1/categorias/{id}`, `DELETE /api/v1/categorias/{id}`

## Base de Datos SQLite

El proyecto incluye soporte para persistencia en base de datos SQLite mediante SQLAlchemy.

### Características

- Base de datos SQLite ubicada en `app/data/cafeteria.db`
- Modelos SQLAlchemy para `Producto` y `Categoria`
- Inicialización automática de tablas al usar `REPO_BACKEND=database`
- Integración con Circuit Breaker para proteger operaciones de base de datos

### Estructura de la Base de Datos

**Tabla `categorias`:**
- `id` (Integer, Primary Key)
- `nombre` (String, Indexed)
- `descripcion` (Text)
- `tipo` (String, Indexed) - Valor del enum `TipoCategoria`
- `activa` (Boolean)

**Tabla `productos`:**
- `id` (Integer, Primary Key)
- `nombre` (String, Indexed)
- `descripcion` (Text)
- `precio` (Float)
- `categoria_id` (Integer, Foreign Key a `categorias.id`, Indexed)
- `disponible` (Boolean)
- `tamano` (String, Nullable) - Valor del enum `TamanoProducto`
- `ingredientes` (JSON, Nullable) - Lista de strings
- `calorias` (Integer, Nullable)

### Uso

La base de datos se inicializa automáticamente cuando se usa `REPO_BACKEND=database`. Las tablas se crean en la primera ejecución si no existen.

```python
# La base de datos se crea automáticamente en app/data/cafeteria.db
# Las tablas se inicializan mediante SQLAlchemy
```

### Configuración

La conexión a SQLite está configurada en `db/session.py`:
- Pool estático para SQLite
- Soporte para threads (`check_same_thread=False`)
- Las sesiones se gestionan mediante dependency injection de FastAPI

## Circuit Breaker

El proyecto implementa el patrón **Circuit Breaker** para proteger operaciones de archivo y base de datos.

### ¿Qué es?

El Circuit Breaker protege contra fallos en cascada:
- **CLOSED**: Funciona normalmente, permite todas las llamadas
- **OPEN**: Bloqueado después de muchos fallos, responde rápido sin intentar
- **HALF_OPEN**: Estado de prueba, permite algunas llamadas para verificar recuperación

### Implementación

- Protege operaciones de lectura/escritura de archivos JSON (cuando `REPO_BACKEND=file`)
- Protege operaciones de base de datos SQLite (cuando `REPO_BACKEND=database`)
- Se activa automáticamente según el backend configurado
- Configurable mediante variables de entorno:
  - `CIRCUIT_BREAKER_FAILURE_THRESHOLD`: Número de fallos antes de abrir (default: 3)
  - `CIRCUIT_BREAKER_RECOVERY_TIMEOUT`: Segundos antes de intentar recuperación (default: 30.0)

### Ejemplo de uso

```python
from core.circuit_breaker import CircuitBreaker, circuit_breaker

# Uso directo
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
result = breaker.call(mi_funcion_riesgosa, arg1, arg2)

# Como decorador
@circuit_breaker(failure_threshold=5, recovery_timeout=60.0)
def llamar_servicio_externo():
    # código que puede fallar
    pass
```

### Protección en Repositorios

- **FileRepository**: Protege operaciones de lectura/escritura de archivos JSON
- **DatabaseRepository**: Protege operaciones de base de datos contra `SQLAlchemyError`, `OperationalError` y `TimeoutError`


## Acceso al Frontend

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

- Tests unitarios y de integración.
- Migraciones de base de datos con Alembic.
- Soporte para otras bases de datos (PostgreSQL, MySQL).

