"""
Circuit Breaker Pattern Implementation

Protege contra fallos en cascada al detectar cuando un servicio
está fallando y bloquea temporalmente las llamadas.
"""
from enum import Enum
from time import time
from typing import Callable, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del Circuit Breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Bloqueado por muchos fallos
    HALF_OPEN = "half_open"  # Probando si se recuperó


class CircuitBreakerError(Exception):
    """Excepción lanzada cuando el Circuit Breaker está abierto"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker que protege operaciones que pueden fallar.
    
    Estados:
    - CLOSED: Permite todas las llamadas normalmente
    - OPEN: Bloquea llamadas después de muchos fallos
    - HALF_OPEN: Permite algunas llamadas de prueba para verificar recuperación
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "default"
    ):
        """
        Args:
            failure_threshold: Número de fallos antes de abrir el circuito
            recovery_timeout: Segundos antes de intentar recuperación (half-open)
            expected_exception: Tipo de excepción que cuenta como fallo
            name: Nombre del circuit breaker para logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        # Estado interno
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función protegida por el Circuit Breaker.
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            CircuitBreakerError: Si el circuito está abierto
        """
        # Verificar si podemos intentar la llamada
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit Breaker '{self.name}' cambió a HALF_OPEN")
            else:
                raise CircuitBreakerError(
                    f"Circuit Breaker '{self.name}' está ABIERTO. "
                    f"Esperando recuperación. Fallos: {self.failure_count}"
                )
        
        # Intentar ejecutar la función
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si es tiempo de intentar recuperación"""
        if self.last_failure_time is None:
            return False
        return (time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Maneja una llamada exitosa"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # Si tenemos suficientes éxitos, cerramos el circuito
            if self.success_count >= 2:  # Requiere 2 éxitos consecutivos
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_failure_time = None
                logger.info(f"Circuit Breaker '{self.name}' se RECUPERÓ (CLOSED)")
        elif self.state == CircuitState.CLOSED:
            # Resetear contador de fallos en caso de éxito
            self.failure_count = 0
    
    def _on_failure(self):
        """Maneja una llamada fallida"""
        self.failure_count += 1
        self.last_failure_time = time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Si falla en half-open, volver a abrir
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(
                f"Circuit Breaker '{self.name}' volvió a ABIERTE desde HALF_OPEN. "
                f"Fallos: {self.failure_count}"
            )
        elif self.state == CircuitState.CLOSED:
            # Verificar si debemos abrir el circuito
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"Circuit Breaker '{self.name}' se ABIERTO. "
                    f"Fallos: {self.failure_count}/{self.failure_threshold}"
                )
    
    def reset(self):
        """Resetea manualmente el Circuit Breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit Breaker '{self.name}' fue RESETEADO manualmente")
    
    def get_state(self) -> CircuitState:
        """Retorna el estado actual"""
        return self.state
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del Circuit Breaker"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception,
    name: Optional[str] = None
):
    """
    Decorador para aplicar Circuit Breaker a una función.
    
    Ejemplo:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30.0)
        def mi_funcion_riesgosa():
            # código que puede fallar
            pass
    """
    def decorator(func: Callable) -> Callable:
        cb_name = name or f"{func.__module__}.{func.__name__}"
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=cb_name
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Agregar referencia al breaker para acceso externo
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator

