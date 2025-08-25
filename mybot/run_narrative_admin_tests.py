#!/usr/bin/env python
"""
Script para ejecutar y verificar la cobertura de las pruebas del sistema administrativo de narrativa.
"""
import sys
import os
import subprocess
import argparse

def run_tests(coverage=False, verbose=False, specific=None):
    """Ejecuta las pruebas del sistema administrativo de narrativa con los parámetros especificados."""
    # Determinar qué python usar
    python_cmd = "python"
    if os.path.exists("venv/bin/python"):
        python_cmd = "venv/bin/python"
    elif os.path.exists("venv/Scripts/python"):
        python_cmd = "venv/Scripts/python"
    
    test_modules = [
        "tests/services/test_fragment_integrity.py",
        "tests/services/test_event_bus_integration.py",
        "tests/services/test_database_transactions.py",
        "tests/services/test_clue_system_validation.py",
        "tests/services/test_performance_benchmarks.py",
        "tests/services/test_concurrent_operations.py",
        "tests/services/test_failure_scenarios.py",
        "tests/services/test_fragment_connections.py",
    ]
    
    # Pruebas existentes
    existing_tests = [
        "tests/services/test_narrative_admin_service.py",
        "tests/integration/test_narrative_admin_integration.py",
    ]
    
    # Si se especifica un test específico, ejecutar solo ese
    if specific:
        if '::' in specific:
            # Es un test específico (archivo::función)
            all_tests = [specific]
        elif os.path.exists(specific):
            # Es un archivo
            all_tests = [specific]
        else:
            # Buscar por nombre entre los tests
            all_tests = [test for test in test_modules + existing_tests if specific in test]
    else:
        all_tests = test_modules + existing_tests
    
    # Construir comando base
    cmd = [python_cmd, "-m", "pytest"]
    
    # Agregar opción de verbose si se solicita
    if verbose:
        cmd.append("-v")
    
    # Configurar cobertura si se solicita
    if coverage:
        cmd.extend([
            "--cov=services.narrative_admin_service",
            "--cov=database.narrative_unified",
            "--cov-report=term",
            "--cov-report=html"
        ])
    
    # Agregar los tests a ejecutar
    cmd.extend(all_tests)
    
    # Mostrar el comando que se va a ejecutar
    print(f"Ejecutando: {' '.join(cmd)}")
    
    return subprocess.run(cmd)

def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Ejecutar pruebas del sistema administrativo de narrativa.")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generar informe de cobertura")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar salida detallada")
    parser.add_argument("--test", "-t", help="Ejecutar un test específico")
    parser.add_argument("--fix-session", "-f", action="store_true", 
                       help="Usar fix temporal para resolver problemas de session y AsyncMock")
    
    args = parser.parse_args()
    
    # Si se solicita el fix temporal, aplicar parche al entorno
    if args.fix_session:
        print("Aplicando parche temporal para AsyncMock + session.begin()...")
        os.environ["PYTEST_MOCK_PATCH_ASYNCIO"] = "1"
    
    # Ejecutar los tests con los parámetros solicitados
    result = run_tests(
        coverage=args.coverage, 
        verbose=args.verbose, 
        specific=args.test
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())