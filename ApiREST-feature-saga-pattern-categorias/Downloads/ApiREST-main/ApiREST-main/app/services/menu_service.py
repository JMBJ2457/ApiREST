from typing import List, Optional, Dict
from decimal import Decimal
from domain.models import Producto, Categoria, TipoCategoria
from repositories.interfaces import IProductoRepository, ICategoriaRepository


class MenuService:
    def __init__(self, producto_repo: IProductoRepository, categoria_repo: ICategoriaRepository):
        self._producto_repo = producto_repo
        self._categoria_repo = categoria_repo

    def obtener_menu_completo(self) -> Dict[str, List[Producto]]:
        categorias = self._categoria_repo.obtener_activas()
        productos = self._producto_repo.obtener_disponibles()
        menu = {}
        for categoria in categorias:
            productos_categoria = [p for p in productos if p.categoria_id == categoria.id]
            if productos_categoria:
                menu[categoria.nombre] = productos_categoria
        return menu

    def buscar_productos(self, termino: str) -> List[Producto]:
        return self._producto_repo.buscar_por_nombre(termino)

    def obtener_productos_por_categoria(self, categoria_id: int) -> List[Producto]:
        productos = self._producto_repo.obtener_por_categoria(categoria_id)
        return [p for p in productos if p.disponible]

    def obtener_productos_por_tipo_categoria(self, tipo: TipoCategoria) -> List[Producto]:
        categorias = self._categoria_repo.obtener_por_tipo(tipo)
        productos: List[Producto] = []
        for categoria in categorias:
            if categoria.activa:
                productos_categoria = self.obtener_productos_por_categoria(categoria.id)
                productos.extend(productos_categoria)
        return productos

    def obtener_producto_detalle(self, producto_id: int) -> Optional[Dict]:
        producto = self._producto_repo.obtener_por_id(producto_id)
        if not producto:
            return None
        categoria = self._categoria_repo.obtener_por_id(producto.categoria_id)
        return {
            'producto': producto,
            'categoria': categoria,
            'ingredientes': producto.ingredientes,
            'informacion_nutricional': {
                'calorias': producto.calorias or 'No disponible'
            }
        }

    def filtrar_productos_por_precio(self, precio_min: Decimal = None, precio_max: Decimal = None) -> List[Producto]:
        productos = self._producto_repo.obtener_disponibles()
        if precio_min is not None:
            productos = [p for p in productos if p.precio >= precio_min]
        if precio_max is not None:
            productos = [p for p in productos if p.precio <= precio_max]
        return productos

    def obtener_productos_por_calorias(self, max_calorias: int) -> List[Producto]:
        productos = self._producto_repo.obtener_disponibles()
        return [p for p in productos if p.calorias and p.calorias <= max_calorias]

    def obtener_estadisticas_menu(self) -> Dict:
        productos = self._producto_repo.obtener_todos()
        productos_disponibles = self._producto_repo.obtener_disponibles()
        categorias = self._categoria_repo.obtener_todas()
        categorias_activas = self._categoria_repo.obtener_activas()
        precios = [p.precio for p in productos_disponibles]
        precio_promedio = sum(precios) / len(precios) if precios else 0
        producto_mas_caro = max(productos_disponibles, key=lambda p: p.precio) if productos_disponibles else None
        producto_mas_barato = min(productos_disponibles, key=lambda p: p.precio) if productos_disponibles else None
        productos_por_categoria = {}
        for categoria in categorias_activas:
            count = len(self.obtener_productos_por_categoria(categoria.id))
            if count > 0:
                productos_por_categoria[categoria.nombre] = count
        return {
            'total_productos': len(productos),
            'productos_disponibles': len(productos_disponibles),
            'total_categorias': len(categorias),
            'categorias_activas': len(categorias_activas),
            'precio_promedio': precio_promedio,
            'producto_mas_caro': producto_mas_caro,
            'producto_mas_barato': producto_mas_barato,
            'productos_por_categoria': productos_por_categoria
        }

    def obtener_todas_las_categorias(self) -> List[Categoria]:
        return self._categoria_repo.obtener_activas()

    def recomendar_productos_similares(self, producto_id: int, limite: int = 3) -> List[Producto]:
        producto = self._producto_repo.obtener_por_id(producto_id)
        if not producto:
            return []
        productos_similares = self.obtener_productos_por_categoria(producto.categoria_id)
        productos_similares = [p for p in productos_similares if p.id != producto_id]
        return productos_similares[:limite]
