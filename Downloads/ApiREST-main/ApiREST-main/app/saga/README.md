# Patrón SAGA - Implementación

Este módulo implementa el patrón SAGA (Saga Orchestration Pattern) para operaciones transaccionales distribuidas.

## ¿Qué es SAGA?

SAGA es un patrón que maneja transacciones distribuidas mediante una secuencia de pasos locales. Si un paso falla, se ejecutan funciones de compensación para revertir los pasos anteriores.

## Características

- ✅ Ejecución secuencial de pasos
- ✅ Compensación automática en orden inverso si falla
- ✅ ✅ Contexto compartido entre pasos
- ✅ Logging detallado
- ✅ Estado rastreable de cada paso

## Estructura

```
app/saga/
├── __init__.py              # Exportaciones del módulo
├── orchestrator.py           # Orquestador SAGA base
└── README.md                 # Esta documentación
```

## Uso Básico

```python
from saga.orchestrator import SagaOrchestrator

# Crear orquestador
orchestrator = SagaOrchestrator("mi_operacion")

# Agregar pasos
orchestrator.add_step(
    "paso1",
    lambda: hacer_algo(),           # Función de ejecución
    lambda resultado: deshacer()    # Función de compensación
)

orchestrator.add_step(
    "paso2",
    lambda: hacer_otra_cosa(),
    lambda resultado: deshacer_otra_cosa(resultado)
)

# Ejecutar
try:
    resultado = orchestrator.execute()
    print(f"Éxito: {resultado}")
except SagaExecutionError as e:
    print(f"Error: {e.message}")
    print(f"Compensación aplicada: {e.compensation_results}")
```

## Ejemplo: Eliminar Categoría con Productos

Este es el caso de uso implementado en `services/categoria_saga_service.py`.

### Problema

Cuando eliminamos una categoría que tiene productos, necesitamos:
1. Mover los productos a otra categoría
2. Eliminar la categoría original

Si falla cualquier paso, debemos revertir todo.

### Solución con SAGA

```python
from services.categoria_saga_service import CategoriaSagaService

service = CategoriaSagaService(producto_repo, categoria_repo)

resultado = service.eliminar_categoria_con_productos(
    categoria_id=1,
    categoria_destino_id=2
)
```

### Pasos del SAGA

1. **Validar destino**: Verifica que la categoría destino existe y está activa
2. **Mover productos**: Mueve cada producto a la categoría destino
3. **Eliminar categoría**: Elimina la categoría original

### Compensación

Si falla en el paso 3 (eliminar categoría):
- Se recrea la categoría eliminada
- Se revierten los productos a su categoría original

Si falla en el paso 2 (mover productos):
- Se revierten los productos ya movidos
- No se elimina la categoría

## Endpoint REST

```
DELETE /api/v1/categorias/{categoria_id}/eliminar-con-productos?categoria_destino_id={destino_id}
```

### Ejemplo de Request

```bash
curl -X DELETE "http://localhost:8000/api/v1/categorias/1/eliminar-con-productos?categoria_destino_id=2"
```

### Ejemplo de Response (Éxito)

```json
{
    "success": true,
    "saga_id": "abc123-def456-...",
    "categoria_eliminada": 1,
    "categoria_eliminada_nombre": "Bebidas",
    "categoria_destino": 2,
    "categoria_destino_nombre": "Bebidas Frías",
    "productos_migrados": 5,
    "total_time": 0.123,
    "steps_completed": 3,
    "results": {
        "validar_destino": {...},
        "mover_productos": [...],
        "eliminar_categoria": {...}
    }
}
```

### Ejemplo de Response (Error)

```json
{
    "detail": {
        "error": "Error durante la eliminación de categoría",
        "message": "SAGA falló en paso 'eliminar_categoria': ...",
        "failed_step": "eliminar_categoria",
        "saga_id": "abc123-...",
        "compensation_applied": true
    }
}
```

## Estados de un Paso

- `PENDING`: Pendiente de ejecutar
- `EXECUTING`: En ejecución
- `COMPLETED`: Completado exitosamente
- `FAILED`: Falló durante la ejecución
- `COMPENSATING`: En proceso de compensación
- `COMPENSATED`: Compensado exitosamente

## Logging

El orquestador registra cada operación:

```
[SAGA abc12345] Iniciando 'eliminar_categoria_con_productos' con 3 pasos
[SAGA abc12345] Ejecutando paso: validar_destino
[SAGA abc12345] Paso 'validar_destino' completado en 0.01s
[SAGA abc12345] Ejecutando paso: mover_productos
[SAGA abc12345] Paso 'mover_productos' completado en 0.05s
[SAGA abc12345] Ejecutando paso: eliminar_categoria
[SAGA abc12345] Paso 'eliminar_categoria' completado en 0.02s
[SAGA abc12345] SAGA 'eliminar_categoria_con_productos' completado exitosamente en 0.08s
```

## Mejores Prácticas

1. **Funciones de compensación idempotentes**: Deben poder ejecutarse múltiples veces sin efectos secundarios
2. **Validaciones tempranas**: Validar todo lo posible antes de empezar el SAGA
3. **Logging detallado**: Registrar cada paso para debugging
4. **Manejo de errores**: Capturar excepciones específicas y proporcionar mensajes claros
5. **Contexto compartido**: Usar `orchestrator.context.metadata` para compartir datos entre pasos

## Extensión

Para agregar nuevos casos de uso SAGA:

1. Crear un nuevo servicio en `services/` (ej: `mi_saga_service.py`)
2. Usar `SagaOrchestrator` para definir los pasos
3. Implementar funciones de ejecución y compensación
4. Agregar endpoint en `api/v1/routers/` si es necesario

## Referencias

- [SAGA Pattern - Microservices.io](https://microservices.io/patterns/data/saga.html)
- [Saga Orchestration Pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Saga.html)

