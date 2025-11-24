import json
import os
from typing import List, Optional
from decimal import Decimal
from domain.models import Producto, Categoria, TipoCategoria, TamanoProducto
from repositories.interfaces import IProductoRepository, ICategoriaRepository
from core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from core.config import get_settings


class ProductoFileRepository(IProductoRepository):
    def __init__(self, archivo_path: str = "data/productos.json"):
        self.archivo_path = archivo_path
        self._productos: List[Producto] = []
        # Circuit Breaker para proteger operaciones de archivo
        settings = get_settings()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            expected_exception=Exception,
            name="ProductoFileRepository"
        )
        self._cargar_desde_archivo()

    def _cargar_desde_archivo(self):
        """Carga productos desde archivo protegido por Circuit Breaker"""
        def _leer_archivo():
            if os.path.exists(self.archivo_path):
                with open(self.archivo_path, 'r', encoding='utf-8') as archivo:
                    datos = json.load(archivo)
                    return [self._dict_a_producto(item) for item in datos]
            return []
        
        try:
            self._productos = self._circuit_breaker.call(_leer_archivo)
        except CircuitBreakerError:
            # Si el circuito está abierto, usar datos en memoria como fallback
            # o mantener los datos actuales
            pass
        except Exception:
            # Si hay otro error, mantener lista vacía o datos actuales
            if not self._productos:
                self._productos = []

    def _guardar_en_archivo(self):
        """Guarda productos en archivo protegido por Circuit Breaker"""
        def _escribir_archivo():
            os.makedirs(os.path.dirname(self.archivo_path), exist_ok=True)
            with open(self.archivo_path, 'w', encoding='utf-8') as archivo:
                datos = [self._producto_a_dict(p) for p in self._productos]
                json.dump(datos, archivo, indent=2, ensure_ascii=False)
        
        try:
            self._circuit_breaker.call(_escribir_archivo)
        except CircuitBreakerError:
            # Si el circuito está abierto, no podemos guardar
            # Los datos quedan solo en memoria
            raise
        except Exception as e:
            # Re-lanzar para que el Circuit Breaker lo capture
            raise

    def _dict_a_producto(self, data: dict) -> Producto:
        tamano = None
        if data.get('tamano'):
            tamano = TamanoProducto(data['tamano'])
        return Producto(
            id=data['id'],
            nombre=data['nombre'],
            descripcion=data['descripcion'],
            precio=Decimal(str(data['precio'])),
            categoria_id=data['categoria_id'],
            disponible=data.get('disponible', True),
            tamano=tamano,
            ingredientes=data.get('ingredientes', []),
            calorias=data.get('calorias')
        )

    def _producto_a_dict(self, producto: Producto) -> dict:
        return {
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': float(producto.precio),
            'categoria_id': producto.categoria_id,
            'disponible': producto.disponible,
            'tamano': producto.tamano.value if producto.tamano else None,
            'ingredientes': producto.ingredientes,
            'calorias': producto.calorias
        }

    def obtener_todos(self) -> List[Producto]:
        self._cargar_desde_archivo()
        return self._productos.copy()

    def obtener_por_id(self, id: int) -> Optional[Producto]:
        self._cargar_desde_archivo()
        return next((p for p in self._productos if p.id == id), None)

    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        self._cargar_desde_archivo()
        return [p for p in self._productos if p.categoria_id == categoria_id]

    def obtener_disponibles(self) -> List[Producto]:
        self._cargar_desde_archivo()
        return [p for p in self._productos if p.disponible]

    def agregar(self, producto: Producto) -> bool:
        try:
            self._cargar_desde_archivo()
            if any(p.id == producto.id for p in self._productos):
                return False
            self._productos.append(producto)
            self._guardar_en_archivo()
            return True
        except Exception:
            return False

    def actualizar(self, producto: Producto) -> bool:
        try:
            self._cargar_desde_archivo()
            for i, p in enumerate(self._productos):
                if p.id == producto.id:
                    self._productos[i] = producto
                    self._guardar_en_archivo()
                    return True
            return False
        except Exception:
            return False

    def eliminar(self, id: int) -> bool:
        try:
            self._cargar_desde_archivo()
            for i, p in enumerate(self._productos):
                if p.id == id:
                    del self._productos[i]
                    self._guardar_en_archivo()
                    return True
            return False
        except Exception:
            return False

    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        self._cargar_desde_archivo()
        nombre_lower = nombre.lower()
        return [p for p in self._productos if nombre_lower in p.nombre.lower()]


class CategoriaFileRepository(ICategoriaRepository):
    def __init__(self, archivo_path: str = "data/categorias.json"):
        self.archivo_path = archivo_path
        self._categorias: List[Categoria] = []
        # Circuit Breaker para proteger operaciones de archivo
        settings = get_settings()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            expected_exception=Exception,
            name="CategoriaFileRepository"
        )
        self._cargar_desde_archivo()

    def _cargar_desde_archivo(self):
        """Carga categorías desde archivo protegido por Circuit Breaker"""
        def _leer_archivo():
            if os.path.exists(self.archivo_path):
                with open(self.archivo_path, 'r', encoding='utf-8') as archivo:
                    datos = json.load(archivo)
                    return [self._dict_a_categoria(item) for item in datos]
            return []
        
        try:
            self._categorias = self._circuit_breaker.call(_leer_archivo)
        except CircuitBreakerError:
            # Si el circuito está abierto, mantener datos actuales
            pass
        except Exception:
            # Si hay otro error, mantener lista vacía o datos actuales
            if not self._categorias:
                self._categorias = []

    def _guardar_en_archivo(self):
        """Guarda categorías en archivo protegido por Circuit Breaker"""
        def _escribir_archivo():
            os.makedirs(os.path.dirname(self.archivo_path), exist_ok=True)
            with open(self.archivo_path, 'w', encoding='utf-8') as archivo:
                datos = [self._categoria_a_dict(c) for c in self._categorias]
                json.dump(datos, archivo, indent=2, ensure_ascii=False)
        
        try:
            self._circuit_breaker.call(_escribir_archivo)
        except CircuitBreakerError:
            # Si el circuito está abierto, no podemos guardar
            raise
        except Exception as e:
            # Re-lanzar para que el Circuit Breaker lo capture
            raise

    def _dict_a_categoria(self, data: dict) -> Categoria:
        return Categoria(
            id=data['id'],
            nombre=data['nombre'],
            descripcion=data['descripcion'],
            tipo=TipoCategoria(data['tipo']),
            activa=data.get('activa', True)
        )

    def _categoria_a_dict(self, categoria: Categoria) -> dict:
        return {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'descripcion': categoria.descripcion,
            'tipo': categoria.tipo.value,
            'activa': categoria.activa
        }

    def obtener_todas(self) -> List[Categoria]:
        self._cargar_desde_archivo()
        return self._categorias.copy()

    def obtener_por_id(self, id: int) -> Optional[Categoria]:
        self._cargar_desde_archivo()
        return next((c for c in self._categorias if c.id == id), None)

    def obtener_por_tipo(self, tipo: TipoCategoria) -> List[Categoria]:
        self._cargar_desde_archivo()
        return [c for c in self._categorias if c.tipo == tipo]

    def obtener_activas(self) -> List[Categoria]:
        self._cargar_desde_archivo()
        return [c for c in self._categorias if c.activa]

    def agregar(self, categoria: Categoria) -> bool:
        try:
            self._cargar_desde_archivo()
            if any(c.id == categoria.id for c in self._categorias):
                return False
            self._categorias.append(categoria)
            self._guardar_en_archivo()
            return True
        except Exception:
            return False

    def actualizar(self, categoria: Categoria) -> bool:
        try:
            self._cargar_desde_archivo()
            for i, c in enumerate(self._categorias):
                if c.id == categoria.id:
                    self._categorias[i] = categoria
                    self._guardar_en_archivo()
                    return True
            return False
        except Exception:
            return False

    def eliminar(self, id: int) -> bool:
        try:
            self._cargar_desde_archivo()
            for i, c in enumerate(self._categorias):
                if c.id == id:
                    del self._categorias[i]
                    self._guardar_en_archivo()
                    return True
            return False
        except Exception:
            return False
