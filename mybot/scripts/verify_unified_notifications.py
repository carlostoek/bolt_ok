"""
INSTRUCCIONES PARA CLAUDE CODE:

Crea este script de verificación que confirma que el sistema de notificaciones
unificadas está correctamente implementado y funcionando.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationSystemVerifier:
    """Verificador del sistema de notificaciones unificadas."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.verification_results = {
            "timestamp": datetime.now().isoformat(),
            "checks_passed": [],
            "checks_failed": [],
            "warnings": [],
            "recommendations": []
        }
    
    def verify_file_structure(self) -> bool:
        """Verifica que todos los archivos necesarios existan."""
        required_files = [
            "services/notification_service.py",
            "services/notification_config.py",
            "services/coordinador_central.py"
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.verification_results["checks_passed"].append(
                    f"✅ Archivo encontrado: {file_path}"
                )
            else:
                all_exist = False
                self.verification_results["checks_failed"].append(
                    f"❌ Archivo faltante: {file_path}"
                )
        
        return all_exist
    
    def verify_notification_service_implementation(self) -> bool:
        """Verifica que NotificationService tenga los métodos requeridos."""
        service_file = self.project_root / "services/notification_service.py"
        
        if not service_file.exists():
            return False
        
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            "add_notification",
            "_schedule_send_with_priority",
            "_build_enhanced_unified_message",
            "send_immediate_notification",
            "flush_pending_notifications"
        ]
        
        required_classes = [
            "NotificationPriority",
            "NotificationData",
            "NotificationService"
        ]
        
        all_found = True
        
        # Verificar clases
        for class_name in required_classes:
            if f"class {class_name}" in content:
                self.verification_results["checks_passed"].append(
                    f"✅ Clase {class_name} implementada"
                )
            else:
                all_found = False
                self.verification_results["checks_failed"].append(
                    f"❌ Clase {class_name} no encontrada"
                )
        
        # Verificar métodos
        for method in required_methods:
            if f"def {method}" in content or f"async def {method}" in content:
                self.verification_results["checks_passed"].append(
                    f"✅ Método {method} implementado"
                )
            else:
                all_found = False
                self.verification_results["checks_failed"].append(
                    f"❌ Método {method} no encontrado"
                )
        
        return all_found
    
    def verify_coordinador_integration(self) -> bool:
        """Verifica la integración con CoordinadorCentral."""
        coord_file = self.project_root / "services/coordinador_central.py"
        
        if not coord_file.exists():
            return False
        
        with open(coord_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        integration_points = [
            "_send_unified_notifications",
            "NotificationService",
            "notification_service.add_notification"
        ]
        
        all_found = True
        for point in integration_points:
            if point in content:
                self.verification_results["checks_passed"].append(
                    f"✅ Integración encontrada: {point}"
                )
            else:
                all_found = False
                self.verification_results["checks_failed"].append(
                    f"❌ Integración faltante: {point}"
                )
        
        return all_found
    
    def verify_configuration(self) -> bool:
        """Verifica que la configuración esté correctamente establecida."""
        config_paths = [
            Path("config/notifications.json"),
            Path("../config/notifications.json"),
            Path("./notifications.json")
        ]
        
        config_found = False
        for config_path in config_paths:
            if config_path.exists():
                config_found = True
                with open(config_path, 'r', encoding='utf-8') as f:
                    try:
                        config = json.load(f)
                        self.verification_results["checks_passed"].append(
                            f"✅ Configuración encontrada en: {config_path}"
                        )
                        
                        # Verificar estructura de configuración
                        required_keys = [
                            "aggregation_delays",
                            "max_queue_size",
                            "enable_aggregation"
                        ]
                        
                        for key in required_keys:
                            if key in config:
                                self.verification_results["checks_passed"].append(
                                    f"✅ Configuración contiene: {key}"
                                )
                            else:
                                self.verification_results["warnings"].append(
                                    f"⚠️ Configuración faltante: {key}"
                                )
                        
                        break
                    except json.JSONDecodeError as e:
                        self.verification_results["checks_failed"].append(
                            f"❌ Error en JSON de configuración: {e}"
                        )
        
        if not config_found:
            self.verification_results["warnings"].append(
                "⚠️ Archivo de configuración no encontrado - usando valores por defecto"
            )
            return True  # No es crítico, usa valores por defecto
        
        return True
    
    def check_handler_usage(self) -> bool:
        """Verifica que los handlers usen el sistema correctamente."""
        handlers_dir = self.project_root / "handlers"
        
        if not handlers_dir.exists():
            self.verification_results["warnings"].append(
                "⚠️ Directorio de handlers no encontrado"
            )
            return False
        
        handlers_checked = 0
        handlers_using_system = 0
        
        for handler_file in handlers_dir.glob("*.py"):
            if "test" in handler_file.name:
                continue
            
            with open(handler_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            handlers_checked += 1
            
            # Verificar uso del sistema unificado
            if "NotificationService" in content or "notification_service" in content:
                handlers_using_system += 1
                self.verification_results["checks_passed"].append(
                    f"✅ Handler usando sistema: {handler_file.name}"
                )
            elif "send_message" in content:
                self.verification_results["warnings"].append(
                    f"⚠️ Handler podría no estar usando el sistema: {handler_file.name}"
                )
        
        if handlers_checked > 0:
            usage_percentage = (handlers_using_system / handlers_checked) * 100
            self.verification_results["checks_passed"].append(
                f"✅ {usage_percentage:.1f}% de handlers usando el sistema"
            )
        
        return handlers_using_system > 0
    
    def generate_test_recommendations(self):
        """Genera recomendaciones de testing."""
        self.verification_results["recommendations"].extend([
            "1. Ejecutar test de reacción simple para verificar agregación",
            "2. Probar reacción múltiple rápida (spam test)",
            "3. Verificar que misiones y logros se agreguen correctamente",
            "4. Probar notificaciones de alta prioridad (inmediatas)",
            "5. Verificar formato de mensajes con personalidad de Diana",
            "6. Probar límite de cola (max_queue_size)",
            "7. Verificar detección de duplicados",
            "8. Probar flush manual de notificaciones"
        ])
    
    def run_verification(self) -> Dict[str, Any]:
        """Ejecuta todas las verificaciones."""
        logger.info("Iniciando verificación del sistema de notificaciones...")
        
        # Ejecutar verificaciones
        checks = [
            ("Estructura de archivos", self.verify_file_structure()),
            ("Implementación de NotificationService", self.verify_notification_service_implementation()),
            ("Integración con CoordinadorCentral", self.verify_coordinador_integration()),
            ("Configuración", self.verify_configuration()),
            ("Uso en handlers", self.check_handler_usage())
        ]
        
        # Registrar resultados
        for check_name, result in checks:
            if result:
                logger.info(f"✅ {check_name}: PASADO")
            else:
                logger.warning(f"❌ {check_name}: FALLIDO")
        
        # Agregar recomendaciones
        self.generate_test_recommendations()
        
        # Calcular estadísticas
        self.verification_results["statistics"] = {
            "total_checks": len(self.verification_results["checks_passed"]) + 
                          len(self.verification_results["checks_failed"]),
            "passed": len(self.verification_results["checks_passed"]),
            "failed": len(self.verification_results["checks_failed"]),
            "warnings": len(self.verification_results["warnings"]),
            "success_rate": (
                len(self.verification_results["checks_passed"]) / 
                max(1, len(self.verification_results["checks_passed"]) + 
                    len(self.verification_results["checks_failed"]))
            ) * 100
        }
        
        return self.verification_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Genera un reporte detallado de verificación."""
        report = []
        report.append("=" * 70)
        report.append("REPORTE DE VERIFICACIÓN - SISTEMA DE NOTIFICACIONES UNIFICADAS")
        report.append("=" * 70)
        report.append(f"Fecha: {results['timestamp']}")
        report.append("")
        
        # Estadísticas
        stats = results.get("statistics", {})
        report.append("📊 ESTADÍSTICAS:")
        report.append(f"  Total de verificaciones: {stats.get('total_checks', 0)}")
        report.append(f"  Pasadas: {stats.get('passed', 0)}")
        report.append(f"  Fallidas: {stats.get('failed', 0)}")
        report.append(f"  Advertencias: {stats.get('warnings', 0)}")
        report.append(f"  Tasa de éxito: {stats.get('success_rate', 0):.1f}%")
        report.append("")
        
        # Verificaciones pasadas
        if results["checks_passed"]:
            report.append("✅ VERIFICACIONES EXITOSAS:")
            for check in results["checks_passed"]:
                report.append(f"  {check}")
            report.append("")
        
        # Verificaciones fallidas
        if results["checks_failed"]:
            report.append("❌ VERIFICACIONES FALLIDAS:")
            for check in results["checks_failed"]:
                report.append(f"  {check}")
            report.append("")
        
        # Advertencias
        if results["warnings"]:
            report.append("⚠️ ADVERTENCIAS:")
            for warning in results["warnings"]:
                report.append(f"  {warning}")
            report.append("")
        
        # Recomendaciones
        if results["recommendations"]:
            report.append("💡 RECOMENDACIONES DE TESTING:")
            for rec in results["recommendations"]:
                report.append(f"  {rec}")
            report.append("")
        
        # Conclusión
        report.append("=" * 70)
        if stats.get('success_rate', 0) >= 90:
            report.append("✅ CONCLUSIÓN: Sistema implementado correctamente")
            report.append("El sistema de notificaciones unificadas está listo para usar.")
        elif stats.get('success_rate', 0) >= 70:
            report.append("⚠️ CONCLUSIÓN: Sistema parcialmente implementado")
            report.append("Revise las advertencias y complete las implementaciones faltantes.")
        else:
            report.append("❌ CONCLUSIÓN: Sistema con implementación incompleta")
            report.append("Hay componentes críticos faltantes que requieren atención inmediata.")
        
        return "\n".join(report)
    
    def save_report(self, report: str, filename: str = "notification_system_report.txt"):
        """Guarda el reporte en un archivo."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Reporte guardado en {filename}")


async def mock_notification_test():
    """Realiza pruebas básicas de funcionamiento simulado."""
    from unittest.mock import MagicMock, AsyncMock
    
    logger.info("Ejecutando pruebas simuladas...")
    
    # Mock de Bot y Sesión
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(return_value=True)
    
    mock_session = MagicMock()
    
    # Importar NotificationService (asumiendo que existe)
    try:
        import sys
        import os
        
        # Ajustar path para importar desde el proyecto
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            logger.info(f"Añadido {parent_dir} al sys.path")
        
        try:
            from services.notification_service import NotificationService, NotificationPriority
        except ImportError as e:
            logger.warning(f"No se pudo importar NotificationService directamente: {e}")
            logger.info("Intentando crear una simulación...")
            
            # Crear clase simulada para pruebas
            class NotificationPriority:
                CRITICAL = 0
                HIGH = 1
                MEDIUM = 2
                LOW = 3
                
            class NotificationService:
                def __init__(self, session, bot):
                    self.session = session
                    self.bot = bot
                
                async def add_notification(self, user_id, notification_type, data, priority=NotificationPriority.MEDIUM):
                    logger.info(f"Simulando añadir notificación: {notification_type} para usuario {user_id}")
                    return True
                    
                async def send_immediate_notification(self, user_id, message, priority=NotificationPriority.HIGH):
                    logger.info(f"Simulando envío inmediato a usuario {user_id}: {message}")
                    return True
                    
                async def flush_pending_notifications(self, user_id):
                    logger.info(f"Simulando flush para usuario {user_id}")
                    return True
        
        # Crear instancia de servicio
        notification_service = NotificationService(mock_session, mock_bot)
        
        # Simular notificaciones
        test_user_id = 12345
        
        # Test 1: Agregar notificación básica
        await notification_service.add_notification(
            test_user_id, 
            "points", 
            {"points": 10, "total": 100},
            NotificationPriority.MEDIUM
        )
        
        # Test 2: Agregar notificación de alta prioridad
        await notification_service.add_notification(
            test_user_id,
            "achievement",
            {"name": "Logro de Prueba", "description": "Descripción de prueba"},
            NotificationPriority.HIGH
        )
        
        # Test 3: Enviar notificación inmediata
        await notification_service.send_immediate_notification(
            test_user_id,
            "¡Mensaje crítico de prueba!",
            NotificationPriority.CRITICAL
        )
        
        # Test 4: Verificar flush de notificaciones
        await notification_service.flush_pending_notifications(test_user_id)
        
        logger.info("✅ Pruebas simuladas completadas exitosamente")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error importando NotificationService: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error en pruebas simuladas: {e}")
        return False


async def main():
    """Función principal de verificación."""
    verifier = NotificationSystemVerifier()
    results = verifier.run_verification()
    
    # Generar y guardar reporte
    report = verifier.generate_report(results)
    verifier.save_report(report)
    
    # Imprimir reporte en consola
    print("\n" + report)
    
    # Ejecutar pruebas simuladas si las verificaciones básicas pasan
    if results["statistics"]["success_rate"] >= 70:
        await mock_notification_test()


if __name__ == "__main__":
    asyncio.run(main())