from typing import List
from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_menu_service
from api.v1.schemas.categoria import CategoriaIn, CategoriaOut
from services.menu_service import MenuService
from domain.models import Categoria as CategoriaDomain, TipoCategoria

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("/", response_model=List[CategoriaOut])
def listar_categorias(menu: MenuService = Depends(get_menu_service)):
    categorias = menu._categoria_repo.obtener_todas()
    return [CategoriaOut.model_validate(c, from_attributes=True) for c in categorias]


@router.get("/{categoria_id}", response_model=CategoriaOut)
def obtener_categoria(categoria_id: int, menu: MenuService = Depends(get_menu_service)):
    c = menu._categoria_repo.obtener_por_id(categoria_id)
    if not c:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return CategoriaOut.model_validate(c, from_attributes=True)


@router.post("/", response_model=CategoriaOut, status_code=201)
def crear_categoria(data: CategoriaIn, menu: MenuService = Depends(get_menu_service)):
    existentes = menu._categoria_repo.obtener_todas()
    next_id = max([c.id for c in existentes], default=0) + 1
    nueva = CategoriaDomain(
        id=next_id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        tipo=TipoCategoria(data.tipo.value),
        activa=data.activa,
    )
    ok = menu._categoria_repo.agregar(nueva)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo crear la categoría")
    return CategoriaOut.model_validate(nueva, from_attributes=True)


@router.put("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(categoria_id: int, data: CategoriaIn, menu: MenuService = Depends(get_menu_service)):
    actual = menu._categoria_repo.obtener_por_id(categoria_id)
    if not actual:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    actualizada = CategoriaDomain(
        id=categoria_id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        tipo=TipoCategoria(data.tipo.value),
        activa=data.activa,
    )
    ok = menu._categoria_repo.actualizar(actualizada)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo actualizar la categoría")
    return CategoriaOut.model_validate(actualizada, from_attributes=True)


@router.delete("/{categoria_id}", status_code=204)
def eliminar_categoria(categoria_id: int, menu: MenuService = Depends(get_menu_service)):
    ok = menu._categoria_repo.eliminar(categoria_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return None
