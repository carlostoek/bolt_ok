"""
Script para migrar el código existente al nuevo sistema de notificaciones unificadas.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple

class NotificationMigrator:
    """Migrador automático al sistema de notificaciones unificadas."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.changes_made = []
        
    def find_send_message_calls(self) -> List[Tuple[Path, int, str]]:
        """Encuentra todas las llamadas directas a bot.send_message."""
        matches = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "test" in str(py_file) or "migration" in str(py_file):
                continue
                
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                if 'bot.send_message' in line or 'safe_send_message' in line:
                    matches.append((py_file, i, line.strip()))
        
        return matches
    
    def analyze_message_patterns(self, matches: List[Tuple[Path, int, str]]) -> dict:
        """Analiza patrones de mensajes para clasificarlos."""
        patterns = {
            'points': [],
            'missions': [],
            'achievements': [],
            'hints': [],
            'errors': [],
            'other': []
        }
        
        for file_path, line_num, line in matches:
            if 'besitos' in line or 'puntos' in line or 'points' in line:
                patterns['points'].append((file_path, line_num))
            elif 'misión' in line or 'mission' in line:
                patterns['missions'].append((file_path, line_num))
            elif 'logro' in line or 'achievement' in line:
                patterns['achievements'].append((file_path, line_num))
            elif 'pista' in line or 'hint' in line:
                patterns['hints'].append((file_path, line_num))
            elif 'error' in line or 'Error' in line:
                patterns['errors'].append((file_path, line_num))
            else:
                patterns['other'].append((file_path, line_num))
        
        return patterns
    
    def generate_migration_report(self) -> str:
        """Genera un reporte de migración."""
        matches = self.find_send_message_calls()
        patterns = self.analyze_message_patterns(matches)
        
        report = []
        report.append("=" * 60)
        report.append("REPORTE DE MIGRACIÓN - SISTEMA DE NOTIFICACIONES UNIFICADAS")
        report.append("=" * 60)
        report.append(f"\nTotal de llamadas a migrar: {len(matches)}\n")
        
        report.append("Clasificación por tipo:")
        for pattern_type, locations in patterns.items():
            report.append(f"  - {pattern_type}: {len(locations)} ocurrencias")
        
        report.append("\n" + "=" * 60)
        report.append("ARCHIVOS A MODIFICAR:")
        report.append("=" * 60)
        
        files_to_modify = set()
        for file_path, _, _ in matches:
            files_to_modify.add(file_path)
        
        for file_path in sorted(files_to_modify):
            count = sum(1 for f, _, _ in matches if f == file_path)
            report.append(f"  {file_path}: {count} cambios necesarios")
        
        report.append("\n" + "=" * 60)
        report.append("RECOMENDACIONES:")
        report.append("=" * 60)
        
        report.append("""
1. Actualizar handlers de reacciones primero
2. Migrar sistema de misiones después
3. Actualizar sistema de logros
4. Probar cada módulo individualmente
5. Ejecutar suite de tests completa
        """)
        
        return "\n".join(report)
    
    def create_migration_checklist(self) -> str:
        """Crea una checklist de migración."""
        checklist = """
# CHECKLIST DE MIGRACIÓN - NOTIFICACIONES UNIFICADAS

## Fase 1: Preparación
- [ ] Backup del código actual
- [ ] Crear branch de migración
- [ ] Instalar dependencias nuevas
- [ ] Configurar archivo notifications.json

## Fase 2: Implementación Base
- [ ] Implementar NotificationService mejorado
- [ ] Actualizar CoordinadorCentral
- [ ] Crear NotificationConfig
- [ ] Añadir tests unitarios

## Fase 3: Migración de Handlers
- [ ] native_reaction_handler.py
- [ ] reaction_handler.py
- [ ] reaction_callback.py
- [ ] mission_handler.py
- [ ] achievement_handler.py

## Fase 4: Migración de Servicios
- [ ] mission_service.py
- [ ] point_service.py
- [ ] narrative_service.py
- [ ] channel_engagement_service.py

## Fase 5: Testing
- [ ] Tests unitarios del NotificationService
- [ ] Tests de integración con CoordinadorCentral
- [ ] Tests end-to-end de flujos completos
- [ ] Tests de carga y rendimiento

## Fase 6: Deployment
- [ ] Review de código
- [ ] Documentación actualizada
- [ ] Configuración de producción
- [ ] Monitoreo activado
- [ ] Rollback plan preparado

## Fase 7: Post-Deployment
- [ ] Monitorear métricas de engagement
- [ ] Recopilar feedback de usuarios
- [ ] Ajustar delays de agregación
- [ ] Optimizar formatos de mensaje
        """
        
        return checklist


if __name__ == "__main__":
    # Ejecutar análisis de migración
    migrator = NotificationMigrator("./mybot")
    
    # Generar reporte
    report = migrator.generate_migration_report()
    with open("migration_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(report)
    
    # Generar checklist
    checklist = migrator.create_migration_checklist()
    with open("migration_checklist.md", "w", encoding="utf-8") as f:
        f.write(checklist)
    
    print("\n✅ Archivos de migración generados:")
    print("  - migration_report.txt")
    print("  - migration_checklist.md")