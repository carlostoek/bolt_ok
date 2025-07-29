#!/usr/bin/env python
"""
Script para ejecutar todas las pruebas relacionadas con Diana.

Este script facilita la ejecución de todas las pruebas de Diana en un solo comando,
organizadas por categorías para un mejor análisis y depuración.
"""

import os
import sys
import subprocess
import argparse
import time


def run_command(command):
    """Ejecuta un comando y muestra la salida en tiempo real."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True
    )
    
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    return process.returncode


def get_tests_by_category():
    """Organiza los tests de Diana por categorías."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    return {
        "servicio": [
            os.path.join(base_dir, "unit/diana/test_diana_emotional_service.py")
        ],
        "handlers": [
            os.path.join(base_dir, "unit/diana/test_diana_handlers.py")
        ],
        "personalizacion": [
            os.path.join(base_dir, "unit/diana/test_diana_personalization.py")
        ],
        "contradicciones": [
            os.path.join(base_dir, "unit/diana/test_diana_contradictions.py")
        ],
        "integracion": [
            os.path.join(base_dir, "integration/diana/test_diana_integration.py")
        ],
        "persistencia": [
            os.path.join(base_dir, "integration/diana/test_diana_persistence.py")
        ],
        "carga": [
            os.path.join(base_dir, "integration/diana/test_diana_load.py")
        ],
        "no_interferencia": [
            os.path.join(base_dir, "integration/diana/test_diana_non_interference.py")
        ]
    }


def main():
    """Función principal que ejecuta las pruebas según los argumentos proporcionados."""
    parser = argparse.ArgumentParser(description="Ejecutar pruebas de Diana")
    parser.add_argument(
        "--category",
        choices=["all", "unit", "integration", "servicio", "handlers", "personalizacion", 
                "contradicciones", "integracion", "persistencia", "carga", "no_interferencia"],
        default="all",
        help="Categoría de pruebas a ejecutar"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ejecutar pruebas en modo verbose"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generar informe de cobertura"
    )
    
    args = parser.parse_args()
    tests_by_category = get_tests_by_category()
    
    # Determinar qué pruebas ejecutar
    tests_to_run = []
    
    if args.category == "all":
        for category_tests in tests_by_category.values():
            tests_to_run.extend(category_tests)
    elif args.category == "unit":
        tests_to_run.extend(tests_by_category["servicio"])
        tests_to_run.extend(tests_by_category["handlers"])
        tests_to_run.extend(tests_by_category["personalizacion"])
        tests_to_run.extend(tests_by_category["contradicciones"])
    elif args.category == "integration":
        tests_to_run.extend(tests_by_category["integracion"])
        tests_to_run.extend(tests_by_category["persistencia"])
        tests_to_run.extend(tests_by_category["carga"])
        tests_to_run.extend(tests_by_category["no_interferencia"])
    else:
        tests_to_run.extend(tests_by_category[args.category])
    
    # Construir el comando
    command = ["python", "-m", "pytest"]
    
    if args.verbose:
        command.append("-v")
    
    if args.coverage:
        command.extend([
            "--cov=services.diana_emotional_service",
            "--cov=handlers.diana_test_handler",
            "--cov=handlers.diana_emotional_handlers",
            "--cov-report=term",
            "--cov-report=html:coverage_html"
        ])
    
    command.extend(tests_to_run)
    
    # Ejecutar las pruebas
    print(f"Ejecutando pruebas de Diana ({args.category})...")
    start_time = time.time()
    result = run_command(" ".join(command))
    duration = time.time() - start_time
    
    print(f"\nPruebas completadas en {duration:.2f} segundos")
    
    if args.coverage:
        print("\nInforme de cobertura generado en: coverage_html/index.html")
    
    return result


if __name__ == "__main__":
    sys.exit(main())