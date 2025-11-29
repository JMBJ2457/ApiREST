"""
Eventos de Dominio para Event Sourcing.

Cada evento representa un cambio de estado inmutable en el sistema.
Los eventos son la fuente de verdad del sistema.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import uuid


class EventType(Enum):
    """Tipos de eventos en el sistema"""
    # Eventos de Producto
    PRODUCTO_CREADO = "producto_creado"
    PRODUCTO_ACTUALIZADO = "producto_actualizado"
    PRODUCTO_ELIMINADO = "producto_eliminado"
    PRODUCTO_PRECIO_CAMBIADO = "producto_precio_cambiado"
    PRODUCTO_DISPONIBILIDAD_CAMBIADA = "producto_disponibilidad_cambiada"
    
    # Eventos de Categoría
    CATEGORIA_CREADA = "categoria_creada"
    CATEGORIA_ACTUALIZADA = "categoria_actualizada"
    CATEGORIA_ELIMINADA = "categoria_eliminada"
    CATEGORIA_ACTIVADA = "categoria_activada"
    CATEGORIA_DESACTIVADA = "categoria_desactivada"
    
    # Eventos de SAGA
    SAGA_INICIADO = "saga_iniciado"
    SAGA_PASO_EJECUTADO = "saga_paso_ejecutado"
    SAGA_PASO_COMPENSADO = "saga_paso_compensado"
    SAGA_COMPLETADO = "saga_completado"
    SAGA_FALLIDO = "saga_fallido"
    
    # Eventos de Rollback
    ROLLBACK_INICIADO = "rollback_iniciado"
    ROLLBACK_COMPLETADO = "rollback_completado"
    ROLLBACK_FALLIDO = "rollback_fallido"


@dataclass
class DomainEvent:
    """
    Evento de dominio base.
    
    Todos los eventos heredan de esta clase y representan
    un hecho que ocurrió en el pasado (inmutable).
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = None
    aggregate_id: int = None  # ID de la entidad afectada (producto_id, categoria_id, etc.)
    aggregate_type: str = None  # Tipo de entidad (Producto, Categoria, etc.)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None  # Quién ejecutó la acción
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario para persistencia"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if self.event_type else None,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "metadata": self.metadata
        }


# ==================== EVENTOS DE PRODUCTO ====================

@dataclass
class ProductoCreadoEvent(DomainEvent):
    """Evento: Se creó un nuevo producto"""
    nombre: str = None
    descripcion: str = None
    precio: float = None
    categoria_id: int = None
    disponible: bool = True
    
    def __post_init__(self):
        self.event_type = EventType.PRODUCTO_CREADO
        self.aggregate_type = "Producto"
        self.metadata.update({
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": self.precio,
            "categoria_id": self.categoria_id,
            "disponible": self.disponible
        })


@dataclass
class ProductoActualizadoEvent(DomainEvent):
    """Evento: Se actualizó un producto existente"""
    cambios: Dict[str, Any] = field(default_factory=dict)
    estado_anterior: Dict[str, Any] = field(default_factory=dict)
    estado_nuevo: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.PRODUCTO_ACTUALIZADO
        self.aggregate_type = "Producto"
        self.metadata.update({
            "cambios": self.cambios,
            "estado_anterior": self.estado_anterior,
            "estado_nuevo": self.estado_nuevo
        })


@dataclass
class ProductoEliminadoEvent(DomainEvent):
    """Evento: Se eliminó un producto"""
    producto_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.PRODUCTO_ELIMINADO
        self.aggregate_type = "Producto"
        self.metadata.update({
            "producto_data": self.producto_data
        })


@dataclass
class ProductoPrecioCambiadoEvent(DomainEvent):
    """Evento: Se cambió el precio de un producto"""
    precio_anterior: float = None
    precio_nuevo: float = None
    razon: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = EventType.PRODUCTO_PRECIO_CAMBIADO
        self.aggregate_type = "Producto"
        self.metadata.update({
            "precio_anterior": self.precio_anterior,
            "precio_nuevo": self.precio_nuevo,
            "razon": self.razon
        })


@dataclass
class ProductoDisponibilidadCambiadaEvent(DomainEvent):
    """Evento: Se cambió la disponibilidad de un producto"""
    disponible_anterior: bool = None
    disponible_nuevo: bool = None
    razon: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = EventType.PRODUCTO_DISPONIBILIDAD_CAMBIADA
        self.aggregate_type = "Producto"
        self.metadata.update({
            "disponible_anterior": self.disponible_anterior,
            "disponible_nuevo": self.disponible_nuevo,
            "razon": self.razon
        })


# ==================== EVENTOS DE CATEGORÍA ====================

@dataclass
class CategoriaCreadaEvent(DomainEvent):
    """Evento: Se creó una nueva categoría"""
    nombre: str = None
    descripcion: str = None
    tipo: str = None
    activa: bool = True
    
    def __post_init__(self):
        self.event_type = EventType.CATEGORIA_CREADA
        self.aggregate_type = "Categoria"
        self.metadata.update({
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "activa": self.activa
        })


@dataclass
class CategoriaActualizadaEvent(DomainEvent):
    """Evento: Se actualizó una categoría existente"""
    cambios: Dict[str, Any] = field(default_factory=dict)
    estado_anterior: Dict[str, Any] = field(default_factory=dict)
    estado_nuevo: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.CATEGORIA_ACTUALIZADA
        self.aggregate_type = "Categoria"
        self.metadata.update({
            "cambios": self.cambios,
            "estado_anterior": self.estado_anterior,
            "estado_nuevo": self.estado_nuevo
        })


@dataclass
class CategoriaEliminadaEvent(DomainEvent):
    """Evento: Se eliminó una categoría"""
    categoria_data: Dict[str, Any] = field(default_factory=dict)
    productos_movidos: int = 0
    categoria_destino_id: Optional[int] = None
    
    def __post_init__(self):
        self.event_type = EventType.CATEGORIA_ELIMINADA
        self.aggregate_type = "Categoria"
        self.metadata.update({
            "categoria_data": self.categoria_data,
            "productos_movidos": self.productos_movidos,
            "categoria_destino_id": self.categoria_destino_id
        })


# ==================== EVENTOS DE SAGA ====================

@dataclass
class SagaIniciadoEvent(DomainEvent):
    """Evento: Se inició un SAGA"""
    saga_id: str = None
    saga_name: str = None
    total_pasos: int = 0
    
    def __post_init__(self):
        self.event_type = EventType.SAGA_INICIADO
        self.aggregate_type = "Saga"
        self.metadata.update({
            "saga_id": self.saga_id,
            "saga_name": self.saga_name,
            "total_pasos": self.total_pasos
        })


@dataclass
class SagaPasoEjecutadoEvent(DomainEvent):
    """Evento: Se ejecutó un paso del SAGA"""
    saga_id: str = None
    paso_nombre: str = None
    paso_resultado: Any = None
    
    def __post_init__(self):
        self.event_type = EventType.SAGA_PASO_EJECUTADO
        self.aggregate_type = "Saga"
        self.metadata.update({
            "saga_id": self.saga_id,
            "paso_nombre": self.paso_nombre,
            "paso_resultado": str(self.paso_resultado) if self.paso_resultado else None
        })


@dataclass
class SagaPasoCompensadoEvent(DomainEvent):
    """Evento: Se compensó un paso del SAGA"""
    saga_id: str = None
    paso_nombre: str = None
    
    def __post_init__(self):
        self.event_type = EventType.SAGA_PASO_COMPENSADO
        self.aggregate_type = "Saga"
        self.metadata.update({
            "saga_id": self.saga_id,
            "paso_nombre": self.paso_nombre
        })


@dataclass
class SagaCompletadoEvent(DomainEvent):
    """Evento: Se completó un SAGA exitosamente"""
    saga_id: str = None
    saga_name: str = None
    total_time: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.SAGA_COMPLETADO
        self.aggregate_type = "Saga"
        self.metadata.update({
            "saga_id": self.saga_id,
            "saga_name": self.saga_name,
            "total_time": self.total_time
        })


@dataclass
class SagaFallidoEvent(DomainEvent):
    """Evento: Falló un SAGA"""
    saga_id: str = None
    saga_name: str = None
    paso_fallido: str = None
    error_message: str = None
    
    def __post_init__(self):
        self.event_type = EventType.SAGA_FALLIDO
        self.aggregate_type = "Saga"
        self.metadata.update({
            "saga_id": self.saga_id,
            "saga_name": self.saga_name,
            "paso_fallido": self.paso_fallido,
            "error_message": self.error_message
        })


# ==================== EVENTOS DE ROLLBACK ====================

@dataclass
class RollbackIniciadoEvent(DomainEvent):
    """Evento: Se inició un rollback"""
    rollback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_event_id: str = None
    razon: str = None
    
    def __post_init__(self):
        self.event_type = EventType.ROLLBACK_INICIADO
        self.aggregate_type = "Rollback"
        self.metadata.update({
            "rollback_id": self.rollback_id,
            "target_event_id": self.target_event_id,
            "razon": self.razon
        })


@dataclass
class RollbackCompletadoEvent(DomainEvent):
    """Evento: Se completó un rollback exitosamente"""
    rollback_id: str = None
    eventos_revertidos: int = 0
    
    def __post_init__(self):
        self.event_type = EventType.ROLLBACK_COMPLETADO
        self.aggregate_type = "Rollback"
        self.metadata.update({
            "rollback_id": self.rollback_id,
            "eventos_revertidos": self.eventos_revertidos
        })


@dataclass
class RollbackFallidoEvent(DomainEvent):
    """Evento: Falló un rollback"""
    rollback_id: str = None
    error_message: str = None
    
    def __post_init__(self):
        self.event_type = EventType.ROLLBACK_FALLIDO
        self.aggregate_type = "Rollback"
        self.metadata.update({
            "rollback_id": self.rollback_id,
            "error_message": self.error_message
        })
