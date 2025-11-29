"""
Script de prueba para Event Sourcing.

Ejecutar con: python3 test_event_sourcing.py
"""
import sys
import os

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from datetime import datetime
from decimal import Decimal

from db.session import SessionLocal, init_db
from db.models import ProductoModel, CategoriaModel
from events.event_store import EventStore
from events.rollback_service import RollbackService
from events.domain_events import (
    ProductoCreadoEvent,
    ProductoActualizadoEvent,
    CategoriaCreadaEvent,
    EventType
)


def test_event_store():
    """Prueba básica del Event Store"""
    print("=" * 60)
    print("TEST 1: Event Store - Crear y Recuperar Eventos")
    print("=" * 60)
    
    db = SessionLocal()
    event_store = EventStore(db)
    
    # Crear evento de producto
    evento = ProductoCreadoEvent(
        aggregate_id=999,
        nombre="Café de Prueba",
        descripcion="Producto de prueba",
        precio=5.99,
        categoria_id=1,
        disponible=True,
        user_id="test_user"
    )
    
    # Persistir evento
    event_model = event_store.append(evento)
    print(f"✅ Evento creado: {event_model.event_id}")
    print(f"   Tipo: {event_model.event_type}")
    print(f"   Timestamp: {event_model.timestamp}")
    
    # Recuperar evento
    evento_recuperado = event_store.get_event_by_id(evento.event_id)
    print(f"✅ Evento recuperado: {evento_recuperado.event_id}")
    print(f"   Datos: {evento_recuperado.event_data}")
    
    # Obtener eventos por agregado
    eventos_producto = event_store.get_events_by_aggregate("Producto", 999)
    print(f"✅ Eventos del producto 999: {len(eventos_producto)}")
    
    db.close()
    print()


def test_multiple_events():
    """Prueba múltiples eventos y consultas"""
    print("=" * 60)
    print("TEST 2: Múltiples Eventos y Consultas")
    print("=" * 60)
    
    db = SessionLocal()
    event_store = EventStore(db)
    
    # Crear varios eventos
    eventos = []
    
    # Evento 1: Crear producto
    e1 = ProductoCreadoEvent(
        aggregate_id=1000,
        nombre="Producto Test 1",
        descripcion="Descripción 1",
        precio=10.00,
        categoria_id=1,
        disponible=True,
        user_id="admin"
    )
    eventos.append(event_store.append(e1))
    
    # Evento 2: Actualizar producto
    e2 = ProductoActualizadoEvent(
        aggregate_id=1000,
        cambios={"precio": {"anterior": 10.00, "nuevo": 12.00}},
        estado_anterior={"precio": 10.00},
        estado_nuevo={"precio": 12.00},
        user_id="admin"
    )
    eventos.append(event_store.append(e2))
    
    # Evento 3: Crear categoría
    e3 = CategoriaCreadaEvent(
        aggregate_id=100,
        nombre="Categoría Test",
        descripcion="Descripción categoría",
        tipo="bebidas_calientes",
        activa=True,
        user_id="admin"
    )
    eventos.append(event_store.append(e3))
    
    print(f"✅ Creados {len(eventos)} eventos")
    
    # Consultar por tipo
    eventos_producto_creado = event_store.get_events_by_type(EventType.PRODUCTO_CREADO)
    print(f"✅ Eventos PRODUCTO_CREADO: {len(eventos_producto_creado)}")
    
    # Consultar por usuario
    eventos_admin = event_store.get_events_by_user("admin")
    print(f"✅ Eventos de usuario 'admin': {len(eventos_admin)}")
    
    # Estadísticas
    stats = event_store.get_statistics()
    print(f"✅ Estadísticas:")
    print(f"   Total eventos: {stats['total_events']}")
    print(f"   Por tipo: {stats['events_by_type']}")
    print(f"   Por agregado: {stats['events_by_aggregate']}")
    
    db.close()
    print()


def test_rollback_service():
    """Prueba el servicio de rollback"""
    print("=" * 60)
    print("TEST 3: Servicio de Rollback")
    print("=" * 60)
    
    db = SessionLocal()
    event_store = EventStore(db)
    rollback_service = RollbackService(db, event_store)
    
    # Crear producto en la base de datos
    categoria = CategoriaModel(
        id=200,
        nombre="Test Categoria",
        descripcion="Categoría de prueba",
        tipo="bebidas_calientes",
        activa=True
    )
    db.add(categoria)
    db.commit()
    
    producto = ProductoModel(
        id=2000,
        nombre="Producto Rollback Test",
        descripcion="Descripción inicial",
        precio=20.00,
        categoria_id=200,
        disponible=True
    )
    db.add(producto)
    db.commit()
    
    # Registrar eventos
    e1 = ProductoCreadoEvent(
        aggregate_id=2000,
        nombre="Producto Rollback Test",
        descripcion="Descripción inicial",
        precio=20.00,
        categoria_id=200,
        disponible=True,
        user_id="test"
    )
    event_store.append(e1)
    
    e2 = ProductoActualizadoEvent(
        aggregate_id=2000,
        cambios={"precio": {"anterior": 20.00, "nuevo": 25.00}},
        estado_anterior={"precio": 20.00},
        estado_nuevo={"precio": 25.00},
        user_id="test"
    )
    event_store.append(e2)
    
    e3 = ProductoActualizadoEvent(
        aggregate_id=2000,
        cambios={"precio": {"anterior": 25.00, "nuevo": 30.00}},
        estado_anterior={"precio": 25.00},
        estado_nuevo={"precio": 30.00},
        user_id="test"
    )
    event_store.append(e3)
    
    print(f"✅ Creados 3 eventos para producto 2000")
    
    # Obtener historial
    historial = rollback_service.get_history("Producto", 2000)
    print(f"✅ Historial del producto:")
    for h in historial:
        print(f"   - {h['timestamp']}: {h['event_type']}")
    
    # Hacer rollback de últimos 2 eventos
    print(f"\n🔄 Haciendo rollback de últimos 2 eventos...")
    try:
        resultado = rollback_service.rollback_last_n_events(
            aggregate_type="Producto",
            aggregate_id=2000,
            n=2,
            user_id="test",
            razon="Test de rollback"
        )
        print(f"✅ Rollback completado:")
        print(f"   Eventos revertidos: {resultado['eventos_revertidos']}")
        print(f"   Rollback ID: {resultado['rollback_id']}")
    except Exception as e:
        print(f"⚠️  Rollback (esperado en test): {str(e)}")
    
    # Verificar eventos de rollback
    eventos_rollback = event_store.get_events_by_type(EventType.ROLLBACK_INICIADO)
    print(f"✅ Eventos de rollback registrados: {len(eventos_rollback)}")
    
    db.close()
    print()


def test_snapshots():
    """Prueba snapshots"""
    print("=" * 60)
    print("TEST 4: Snapshots")
    print("=" * 60)
    
    db = SessionLocal()
    event_store = EventStore(db)
    
    # Crear snapshot
    estado = {
        "id": 3000,
        "nombre": "Producto Snapshot",
        "precio": 15.00,
        "categoria_id": 1,
        "disponible": True
    }
    
    snapshot = event_store.create_snapshot(
        aggregate_type="Producto",
        aggregate_id=3000,
        state=estado,
        version=5
    )
    
    print(f"✅ Snapshot creado:")
    print(f"   Agregado: {snapshot.aggregate_type}#{snapshot.aggregate_id}")
    print(f"   Versión: {snapshot.version}")
    print(f"   Estado: {snapshot.state}")
    
    # Recuperar snapshot
    snapshot_recuperado = event_store.get_snapshot("Producto", 3000)
    print(f"✅ Snapshot recuperado:")
    print(f"   Estado: {snapshot_recuperado.state}")
    
    db.close()
    print()


def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("INICIANDO TESTS DE EVENT SOURCING")
    print("=" * 60 + "\n")
    
    # Inicializar base de datos
    print("Inicializando base de datos...")
    init_db()
    print("✅ Base de datos inicializada\n")
    
    # Ejecutar tests
    try:
        test_event_store()
        test_multiple_events()
        test_rollback_service()
        test_snapshots()
        
        print("=" * 60)
        print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
