# Event Sourcing - Documentación Completa

## 📋 Resumen Ejecutivo

Se ha implementado **Event Sourcing completo** en el proyecto API REST de Cafetería. Esta implementación proporciona:

✅ **Event Store** - Almacén persistente de todos los eventos del sistema  
✅ **Registro automático de cambios** - Todos los cambios CRUD se registran como eventos inmutables  
✅ **Sistema de Rollback** - Capacidad de revertir cambios a estados anteriores  
✅ **Auditoría completa** - Registro de quién, cuándo y qué cambió  
✅ **Historial de versiones** - Reconstrucción del estado en cualquier punto del tiempo  
✅ **Integración con SAGA** - Los eventos del patrón SAGA también se registran  

---

## 🎯 ¿Qué es Event Sourcing?

**Event Sourcing** es un patrón arquitectónico donde todos los cambios de estado se almacenan como una secuencia de eventos inmutables, en lugar de solo guardar el estado actual.

### Principios Fundamentales

1. **Los eventos son la fuente de verdad**: El estado actual se deriva de la secuencia de eventos
2. **Inmutabilidad**: Los eventos nunca se modifican o eliminan, solo se agregan
3. **Auditoría completa**: Cada cambio queda registrado con timestamp y usuario
4. **Reconstrucción de estado**: Se puede reconstruir el estado en cualquier punto del tiempo
5. **Rollback**: Se pueden revertir cambios aplicando eventos en orden inverso

---

## 🏗️ Arquitectura Implementada

### Componentes Principales

```
app/
├── events/                          # Módulo de Event Sourcing
│   ├── domain_events.py             # Definición de eventos de dominio
│   ├── event_store.py               # Almacén de eventos
│   ├── rollback_service.py          # Servicio de rollback
│   └── __init__.py
├── db/
│   ├── event_store_model.py         # Modelos de base de datos (Event Store, Snapshots)
│   └── session.py                   # Configuración de DB (actualizada)
├── repositories/
│   └── event_sourced_repository.py  # Wrappers con event sourcing
└── api/v1/routers/
    └── eventos.py                   # Endpoints REST para eventos y rollback
```

---

## 📊 Modelo de Datos

### Tabla `event_store`

Almacena todos los eventos del sistema:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID autoincremental |
| `event_id` | String(36) | UUID único del evento |
| `event_type` | String(100) | Tipo de evento (producto_creado, etc.) |
| `aggregate_id` | Integer | ID de la entidad afectada |
| `aggregate_type` | String(50) | Tipo de entidad (Producto, Categoria) |
| `timestamp` | DateTime | Cuándo ocurrió el evento |
| `user_id` | String(100) | Quién ejecutó la acción |
| `event_data` | JSON | Datos del evento |
| `metadata` | JSON | Metadata adicional |
| `version` | Integer | Versión del esquema |

**Índices optimizados:**
- `idx_aggregate`: (aggregate_type, aggregate_id)
- `idx_type_time`: (event_type, timestamp)
- `idx_user_time`: (user_id, timestamp)

### Tabla `snapshots`

Almacena instantáneas del estado para optimización:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID autoincremental |
| `aggregate_id` | Integer | ID del agregado |
| `aggregate_type` | String(50) | Tipo de agregado |
| `version` | Integer | Número de eventos aplicados |
| `state` | JSON | Estado completo del agregado |
| `timestamp` | DateTime | Cuándo se creó el snapshot |

---

## 🔄 Tipos de Eventos

### Eventos de Producto

- **`PRODUCTO_CREADO`**: Se creó un nuevo producto
- **`PRODUCTO_ACTUALIZADO`**: Se actualizó un producto existente
- **`PRODUCTO_ELIMINADO`**: Se eliminó un producto
- **`PRODUCTO_PRECIO_CAMBIADO`**: Se cambió el precio (evento específico)
- **`PRODUCTO_DISPONIBILIDAD_CAMBIADA`**: Se cambió la disponibilidad

### Eventos de Categoría

- **`CATEGORIA_CREADA`**: Se creó una nueva categoría
- **`CATEGORIA_ACTUALIZADA`**: Se actualizó una categoría
- **`CATEGORIA_ELIMINADA`**: Se eliminó una categoría
- **`CATEGORIA_ACTIVADA`**: Se activó una categoría
- **`CATEGORIA_DESACTIVADA`**: Se desactivó una categoría

### Eventos de SAGA

- **`SAGA_INICIADO`**: Se inició un SAGA
- **`SAGA_PASO_EJECUTADO`**: Se ejecutó un paso del SAGA
- **`SAGA_PASO_COMPENSADO`**: Se compensó un paso del SAGA
- **`SAGA_COMPLETADO`**: Se completó un SAGA exitosamente
- **`SAGA_FALLIDO`**: Falló un SAGA

### Eventos de Rollback

- **`ROLLBACK_INICIADO`**: Se inició un rollback
- **`ROLLBACK_COMPLETADO`**: Se completó un rollback
- **`ROLLBACK_FALLIDO`**: Falló un rollback

---

## 🚀 Endpoints de la API

### Listar Eventos

```http
GET /api/v1/eventos?limit=100&offset=0
```

Retorna todos los eventos del sistema (paginado).

**Respuesta:**
```json
[
  {
    "id": 1,
    "event_id": "abc123...",
    "event_type": "producto_creado",
    "aggregate_id": 1,
    "aggregate_type": "Producto",
    "timestamp": "2024-01-15T10:30:00",
    "user_id": "admin",
    "event_data": {
      "nombre": "Café Americano",
      "precio": 3.50
    }
  }
]
```

### Obtener Evento Específico

```http
GET /api/v1/eventos/{event_id}
```

Retorna un evento específico por su UUID.

### Eventos de un Agregado

```http
GET /api/v1/eventos/agregado/{aggregate_type}/{aggregate_id}
```

Ejemplo:
```http
GET /api/v1/eventos/agregado/Producto/1
```

Retorna todos los eventos de un producto específico.

### Historial de Cambios

```http
GET /api/v1/eventos/historial/{aggregate_type}/{aggregate_id}
```

Ejemplo:
```http
GET /api/v1/eventos/historial/Producto/1
```

Retorna el historial completo de cambios formateado.

**Respuesta:**
```json
{
  "aggregate_type": "Producto",
  "aggregate_id": 1,
  "total_eventos": 5,
  "historial": [
    {
      "event_id": "abc123...",
      "event_type": "producto_creado",
      "timestamp": "2024-01-15T10:30:00",
      "user_id": "admin",
      "data": {...}
    },
    {
      "event_id": "def456...",
      "event_type": "producto_precio_cambiado",
      "timestamp": "2024-01-16T14:20:00",
      "user_id": "admin",
      "data": {
        "precio_anterior": 3.50,
        "precio_nuevo": 3.99
      }
    }
  ]
}
```

### Rollback a Evento Específico

```http
POST /api/v1/eventos/rollback/to-event
```

**Body:**
```json
{
  "event_id": "abc123...",
  "user_id": "admin",
  "razon": "Revertir cambios incorrectos"
}
```

Revierte todos los cambios hasta un evento específico.

### Rollback a Timestamp

```http
POST /api/v1/eventos/rollback/to-timestamp
```

**Body:**
```json
{
  "aggregate_type": "Producto",
  "aggregate_id": 1,
  "target_timestamp": "2024-01-15T10:00:00",
  "user_id": "admin",
  "razon": "Revertir a estado de ayer"
}
```

Revierte un agregado específico a un timestamp.

### Rollback de Últimos N Eventos

```http
POST /api/v1/eventos/rollback/last-n
```

**Body:**
```json
{
  "aggregate_type": "Producto",
  "aggregate_id": 1,
  "n": 3,
  "user_id": "admin",
  "razon": "Revertir últimos 3 cambios"
}
```

Revierte los últimos N eventos de un agregado.

### Estadísticas del Event Store

```http
GET /api/v1/eventos/estadisticas
```

Retorna estadísticas del Event Store.

**Respuesta:**
```json
{
  "total_events": 1523,
  "events_by_type": {
    "producto_creado": 45,
    "producto_actualizado": 123,
    "categoria_creada": 12
  },
  "events_by_aggregate": {
    "Producto": 890,
    "Categoria": 234,
    "Saga": 56
  },
  "last_event_timestamp": "2024-01-20T15:30:00",
  "snapshots_count": 23
}
```

---

## 💡 Casos de Uso

### Caso 1: Auditoría de Cambios de Precio

**Escenario:** Necesitas saber quién cambió el precio de un producto y cuándo.

```bash
# Obtener historial del producto
curl http://localhost:8000/api/v1/eventos/historial/Producto/1
```

**Resultado:** Verás todos los cambios de precio con timestamp y usuario.

### Caso 2: Revertir Cambios Incorrectos

**Escenario:** Un usuario actualizó incorrectamente varios productos. Necesitas revertir los cambios.

```bash
# Rollback a timestamp anterior al error
curl -X POST http://localhost:8000/api/v1/eventos/rollback/to-timestamp \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_type": "Producto",
    "aggregate_id": 5,
    "target_timestamp": "2024-01-15T09:00:00",
    "user_id": "admin",
    "razon": "Revertir cambios incorrectos"
  }'
```

### Caso 3: Investigar Eliminación de Categoría

**Escenario:** Una categoría fue eliminada y necesitas saber qué pasó.

```bash
# Obtener eventos de la categoría
curl http://localhost:8000/api/v1/eventos/agregado/Categoria/7
```

**Resultado:** Verás:
- Cuándo se creó
- Todas las actualizaciones
- Cuándo se eliminó
- Si hubo un SAGA (movimiento de productos)

### Caso 4: Reconstruir Estado Histórico

**Escenario:** Necesitas saber cómo estaba un producto hace 1 semana.

```bash
# Obtener todos los eventos hasta esa fecha
curl http://localhost:8000/api/v1/eventos/agregado/Producto/1
```

Luego, en el código, puedes reconstruir el estado aplicando solo los eventos hasta esa fecha.

---

## 🔧 Integración con Repositorios

Los repositorios ahora están envueltos con Event Sourcing:

```python
from repositories.event_sourced_repository import EventSourcedProductoRepository
from repositories.database_repository import DatabaseProductoRepository

# Crear repositorio base
base_repo = DatabaseProductoRepository(db)

# Envolver con event sourcing
event_sourced_repo = EventSourcedProductoRepository(base_repo, db)

# Usar normalmente - los eventos se registran automáticamente
producto = Producto(...)
event_sourced_repo.agregar(producto)  # ✅ Evento registrado automáticamente
```

---

## 🎯 Diferencias: SAGA vs Event Sourcing

| Aspecto | SAGA | Event Sourcing |
|---------|------|----------------|
| **Propósito** | Garantizar atomicidad en operaciones multi-paso | Registrar todos los cambios como eventos |
| **Alcance** | Solo durante la ejecución de la transacción | Histórico completo de la aplicación |
| **Persistencia** | No persiste el historial (solo logs) | Todos los eventos se guardan permanentemente |
| **Rollback** | Solo durante compensación en tiempo real | Rollback a cualquier punto en el tiempo |
| **Auditoría** | Limitada a logs de consola | Auditoría completa en base de datos |
| **Uso** | Operaciones complejas (ej: eliminar categoría con productos) | Todas las operaciones CRUD |

**Ahora ambos están integrados:**
- El SAGA maneja la lógica de compensación en tiempo real
- Event Sourcing registra todos los pasos del SAGA como eventos
- Puedes hacer rollback de un SAGA completo usando Event Sourcing

---

## 📈 Ventajas de la Implementación

1. **Auditoría Completa**: Sabes exactamente qué pasó, cuándo y quién lo hizo
2. **Rollback Flexible**: Puedes revertir cambios a cualquier punto en el tiempo
3. **Debugging Mejorado**: Puedes reproducir bugs reconstruyendo el estado
4. **Compliance**: Cumple con requisitos de auditoría y regulación
5. **Análisis Histórico**: Puedes analizar tendencias y patrones de cambios
6. **Reconstrucción de Estado**: Si la base de datos se corrompe, puedes reconstruir desde eventos
7. **Integración con SAGA**: Los eventos del SAGA también se registran

---

## 🚦 Próximos Pasos Recomendados

### Implementado ✅
- Event Store con base de datos SQLite
- Eventos de dominio para Producto, Categoría, SAGA y Rollback
- Servicio de Rollback con 3 estrategias
- Endpoints REST para consulta y rollback
- Integración con repositorios existentes
- Snapshots para optimización

### Por Implementar (Opcional)
- [ ] **Workflow de Aprobación (Pull Request)**
  - Estados: pending, approved, rejected
  - Tabla de change requests
  - Endpoints para aprobar/rechazar cambios
  
- [ ] **Proyecciones de Eventos**
  - Vistas materializadas optimizadas
  - Reconstrucción automática desde eventos
  
- [ ] **Event Replay**
  - Capacidad de reproducir eventos para testing
  - Reconstrucción completa de la base de datos
  
- [ ] **Notificaciones de Eventos**
  - WebSockets para eventos en tiempo real
  - Integración con sistemas externos

---

## 📚 Ejemplos de Código

### Registrar Evento Manualmente

```python
from events import EventStore, ProductoCreadoEvent
from db.session import get_db

db = next(get_db())
event_store = EventStore(db)

# Crear evento
evento = ProductoCreadoEvent(
    aggregate_id=1,
    nombre="Café Latte",
    descripcion="Café con leche",
    precio=4.50,
    categoria_id=1,
    disponible=True,
    user_id="admin"
)

# Persistir evento
event_store.append(evento)
```

### Obtener Historial de un Producto

```python
from events import EventStore, RollbackService
from db.session import get_db

db = next(get_db())
event_store = EventStore(db)
rollback_service = RollbackService(db, event_store)

# Obtener historial
historial = rollback_service.get_history("Producto", 1)

for evento in historial:
    print(f"{evento['timestamp']}: {evento['event_type']}")
```

### Hacer Rollback

```python
from events import EventStore, RollbackService
from db.session import get_db
from datetime import datetime

db = next(get_db())
event_store = EventStore(db)
rollback_service = RollbackService(db, event_store)

# Rollback a timestamp
resultado = rollback_service.rollback_aggregate_to_timestamp(
    aggregate_type="Producto",
    aggregate_id=1,
    target_timestamp=datetime(2024, 1, 15, 10, 0, 0),
    user_id="admin",
    razon="Revertir cambios incorrectos"
)

print(f"Eventos revertidos: {resultado['eventos_revertidos']}")
```

---

## 🔍 Testing

### Probar Event Store

```bash
# Crear un producto (genera evento)
curl -X POST http://localhost:8000/api/v1/productos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test Producto",
    "descripcion": "Producto de prueba",
    "precio": 5.99,
    "categoria_id": 1,
    "disponible": true
  }'

# Ver eventos del producto
curl http://localhost:8000/api/v1/eventos/agregado/Producto/1

# Actualizar el producto (genera más eventos)
curl -X PUT http://localhost:8000/api/v1/productos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test Producto Actualizado",
    "descripcion": "Producto de prueba",
    "precio": 6.99,
    "categoria_id": 1,
    "disponible": true
  }'

# Ver historial completo
curl http://localhost:8000/api/v1/eventos/historial/Producto/1

# Hacer rollback del último cambio
curl -X POST http://localhost:8000/api/v1/eventos/rollback/last-n \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_type": "Producto",
    "aggregate_id": 1,
    "n": 1,
    "user_id": "admin",
    "razon": "Test de rollback"
  }'
```

---

## 📖 Referencias

- **Event Sourcing Pattern**: [Martin Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)
- **CQRS**: [Microsoft Docs](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- **Event Store**: [Greg Young](https://www.eventstore.com/)

---

**Documentación creada para el equipo de desarrollo**  
**Fecha**: Noviembre 2024  
**Versión**: 1.0
