#!/usr/bin/env python3
"""
Script para ejecutar las pruebas de protección de integración críticas.
Estas pruebas protegen los flujos críticos del sistema durante refactoring.

Uso:
    python run_protection_tests.py

Las pruebas cubren:
1. Servicio de puntos (PointService) - Gamificación crítica
2. Servicio de badges (BadgeService) - Sistema de logros
3. Integración VIP por badges - Desbloqueo automático VIP
4. Recuperación de fragmentos narrativos - Sistema narrativo
5. Integración engagement-puntos - Recompensas por participación
6. Integridad de datos bajo carga - Resistencia a condiciones de carrera
7. Manejo de errores - Resistencia a fallos
"""

import os
import sys
import asyncio

# Añadir el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.integration.test_simple_integration import (
    test_point_service_critical_flow,
    test_badge_service_critical_flow,
    test_vip_badge_integration,
    test_narrative_fragment_retrieval,
    test_engagement_points_integration,
    test_data_integrity_under_load,
    test_error_handling_resilience
)


async def run_all_protection_tests():
    """Ejecuta todas las pruebas de protección críticas."""
    
    tests = [
        ("Point Service Critical Flow", test_point_service_critical_flow),
        ("Badge Service Critical Flow", test_badge_service_critical_flow),
        ("VIP Badge Integration", test_vip_badge_integration),
        ("Narrative Fragment Retrieval", test_narrative_fragment_retrieval),
        ("Engagement Points Integration", test_engagement_points_integration),
        ("Data Integrity Under Load", test_data_integrity_under_load),
        ("Error Handling Resilience", test_error_handling_resilience),
    ]
    
    print("🔒 EJECUTANDO PRUEBAS DE PROTECCIÓN CRÍTICAS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"⚡ Ejecutando: {test_name}...")
            await test_func()
            print(f"✅ PASÓ: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FALLÓ: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
        print()
    
    print("=" * 50)
    print("📊 RESUMEN DE PRUEBAS DE PROTECCIÓN")
    print(f"✅ Pruebas exitosas: {passed}")
    print(f"❌ Pruebas fallidas: {failed}")
    print(f"📈 Total ejecutadas: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS DE PROTECCIÓN PASARON!")
        print("🛡️  Los flujos críticos están protegidos para refactoring.")
        return True
    else:
        print(f"\n⚠️  {failed} pruebas fallaron. Revisar antes de refactoring.")
        return False


def main():
    """Función principal."""
    print("🚀 Iniciando pruebas de protección del sistema...")
    
    # Ejecutar las pruebas
    success = asyncio.run(run_all_protection_tests())
    
    if success:
        print("\n✨ Sistema listo para refactoring seguro.")
        sys.exit(0)
    else:
        print("\n🚨 Corregir pruebas fallidas antes de continuar.")
        sys.exit(1)


if __name__ == "__main__":
    main()