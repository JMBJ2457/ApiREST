"""
Router para gestión de eventos y rollback.

Endpoints:
- GET /eventos - Listar eventos
- GET /eventos/{event_id} - Obtener evento específico
- GET /eventos/agregado/{tipo}/{id} - Eventos de un agregado
- GET /eventos/historial/{tipo}/{id} - Historial de cambios
- POST /eventos/rollback/to-event - Rollback a evento específico
- POST /eventos/rollback/to-timestamp - Rollback a timestamp
- POST /eventos/rollback/last-n - Rollback últimos N eventos
- GET /eventos/estadisticas - Estadísticas del Event Store
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from db.session import get_db
from events.event_store import EventStore
from events.rollback_service import RollbackService

router = APIRouter(prefix="/eventos", tags=["Eventos y Rollback"])


# ==================== SCHEMAS ====================

class EventoResponse(BaseModel):
    """Schema para respuesta de evento"""
    id: int
    event_id: str
    event_type: str
    aggregate_id: Optional[int]
    aggregate_type: str
    timestamp: str
    user_id: Optional[str]
    event_data: dict
    
    class Config:
        from_attributes = True


class RollbackToEventRequest(BaseModel):
    """Schema para rollback a evento específico"""
    event_id: str
    user_id: Optional[str] = "system"
    razon: str = "Rollback manual"


class RollbackToTimestampRequest(BaseModel):
    """Schema para rollback a timestamp"""
    aggregate_type: str
    aggregate_id: int
    target_timestamp: str  # ISO format
    user_id: Optional[str] = "system"
    razon: str = "Rollback a timestamp específico"


class RollbackLastNRequest(BaseModel):
    """Schema para rollback de últimos N eventos"""
    aggregate_type: str
    aggregate_id: int
    n: int
    user_id: Optional[str] = "system"
    razon: str = "Rollback de últimos N eventos"


# ==================== ENDPOINTS ====================

@router.get("/", response_model=List[EventoResponse])
def listar_eventos(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lista todos los eventos del sistema (paginado).
    
    Args:
        limit: Número máximo de eventos a retornar
        offset: Offset para paginación
        db: Sesión de base de datos
        
    Returns:
        Lista de eventos
    """
    event_store = EventStore(db)
    eventos = event_store.get_all_events(limit=limit, offset=offset)
    
    return [
        EventoResponse(
            id=e.id,
            event_id=e.event_id,
            event_type=e.event_type,
            aggregate_id=e.aggregate_id,
            aggregate_type=e.aggregate_type,
            timestamp=e.timestamp.isoformat(),
            user_id=e.user_id,
            event_data=e.event_data
        )
        for e in eventos
    ]


@router.get("/{event_id}", response_model=EventoResponse)
def obtener_evento(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un evento específico por su ID.
    
    Args:
        event_id: UUID del evento
        db: Sesión de base de datos
        
    Returns:
        Evento encontrado
    """
    event_store = EventStore(db)
    evento = event_store.get_event_by_id(event_id)
    
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    return EventoResponse(
        id=evento.id,
        event_id=evento.event_id,
        event_type=evento.event_type,
        aggregate_id=evento.aggregate_id,
        aggregate_type=evento.aggregate_type,
        timestamp=evento.timestamp.isoformat(),
        user_id=evento.user_id,
        event_data=evento.event_data
    )


@router.get("/agregado/{aggregate_type}/{aggregate_id}", response_model=List[EventoResponse])
def obtener_eventos_agregado(
    aggregate_type: str,
    aggregate_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los eventos de un agregado específico.
    
    Args:
        aggregate_type: Tipo de agregado (Producto, Categoria)
        aggregate_id: ID del agregado
        db: Sesión de base de datos
        
    Returns:
        Lista de eventos del agregado
    """
    event_store = EventStore(db)
    eventos = event_store.get_events_by_aggregate(aggregate_type, aggregate_id)
    
    return [
        EventoResponse(
            id=e.id,
            event_id=e.event_id,
            event_type=e.event_type,
            aggregate_id=e.aggregate_id,
            aggregate_type=e.aggregate_type,
            timestamp=e.timestamp.isoformat(),
            user_id=e.user_id,
            event_data=e.event_data
        )
        for e in eventos
    ]


@router.get("/historial/{aggregate_type}/{aggregate_id}")
def obtener_historial(
    aggregate_type: str,
    aggregate_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial completo de cambios de un agregado.
    
    Args:
        aggregate_type: Tipo de agregado
        aggregate_id: ID del agregado
        db: Sesión de base de datos
        
    Returns:
        Historial de cambios formateado
    """
    event_store = EventStore(db)
    rollback_service = RollbackService(db, event_store)
    
    historial = rollback_service.get_history(aggregate_type, aggregate_id)
    
    return {
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "total_eventos": len(historial),
        "historial": historial
    }


@router.post("/rollback/to-event")
def rollback_to_event(
    request: RollbackToEventRequest,
    db: Session = Depends(get_db)
):
    """
    Revierte todos los cambios hasta un evento específico.
    
    Args:
        request: Datos del rollback
        db: Sesión de base de datos
        
    Returns:
        Resultado del rollback
    """
    event_store = EventStore(db)
    rollback_service = RollbackService(db, event_store)
    
    try:
        resultado = rollback_service.rollback_to_event(
            event_id=request.event_id,
            user_id=request.user_id,
            razon=request.razon
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback/to-timestamp")
def rollback_to_timestamp(
    request: RollbackToTimestampRequest,
    db: Session = Depends(get_db)
):
    """
    Revierte un agregado a un timestamp específico.
    
    Args:
        request: Datos del rollback
        db: Sesión de base de datos
        
    Returns:
        Resultado del rollback
    """
    event_store = EventStore(db)
    rollback_service = RollbackService(db, event_store)
    
    try:
        target_timestamp = datetime.fromisoformat(request.target_timestamp)
        
        resultado = rollback_service.rollback_aggregate_to_timestamp(
            aggregate_type=request.aggregate_type,
            aggregate_id=request.aggregate_id,
            target_timestamp=target_timestamp,
            user_id=request.user_id,
            razon=request.razon
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Timestamp inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback/last-n")
def rollback_last_n(
    request: RollbackLastNRequest,
    db: Session = Depends(get_db)
):
    """
    Revierte los últimos N eventos de un agregado.
    
    Args:
        request: Datos del rollback
        db: Sesión de base de datos
        
    Returns:
        Resultado del rollback
    """
    event_store = EventStore(db)
    rollback_service = RollbackService(db, event_store)
    
    try:
        resultado = rollback_service.rollback_last_n_events(
            aggregate_type=request.aggregate_type,
            aggregate_id=request.aggregate_id,
            n=request.n,
            user_id=request.user_id,
            razon=request.razon
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas del Event Store.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Estadísticas del Event Store
    """
    event_store = EventStore(db)
    estadisticas = event_store.get_statistics()
    
    return estadisticas
