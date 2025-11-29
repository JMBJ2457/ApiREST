"""
Repositorio de base de datos con Circuit Breaker integrado
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, TimeoutError

from domain.models import Producto, Categoria, TipoCategoria, TamanoProducto
from repositories.interfaces import IProductoRepository, ICategoriaRepository
from core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from core.config import get_settings
from db.models import ProductoModel, CategoriaModel


class ProductoDatabaseRepository(IProductoRepository):
    """Repositorio de productos con base de datos y Circuit Breaker"""
    
    def __init__(self, db: Session):
        self.db = db
        settings = get_settings()
        # Circuit Breaker para proteger operaciones de BD
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            expected_exception=(SQLAlchemyError, OperationalError, TimeoutError),
            name="ProductoDatabaseRepository"
        )
    
    def _modelo_a_dominio(self, modelo: ProductoModel) -> Producto:
        """Convierte modelo de BD a objeto de dominio"""
        tamano = None
        if modelo.tamano:
            tamano = TamanoProducto(modelo.tamano)
        
        return Producto(
            id=modelo.id,
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            precio=Decimal(str(modelo.precio)),
            categoria_id=modelo.categoria_id,
            disponible=modelo.disponible,
            tamano=tamano,
            ingredientes=modelo.ingredientes or [],
            calorias=modelo.calorias
        )
    
    def _dominio_a_modelo(self, producto: Producto) -> ProductoModel:
        """Convierte objeto de dominio a modelo de BD"""
        return ProductoModel(
            id=producto.id if producto.id > 0 else None,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=float(producto.precio),
            categoria_id=producto.categoria_id,
            disponible=producto.disponible,
            tamano=producto.tamano.value if producto.tamano else None,
            ingredientes=producto.ingredientes or [],
            calorias=producto.calorias
        )
    
    def obtener_todos(self) -> List[Producto]:
        def _obtener():
            modelos = self.db.query(ProductoModel).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return []  # Fallback: lista vacía
    
    def obtener_por_id(self, id: int) -> Optional[Producto]:
        def _obtener():
            modelo = self.db.query(ProductoModel).filter(ProductoModel.id == id).first()
            return self._modelo_a_dominio(modelo) if modelo else None
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return None
    
    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        def _obtener():
            modelos = self.db.query(ProductoModel).filter(
                ProductoModel.categoria_id == categoria_id
            ).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return []
    
    def obtener_disponibles(self) -> List[Producto]:
        def _obtener():
            modelos = self.db.query(ProductoModel).filter(
                ProductoModel.disponible == True
            ).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return []
    
    def agregar(self, producto: Producto) -> bool:
        def _agregar():
            # Verificar si ya existe
            existente = self.db.query(ProductoModel).filter(
                ProductoModel.id == producto.id
            ).first()
            if existente:
                return False
            
            modelo = self._dominio_a_modelo(producto)
            self.db.add(modelo)
            self.db.commit()
            self.db.refresh(modelo)
            # Actualizar el ID del producto de dominio
            producto.id = modelo.id
            return True
        
        try:
            return self._circuit_breaker.call(_agregar)
        except CircuitBreakerError:
            return False
        except Exception:
            self.db.rollback()
            return False
    
    def actualizar(self, producto: Producto) -> bool:
        def _actualizar():
            modelo = self.db.query(ProductoModel).filter(
                ProductoModel.id == producto.id
            ).first()
            if not modelo:
                return False
            
            modelo.nombre = producto.nombre
            modelo.descripcion = producto.descripcion
            modelo.precio = float(producto.precio)
            modelo.categoria_id = producto.categoria_id
            modelo.disponible = producto.disponible
            modelo.tamano = producto.tamano.value if producto.tamano else None
            modelo.ingredientes = producto.ingredientes or []
            modelo.calorias = producto.calorias
            
            self.db.commit()
            return True
        
        try:
            return self._circuit_breaker.call(_actualizar)
        except CircuitBreakerError:
            return False
        except Exception:
            self.db.rollback()
            return False
    
    def eliminar(self, id: int) -> bool:
        def _eliminar():
            modelo = self.db.query(ProductoModel).filter(ProductoModel.id == id).first()
            if not modelo:
                return False
            
            self.db.delete(modelo)
            self.db.commit()
            return True
        
        try:
            return self._circuit_breaker.call(_eliminar)
        except CircuitBreakerError:
            return False
        except Exception:
            self.db.rollback()
            return False
    
    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        def _buscar():
            modelos = self.db.query(ProductoModel).filter(
                ProductoModel.nombre.ilike(f"%{nombre}%")
            ).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_buscar)
        except CircuitBreakerError:
            return []


class CategoriaDatabaseRepository(ICategoriaRepository):
    """Repositorio de categorías con base de datos y Circuit Breaker"""
    
    def __init__(self, db: Session):
        self.db = db
        settings = get_settings()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            expected_exception=(SQLAlchemyError, OperationalError, TimeoutError),
            name="CategoriaDatabaseRepository"
        )
    
    def _modelo_a_dominio(self, modelo: CategoriaModel) -> Categoria:
        """Convierte modelo de BD a objeto de dominio"""
        return Categoria(
            id=modelo.id,
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            tipo=TipoCategoria(modelo.tipo),
            activa=modelo.activa
        )
    
    def _dominio_a_modelo(self, categoria: Categoria) -> CategoriaModel:
        """Convierte objeto de dominio a modelo de BD"""
        return CategoriaModel(
            id=categoria.id if categoria.id > 0 else None,
            nombre=categoria.nombre,
            descripcion=categoria.descripcion,
            tipo=categoria.tipo.value,
            activa=categoria.activa
        )
    
    def obtener_todas(self) -> List[Categoria]:
        def _obtener():
            modelos = self.db.query(CategoriaModel).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return []
    
    def obtener_por_id(self, id: int) -> Optional[Categoria]:
        def _obtener():
            modelo = self.db.query(CategoriaModel).filter(CategoriaModel.id == id).first()
            return self._modelo_a_dominio(modelo) if modelo else None
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return None
    
    def obtener_por_tipo(self, tipo: TipoCategoria) -> List[Categoria]:
        def _obtener():
            modelos = self.db.query(CategoriaModel).filter(
                CategoriaModel.tipo == tipo.value
            ).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return []
    
    def obtener_activas(self) -> List[Categoria]:
        def _obtener():
            modelos = self.db.query(CategoriaModel).filter(
                CategoriaModel.activa == True
            ).all()
            return [self._modelo_a_dominio(m) for m in modelos]
        
        try:
            return self._circuit_breaker.call(_obtener)
        except CircuitBreakerError:
            return []
    
    def agregar(self, categoria: Categoria) -> bool:
        def _agregar():
            existente = self.db.query(CategoriaModel).filter(
                CategoriaModel.id == categoria.id
            ).first()
            if existente:
                return False
            
            modelo = self._dominio_a_modelo(categoria)
            self.db.add(modelo)
            self.db.commit()
            self.db.refresh(modelo)
            categoria.id = modelo.id
            return True
        
        try:
            return self._circuit_breaker.call(_agregar)
        except CircuitBreakerError:
            return False
        except Exception:
            self.db.rollback()
            return False
    
    def actualizar(self, categoria: Categoria) -> bool:
        def _actualizar():
            modelo = self.db.query(CategoriaModel).filter(
                CategoriaModel.id == categoria.id
            ).first()
            if not modelo:
                return False
            
            modelo.nombre = categoria.nombre
            modelo.descripcion = categoria.descripcion
            modelo.tipo = categoria.tipo.value
            modelo.activa = categoria.activa
            
            self.db.commit()
            return True
        
        try:
            return self._circuit_breaker.call(_actualizar)
        except CircuitBreakerError:
            return False
        except Exception:
            self.db.rollback()
            return False
    
    def eliminar(self, id: int) -> bool:
        def _eliminar():
            modelo = self.db.query(CategoriaModel).filter(CategoriaModel.id == id).first()
            if not modelo:
                return False
            
            self.db.delete(modelo)
            self.db.commit()
            return True
        
        try:
            return self._circuit_breaker.call(_eliminar)
        except CircuitBreakerError:
            return False
        except Exception:
            self.db.rollback()
            return False

