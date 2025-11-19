from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_menu_service
from api.v1.schemas.producto import ProductoOut
from api.v1.schemas.categoria import TipoCategoriaEnum
from services.menu_service import MenuService
from domain.models import TipoCategoria

router = APIRouter(prefix="", tags=["menu"])


@router.get("/menu", response_model=Dict[str, List[ProductoOut]])
def obtener_menu(menu: MenuService = Depends(get_menu_service)):
    data = menu.obtener_menu_completo()
    return {k: [ProductoOut.model_validate(p, from_attributes=True) for p in v] for k, v in data.items()}


@router.get("/estadisticas")
def obtener_estadisticas(menu: MenuService = Depends(get_menu_service)):
    return menu.obtener_estadisticas_menu()


@router.get("/productos/por-categoria/{categoria_id}", response_model=List[ProductoOut])
def productos_por_categoria(categoria_id: int, menu: MenuService = Depends(get_menu_service)):
    items = menu.obtener_productos_por_categoria(categoria_id)
    return [ProductoOut.model_validate(p, from_attributes=True) for p in items]


@router.get("/productos/por-tipo", response_model=List[ProductoOut])
def productos_por_tipo(tipo: TipoCategoriaEnum = Query(...)):
    menu = get_menu_service()
    tipo_domain = TipoCategoria(tipo.value)
    items = menu.obtener_productos_por_tipo_categoria(tipo_domain)
    return [ProductoOut.model_validate(p, from_attributes=True) for p in items]
