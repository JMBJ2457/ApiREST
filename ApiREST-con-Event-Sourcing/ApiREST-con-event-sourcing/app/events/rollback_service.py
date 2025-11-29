"""
Servicio de Rollback basado en Event Sourcing.

Permite revertir cambios a estados anteriores utilizando
el historial de eventos almacenado en el Event Store.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from events.event_store import EventStore
from events.domain_events import (
    EventType,
    RollbackIniciadoEvent,
    RollbackCompletadoEvent,
    RollbackFallidoEvent,
    ProductoCreadoEvent,
    ProductoActualizadoEvent,
    ProductoEliminadoEvent,
    CategoriaCreadaEvent,
    CategoriaActualizadaEvent,
    CategoriaEliminadaEvent
)
from db.models import ProductoModel, CategoriaModel

logger = logging.getLogger(__name__)


class RollbackService:
    """
    Servicio para realizar rollback de operaciones.
    
    Utiliza el Event Store para identificar cambios y revertirlos.
    """
    
    def __init__(self, db: Session, event_store: EventStore):
        """
        Inicializa el servicio de rollback.
        
        Args:
            db: Sesión de base de datos
            event_store: Event Store para consultar eventos
        """
        self.db = db
        self.event_store = event_store
    
    def rollback_to_event(
        self,
        event_id: str,
        user_id: Optional[str] = None,
        razon: str = "Rollback manual"
    ) -> Dict[str, Any]:
        """
        Revierte todos los cambios hasta un evento específico.
        
        Args:
            event_id: ID del evento hasta el cual revertir
            user_id: Usuario que ejecuta el rollback
            razon: Razón del rollback
            
        Returns:
            Diccionario con resultados del rollback
        """
        # Registrar inicio del rollback
        rollback_event = RollbackIniciadoEvent(
            target_event_id=event_id,
            razon=razon,
            user_id=user_id
        )
        self.event_store.append(rollback_event)
        
        try:
            # Obtener el evento objetivo
            target_event = self.event_store.get_event_by_id(event_id)
            if not target_event:
                raise ValueError(f"Evento {event_id} no encontrado")
            
            logger.info(
                f"Iniciando rollback hasta evento {event_id[:8]}... "
                f"(timestamp: {target_event.timestamp})"
            )
            
            # Obtener todos los eventos posteriores al objetivo
            eventos_a_revertir = self.db.query(
                self.event_store.db.query(type(target_event)).filter(
                    type(target_event).timestamp > target_event.timestamp
                ).order_by(type(target_event).timestamp.desc()).all()
            )
            
            eventos_revertidos = 0
            
            # Revertir cada evento en orden inverso
            for evento in eventos_a_revertir:
                self._revertir_evento(evento)
                eventos_revertidos += 1
            
            # Registrar éxito del rollback
            success_event = RollbackCompletadoEvent(
                rollback_id=rollback_event.rollback_id,
                eventos_revertidos=eventos_revertidos,
                user_id=user_id
            )
            self.event_store.append(success_event)
            
            logger.info(
                f"Rollback completado: {eventos_revertidos} eventos revertidos"
            )
            
            return {
                "success": True,
                "rollback_id": rollback_event.rollback_id,
                "eventos_revertidos": eventos_revertidos,
                "target_event_id": event_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Registrar fallo del rollback
            error_event = RollbackFallidoEvent(
                rollback_id=rollback_event.rollback_id,
                error_message=str(e),
                user_id=user_id
            )
            self.event_store.append(error_event)
            
            logger.error(f"Error en rollback: {str(e)}")
            raise
    
    def rollback_aggregate_to_timestamp(
        self,
        aggregate_type: str,
        aggregate_id: int,
        target_timestamp: datetime,
        user_id: Optional[str] = None,
        razon: str = "Rollback a timestamp específico"
    ) -> Dict[str, Any]:
        """
        Revierte un agregado específico a un timestamp.
        
        Args:
            aggregate_type: Tipo de agregado (Producto, Categoria)
            aggregate_id: ID del agregado
            target_timestamp: Timestamp objetivo
            user_id: Usuario que ejecuta el rollback
            razon: Razón del rollback
            
        Returns:
            Diccionario con resultados del rollback
        """
        rollback_event = RollbackIniciadoEvent(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            razon=razon,
            user_id=user_id
        )
        self.event_store.append(rollback_event)
        
        try:
            logger.info(
                f"Iniciando rollback de {aggregate_type}#{aggregate_id} "
                f"a timestamp {target_timestamp}"
            )
            
            # Obtener todos los eventos del agregado
            todos_eventos = self.event_store.get_events_by_aggregate(
                aggregate_type, aggregate_id
            )
            
            # Separar eventos antes y después del timestamp
            eventos_validos = [e for e in todos_eventos if e.timestamp <= target_timestamp]
            eventos_a_revertir = [e for e in todos_eventos if e.timestamp > target_timestamp]
            
            # Revertir eventos posteriores
            for evento in reversed(eventos_a_revertir):
                self._revertir_evento(evento)
            
            # Reconstruir estado desde eventos válidos
            estado_reconstruido = self._reconstruir_estado(
                aggregate_type, aggregate_id, eventos_validos
            )
            
            # Registrar éxito
            success_event = RollbackCompletadoEvent(
                rollback_id=rollback_event.rollback_id,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                eventos_revertidos=len(eventos_a_revertir),
                user_id=user_id
            )
            self.event_store.append(success_event)
            
            logger.info(
                f"Rollback completado: {len(eventos_a_revertir)} eventos revertidos"
            )
            
            return {
                "success": True,
                "rollback_id": rollback_event.rollback_id,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "eventos_revertidos": len(eventos_a_revertir),
                "estado_reconstruido": estado_reconstruido,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_event = RollbackFallidoEvent(
                rollback_id=rollback_event.rollback_id,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                error_message=str(e),
                user_id=user_id
            )
            self.event_store.append(error_event)
            
            logger.error(f"Error en rollback: {str(e)}")
            raise
    
    def rollback_last_n_events(
        self,
        aggregate_type: str,
        aggregate_id: int,
        n: int,
        user_id: Optional[str] = None,
        razon: str = "Rollback de últimos N eventos"
    ) -> Dict[str, Any]:
        """
        Revierte los últimos N eventos de un agregado.
        
        Args:
            aggregate_type: Tipo de agregado
            aggregate_id: ID del agregado
            n: Número de eventos a revertir
            user_id: Usuario que ejecuta el rollback
            razon: Razón del rollback
            
        Returns:
            Diccionario con resultados
        """
        rollback_event = RollbackIniciadoEvent(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            razon=razon,
            user_id=user_id
        )
        self.event_store.append(rollback_event)
        
        try:
            logger.info(
                f"Iniciando rollback de últimos {n} eventos de "
                f"{aggregate_type}#{aggregate_id}"
            )
            
            # Obtener todos los eventos del agregado
            todos_eventos = self.event_store.get_events_by_aggregate(
                aggregate_type, aggregate_id
            )
            
            if len(todos_eventos) < n:
                raise ValueError(
                    f"Solo hay {len(todos_eventos)} eventos, no se pueden revertir {n}"
                )
            
            # Obtener últimos N eventos
            eventos_a_revertir = todos_eventos[-n:]
            
            # Revertir en orden inverso
            for evento in reversed(eventos_a_revertir):
                self._revertir_evento(evento)
            
            # Registrar éxito
            success_event = RollbackCompletadoEvent(
                rollback_id=rollback_event.rollback_id,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                eventos_revertidos=n,
                user_id=user_id
            )
            self.event_store.append(success_event)
            
            logger.info(f"Rollback completado: {n} eventos revertidos")
            
            return {
                "success": True,
                "rollback_id": rollback_event.rollback_id,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "eventos_revertidos": n,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_event = RollbackFallidoEvent(
                rollback_id=rollback_event.rollback_id,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                error_message=str(e),
                user_id=user_id
            )
            self.event_store.append(error_event)
            
            logger.error(f"Error en rollback: {str(e)}")
            raise
    
    def _revertir_evento(self, evento) -> None:
        """
        Revierte un evento específico.
        
        Args:
            evento: Modelo de evento a revertir
        """
        event_type = evento.event_type
        aggregate_type = evento.aggregate_type
        aggregate_id = evento.aggregate_id
        event_data = evento.event_data
        
        logger.debug(f"Revirtiendo evento {event_type} para {aggregate_type}#{aggregate_id}")
        
        # Producto creado -> eliminar producto
        if event_type == EventType.PRODUCTO_CREADO.value:
            producto = self.db.query(ProductoModel).filter(
                ProductoModel.id == aggregate_id
            ).first()
            if producto:
                self.db.delete(producto)
                self.db.commit()
        
        # Producto actualizado -> restaurar estado anterior
        elif event_type == EventType.PRODUCTO_ACTUALIZADO.value:
            producto = self.db.query(ProductoModel).filter(
                ProductoModel.id == aggregate_id
            ).first()
            if producto and "estado_anterior" in event_data:
                estado_anterior = event_data["estado_anterior"]
                for key, value in estado_anterior.items():
                    if hasattr(producto, key):
                        setattr(producto, key, value)
                self.db.commit()
        
        # Producto eliminado -> recrear producto
        elif event_type == EventType.PRODUCTO_ELIMINADO.value:
            if "producto_data" in event_data:
                producto_data = event_data["producto_data"]
                producto = ProductoModel(**producto_data)
                self.db.add(producto)
                self.db.commit()
        
        # Categoría creada -> eliminar categoría
        elif event_type == EventType.CATEGORIA_CREADA.value:
            categoria = self.db.query(CategoriaModel).filter(
                CategoriaModel.id == aggregate_id
            ).first()
            if categoria:
                self.db.delete(categoria)
                self.db.commit()
        
        # Categoría actualizada -> restaurar estado anterior
        elif event_type == EventType.CATEGORIA_ACTUALIZADA.value:
            categoria = self.db.query(CategoriaModel).filter(
                CategoriaModel.id == aggregate_id
            ).first()
            if categoria and "estado_anterior" in event_data:
                estado_anterior = event_data["estado_anterior"]
                for key, value in estado_anterior.items():
                    if hasattr(categoria, key):
                        setattr(categoria, key, value)
                self.db.commit()
        
        # Categoría eliminada -> recrear categoría
        elif event_type == EventType.CATEGORIA_ELIMINADA.value:
            if "categoria_data" in event_data:
                categoria_data = event_data["categoria_data"]
                categoria = CategoriaModel(**categoria_data)
                self.db.add(categoria)
                self.db.commit()
    
    def _reconstruir_estado(
        self,
        aggregate_type: str,
        aggregate_id: int,
        eventos: List
    ) -> Dict[str, Any]:
        """
        Reconstruye el estado de un agregado desde sus eventos.
        
        Args:
            aggregate_type: Tipo de agregado
            aggregate_id: ID del agregado
            eventos: Lista de eventos a aplicar
            
        Returns:
            Estado reconstruido
        """
        estado = {}
        
        for evento in eventos:
            event_data = evento.event_data
            
            # Aplicar cambios según el tipo de evento
            if evento.event_type == EventType.PRODUCTO_CREADO.value:
                estado = event_data
            elif evento.event_type == EventType.PRODUCTO_ACTUALIZADO.value:
                if "estado_nuevo" in event_data:
                    estado.update(event_data["estado_nuevo"])
            elif evento.event_type == EventType.CATEGORIA_CREADA.value:
                estado = event_data
            elif evento.event_type == EventType.CATEGORIA_ACTUALIZADA.value:
                if "estado_nuevo" in event_data:
                    estado.update(event_data["estado_nuevo"])
        
        return estado
    
    def get_history(
        self,
        aggregate_type: str,
        aggregate_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial completo de cambios de un agregado.
        
        Args:
            aggregate_type: Tipo de agregado
            aggregate_id: ID del agregado
            
        Returns:
            Lista de eventos formateados
        """
        eventos = self.event_store.get_events_by_aggregate(
            aggregate_type, aggregate_id
        )
        
        historial = []
        for evento in eventos:
            historial.append({
                "event_id": evento.event_id,
                "event_type": evento.event_type,
                "timestamp": evento.timestamp.isoformat(),
                "user_id": evento.user_id,
                "data": evento.event_data
            })
        
        return historial
