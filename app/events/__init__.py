"""
Módulo de Event Sourcing.

Contiene:
- Eventos de dominio
- Event Store
- Servicio de Rollback
"""
from events.domain_events import (
    DomainEvent,
    EventType,
    ProductoCreadoEvent,
    ProductoActualizadoEvent,
    ProductoEliminadoEvent,
    ProductoPrecioCambiadoEvent,
    ProductoDisponibilidadCambiadaEvent,
    CategoriaCreadaEvent,
    CategoriaActualizadaEvent,
    CategoriaEliminadaEvent,
    SagaIniciadoEvent,
    SagaPasoEjecutadoEvent,
    SagaPasoCompensadoEvent,
    SagaCompletadoEvent,
    SagaFallidoEvent,
    RollbackIniciadoEvent,
    RollbackCompletadoEvent,
    RollbackFallidoEvent
)

from events.event_store import EventStore
from events.rollback_service import RollbackService

__all__ = [
    "DomainEvent",
    "EventType",
    "ProductoCreadoEvent",
    "ProductoActualizadoEvent",
    "ProductoEliminadoEvent",
    "ProductoPrecioCambiadoEvent",
    "ProductoDisponibilidadCambiadaEvent",
    "CategoriaCreadaEvent",
    "CategoriaActualizadaEvent",
    "CategoriaEliminadaEvent",
    "SagaIniciadoEvent",
    "SagaPasoEjecutadoEvent",
    "SagaPasoCompensadoEvent",
    "SagaCompletadoEvent",
    "SagaFallidoEvent",
    "RollbackIniciadoEvent",
    "RollbackCompletadoEvent",
    "RollbackFallidoEvent",
    "EventStore",
    "RollbackService"
]
