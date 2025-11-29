"""
Servicio para operaciones complejas de categorías usando el patrón SAGA.

Este servicio maneja operaciones que requieren múltiples pasos y garantiza
consistencia mediante compensación automática si algo falla.
"""
from typing import Dict, Any, Optional
from repositories.interfaces import IProductoRepository, ICategoriaRepository
from saga.orchestrator import SagaOrchestrator, SagaExecutionError
from domain.models import Categoria, Producto
import logging

logger = logging.getLogger(__name__)

class CategoriaSagaService:
    """
    Servicio que maneja operaciones complejas de categorías usando SAGA.
    
    El patrón SAGA garantiza que si una operación multi-paso falla,
    todos los cambios se revierten automáticamente.
    """
    
    def __init__(
        self, 
        producto_repo: IProductoRepository, 
        categoria_repo: ICategoriaRepository
    ):
        """
        Inicializa el servicio.
        
        Args:
            producto_repo: Repositorio de productos
            categoria_repo: Repositorio de categorías
        """
        self.producto_repo = producto_repo
        self.categoria_repo = categoria_repo
    
    def eliminar_categoria_con_productos(
        self, 
        categoria_id: int, 
        categoria_destino_id: int
    ) -> Dict[str, Any]:
        """
        Elimina una categoría moviendo todos sus productos a otra categoría.
        
        Esta operación usa el patrón SAGA para garantizar atomicidad:
        - Si todos los pasos se completan: la categoría se elimina y los productos se mueven
        - Si algún paso falla: todos los cambios se revierten automáticamente
        
        Pasos del SAGA:
        1. Validar que ambas categorías existen y la destino está activa
        2. Obtener todos los productos de la categoría a eliminar
        3. Mover cada producto a la categoría destino
        4. Eliminar la categoría original
        
        Args:
            categoria_id: ID de la categoría a eliminar
            categoria_destino_id: ID de la categoría destino para los productos
        
        Returns:
            Dict con resultados de la operación:
            {
                "success": True,
                "saga_id": "...",
                "categoria_eliminada": 1,
                "productos_migrados": 5,
                "total_time": 0.123,
                ...
            }
        
        Raises:
            ValueError: Si las categorías no existen o son inválidas
            SagaExecutionError: Si algún paso del SAGA falla
        """
        logger.info(
            f"Iniciando eliminación de categoría {categoria_id} "
            f"moviendo productos a categoría {categoria_destino_id}"
        )
        
        # ============================================================
        # VALIDACIONES INICIALES (antes del SAGA)
        # ============================================================
        
        categoria_original = self.categoria_repo.obtener_por_id(categoria_id)
        if not categoria_original:
            raise ValueError(f"Categoría {categoria_id} no existe")
        
        categoria_destino = self.categoria_repo.obtener_por_id(categoria_destino_id)
        if not categoria_destino:
            raise ValueError(f"Categoría destino {categoria_destino_id} no existe")
        
        if categoria_id == categoria_destino_id:
            raise ValueError("No se puede mover productos a la misma categoría")
        
        # Obtener productos de la categoría a eliminar
        productos = self.producto_repo.obtener_por_categoria(categoria_id)
        
        logger.info(f"Encontrados {len(productos)} productos en categoría {categoria_id}")
        
        # ============================================================
        # PREPARAR DATOS PARA COMPENSACIÓN
        # ============================================================
        
        # Guardar copia de la categoría original para poder recrearla si falla
        categoria_original_copy = Categoria(
            id=categoria_original.id,
            nombre=categoria_original.nombre,
            descripcion=categoria_original.descripcion,
            tipo=categoria_original.tipo,
            activa=categoria_original.activa
        )
        
        # Guardar estados originales de productos (para compensación)
        productos_originales = []
        for producto in productos:
            productos_originales.append({
                "id": producto.id,
                "categoria_id": producto.categoria_id,
                "nombre": producto.nombre
            })
        
        # ============================================================
        # CREAR ORQUESTADOR SAGA
        # ============================================================
        
        orchestrator = SagaOrchestrator("eliminar_categoria_con_productos")
        
        # Guardar información en el contexto del SAGA
        orchestrator.context.metadata = {
            "categoria_id": categoria_id,
            "categoria_nombre": categoria_original.nombre,
            "categoria_destino_id": categoria_destino_id,
            "categoria_destino_nombre": categoria_destino.nombre,
            "productos_count": len(productos)
        }
        
        # ============================================================
        # PASO 1: VALIDAR DESTINO
        # ============================================================
        
        def validar_destino():
            """
            Valida que la categoría destino puede recibir productos.
            """
            # Verificar que la categoría destino está activa
            if not categoria_destino.activa:
                raise ValueError(
                    f"La categoría destino '{categoria_destino.nombre}' no está activa. "
                    f"No se pueden mover productos a una categoría inactiva."
                )
            
            logger.info(
                f"Validación exitosa: categoría destino '{categoria_destino.nombre}' "
                f"está activa y puede recibir {len(productos)} productos"
            )
            
            return {
                "validated": True,
                "productos_count": len(productos),
                "categoria_destino_activa": True
            }
        
        def compensar_validar_destino(resultado):
            """
            No hay nada que compensar en una validación.
            Si llegamos aquí, significa que la validación pasó pero algo después falló.
            """
            pass
        
        orchestrator.add_step("validar_destino", validar_destino, compensar_validar_destino)
        
        # ============================================================
        # PASO 2: MOVER PRODUCTOS
        # ============================================================
        
        def mover_productos():
            """
            Mueve todos los productos de la categoría original a la categoría destino.
            
            Returns:
                Lista con información de cada producto movido
            """
            productos_movidos = []
            
            for producto in productos:
                # Guardar categoría original del producto
                categoria_original_producto = producto.categoria_id
                
                # Actualizar categoría del producto
                producto.categoria_id = categoria_destino_id
                
                # Guardar en repositorio
                if not self.producto_repo.actualizar(producto):
                    raise RuntimeError(
                        f"No se pudo mover producto '{producto.nombre}' (ID: {producto.id}) "
                        f"a la categoría {categoria_destino_id}"
                    )
                
                # Registrar el movimiento
                productos_movidos.append({
                    "producto_id": producto.id,
                    "producto_nombre": producto.nombre,
                    "categoria_original": categoria_original_producto,
                    "categoria_nueva": categoria_destino_id
                })
                
                logger.debug(
                    f"Producto '{producto.nombre}' (ID: {producto.id}) movido de "
                    f"categoría {categoria_original_producto} a {categoria_destino_id}"
                )
            
            # Guardar IDs de productos movidos en el contexto del SAGA
            orchestrator.context.metadata["productos_movidos_ids"] = [
                p["producto_id"] for p in productos_movidos
            ]
            
            logger.info(f"Todos los productos ({len(productos_movidos)}) movidos exitosamente")
            
            return productos_movidos
        
        def compensar_mover_productos(resultado):
            """
            Revierte los productos a su categoría original.
            
            Args:
                resultado: Lista de productos movidos (del paso mover_productos)
            """
            logger.info(f"Iniciando compensación: revirtiendo {len(resultado)} productos")
            
            for producto_info in resultado:
                try:
                    # Obtener el producto actual
                    producto = self.producto_repo.obtener_por_id(producto_info["producto_id"])
                    
                    if producto:
                        # Revertir a la categoría original
                        producto.categoria_id = producto_info["categoria_original"]
                        self.producto_repo.actualizar(producto)
                        
                        logger.debug(
                            f"Producto {producto_info['producto_id']} revertido a "
                            f"categoría {producto_info['categoria_original']}"
                        )
                    else:
                        logger.warning(
                            f"Producto {producto_info['producto_id']} no encontrado "
                            f"durante compensación"
                        )
                
                except Exception as e:
                    logger.error(
                        f"Error al revertir producto {producto_info['producto_id']}: {str(e)}"
                    )
                    # Continuamos con los demás productos aunque uno falle
        
        orchestrator.add_step("mover_productos", mover_productos, compensar_mover_productos)
        
        # ============================================================
        # PASO 3: ELIMINAR CATEGORÍA
        # ============================================================
        
        def eliminar_categoria():
            """
            Elimina la categoría original.
            
            Returns:
                Dict con información de la categoría eliminada
            """
            # ============================================================
            # FALLO SIMULADO PARA DEMOSTRAR COMPENSACIÓN
            # Descomenta la siguiente línea para simular un fallo:
            # ============================================================
            # raise RuntimeError("FALLO SIMULADO: Error al eliminar categoría para demostrar compensación")
            
            if not self.categoria_repo.eliminar(categoria_id):
                raise RuntimeError(
                    f"No se pudo eliminar la categoría {categoria_id} "
                    f"('{categoria_original.nombre}')"
                )
            
            logger.info(f"Categoría '{categoria_original.nombre}' (ID: {categoria_id}) eliminada")
            
            return {
                "categoria_eliminada": categoria_id,
                "categoria_nombre": categoria_original.nombre
            }
        
        def compensar_eliminar_categoria(resultado):
            """
            Recrea la categoría eliminada.
            
            Args:
                resultado: Información de la categoría eliminada
            """
            logger.info(
                f"Compensando: recreando categoría '{resultado['categoria_nombre']}' "
                f"(ID: {resultado['categoria_eliminada']})"
            )
            
            try:
                # Recrear la categoría con sus datos originales
                self.categoria_repo.agregar(categoria_original_copy)
                logger.info(f"Categoría {resultado['categoria_eliminada']} recreada exitosamente")
            except Exception as e:
                logger.error(
                    f"Error al recrear categoría {resultado['categoria_eliminada']}: {str(e)}"
                )
                raise
        
        orchestrator.add_step("eliminar_categoria", eliminar_categoria, compensar_eliminar_categoria)
        
        # ============================================================
        # EJECUTAR SAGA
        # ============================================================
        
        try:
            resultado = orchestrator.execute()
            
            # Agregar información adicional al resultado
            resultado["categoria_eliminada"] = categoria_id
            resultado["categoria_eliminada_nombre"] = categoria_original.nombre
            resultado["categoria_destino"] = categoria_destino_id
            resultado["categoria_destino_nombre"] = categoria_destino.nombre
            resultado["productos_migrados"] = len(productos)
            
            logger.info(
                f"Operación completada exitosamente: "
                f"categoría {categoria_id} eliminada, "
                f"{len(productos)} productos migrados a categoría {categoria_destino_id}"
            )
            
            return resultado
        
        except SagaExecutionError as e:
            logger.error(
                f"Error en SAGA de eliminación de categoría: {e.message}\n"
                f"Paso fallido: {e.failed_step}\n"
                f"Compensación: {e.compensation_results}"
            )
            raise
        except Exception as e:
            logger.error(f"Error inesperado en eliminación de categoría: {str(e)}")
            raise

