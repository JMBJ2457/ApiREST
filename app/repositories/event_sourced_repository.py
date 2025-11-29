"""
Wrapper de repositorios con Event Sourcing.

Intercepta operaciones CRUD y registra eventos de dominio.
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from repositories.interfaces import ProductoRepository, CategoriaRepository
from domain.models import Producto, Categoria
from events.event_store import EventStore
from events.domain_events import (
    ProductoCreadoEvent,
    ProductoActualizadoEvent,
    ProductoEliminadoEvent,
    ProductoPrecioCambiadoEvent,
    ProductoDisponibilidadCambiadaEvent,
    CategoriaCreadaEvent,
    CategoriaActualizadaEvent,
    CategoriaEliminadaEvent
)
import logging

logger = logging.getLogger(__name__)


class EventSourcedProductoRepository(ProductoRepository):
    """
    Repositorio de productos con Event Sourcing.
    
    Intercepta todas las operaciones y registra eventos.
    """
    
    def __init__(self, base_repository: ProductoRepository, db: Session):
        """
        Inicializa el repositorio con event sourcing.
        
        Args:
            base_repository: Repositorio base a envolver
            db: Sesión de base de datos para el Event Store
        """
        self.base_repo = base_repository
        self.event_store = EventStore(db)
        self.user_id = "system"  # TODO: Obtener del contexto de autenticación
    
    def obtener_todos(self) -> List[Producto]:
        """Obtiene todos los productos"""
        return self.base_repo.obtener_todos()
    
    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        """Obtiene un producto por ID"""
        return self.base_repo.obtener_por_id(producto_id)
    
    def buscar_por_nombre(self, query: str) -> List[Producto]:
        """Busca productos por nombre"""
        return self.base_repo.buscar_por_nombre(query)
    
    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        """Obtiene productos por categoría"""
        return self.base_repo.obtener_por_categoria(categoria_id)
    
    def agregar(self, producto: Producto) -> bool:
        """
        Agrega un producto y registra evento.
        
        Args:
            producto: Producto a agregar
            
        Returns:
            True si se agregó correctamente
        """
        # Ejecutar operación base
        resultado = self.base_repo.agregar(producto)
        
        if resultado:
            # Registrar evento
            evento = ProductoCreadoEvent(
                aggregate_id=producto.id,
                nombre=producto.nombre,
                descripcion=producto.descripcion,
                precio=float(producto.precio),
                categoria_id=producto.categoria_id,
                disponible=producto.disponible,
                user_id=self.user_id
            )
            self.event_store.append(evento)
            
            logger.info(f"Producto {producto.id} creado y evento registrado")
        
        return resultado
    
    def actualizar(self, producto: Producto) -> bool:
        """
        Actualiza un producto y registra evento.
        
        Args:
            producto: Producto actualizado
            
        Returns:
            True si se actualizó correctamente
        """
        # Obtener estado anterior
        producto_anterior = self.base_repo.obtener_por_id(producto.id)
        
        if not producto_anterior:
            return False
        
        # Ejecutar operación base
        resultado = self.base_repo.actualizar(producto)
        
        if resultado:
            # Detectar cambios
            cambios = {}
            estado_anterior = {}
            estado_nuevo = {}
            
            if producto_anterior.nombre != producto.nombre:
                cambios["nombre"] = {"anterior": producto_anterior.nombre, "nuevo": producto.nombre}
                estado_anterior["nombre"] = producto_anterior.nombre
                estado_nuevo["nombre"] = producto.nombre
            
            if producto_anterior.descripcion != producto.descripcion:
                cambios["descripcion"] = {"anterior": producto_anterior.descripcion, "nuevo": producto.descripcion}
                estado_anterior["descripcion"] = producto_anterior.descripcion
                estado_nuevo["descripcion"] = producto.descripcion
            
            if producto_anterior.precio != producto.precio:
                cambios["precio"] = {"anterior": float(producto_anterior.precio), "nuevo": float(producto.precio)}
                estado_anterior["precio"] = float(producto_anterior.precio)
                estado_nuevo["precio"] = float(producto.precio)
                
                # Evento específico de cambio de precio
                evento_precio = ProductoPrecioCambiadoEvent(
                    aggregate_id=producto.id,
                    precio_anterior=float(producto_anterior.precio),
                    precio_nuevo=float(producto.precio),
                    razon="Actualización manual",
                    user_id=self.user_id
                )
                self.event_store.append(evento_precio)
            
            if producto_anterior.disponible != producto.disponible:
                cambios["disponible"] = {"anterior": producto_anterior.disponible, "nuevo": producto.disponible}
                estado_anterior["disponible"] = producto_anterior.disponible
                estado_nuevo["disponible"] = producto.disponible
                
                # Evento específico de cambio de disponibilidad
                evento_disponibilidad = ProductoDisponibilidadCambiadaEvent(
                    aggregate_id=producto.id,
                    disponible_anterior=producto_anterior.disponible,
                    disponible_nuevo=producto.disponible,
                    razon="Actualización manual",
                    user_id=self.user_id
                )
                self.event_store.append(evento_disponibilidad)
            
            if producto_anterior.categoria_id != producto.categoria_id:
                cambios["categoria_id"] = {"anterior": producto_anterior.categoria_id, "nuevo": producto.categoria_id}
                estado_anterior["categoria_id"] = producto_anterior.categoria_id
                estado_nuevo["categoria_id"] = producto.categoria_id
            
            # Registrar evento general de actualización
            if cambios:
                evento = ProductoActualizadoEvent(
                    aggregate_id=producto.id,
                    cambios=cambios,
                    estado_anterior=estado_anterior,
                    estado_nuevo=estado_nuevo,
                    user_id=self.user_id
                )
                self.event_store.append(evento)
                
                logger.info(f"Producto {producto.id} actualizado y evento registrado")
        
        return resultado
    
    def eliminar(self, producto_id: int) -> bool:
        """
        Elimina un producto y registra evento.
        
        Args:
            producto_id: ID del producto a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        # Obtener producto antes de eliminar
        producto = self.base_repo.obtener_por_id(producto_id)
        
        if not producto:
            return False
        
        # Guardar datos del producto
        producto_data = {
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": float(producto.precio),
            "categoria_id": producto.categoria_id,
            "disponible": producto.disponible
        }
        
        # Ejecutar operación base
        resultado = self.base_repo.eliminar(producto_id)
        
        if resultado:
            # Registrar evento
            evento = ProductoEliminadoEvent(
                aggregate_id=producto_id,
                producto_data=producto_data,
                user_id=self.user_id
            )
            self.event_store.append(evento)
            
            logger.info(f"Producto {producto_id} eliminado y evento registrado")
        
        return resultado


class EventSourcedCategoriaRepository(CategoriaRepository):
    """
    Repositorio de categorías con Event Sourcing.
    
    Intercepta todas las operaciones y registra eventos.
    """
    
    def __init__(self, base_repository: CategoriaRepository, db: Session):
        """
        Inicializa el repositorio con event sourcing.
        
        Args:
            base_repository: Repositorio base a envolver
            db: Sesión de base de datos para el Event Store
        """
        self.base_repo = base_repository
        self.event_store = EventStore(db)
        self.user_id = "system"  # TODO: Obtener del contexto de autenticación
    
    def obtener_todas(self) -> List[Categoria]:
        """Obtiene todas las categorías"""
        return self.base_repo.obtener_todas()
    
    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        """Obtiene una categoría por ID"""
        return self.base_repo.obtener_por_id(categoria_id)
    
    def obtener_activas(self) -> List[Categoria]:
        """Obtiene categorías activas"""
        return self.base_repo.obtener_activas()
    
    def agregar(self, categoria: Categoria) -> bool:
        """
        Agrega una categoría y registra evento.
        
        Args:
            categoria: Categoría a agregar
            
        Returns:
            True si se agregó correctamente
        """
        # Ejecutar operación base
        resultado = self.base_repo.agregar(categoria)
        
        if resultado:
            # Registrar evento
            evento = CategoriaCreadaEvent(
                aggregate_id=categoria.id,
                nombre=categoria.nombre,
                descripcion=categoria.descripcion,
                tipo=categoria.tipo.value,
                activa=categoria.activa,
                user_id=self.user_id
            )
            self.event_store.append(evento)
            
            logger.info(f"Categoría {categoria.id} creada y evento registrado")
        
        return resultado
    
    def actualizar(self, categoria: Categoria) -> bool:
        """
        Actualiza una categoría y registra evento.
        
        Args:
            categoria: Categoría actualizada
            
        Returns:
            True si se actualizó correctamente
        """
        # Obtener estado anterior
        categoria_anterior = self.base_repo.obtener_por_id(categoria.id)
        
        if not categoria_anterior:
            return False
        
        # Ejecutar operación base
        resultado = self.base_repo.actualizar(categoria)
        
        if resultado:
            # Detectar cambios
            cambios = {}
            estado_anterior = {}
            estado_nuevo = {}
            
            if categoria_anterior.nombre != categoria.nombre:
                cambios["nombre"] = {"anterior": categoria_anterior.nombre, "nuevo": categoria.nombre}
                estado_anterior["nombre"] = categoria_anterior.nombre
                estado_nuevo["nombre"] = categoria.nombre
            
            if categoria_anterior.descripcion != categoria.descripcion:
                cambios["descripcion"] = {"anterior": categoria_anterior.descripcion, "nuevo": categoria.descripcion}
                estado_anterior["descripcion"] = categoria_anterior.descripcion
                estado_nuevo["descripcion"] = categoria.descripcion
            
            if categoria_anterior.tipo != categoria.tipo:
                cambios["tipo"] = {"anterior": categoria_anterior.tipo.value, "nuevo": categoria.tipo.value}
                estado_anterior["tipo"] = categoria_anterior.tipo.value
                estado_nuevo["tipo"] = categoria.tipo.value
            
            if categoria_anterior.activa != categoria.activa:
                cambios["activa"] = {"anterior": categoria_anterior.activa, "nuevo": categoria.activa}
                estado_anterior["activa"] = categoria_anterior.activa
                estado_nuevo["activa"] = categoria.activa
            
            # Registrar evento
            if cambios:
                evento = CategoriaActualizadaEvent(
                    aggregate_id=categoria.id,
                    cambios=cambios,
                    estado_anterior=estado_anterior,
                    estado_nuevo=estado_nuevo,
                    user_id=self.user_id
                )
                self.event_store.append(evento)
                
                logger.info(f"Categoría {categoria.id} actualizada y evento registrado")
        
        return resultado
    
    def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina una categoría y registra evento.
        
        Args:
            categoria_id: ID de la categoría a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        # Obtener categoría antes de eliminar
        categoria = self.base_repo.obtener_por_id(categoria_id)
        
        if not categoria:
            return False
        
        # Guardar datos de la categoría
        categoria_data = {
            "id": categoria.id,
            "nombre": categoria.nombre,
            "descripcion": categoria.descripcion,
            "tipo": categoria.tipo.value,
            "activa": categoria.activa
        }
        
        # Ejecutar operación base
        resultado = self.base_repo.eliminar(categoria_id)
        
        if resultado:
            # Registrar evento
            evento = CategoriaEliminadaEvent(
                aggregate_id=categoria_id,
                categoria_data=categoria_data,
                user_id=self.user_id
            )
            self.event_store.append(evento)
            
            logger.info(f"Categoría {categoria_id} eliminada y evento registrado")
        
        return resultado
