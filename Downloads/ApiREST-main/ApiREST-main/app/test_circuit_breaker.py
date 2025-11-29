"""
Script de prueba para demostrar el funcionamiento del Circuit Breaker.

Este script simula diferentes escenarios para verificar que el Circuit Breaker
funciona correctamente.

Uso:
    python test_circuit_breaker.py
"""
import os
import sys
import time
from core.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState


def operacion_exitosa():
    """Operación que siempre tiene éxito"""
    return "Éxito!"


def operacion_que_falla():
    """Operación que siempre falla"""
    raise Exception("Error simulado")


def operacion_intermitente(contador):
    """Operación que falla las primeras veces y luego funciona"""
    if contador < 3:
        raise Exception(f"Fallo #{contador}")
    return "Éxito después de fallos"


def probar_circuit_breaker():
    """Prueba completa del Circuit Breaker"""
    
    print("=" * 60)
    print("PRUEBA DEL CIRCUIT BREAKER")
    print("=" * 60)
    print()
    
    # Crear un Circuit Breaker con umbral bajo para pruebas rápidas
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=5.0,  # 5 segundos para pruebas
        expected_exception=Exception,
        name="TestBreaker"
    )
    
    print("1. ESTADO INICIAL (CLOSED)")
    print("-" * 60)
    print(f"Estado: {breaker.get_state().value}")
    print(f"Fallos: {breaker.failure_count}/{breaker.failure_threshold}")
    print()
    
    # Prueba 1: Operaciones exitosas
    print("2. PRUEBA: Operaciones exitosas")
    print("-" * 60)
    for i in range(3):
        try:
            result = breaker.call(operacion_exitosa)
            print(f"  [OK] Llamada {i+1}: {result}")
        except Exception as e:
            print(f"  [ERROR] Llamada {i+1}: Error - {e}")
    print(f"Estado después: {breaker.get_state().value}")
    print(f"Fallos: {breaker.failure_count}")
    print()
    
    # Prueba 2: Simular fallos para abrir el circuito
    print("3. PRUEBA: Simulando fallos para abrir el circuito")
    print("-" * 60)
    for i in range(breaker.failure_threshold + 2):
        try:
            breaker.call(operacion_que_falla)
            print(f"  [ERROR] Llamada {i+1}: No debería llegar aquí")
        except CircuitBreakerError as e:
            print(f"  [CIRCUIT OPEN] Llamada {i+1}: Circuit Breaker ABIERTO - {str(e)[:50]}...")
            break
        except Exception as e:
            print(f"  [FALLO] Llamada {i+1}: Fallo capturado - {str(e)[:30]}")
    
    print(f"Estado después: {breaker.get_state().value}")
    print(f"Fallos: {breaker.failure_count}")
    print()
    
    # Prueba 3: Intentar llamadas cuando está abierto
    print("4. PRUEBA: Intentar llamadas cuando el circuito está ABIERTO")
    print("-" * 60)
    for i in range(3):
        try:
            breaker.call(operacion_exitosa)
            print(f"  [ERROR] Llamada {i+1}: No debería permitir llamadas")
        except CircuitBreakerError as e:
            print(f"  [OK] Llamada {i+1}: Correctamente bloqueada - {str(e)[:60]}...")
    print()
    
    # Prueba 4: Esperar recuperación (half-open)
    print("5. PRUEBA: Esperando recuperación (5 segundos)...")
    print("-" * 60)
    print("  Esperando para que el circuito pase a HALF_OPEN...")
    time.sleep(6)  # Esperar más que el recovery_timeout
    
    # Intentar una llamada (debería pasar a half-open)
    try:
        result = breaker.call(operacion_exitosa)
        print(f"  [OK] Llamada de prueba: {result}")
        print(f"  Estado: {breaker.get_state().value}")
    except CircuitBreakerError as e:
        print(f"  [AUN BLOQUEADO] Aún bloqueado: {str(e)[:50]}...")
    print()
    
    # Prueba 5: Recuperación completa
    print("6. PRUEBA: Recuperación completa")
    print("-" * 60)
    if breaker.get_state() == CircuitState.HALF_OPEN:
        # Necesitamos 2 éxitos consecutivos para cerrar
        for i in range(2):
            try:
                result = breaker.call(operacion_exitosa)
                print(f"  [OK] Llamada {i+1}: {result}")
            except Exception as e:
                print(f"  [ERROR] Llamada {i+1}: Error - {e}")
        print(f"Estado final: {breaker.get_state().value}")
    else:
        print(f"  Estado actual: {breaker.get_state().value}")
    print()
    
    # Estadísticas finales
    print("7. ESTADÍSTICAS FINALES")
    print("-" * 60)
    stats = breaker.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    print("=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    try:
        probar_circuit_breaker()
    except KeyboardInterrupt:
        print("\n\nPrueba interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

