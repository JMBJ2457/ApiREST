from typing import List, Optional
from decimal import Decimal
from domain.models import Producto, Categoria, TipoCategoria, TamanoProducto
from repositories.interfaces import IProductoRepository, ICategoriaRepository


class ProductoMemoryRepository(IProductoRepository):
    def __init__(self):
        self._productos: List[Producto] = []
        self._siguiente_id = 1
        self._cargar_datos_iniciales()

    def _cargar_datos_iniciales(self):
        productos_iniciales = [
            Producto(1, "Café Americano", "Café negro clásico", Decimal("2.50"), 1, True, TamanoProducto.MEDIANO, ["Café", "Agua"], 5),
            Producto(2, "Cappuccino", "Café con leche espumosa", Decimal("3.50"), 1, True, TamanoProducto.GRANDE, ["Café", "Leche", "Espuma"], 120),
            Producto(3, "Latte", "Café con mucha leche", Decimal("4.00"), 1, True, TamanoProducto.GRANDE, ["Café", "Leche"], 150),
            Producto(4, "Frappé de Chocolate", "Bebida fría de chocolate", Decimal("5.50"), 2, True, TamanoProducto.GRANDE, ["Café", "Chocolate", "Hielo", "Crema"], 320),
            Producto(5, "Jugo de Naranja", "Jugo natural de naranja", Decimal("3.00"), 2, True, TamanoProducto.MEDIANO, ["Naranja"], 110),
            Producto(6, "Croissant", "Pan francés con mantequilla", Decimal("2.80"), 5, True, None, ["Harina", "Mantequilla", "Huevo"], 231),
            Producto(7, "Cheesecake", "Pastel de queso con fresas", Decimal("4.50"), 3, False, None, ["Queso crema", "Fresas", "Galletas"], 410),
            Producto(8, "Sandwich Club", "Sandwich de pollo, tocino y verduras", Decimal("6.50"), 6, True, None, ["Pan", "Pollo", "Tocino", "Lechuga", "Tomate"], 520),
        ]
        self._productos.extend(productos_iniciales)
        self._siguiente_id = max(p.id for p in productos_iniciales) + 1

    def obtener_todos(self) -> List[Producto]:
        return self._productos.copy()

    def obtener_por_id(self, id: int) -> Optional[Producto]:
        return next((p for p in self._productos if p.id == id), None)

    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        return [p for p in self._productos if p.categoria_id == categoria_id]

    def obtener_disponibles(self) -> List[Producto]:
        return [p for p in self._productos if p.disponible]

    def agregar(self, producto: Producto) -> bool:
        try:
            if producto.id == 0:
                producto.id = self._siguiente_id
                self._siguiente_id += 1
            if any(p.id == producto.id for p in self._productos):
                return False
            self._productos.append(producto)
            return True
        except Exception:
            return False

    def actualizar(self, producto: Producto) -> bool:
        try:
            for i, p in enumerate(self._productos):
                if p.id == producto.id:
                    self._productos[i] = producto
                    return True
            return False
        except Exception:
            return False

    def eliminar(self, id: int) -> bool:
        try:
            for i, p in enumerate(self._productos):
                if p.id == id:
                    del self._productos[i]
                    return True
            return False
        except Exception:
            return False

    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        nombre_lower = nombre.lower()
        return [p for p in self._productos if nombre_lower in p.nombre.lower()]


class CategoriaMemoryRepository(ICategoriaRepository):
    def __init__(self):
        self._categorias: List[Categoria] = []
        self._siguiente_id = 1
        self._cargar_datos_iniciales()

    def _cargar_datos_iniciales(self):
        categorias_iniciales = [
            Categoria(1, "Bebidas Calientes", "Cafés, tés y bebidas calientes", TipoCategoria.BEBIDAS_CALIENTES, True),
            Categoria(2, "Bebidas Frías", "Jugos, batidos y bebidas refrescantes", TipoCategoria.BEBIDAS_FRIAS, True),
            Categoria(3, "Postres", "Pasteles, galletas y dulces", TipoCategoria.POSTRES, True),
            Categoria(4, "Snacks", "Bocadillos y aperitivos", TipoCategoria.SNACKS, True),
            Categoria(5, "Desayunos", "Panes, croissants y opciones matutinas", TipoCategoria.DESAYUNOS, True),
            Categoria(6, "Almuerzo", "Sandwiches, ensaladas y comidas principales", TipoCategoria.ALMUERZO, True),
        ]
        self._categorias.extend(categorias_iniciales)
        self._siguiente_id = max(c.id for c in categorias_iniciales) + 1

    def obtener_todas(self) -> List[Categoria]:
        return self._categorias.copy()

    def obtener_por_id(self, id: int) -> Optional[Categoria]:
        return next((c for c in self._categorias if c.id == id), None)

    def obtener_por_tipo(self, tipo: TipoCategoria) -> List[Categoria]:
        return [c for c in self._categorias if c.tipo == tipo]

    def obtener_activas(self) -> List[Categoria]:
        return [c for c in self._categorias if c.activa]

    def agregar(self, categoria: Categoria) -> bool:
        try:
            if categoria.id == 0:
                categoria.id = self._siguiente_id
                self._siguiente_id += 1
            if any(c.id == categoria.id for c in self._categorias):
                return False
            self._categorias.append(categoria)
            return True
        except Exception:
            return False

    def actualizar(self, categoria: Categoria) -> bool:
        try:
            for i, c in enumerate(self._categorias):
                if c.id == categoria.id:
                    self._categorias[i] = categoria
                    return True
            return False
        except Exception:
            return False

    def eliminar(self, id: int) -> bool:
        try:
            for i, c in enumerate(self._categorias):
                if c.id == id:
                    del self._categorias[i]
                    return True
            return False
        except Exception:
            return False
