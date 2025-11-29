"""
Modelo de Event Store para persistir eventos de dominio.

Esta tabla almacena TODOS los eventos que ocurren en el sistema,
proporcionando una fuente de verdad inmutable.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class EventStoreModel(Base):
    """
    Modelo de base de datos para el Event Store.
    
    Cada fila representa un evento inmutable que ocurrió en el sistema.
    Los eventos NUNCA se modifican o eliminan, solo se agregan.
    """
    __tablename__ = "event_store"
    
    # Identificador único del evento
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # UUID del evento (para referencia externa)
    event_id = Column(String(36), unique=True, nullable=False, index=True)
    
    # Tipo de evento (producto_creado, categoria_actualizada, etc.)
    event_type = Column(String(100), nullable=False, index=True)
    
    # ID de la entidad afectada (producto_id, categoria_id, etc.)
    aggregate_id = Column(Integer, nullable=True, index=True)
    
    # Tipo de agregado (Producto, Categoria, Saga, etc.)
    aggregate_type = Column(String(50), nullable=False, index=True)
    
    # Timestamp del evento (cuándo ocurrió)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    # Usuario que ejecutó la acción (para auditoría)
    user_id = Column(String(100), nullable=True, index=True)
    
    # Datos del evento en formato JSON
    # Contiene toda la información específica del evento
    event_data = Column(JSON, nullable=False)
    
    # Metadata adicional (contexto, IP, etc.)
    event_metadata = Column(JSON, nullable=True)
    
    # Versión del evento (para evolución del esquema)
    version = Column(Integer, default=1, nullable=False)
    
    # Índices compuestos para consultas comunes
    __table_args__ = (
        # Buscar eventos por entidad
        Index('idx_aggregate', 'aggregate_type', 'aggregate_id'),
        # Buscar eventos por tipo y tiempo
        Index('idx_type_time', 'event_type', 'timestamp'),
        # Buscar eventos por usuario
        Index('idx_user_time', 'user_id', 'timestamp'),
    )
    
    def __repr__(self):
        return (
            f"<EventStoreModel("
            f"id={self.id}, "
            f"event_type={self.event_type}, "
            f"aggregate_id={self.aggregate_id}, "
            f"timestamp={self.timestamp}"
            f")>"
        )


class SnapshotModel(Base):
    """
    Modelo para snapshots (instantáneas) del estado de agregados.
    
    Los snapshots permiten reconstruir el estado actual sin
    tener que reproducir todos los eventos desde el inicio.
    """
    __tablename__ = "snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificador del agregado
    aggregate_id = Column(Integer, nullable=False, index=True)
    aggregate_type = Column(String(50), nullable=False, index=True)
    
    # Versión del snapshot (número de eventos aplicados)
    version = Column(Integer, nullable=False)
    
    # Estado completo del agregado en este punto
    state = Column(JSON, nullable=False)
    
    # Timestamp del snapshot
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    
    # Índice único: solo un snapshot por agregado
    __table_args__ = (
        Index('idx_aggregate_snapshot', 'aggregate_type', 'aggregate_id', unique=True),
    )
    
    def __repr__(self):
        return (
            f"<SnapshotModel("
            f"aggregate_type={self.aggregate_type}, "
            f"aggregate_id={self.aggregate_id}, "
            f"version={self.version}"
            f")>"
        )
