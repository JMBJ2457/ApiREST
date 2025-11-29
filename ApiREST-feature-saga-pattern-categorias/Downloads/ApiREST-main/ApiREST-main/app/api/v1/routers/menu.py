from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_menu_service, get_repositorios
from api.v1.schemas.producto import ProductoOut
from api.v1.schemas.categoria import TipoCategoriaEnum
from services.menu_service import MenuService
from domain.models import TipoCategoria
from repositories.file_repository import ProductoFileRepository, CategoriaFileRepository
from core.circuit_breaker import CircuitBreakerError

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


@router.get("/circuit-breaker/estado")
def obtener_estado_circuit_breaker():
    """
    Obtiene el estado de los Circuit Breakers en los repositorios.
    Solo disponible cuando se usa REPO_BACKEND=file
    """
    from core.config import get_settings
    settings = get_settings()
    
    if settings.REPO_BACKEND != "file":
        return {
            "mensaje": "Circuit Breaker solo está activo cuando REPO_BACKEND=file",
            "backend_actual": settings.REPO_BACKEND
        }
    
    producto_repo, categoria_repo = get_repositorios()
    
    estados = {}
    
    if isinstance(producto_repo, ProductoFileRepository):
        estados["producto_repository"] = producto_repo._circuit_breaker.get_stats()
    
    if isinstance(categoria_repo, CategoriaFileRepository):
        estados["categoria_repository"] = categoria_repo._circuit_breaker.get_stats()
    
    return {
        "circuit_breakers": estados,
        "explicacion": {
            "closed": "Funcionando normalmente - permite todas las llamadas",
            "open": "Bloqueado - demasiados fallos, no permite llamadas",
            "half_open": "Probando recuperación - permite algunas llamadas de prueba"
        }
    }


@router.post("/circuit-breaker/test")
def probar_circuit_breaker(accion: str = Query(..., description="Acción: 'forzar_fallo', 'reset', 'simular_fallos'", enum=["forzar_fallo", "reset", "simular_fallos"])):
    """
    Endpoint de prueba para el Circuit Breaker.
    
    Acciones disponibles:
    - 'forzar_fallo': Fuerza un fallo en la operación de archivo
    - 'reset': Resetea el Circuit Breaker manualmente
    - 'simular_fallos': Simula múltiples fallos para abrir el circuito
    """
    from core.config import get_settings
    settings = get_settings()
    
    if settings.REPO_BACKEND != "file":
        raise HTTPException(
            status_code=400,
            detail="Circuit Breaker solo está activo cuando REPO_BACKEND=file"
        )
    
    producto_repo, categoria_repo = get_repositorios()
    
    if not isinstance(producto_repo, ProductoFileRepository):
        raise HTTPException(
            status_code=400,
            detail="Este endpoint solo funciona con FileRepository"
        )
    
    resultados = {}
    breaker = producto_repo._circuit_breaker
    
    if accion == "forzar_fallo":
        # Intentar una operación que fallará (archivo inexistente o sin permisos)
        try:
            # Guardar el path original
            path_original = producto_repo.archivo_path
            # Temporalmente cambiar a un path que causará error
            producto_repo.archivo_path = "/ruta/inexistente/productos.json"
            producto_repo._guardar_en_archivo()
        except CircuitBreakerError as e:
            resultados["error"] = str(e)
            resultados["estado_breaker"] = breaker.get_state().value
        except Exception as e:
            resultados["error"] = f"Error capturado: {str(e)}"
            resultados["estado_breaker"] = breaker.get_state().value
        finally:
            # Restaurar el path original
            producto_repo.archivo_path = path_original
    
    elif accion == "reset":
        breaker.reset()
        resultados["mensaje"] = "Circuit Breaker reseteado exitosamente"
        resultados["estado_breaker"] = breaker.get_state().value
    
    elif accion == "simular_fallos":
        # Simular múltiples fallos para abrir el circuito
        path_original = producto_repo.archivo_path
        producto_repo.archivo_path = "/ruta/inexistente/productos.json"
        
        fallos_simulados = 0
        for i in range(breaker.failure_threshold + 1):
            try:
                producto_repo._guardar_en_archivo()
            except CircuitBreakerError:
                fallos_simulados += 1
                break
            except Exception:
                fallos_simulados += 1
        
        producto_repo.archivo_path = path_original
        
        resultados["fallos_simulados"] = fallos_simulados
        resultados["estado_breaker"] = breaker.get_state().value
        resultados["failure_count"] = breaker.failure_count
        resultados["threshold"] = breaker.failure_threshold
    
    resultados["estadisticas"] = breaker.get_stats()
    
    return {
        "accion": accion,
        "resultado": resultados,
        "explicacion": {
            "estado_actual": breaker.get_state().value,
            "fallos": breaker.failure_count,
            "threshold": breaker.failure_threshold
        }
    }
