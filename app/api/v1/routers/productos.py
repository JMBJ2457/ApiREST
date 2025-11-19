from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from decimal import Decimal

from core.dependencies import get_menu_service, get_producto_repo
from api.v1.schemas.producto import ProductoIn, ProductoOut, TamanoProductoEnum
from services.menu_service import MenuService
from domain.models import Producto as ProductoDomain, TamanoProducto

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("/", response_model=List[ProductoOut])
def listar_productos(menu: MenuService = Depends(get_menu_service)):
    productos = menu._producto_repo.obtener_todos()
    return [ProductoOut.model_validate(p, from_attributes=True) for p in productos]


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int, menu: MenuService = Depends(get_menu_service)):
    p = menu._producto_repo.obtener_por_id(producto_id)
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductoOut.model_validate(p, from_attributes=True)


@router.get("/search", response_model=List[ProductoOut])
def buscar_productos(q: str = Query(..., min_length=1), menu: MenuService = Depends(get_menu_service)):
    productos = menu.buscar_productos(q)
    return [ProductoOut.model_validate(p, from_attributes=True) for p in productos]


@router.get("/{producto_id}/similares", response_model=List[ProductoOut])
def similares(producto_id: int, menu: MenuService = Depends(get_menu_service)):
    items = menu.recomendar_productos_similares(producto_id)
    return [ProductoOut.model_validate(p, from_attributes=True) for p in items]


@router.post("/", response_model=ProductoOut, status_code=201)
def crear_producto(data: ProductoIn, menu: MenuService = Depends(get_menu_service)):
    existentes = menu._producto_repo.obtener_todos()
    next_id = max([p.id for p in existentes], default=0) + 1
    tamano = None
    if data.tamano is not None:
        tamano = TamanoProducto(data.tamano.value)
    nuevo = ProductoDomain(
        id=next_id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        precio=Decimal(str(data.precio)),
        categoria_id=data.categoria_id,
        disponible=data.disponible,
        tamano=tamano,
        ingredientes=data.ingredientes or [],
        calorias=data.calorias,
    )
    ok = menu._producto_repo.agregar(nuevo)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo crear el producto")
    return ProductoOut.model_validate(nuevo, from_attributes=True)


@router.put("/{producto_id}", response_model=ProductoOut)
def actualizar_producto(producto_id: int, data: ProductoIn, menu: MenuService = Depends(get_menu_service)):
    actual = menu._producto_repo.obtener_por_id(producto_id)
    if not actual:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    tamano = None
    if data.tamano is not None:
        tamano = TamanoProducto(data.tamano.value)
    actualizado = ProductoDomain(
        id=producto_id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        precio=Decimal(str(data.precio)),
        categoria_id=data.categoria_id,
        disponible=data.disponible,
        tamano=tamano,
        ingredientes=data.ingredientes or [],
        calorias=data.calorias,
    )
    ok = menu._producto_repo.actualizar(actualizado)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo actualizar el producto")
    return ProductoOut.model_validate(actualizado, from_attributes=True)


@router.delete("/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int, menu: MenuService = Depends(get_menu_service)):
    ok = menu._producto_repo.eliminar(producto_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return None
