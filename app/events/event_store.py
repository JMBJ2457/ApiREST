"""
Event Store - Almacén de eventos de dominio.

Responsabilidades:
- Persistir eventos de dominio
- Recuperar eventos por agregado, tipo, rango de tiempo
- Proporcionar stream de eventos para reconstrucción de estado
- Gestionar snapshots para optimización
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from events.domain_events import DomainEvent, EventType
from db.event_store_model import EventStoreModel, SnapshotModel
import json
import logging

logger = logging.getLogger(__name__)


class EventStore:
    """
    Almacén de eventos de dominio.
    
    Implementa el patrón Event Store para persistir
    todos los eventos que ocurren en el sistema.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa el Event Store.
        
        Args:
            db: Sesión de base de datos SQLAlchemy
        """
        self.db = db
    
    def append(self, event: DomainEvent) -> EventStoreModel:
        """
        Agrega un nuevo evento al store.
        
        Los eventos son inmutables y nunca se modifican.
        
        Args:
            event: Evento de dominio a persistir
            
        Returns:
            EventStoreModel: Modelo persistido en la base de datos
        """
        try:
            # Crear modelo de base de datos
            event_model = EventStoreModel(
                event_id=event.event_id,
                event_type=event.event_type.value if event.event_type else None,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                timestamp=event.timestamp,
                user_id=event.user_id,
                event_data=event.metadata,
                event_metadata={
                    "source": "event_store",
                    "version": 1
                },
                version=1
            )
            
            self.db.add(event_model)
            self.db.commit()
            self.db.refresh(event_model)
            
            logger.info(
                f"Evento persistido: {event.event_type.value if event.event_type else 'unknown'} "
                f"(ID: {event.event_id[:8]}..., Agregado: {event.aggregate_type}#{event.aggregate_id})"
            )
            
            return event_model
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al persistir evento: {str(e)}")
            raise
    
    def get_events_by_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: int,
        from_version: int = 0
    ) -> List[EventStoreModel]:
        """
        Obtiene todos los eventos de un agregado específico.
        
        Args:
            aggregate_type: Tipo de agregado (Producto, Categoria, etc.)
            aggregate_id: ID del agregado
            from_version: Versión desde la cual obtener eventos (para snapshots)
            
        Returns:
            Lista de eventos ordenados cronológicamente
        """
        try:
            events = self.db.query(EventStoreModel).filter(
                and_(
                    EventStoreModel.aggregate_type == aggregate_type,
                    EventStoreModel.aggregate_id == aggregate_id,
                    EventStoreModel.id > from_version
                )
            ).order_by(EventStoreModel.timestamp).all()
            
            logger.debug(
                f"Recuperados {len(events)} eventos para {aggregate_type}#{aggregate_id}"
            )
            
            return events
            
        except Exception as e:
            logger.error(f"Error al recuperar eventos: {str(e)}")
            raise
    
    def get_events_by_type(
        self,
        event_type: EventType,
        limit: int = 100
    ) -> List[EventStoreModel]:
        """
        Obtiene eventos por tipo.
        
        Args:
            event_type: Tipo de evento a buscar
            limit: Número máximo de eventos a retornar
            
        Returns:
            Lista de eventos del tipo especificado
        """
        try:
            events = self.db.query(EventStoreModel).filter(
                EventStoreModel.event_type == event_type.value
            ).order_by(desc(EventStoreModel.timestamp)).limit(limit).all()
            
            return events
            
        except Exception as e:
            logger.error(f"Error al buscar eventos por tipo: {str(e)}")
            raise
    
    def get_events_by_time_range(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        aggregate_type: Optional[str] = None
    ) -> List[EventStoreModel]:
        """
        Obtiene eventos en un rango de tiempo.
        
        Args:
            start_time: Tiempo de inicio
            end_time: Tiempo de fin (None = ahora)
            aggregate_type: Filtrar por tipo de agregado (opcional)
            
        Returns:
            Lista de eventos en el rango de tiempo
        """
        try:
            query = self.db.query(EventStoreModel).filter(
                EventStoreModel.timestamp >= start_time
            )
            
            if end_time:
                query = query.filter(EventStoreModel.timestamp <= end_time)
            
            if aggregate_type:
                query = query.filter(EventStoreModel.aggregate_type == aggregate_type)
            
            events = query.order_by(EventStoreModel.timestamp).all()
            
            return events
            
        except Exception as e:
            logger.error(f"Error al buscar eventos por rango de tiempo: {str(e)}")
            raise
    
    def get_events_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[EventStoreModel]:
        """
        Obtiene eventos ejecutados por un usuario específico.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de eventos
            
        Returns:
            Lista de eventos del usuario
        """
        try:
            events = self.db.query(EventStoreModel).filter(
                EventStoreModel.user_id == user_id
            ).order_by(desc(EventStoreModel.timestamp)).limit(limit).all()
            
            return events
            
        except Exception as e:
            logger.error(f"Error al buscar eventos por usuario: {str(e)}")
            raise
    
    def get_all_events(
        self,
        limit: int = 1000,
        offset: int = 0
    ) -> List[EventStoreModel]:
        """
        Obtiene todos los eventos (paginado).
        
        Args:
            limit: Número máximo de eventos
            offset: Offset para paginación
            
        Returns:
            Lista de eventos
        """
        try:
            events = self.db.query(EventStoreModel).order_by(
                desc(EventStoreModel.timestamp)
            ).limit(limit).offset(offset).all()
            
            return events
            
        except Exception as e:
            logger.error(f"Error al recuperar todos los eventos: {str(e)}")
            raise
    
    def get_event_by_id(self, event_id: str) -> Optional[EventStoreModel]:
        """
        Obtiene un evento específico por su ID.
        
        Args:
            event_id: UUID del evento
            
        Returns:
            Evento o None si no existe
        """
        try:
            event = self.db.query(EventStoreModel).filter(
                EventStoreModel.event_id == event_id
            ).first()
            
            return event
            
        except Exception as e:
            logger.error(f"Error al buscar evento por ID: {str(e)}")
            raise
    
    def create_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: int,
        state: Dict[str, Any],
        version: int
    ) -> SnapshotModel:
        """
        Crea un snapshot del estado actual de un agregado.
        
        Args:
            aggregate_type: Tipo de agregado
            aggregate_id: ID del agregado
            state: Estado completo del agregado
            version: Versión (número de eventos aplicados)
            
        Returns:
            SnapshotModel creado
        """
        try:
            # Eliminar snapshot anterior si existe
            self.db.query(SnapshotModel).filter(
                and_(
                    SnapshotModel.aggregate_type == aggregate_type,
                    SnapshotModel.aggregate_id == aggregate_id
                )
            ).delete()
            
            # Crear nuevo snapshot
            snapshot = SnapshotModel(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                version=version,
                state=state,
                timestamp=datetime.now()
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            logger.info(
                f"Snapshot creado para {aggregate_type}#{aggregate_id} "
                f"(versión {version})"
            )
            
            return snapshot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear snapshot: {str(e)}")
            raise
    
    def get_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: int
    ) -> Optional[SnapshotModel]:
        """
        Obtiene el snapshot de un agregado.
        
        Args:
            aggregate_type: Tipo de agregado
            aggregate_id: ID del agregado
            
        Returns:
            Snapshot o None si no existe
        """
        try:
            snapshot = self.db.query(SnapshotModel).filter(
                and_(
                    SnapshotModel.aggregate_type == aggregate_type,
                    SnapshotModel.aggregate_id == aggregate_id
                )
            ).first()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error al recuperar snapshot: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del Event Store.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            total_events = self.db.query(EventStoreModel).count()
            
            # Eventos por tipo
            events_by_type = {}
            for event_type in EventType:
                count = self.db.query(EventStoreModel).filter(
                    EventStoreModel.event_type == event_type.value
                ).count()
                if count > 0:
                    events_by_type[event_type.value] = count
            
            # Eventos por agregado
            events_by_aggregate = {}
            for aggregate_type in ["Producto", "Categoria", "Saga", "Rollback"]:
                count = self.db.query(EventStoreModel).filter(
                    EventStoreModel.aggregate_type == aggregate_type
                ).count()
                if count > 0:
                    events_by_aggregate[aggregate_type] = count
            
            # Último evento
            last_event = self.db.query(EventStoreModel).order_by(
                desc(EventStoreModel.timestamp)
            ).first()
            
            return {
                "total_events": total_events,
                "events_by_type": events_by_type,
                "events_by_aggregate": events_by_aggregate,
                "last_event_timestamp": last_event.timestamp.isoformat() if last_event else None,
                "snapshots_count": self.db.query(SnapshotModel).count()
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            raise
