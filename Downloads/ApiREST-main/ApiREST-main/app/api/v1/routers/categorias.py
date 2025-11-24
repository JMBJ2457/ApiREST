from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_menu_service, get_repositorios
from api.v1.schemas.categoria import CategoriaIn, CategoriaOut
from services.menu_service import MenuService
from services.categoria_saga_service import CategoriaSagaService
from saga.orchestrator import SagaExecutionError
from domain.models import Categoria as CategoriaDomain, TipoCategoria
import logging

logger = logging.getLogger(__name__)

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
def eliminar_categoria(
    categoria_id: int,
    categoria_destino_id: Optional[int] = Query(
        None,
        description="ID de la categoría destino para mover los productos. Si se proporciona, los productos se moverán antes de eliminar la categoría."
    ),
    menu: MenuService = Depends(get_menu_service)
):
    """
    Elimina una categoría.
    
    Si se proporciona `categoria_destino_id`, los productos de la categoría
    se moverán automáticamente a la categoría destino antes de eliminar.
    Esta operación usa el patrón SAGA para garantizar atomicidad.
    
    Si no se proporciona `categoria_destino_id`, se intenta eliminar directamente.
    Esto puede fallar si la categoría tiene productos asociados.
    
    **Ejemplo con movimiento de productos:**
    ```
    DELETE /api/v1/categorias/1?categoria_destino_id=2
    ```
    
    **Ejemplo sin movimiento (eliminación directa):**
    ```
    DELETE /api/v1/categorias/1
    ```
    """
    # Si se proporciona categoría destino, usar SAGA para mover productos
    if categoria_destino_id is not None:
        try:
            # Obtener repositorios (con db si es necesario para el backend)
            from core.config import get_settings
            settings = get_settings()
            db = None
            if settings.REPO_BACKEND == "database":
                from db.session import SessionLocal
                db = SessionLocal()
                try:
                    producto_repo, categoria_repo = get_repositorios(db)
                finally:
                    db.close()
            else:
                producto_repo, categoria_repo = get_repositorios()
            
            saga_service = CategoriaSagaService(producto_repo, categoria_repo)
            
            # Ejecutar operación con SAGA
            resultado = saga_service.eliminar_categoria_con_productos(
                categoria_id=categoria_id,
                categoria_destino_id=categoria_destino_id
            )
            
            logger.info(
                f"Categoría {categoria_id} eliminada con {resultado['productos_migrados']} "
                f"productos movidos a categoría {categoria_destino_id}"
            )
            return None
            
        except ValueError as e:
            # Errores de validación (categorías no existen, etc.)
            logger.warning(f"Error de validación al eliminar categoría: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        except SagaExecutionError as e:
            # Error durante la ejecución del SAGA
            logger.error(
                f"SAGA falló al eliminar categoría: {e.message}, paso: {e.failed_step}"
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Error durante la eliminación de categoría",
                    "message": e.message,
                    "failed_step": e.failed_step,
                    "saga_id": e.saga_id,
                    "compensation_applied": e.compensation_results is not None
                }
            )
        
        except Exception as e:
            # Error inesperado
            logger.error(f"Error inesperado al eliminar categoría: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado: {str(e)}"
            )
    
    # Si no se proporciona categoría destino, eliminar directamente
    else:
        # Verificar si la categoría tiene productos
        productos = menu._producto_repo.obtener_por_categoria(categoria_id)
        if productos:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"La categoría tiene {len(productos)} producto(s) asociado(s). "
                    "Proporciona 'categoria_destino_id' para mover los productos antes de eliminar."
                )
            )
        
        ok = menu._categoria_repo.eliminar(categoria_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        return None
