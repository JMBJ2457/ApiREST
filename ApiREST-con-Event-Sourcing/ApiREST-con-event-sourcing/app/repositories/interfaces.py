from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models import Producto, Categoria, TipoCategoria


class IProductoRepository(ABC):
    @abstractmethod
    def obtener_todos(self) -> List[Producto]:
        pass

    @abstractmethod
    def obtener_por_id(self, id: int) -> Optional[Producto]:
        pass

    @abstractmethod
    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        pass

    @abstractmethod
    def obtener_disponibles(self) -> List[Producto]:
        pass

    @abstractmethod
    def agregar(self, producto: Producto) -> bool:
        pass

    @abstractmethod
    def actualizar(self, producto: Producto) -> bool:
        pass

    @abstractmethod
    def eliminar(self, id: int) -> bool:
        pass

    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        pass


class ICategoriaRepository(ABC):
    @abstractmethod
    def obtener_todas(self) -> List[Categoria]:
        pass

    @abstractmethod
    def obtener_por_id(self, id: int) -> Optional[Categoria]:
        pass

    @abstractmethod
    def obtener_por_tipo(self, tipo: TipoCategoria) -> List[Categoria]:
        pass

    @abstractmethod
    def obtener_activas(self) -> List[Categoria]:
        pass

    @abstractmethod
    def agregar(self, categoria: Categoria) -> bool:
        pass

    @abstractmethod
    def actualizar(self, categoria: Categoria) -> bool:
        pass

    @abstractmethod
    def eliminar(self, id: int) -> bool:
        pass
