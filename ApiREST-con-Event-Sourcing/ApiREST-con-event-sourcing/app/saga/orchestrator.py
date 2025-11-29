"""
Orquestador SAGA para ejecutar operaciones transaccionales con compensación automática.

El patrón SAGA garantiza que si una operación multi-paso falla,
todos los pasos ejecutados se revierten automáticamente.
"""
from enum import Enum
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class SagaStepStatus(Enum):
    """Estados posibles de un paso del SAGA"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    """
    Representa un paso individual del SAGA.
    
    Cada paso tiene:
    - Una función de ejecución (execute)
    - Una función de compensación (compensate)
    - Estado y resultados rastreables
    """
    name: str
    execute: Callable
    compensate: Callable
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    execution_time: Optional[float] = None
    compensation_time: Optional[float] = None

@dataclass
class SagaContext:
    """
    Contexto compartido entre todos los pasos del SAGA.
    Permite que los pasos compartan información.
    """
    saga_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

class SagaExecutionError(Exception):
    """
    Excepción lanzada cuando falla la ejecución del SAGA.
    Contiene información detallada sobre qué paso falló y el contexto.
    """
    def __init__(self, message: str, saga_id: str, failed_step: str, context: SagaContext):
        self.message = message
        self.saga_id = saga_id
        self.failed_step = failed_step
        self.context = context
        self.compensation_results: Optional[Dict[str, Any]] = None
        super().__init__(message)

class SagaOrchestrator:
    """
    Orquestador SAGA que ejecuta pasos secuenciales con compensación automática.
    
    Características:
    - Ejecución secuencial de pasos
    - Compensación automática en orden inverso si falla
    - Contexto compartido entre pasos
    - Logging detallado de cada operación
    - Estado de cada paso rastreable
    
    Ejemplo de uso:
        orchestrator = SagaOrchestrator("mi_operacion")
        
        orchestrator.add_step(
            "paso1",
            lambda: hacer_algo(),
            lambda resultado: deshacer_algo(resultado)
        )
        
        resultado = orchestrator.execute()
    """
    
    def __init__(self, saga_name: str = "unnamed_saga"):
        """
        Inicializa el orquestador SAGA.
        
        Args:
            saga_name: Nombre descriptivo del SAGA para logging
        """
        self.saga_id = str(uuid.uuid4())
        self.saga_name = saga_name
        self.steps: List[SagaStep] = []
        self.executed_steps: List[SagaStep] = []
        self.context = SagaContext(saga_id=self.saga_id)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def add_step(self, name: str, execute: Callable, compensate: Callable):
        """
        Agrega un paso al SAGA.
        
        Args:
            name: Nombre descriptivo del paso (para logging y debugging)
            execute: Función que ejecuta el paso. Debe retornar el resultado.
            compensate: Función que compensa el paso. Recibe el resultado del execute.
        
        Returns:
            self: Para permitir encadenamiento de métodos
        """
        self.steps.append(SagaStep(name, execute, compensate))
        return self
    
    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta todos los pasos del SAGA en orden.
        
        Si algún paso falla:
        1. Se detiene la ejecución
        2. Se compensan todos los pasos ejecutados (en orden inverso)
        3. Se lanza SagaExecutionError con detalles
        
        Returns:
            Dict con resultados de la ejecución:
            {
                "success": True,
                "saga_id": "...",
                "saga_name": "...",
                "total_time": 0.123,
                "steps_completed": 3,
                "results": {...},
                "context": {...}
            }
            
        Raises:
            SagaExecutionError: Si algún paso falla
        """
        self.start_time = datetime.now()
        logger.info(
            f"[SAGA {self.saga_id[:8]}] Iniciando '{self.saga_name}' "
            f"con {len(self.steps)} pasos"
        )
        
        try:
            # Ejecutar cada paso secuencialmente
            for step in self.steps:
                step.status = SagaStepStatus.EXECUTING
                step_start = datetime.now()
                
                logger.info(f"[SAGA {self.saga_id[:8]}] Ejecutando paso: {step.name}")
                
                # Ejecutar el paso
                step.result = step.execute()
                
                step.execution_time = (datetime.now() - step_start).total_seconds()
                step.status = SagaStepStatus.COMPLETED
                self.executed_steps.append(step)
                
                logger.info(
                    f"[SAGA {self.saga_id[:8]}] Paso '{step.name}' completado "
                    f"en {step.execution_time:.2f}s"
                )
            
            # Todos los pasos se ejecutaron exitosamente
            self.end_time = datetime.now()
            total_time = (self.end_time - self.start_time).total_seconds()
            
            logger.info(
                f"[SAGA {self.saga_id[:8]}] SAGA '{self.saga_name}' completado "
                f"exitosamente en {total_time:.2f}s"
            )
            
            return {
                "success": True,
                "saga_id": self.saga_id,
                "saga_name": self.saga_name,
                "total_time": total_time,
                "steps_completed": len(self.executed_steps),
                "results": {step.name: step.result for step in self.executed_steps},
                "context": self.context.metadata
            }
        
        except Exception as e:
            # Algo falló, necesitamos compensar
            self.end_time = datetime.now()
            failed_step = step.name if 'step' in locals() else "unknown"
            step.error = e
            step.status = SagaStepStatus.FAILED
            
            logger.error(
                f"[SAGA {self.saga_id[:8]}] Error en paso '{failed_step}': {str(e)}"
            )
            logger.info(f"[SAGA {self.saga_id[:8]}] Iniciando compensación...")
            
            # Compensar en orden inverso
            compensation_results = self._compensate()
            
            # Crear y lanzar excepción con toda la información
            error = SagaExecutionError(
                f"SAGA falló en paso '{failed_step}': {str(e)}",
                self.saga_id,
                failed_step,
                self.context
            )
            error.compensation_results = compensation_results
            raise error
    
    def _compensate(self) -> Dict[str, Any]:
        """
        Compensa todos los pasos ejecutados en orden inverso.
        
        Returns:
            Dict con resultados de la compensación de cada paso
        """
        compensation_results = {}
        
        for step in reversed(self.executed_steps):
            if step.status == SagaStepStatus.COMPLETED:
                try:
                    step.status = SagaStepStatus.COMPENSATING
                    comp_start = datetime.now()
                    
                    logger.info(f"[SAGA {self.saga_id[:8]}] Compensando paso: {step.name}")
                    
                    # Ejecutar función de compensación
                    step.compensate(step.result)
                    
                    step.compensation_time = (datetime.now() - comp_start).total_seconds()
                    step.status = SagaStepStatus.COMPENSATED
                    compensation_results[step.name] = "compensated"
                    
                    logger.info(
                        f"[SAGA {self.saga_id[:8]}] Paso '{step.name}' compensado "
                        f"en {step.compensation_time:.2f}s"
                    )
                
                except Exception as comp_error:
                    logger.error(
                        f"[SAGA {self.saga_id[:8]}] Error al compensar '{step.name}': "
                        f"{str(comp_error)}"
                    )
                    compensation_results[step.name] = f"compensation_failed: {str(comp_error)}"
        
        return compensation_results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del SAGA.
        
        Returns:
            Dict con información detallada del estado:
            {
                "saga_id": "...",
                "saga_name": "...",
                "total_steps": 3,
                "completed": 2,
                "failed": 0,
                "compensated": 0,
                "steps": [...],
                "context": {...}
            }
        """
        return {
            "saga_id": self.saga_id,
            "saga_name": self.saga_name,
            "total_steps": len(self.steps),
            "completed": len([s for s in self.steps if s.status == SagaStepStatus.COMPLETED]),
            "failed": len([s for s in self.steps if s.status == SagaStepStatus.FAILED]),
            "compensated": len([s for s in self.steps if s.status == SagaStepStatus.COMPENSATED]),
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "execution_time": s.execution_time,
                    "compensation_time": s.compensation_time,
                    "has_error": s.error is not None
                }
                for s in self.steps
            ],
            "context": self.context.metadata
        }

