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
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD`: Número de fallos antes de abrir el circuito (default: 3).
- `CIRCUIT_BREAKER_RECOVERY_TIMEOUT`: Segundos antes de intentar recuperación (default: 30.0).

Ejemplo `.env`:

```
REPO_BACKEND=file
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
- `GET /api/v1/circuit-breaker/estado` - Estado de los Circuit Breakers (solo con `REPO_BACKEND=file`)

## Circuit Breaker

El proyecto implementa el patrón **Circuit Breaker** para proteger las operaciones de archivo en `FileRepository`.

### ¿Qué es?

El Circuit Breaker protege contra fallos en cascada:
- **CLOSED**: Funciona normalmente, permite todas las llamadas
- **OPEN**: Bloqueado después de muchos fallos, responde rápido sin intentar
- **HALF_OPEN**: Estado de prueba, permite algunas llamadas para verificar recuperación

### Implementación

- Protege operaciones de lectura/escritura de archivos JSON
- Se activa automáticamente cuando `REPO_BACKEND=file`
- Configurable mediante variables de entorno
- Endpoint `/api/v1/circuit-breaker/estado` para monitoreo

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

## Notas de diseño

- `/api` solo HTTP (routers, schemas). El core no depende de la API.
- `/services` depende de `/repositories` (interfaces), no de implementaciones concretas.
- Repositorio seleccionable por `REPO_BACKEND` sin cambiar código.
- Circuit Breaker protege operaciones de archivo automáticamente.
- Fácil de extender con un `repositories/database_repository.py`.

## Cómo Probar el Circuit Breaker

### Método 1: Script de Prueba Automático

```bash
python test_circuit_breaker.py
```

Este script demuestra todos los estados del Circuit Breaker automáticamente.

### Método 2: Endpoints de Prueba

1. **Ver estado del Circuit Breaker:**
   ```bash
   GET /api/v1/circuit-breaker/estado
   ```

2. **Simular fallos para abrir el circuito:**
   ```bash
   POST /api/v1/circuit-breaker/test?accion=simular_fallos
   ```

3. **Resetear manualmente:**
   ```bash
   POST /api/v1/circuit-breaker/test?accion=reset
   ```

**Nota:** Los endpoints de prueba solo funcionan con `REPO_BACKEND=file`.

Ver `GUIA_PRUEBAS_CIRCUIT_BREAKER.md` para instrucciones detalladas.

## Futuras extensiones

- `db/` + `models/` (SQLAlchemy) y `DatabaseRepository`.
- `core/logging.py`, `core/errors.py`, middlewares.
- Tests unitarios y de integración.
