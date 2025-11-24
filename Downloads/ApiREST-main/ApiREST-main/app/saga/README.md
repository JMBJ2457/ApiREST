# Documentación: Patrón SAGA - Eliminación de Categorías con Productos

## 📋 Resumen Ejecutivo

Se implementó el **patrón SAGA (Saga Orchestration Pattern)** para garantizar la **atomicidad** y **consistencia** de datos al eliminar categorías que contienen productos. Esta implementación asegura que si cualquier paso de la operación falla, todos los cambios se revierten automáticamente.

---

## 🎯 ¿Qué se Implementó?

### Funcionalidad Principal
- **Eliminación segura de categorías con productos**: Al eliminar una categoría, todos sus productos se mueven automáticamente a otra categoría destino.
- **Compensación automática**: Si algo falla durante el proceso, todos los cambios se revierten automáticamente.
- **Integración en endpoint estándar**: La funcionalidad está integrada en el endpoint `DELETE /api/v1/categorias/{id}`.

### Componentes Creados

1. **`SagaOrchestrator`** (`app/saga/orchestrator.py`)
   - Orquestador genérico que ejecuta pasos secuenciales
   - Maneja la compensación automática en orden inverso
   - Proporciona logging detallado y rastreo de estado

2. **`CategoriaSagaService`** (`app/services/categoria_saga_service.py`)
   - Servicio específico que implementa la lógica de negocio
   - Define los pasos del SAGA para eliminar categorías
   - Implementa las funciones de compensación

3. **Endpoint Integrado** (`app/api/v1/routers/categorias.py`)
   - Endpoint `DELETE /api/v1/categorias/{id}?categoria_destino_id={destino}`
   - Maneja tanto eliminación simple como eliminación con movimiento de productos

---

## 🔄 ¿Qué es el Patrón SAGA?

### Concepto General

El **patrón SAGA** es un patrón de diseño para manejar **transacciones distribuidas** o **operaciones multi-paso** que no pueden usar transacciones ACID tradicionales.

### Principios Fundamentales

1. **Operaciones Multi-Paso**: Una operación compleja se divide en pasos más pequeños y manejables.

2. **Compensación en lugar de Rollback**: En lugar de hacer "rollback" (como en transacciones ACID), cada paso tiene una función de **compensación** que deshace sus cambios.

3. **Ejecución Secuencial**: Los pasos se ejecutan uno tras otro en orden.

4. **Compensación Automática**: Si un paso falla, todos los pasos anteriores se compensan automáticamente en **orden inverso**.

### Estados del SAGA

```
PENDING → EXECUTING → COMPLETED
                ↓
            FAILED → COMPENSATING → COMPENSATED
```

---

## ⚙️ ¿Cómo Funciona en Nuestro Caso?

### Escenario: Eliminar "Bebidas Muy Calientes" y mover productos a "Bebidas Calientes"

### Pasos del SAGA

#### **Paso 1: Validar Destino**
- **Acción**: Verifica que la categoría destino existe y está activa
- **Compensación**: No requiere (solo validación)
- **Si falla**: El SAGA se detiene antes de hacer cambios

#### **Paso 2: Mover Productos**
- **Acción**: Cambia el `categoria_id` de cada producto de la categoría original a la categoría destino
- **Compensación**: Revierte cada producto a su `categoria_id` original
- **Si falla**: Se ejecuta la compensación y los productos vuelven a su categoría original

#### **Paso 3: Eliminar Categoría**
- **Acción**: Elimina la categoría original de la base de datos
- **Compensación**: Recrea la categoría con sus datos originales
- **Si falla**: Se ejecuta la compensación:
  1. Se recrea la categoría
  2. Se revierten los productos a su categoría original

### Flujo Visual

```
┌─────────────────────────────────────────────────────────┐
│  INICIO: Eliminar categoría 7, mover a categoría 1     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 1: Validar que categoría 1 existe y está activa  │
│  ✅ Éxito                                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 2: Mover 6 productos de categoría 7 → categoría 1│
│  ✅ Producto 22 movido                                  │
│  ✅ Producto 23 movido                                  │
│  ✅ Producto 24 movido                                  │
│  ✅ Producto 25 movido                                  │
│  ✅ Producto 26 movido                                  │
│  ✅ Producto 27 movido                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 3: Eliminar categoría 7                          │
│  ❌ FALLO SIMULADO                                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  COMPENSACIÓN AUTOMÁTICA (orden inverso)              │
│  🔄 Paso 3: Recrear categoría 7                         │
│  🔄 Paso 2: Revertir productos 22-27 a categoría 7      │
│  ✅ Compensación completada                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  RESULTADO: Estado original restaurado                 │
│  - Categoría 7 existe                                  │
│  - Productos 22-27 están en categoría 7                │
└─────────────────────────────────────────────────────────┘
```

---

## 🛡️ Garantías del SAGA

### 1. **Atomicidad**
- O se completan todos los pasos, o ninguno tiene efecto permanente
- No hay estados intermedios inconsistentes

### 2. **Consistencia**
- Si falla, el sistema vuelve a un estado consistente
- Los datos nunca quedan en un estado corrupto

### 3. **Trazabilidad**
- Cada operación tiene un `saga_id` único
- Todos los pasos se registran en logs
- Se puede rastrear qué pasó en cada operación

### 4. **Recuperación Automática**
- No requiere intervención manual
- La compensación se ejecuta automáticamente

---

## 📝 Ejemplo de Uso

### Desde la API REST

```bash
# Eliminar categoría 7, mover productos a categoría 1
DELETE /api/v1/categorias/7?categoria_destino_id=1
```

### Respuesta Exitosa
```json
{
  "status": 204,
  "message": "Categoría eliminada exitosamente"
}
```

### Respuesta con Error (SAGA falló)
```json
{
  "status": 500,
  "detail": {
    "error": "Error durante la eliminación de categoría",
    "message": "FALLO SIMULADO: Error al eliminar categoría...",
    "failed_step": "eliminar_categoria",
    "saga_id": "abc12345-...",
    "compensation_applied": true
  }
}
```

---

## 🔍 Logs del SAGA

Cuando se ejecuta el SAGA, se generan logs detallados:

```
2024-01-15 10:30:45 - services.categoria_saga_service - INFO - Iniciando eliminación de categoría 7 moviendo productos a categoría 1
2024-01-15 10:30:45 - services.categoria_saga_service - INFO - Encontrados 6 productos en categoría 7
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Iniciando 'eliminar_categoria_con_productos' con 3 pasos
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Ejecutando paso: validar_destino
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Paso 'validar_destino' completado en 0.01s
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Ejecutando paso: mover_productos
2024-01-15 10:30:45 - services.categoria_saga_service - INFO - Todos los productos (6) movidos exitosamente
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Ejecutando paso: eliminar_categoria
2024-01-15 10:30:45 - saga.orchestrator - ERROR - [SAGA abc12345] Error en paso 'eliminar_categoria': FALLO SIMULADO...
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Iniciando compensación...
2024-01-15 10:30:45 - services.categoria_saga_service - INFO - Iniciando compensación: revirtiendo 6 productos
2024-01-15 10:30:45 - saga.orchestrator - INFO - [SAGA abc12345] Compensando paso: mover_productos
2024-01-15 10:30:45 - services.categoria_saga_service - INFO - Producto 22 revertido a categoría 7
2024-01-15 10:30:45 - services.categoria_saga_service - INFO - Producto 23 revertido a categoría 7
...
```

---

## ✅ Ventajas de esta Implementación

1. **Seguridad de Datos**: Los productos nunca se pierden, siempre se mueven o se revierten
2. **Consistencia**: El sistema siempre queda en un estado válido
3. **Trazabilidad**: Logs detallados de cada operación
4. **Mantenibilidad**: Código modular y fácil de extender
5. **Reutilizable**: El `SagaOrchestrator` puede usarse para otros casos de uso
6. **Transparente**: El usuario solo ve éxito o error, la complejidad está oculta

---

## 🚀 Casos de Uso Futuros

El patrón SAGA puede extenderse para:

- **Crear categoría con productos iniciales**: Si falla, eliminar categoría y productos
- **Mover productos entre categorías**: Si falla, revertir movimientos
- **Actualizaciones masivas**: Si falla, revertir todos los cambios
- **Operaciones complejas multi-entidad**: Cualquier operación que requiera atomicidad

---

## 📚 Referencias Técnicas

- **Archivos principales**:
  - `app/saga/orchestrator.py` - Orquestador genérico
  - `app/services/categoria_saga_service.py` - Lógica de negocio
  - `app/api/v1/routers/categorias.py` - Endpoint REST

- **Patrón SAGA**: 
  - [Microservices.io - SAGA Pattern](https://microservices.io/patterns/data/saga.html)
  - [Enterprise Integration Patterns - Saga](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Saga.html)

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si hay productos duplicados por nombre?
El SAGA actual **no verifica duplicados**. Simplemente mueve los productos cambiando su `categoria_id`. Si hay productos con el mismo nombre en ambas categorías, ambos quedarán en la categoría destino.

### ¿Se puede usar con cualquier backend?
Sí, funciona con `memory`, `file` y `database` porque usa las interfaces de repositorio.

### ¿Qué pasa si el servidor se cae durante el SAGA?
Si el servidor se cae, el estado queda en el último paso completado. Al reiniciar, el SAGA no se reanuda automáticamente (requeriría implementación adicional de persistencia de estado).

### ¿Cómo se prueba la compensación?
Se puede simular un fallo agregando una excepción forzada en `categoria_saga_service.py` línea 269 (ver comentario "FALLO SIMULADO").

---

## 📋 Cambios Implementados

### ✅ Implementado

- **Integración en endpoint estándar**: La funcionalidad SAGA está ahora integrada en `DELETE /api/v1/categorias/{id}`
- **Parámetro opcional**: Se puede usar SAGA proporcionando `categoria_destino_id` como query parameter
- **Validación mejorada**: Si una categoría tiene productos, se requiere `categoria_destino_id` para eliminarla
- **Logging configurado**: Se agregó configuración de logging para ver los logs del SAGA en tiempo real

### ❌ Eliminado

- **Router separado**: Se eliminó `app/api/v1/routers/categorias_saga.py`
- **Endpoint duplicado**: Ya no existe `DELETE /api/v1/categorias/{id}/eliminar-con-productos`
- **Importaciones**: Se removieron las referencias a `categorias_saga` en `main.py`

### 🎯 Resultado

La funcionalidad está ahora unificada en un solo endpoint, haciendo la API más simple y consistente.

---

**Documentación creada para el equipo de desarrollo**  
**Fecha**: Enero 2024  
**Versión**: 1.0
