# Guía de Instalación y Uso - API REST con Event Sourcing

## Contenido del Proyecto

El proyecto mejorado incluye:

**Event Sourcing completo** - Registro de todos los cambios como eventos inmutables  
**Sistema de Rollback** - Revertir cambios a estados anteriores  
**Auditoría completa** - Historial de quién, cuándo y qué cambió  
**Integración con SAGA** - Los eventos del patrón SAGA también se registran  
**Endpoints REST** - API completa para consultar eventos y hacer rollback  
**Tests incluidos** - Script de prueba para verificar la implementación  

---

## Instalación

### Opción 1: Instalación Local

```bash
# 1. Descomprimir el proyecto
unzip ApiREST-con-Event-Sourcing.zip
cd ApiREST-con-event-sourcing

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r app/requirements.txt

# 4. Ejecutar tests (opcional)
python3 test_event_sourcing.py

# 5. Iniciar el servidor
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 2: Docker

```bash
# 1. Descomprimir el proyecto
unzip ApiREST-con-Event-Sourcing.zip
cd ApiREST-con-event-sourcing/app

# 2. Construir y ejecutar con Docker
docker compose build
docker compose up
```

---

## Acceso a la Documentación

Una vez iniciado el servidor:

- **Swagger UI (Documentación interactiva)**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Interfaz de usuario**: http://localhost:8000/ui
- **Panel de administración**: http://localhost:8000/ui/admin.html

---

## Probar Event Sourcing

### 1. Ejecutar Tests Automáticos

```bash
cd ApiREST-con-event-sourcing
source venv/bin/activate
python3 test_event_sourcing.py
```

**Resultado esperado:**
```
TODOS LOS TESTS COMPLETADOS EXITOSAMENTE
```

### 2. Probar Endpoints REST

#### Crear un producto (genera evento)

```bash
curl -X POST http://localhost:8000/api/v1/productos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Café Latte",
    "descripcion": "Café con leche",
    "precio": 4.50,
    "categoria_id": 1,
    "disponible": true
  }'
```

#### Ver eventos del producto

```bash
curl http://localhost:8000/api/v1/eventos/agregado/Producto/1
```

#### Ver historial de cambios

```bash
curl http://localhost:8000/api/v1/eventos/historial/Producto/1
```

#### Actualizar el producto (genera más eventos)

```bash
curl -X PUT http://localhost:8000/api/v1/productos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Café Latte Grande",
    "descripcion": "Café con leche",
    "precio": 5.50,
    "categoria_id": 1,
    "disponible": true
  }'
```

#### Hacer rollback del último cambio

```bash
curl -X POST http://localhost:8000/api/v1/eventos/rollback/last-n \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_type": "Producto",
    "aggregate_id": 1,
    "n": 1,
    "user_id": "admin",
    "razon": "Revertir cambio de precio"
  }'
```

#### Ver estadísticas del Event Store

```bash
curl http://localhost:8000/api/v1/eventos/estadisticas
```

---

## 📖 Documentación Completa

### Archivos de Documentación Incluidos

1. **`EVENT_SOURCING_README.md`** - Documentación completa de Event Sourcing
   - Arquitectura
   - Tipos de eventos
   - Endpoints de la API
   - Casos de uso
   - Ejemplos de código

2. **`README.md`** - Documentación original del proyecto
   - Estructura del proyecto
   - Configuración
   - Patrón SAGA
   - Circuit Breaker

3. **`app/saga/README.md`** - Documentación del patrón SAGA
   - Cómo funciona el SAGA
   - Integración con Event Sourcing

---

## Endpoints Principales de Event Sourcing

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/eventos` | Listar todos los eventos |
| GET | `/api/v1/eventos/{event_id}` | Obtener evento específico |
| GET | `/api/v1/eventos/agregado/{tipo}/{id}` | Eventos de un agregado |
| GET | `/api/v1/eventos/historial/{tipo}/{id}` | Historial de cambios |
| POST | `/api/v1/eventos/rollback/to-event` | Rollback a evento |
| POST | `/api/v1/eventos/rollback/to-timestamp` | Rollback a timestamp |
| POST | `/api/v1/eventos/rollback/last-n` | Rollback últimos N eventos |
| GET | `/api/v1/eventos/estadisticas` | Estadísticas del Event Store |

---

## Casos de Uso Comunes

### Caso 1: Auditoría - ¿Quién cambió el precio?

```bash
# Ver historial del producto
curl http://localhost:8000/api/v1/eventos/historial/Producto/5

# Resultado: Verás todos los cambios con usuario y timestamp
```

### Caso 2: Rollback - Revertir cambios incorrectos

```bash
# Rollback a un timestamp anterior
curl -X POST http://localhost:8000/api/v1/eventos/rollback/to-timestamp \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_type": "Producto",
    "aggregate_id": 5,
    "target_timestamp": "2024-01-15T10:00:00",
    "user_id": "admin",
    "razon": "Revertir cambios incorrectos"
  }'
```

### Caso 3: Investigación - ¿Qué pasó con esta categoría?

```bash
# Ver todos los eventos de la categoría
curl http://localhost:8000/api/v1/eventos/agregado/Categoria/7

# Verás: creación, actualizaciones, eliminación, SAGA, etc.
```

---

## Estructura de la Base de Datos

El proyecto crea automáticamente las siguientes tablas:

### Tablas Originales
- `productos` - Productos de la cafetería
- `categorias` - Categorías de productos

### Tablas Nuevas (Event Sourcing)
- **`event_store`** - Almacén de eventos (fuente de verdad)
- **`snapshots`** - Instantáneas del estado para optimización

---

## Configuración

### Variables de Entorno

Crear archivo `.env` en `app/`:

```env
# Backend de repositorio
REPO_BACKEND=database  # memory, file, o database

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0
```

---

## Verificar que Event Sourcing Funciona

### 1. Iniciar el servidor

```bash
cd app
uvicorn main:app --reload
```

### 2. Abrir Swagger UI

Ir a: http://localhost:8000/docs

### 3. Probar endpoints de eventos

En Swagger UI, buscar la sección **"Eventos y Rollback"** y probar:

1. `GET /api/v1/eventos/estadisticas` - Ver estadísticas
2. `GET /api/v1/eventos` - Listar eventos
3. Crear un producto en la sección "productos"
4. `GET /api/v1/eventos/agregado/Producto/1` - Ver eventos del producto creado

---

## Diferencias con el Proyecto Original

| Aspecto | Proyecto Original | Proyecto Mejorado |
|---------|-------------------|-------------------|
| **Registro de cambios** | Solo logs en consola | Eventos persistidos en BD |
| **Auditoría** | No disponible | Completa (quién, cuándo, qué) |
| **Rollback** | Solo en SAGA (tiempo real) | A cualquier punto en el tiempo |
| **Historial** | No disponible | Completo y consultable |
| **Eventos SAGA** | Solo logs | Registrados como eventos |
| **Reconstrucción** | No posible | Reconstruir estado en cualquier momento |

---

## Solución de Problemas

### Error: "Module not found"

```bash
# Asegurarse de estar en el entorno virtual
source venv/bin/activate

# Reinstalar dependencias
pip install -r app/requirements.txt
```

### Error: "Database locked"

```bash
# Detener el servidor y eliminar la base de datos
rm app/data/cafeteria.db

# Reiniciar el servidor (se creará automáticamente)
uvicorn main:app --reload
```

### Los eventos no se registran

Verificar que estás usando `REPO_BACKEND=database` en el archivo `.env`

---

## Soporte

Para preguntas o problemas:

1. Revisar la documentación en `EVENT_SOURCING_README.md`
2. Ejecutar los tests: `python3 test_event_sourcing.py`
3. Revisar los logs del servidor

---

## Checklist de Verificación

- [ ] Proyecto descomprimido
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Tests ejecutados exitosamente
- [ ] Servidor iniciado
- [ ] Swagger UI accesible
- [ ] Endpoints de eventos funcionando
- [ ] Rollback probado

---

**¡Listo para usar!**

El proyecto ahora tiene Event Sourcing completo con capacidad de rollback y auditoría.
