#!/usr/bin/env python3
"""
Menu Validation Test Script for Bolt OK Telegram Bot
====================================================

This script validates that all menu buttons have corresponding callback handlers
and generates a detailed HTML report of the admin menu system status.

Usage: python test_menu_validation.py
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallbackMapping:
    """Represents a callback and its handler mapping"""
    callback_data: str
    keyboard_file: str
    handler_file: str = None
    line_number: int = None
    is_connected: bool = False
    is_dynamic: bool = False


class MenuValidator:
    """Validates admin menu buttons and their callback handlers"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.keyboards_path = self.base_path / "mybot" / "keyboards"
        self.handlers_path = self.base_path / "mybot" / "handlers"
        
        self.callback_mappings: List[CallbackMapping] = []
        self.admin_keyboards: Dict[str, Set[str]] = {}
        self.admin_handlers: Dict[str, Set[str]] = {}
        
    def extract_callbacks_from_keyboard(self, file_path: Path) -> Set[str]:
        """Extract callback_data values from a keyboard file"""
        callbacks = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find callback_data patterns
            patterns = [
                r'callback_data\s*=\s*["\']([^"\']+)["\']',  # Static callbacks
                r'callback_data\s*=\s*f["\']([^"\']*\{[^}]*\}[^"\']*)["\']',  # f-strings
                r'callback_data\s*=\s*["\']([^"\']*\{[^}]*\}[^"\']*)["\']',  # Format strings
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Handle dynamic callbacks
                    if '{' in match:
                        # Extract the base pattern
                        base_pattern = re.sub(r'\{[^}]*\}', '*', match)
                        callbacks.add(base_pattern)
                    else:
                        callbacks.add(match)
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return callbacks
    
    def extract_handlers_from_file(self, file_path: Path) -> Set[str]:
        """Extract callback handlers from a handler file"""
        handlers = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find callback_query handlers with improved patterns
            patterns = [
                # Decorator patterns: @router.callback_query(F.data == "value")
                r'@\w+\.callback_query\(\s*F\.data\s*==\s*["\']([^"\']+)["\']',
                # Decorator patterns: @router.callback_query(text="value")
                r'@\w+\.callback_query\([^)]*text\s*=\s*["\']([^"\']+)["\']',
                # Function level patterns: F.data == "value"
                r'F\.data\s*==\s*["\']([^"\']+)["\']',
                # Manual checks in functions
                r'callback_query\.data\s*==\s*["\']([^"\']+)["\']',
                r'callback\.data\s*==\s*["\']([^"\']+)["\']',
                # startswith patterns
                r'callback_query\.data\.startswith\(["\']([^"\']+)["\']',
                r'callback\.data\.startswith\(["\']([^"\']+)["\']',
                # Pattern matching in if statements
                r'if\s+["\']([^"\']+)["\']\s*==\s*callback_query\.data',
                r'if\s+["\']([^"\']+)["\']\s*==\s*callback\.data',
                # contains patterns
                r'["\']([^"\']+)["\']\s+in\s+callback_query\.data',
                r'["\']([^"\']+)["\']\s+in\s+callback\.data',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                handlers.update(matches)
                
            # Also look for dynamic pattern handlers
            dynamic_patterns = [
                r'callback_query\.data\.startswith\(["\']([^"\']*)["\']',
                r'callback\.data\.startswith\(["\']([^"\']*)["\']',
            ]
            
            for pattern in dynamic_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match and len(match) > 2:  # Only meaningful prefixes
                        handlers.add(match + "*")  # Mark as dynamic
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return handlers
    
    def scan_admin_keyboards(self):
        """Scan all admin keyboard files"""
        print("📋 Scanning admin keyboard files...")
        admin_kb_files = list(self.keyboards_path.glob("admin*.py"))
        
        for kb_file in admin_kb_files:
            callbacks = self.extract_callbacks_from_keyboard(kb_file)
            self.admin_keyboards[kb_file.name] = callbacks
            
            for callback in callbacks:
                mapping = CallbackMapping(
                    callback_data=callback,
                    keyboard_file=kb_file.name,
                    is_dynamic='*' in callback
                )
                self.callback_mappings.append(mapping)
                
        print(f"✅ Found {len(admin_kb_files)} admin keyboard files")
        print(f"✅ Extracted {sum(len(cbs) for cbs in self.admin_keyboards.values())} callback definitions")
    
    def scan_admin_handlers(self):
        """Scan all admin handler files"""
        print("\n🔧 Scanning admin handler files...")
        
        # Scan main admin handlers
        admin_handler_files = list(self.handlers_path.glob("admin*.py"))
        
        # Scan admin subdirectory
        admin_subdir = self.handlers_path / "admin"
        if admin_subdir.exists():
            admin_handler_files.extend(list(admin_subdir.glob("*.py")))
        
        for handler_file in admin_handler_files:
            handlers = self.extract_handlers_from_file(handler_file)
            relative_path = str(handler_file.relative_to(self.handlers_path))
            self.admin_handlers[relative_path] = handlers
            
        print(f"✅ Found {len(admin_handler_files)} admin handler files")
        print(f"✅ Extracted {sum(len(handlers) for handlers in self.admin_handlers.values())} handler definitions")
    
    def match_callbacks_to_handlers(self):
        """Match callbacks to their handlers"""
        print("\n🔗 Matching callbacks to handlers...")
        
        # Flatten all handlers with their file info
        all_handlers = {}
        for file_name, handlers in self.admin_handlers.items():
            for handler in handlers:
                all_handlers[handler] = file_name
        
        # Match each callback
        for mapping in self.callback_mappings:
            callback = mapping.callback_data
            
            # Exact match
            if callback in all_handlers:
                mapping.handler_file = all_handlers[callback]
                mapping.is_connected = True
            # Pattern match for dynamic callbacks
            elif mapping.is_dynamic:
                base_pattern = callback.replace('*', '')
                for handler in all_handlers.keys():
                    if handler.startswith(base_pattern):
                        mapping.handler_file = all_handlers[handler]
                        mapping.is_connected = True
                        break
            # Partial match for complex patterns
            else:
                for handler in all_handlers.keys():
                    if callback in handler or handler in callback:
                        mapping.handler_file = all_handlers[handler]
                        mapping.is_connected = True
                        break
    
    def generate_statistics(self) -> Dict:
        """Generate validation statistics"""
        connected = sum(1 for m in self.callback_mappings if m.is_connected)
        disconnected = len(self.callback_mappings) - connected
        
        # Find orphaned handlers
        used_handlers = {m.handler_file for m in self.callback_mappings if m.is_connected}
        all_handler_files = set(self.admin_handlers.keys())
        orphaned_files = all_handler_files - used_handlers
        
        return {
            'total_callbacks': len(self.callback_mappings),
            'connected_callbacks': connected,
            'disconnected_callbacks': disconnected,
            'connection_rate': (connected / len(self.callback_mappings) * 100) if self.callback_mappings else 0,
            'total_keyboard_files': len(self.admin_keyboards),
            'total_handler_files': len(self.admin_handlers),
            'orphaned_handler_files': len(orphaned_files),
            'orphaned_files_list': list(orphaned_files)
        }
    
    def generate_json_report(self) -> Dict:
        """Generate comprehensive JSON report"""
        stats = self.generate_statistics()
        
        # Separate connected and disconnected
        connected_mappings = [m for m in self.callback_mappings if m.is_connected]
        disconnected_mappings = [m for m in self.callback_mappings if not m.is_connected]
        
        # Group by keyboard file
        keyboard_groups = {}
        for mapping in self.callback_mappings:
            if mapping.keyboard_file not in keyboard_groups:
                keyboard_groups[mapping.keyboard_file] = {
                    "total_callbacks": 0,
                    "connected_callbacks": 0,
                    "disconnected_callbacks": 0,
                    "callbacks": []
                }
            
            keyboard_groups[mapping.keyboard_file]["total_callbacks"] += 1
            if mapping.is_connected:
                keyboard_groups[mapping.keyboard_file]["connected_callbacks"] += 1
            else:
                keyboard_groups[mapping.keyboard_file]["disconnected_callbacks"] += 1
            
            keyboard_groups[mapping.keyboard_file]["callbacks"].append({
                "callback_data": mapping.callback_data,
                "handler_file": mapping.handler_file,
                "is_connected": mapping.is_connected,
                "is_dynamic": mapping.is_dynamic,
                "priority": "high" if "admin_" in mapping.callback_data else "medium"
            })
        
        # Handler files analysis
        handler_files_analysis = {}
        for file_name, handlers in self.admin_handlers.items():
            used_handlers = [m.callback_data for m in self.callback_mappings 
                           if m.handler_file == file_name and m.is_connected]
            
            handler_files_analysis[file_name] = {
                "total_handlers": len(handlers),
                "used_handlers": len(used_handlers),
                "unused_handlers": len(handlers) - len(used_handlers),
                "handlers_list": list(handlers),
                "used_handlers_list": used_handlers
            }
        
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "script_version": "1.0.0",
                "analysis_type": "admin_menu_validation"
            },
            "summary": {
                "total_callbacks": stats['total_callbacks'],
                "connected_callbacks": stats['connected_callbacks'],
                "disconnected_callbacks": stats['disconnected_callbacks'],
                "connection_rate_percentage": round(stats['connection_rate'], 2),
                "total_keyboard_files": stats['total_keyboard_files'],
                "total_handler_files": stats['total_handler_files'],
                "orphaned_handler_files": stats['orphaned_handler_files']
            },
            "keyboard_files": keyboard_groups,
            "handler_files": handler_files_analysis,
            "connected_callbacks": [
                {
                    "callback_data": m.callback_data,
                    "keyboard_file": m.keyboard_file,
                    "handler_file": m.handler_file,
                    "is_dynamic": m.is_dynamic
                } for m in connected_mappings
            ],
            "disconnected_callbacks": [
                {
                    "callback_data": m.callback_data,
                    "keyboard_file": m.keyboard_file,
                    "is_dynamic": m.is_dynamic,
                    "priority": "high" if "admin_" in m.callback_data else "medium"
                } for m in disconnected_mappings
            ],
            "orphaned_files": stats['orphaned_files_list'],
            "recommendations": {
                "critical_actions": [
                    "Implement missing handlers for disconnected callbacks",
                    "Verify callback naming consistency",
                    "Review routing logic for pattern mismatches",
                    "Test all admin menu functionality"
                ],
                "high_priority_callbacks": [
                    m.callback_data for m in disconnected_mappings 
                    if "admin_" in m.callback_data
                ],
                "improvement_suggestions": [
                    f"Connection rate is {stats['connection_rate']:.1f}% - {'Excellent!' if stats['connection_rate'] >= 90 else 'Good but can be improved' if stats['connection_rate'] >= 70 else 'Needs attention'}",
                    f"Focus on {stats['disconnected_callbacks']} disconnected callbacks",
                    f"Review {stats['orphaned_handler_files']} orphaned handler files"
                ]
            }
        }

    def generate_html_report(self) -> str:
        """Generate comprehensive HTML report"""
        stats = self.generate_statistics()
        
        # Separate connected and disconnected
        connected_mappings = [m for m in self.callback_mappings if m.is_connected]
        disconnected_mappings = [m for m in self.callback_mappings if not m.is_connected]
        
        # Group by keyboard file
        keyboard_groups = {}
        for mapping in self.callback_mappings:
            if mapping.keyboard_file not in keyboard_groups:
                keyboard_groups[mapping.keyboard_file] = []
            keyboard_groups[mapping.keyboard_file].append(mapping)
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Validación de Menús - Bolt OK Bot</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            padding: 30px; 
            background: #f8f9fa;
        }}
        .stat-card {{ 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .connected {{ color: #27ae60; }}
        .disconnected {{ color: #e74c3c; }}
        .warning {{ color: #f39c12; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px; 
            margin-bottom: 20px;
        }}
        .keyboard-group {{ 
            background: #f8f9fa; 
            border-radius: 10px; 
            padding: 20px; 
            margin-bottom: 20px; 
            border-left: 5px solid #3498db;
        }}
        .keyboard-title {{ 
            font-weight: bold; 
            color: #2c3e50; 
            margin-bottom: 15px; 
            font-size: 1.2em;
        }}
        .callback-item {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 10px; 
            margin: 5px 0; 
            border-radius: 5px; 
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .callback-name {{ font-family: 'Courier New', monospace; font-weight: bold; }}
        .callback-status {{ 
            padding: 5px 15px; 
            border-radius: 20px; 
            font-size: 0.8em; 
            font-weight: bold;
        }}
        .status-connected {{ background: #d4edda; color: #155724; }}
        .status-disconnected {{ background: #f8d7da; color: #721c24; }}
        .status-dynamic {{ background: #fff3cd; color: #856404; }}
        .handler-info {{ font-size: 0.9em; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .timestamp {{ 
            text-align: center; 
            color: #666; 
            font-size: 0.9em; 
            padding: 20px; 
            border-top: 1px solid #eee; 
        }}
        .alert {{ 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0; 
        }}
        .alert-warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }}
        .alert-danger {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
        .alert-success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Reporte de Validación de Menús</h1>
            <p>Sistema de Administración - Bolt OK Telegram Bot</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number connected">{stats['connected_callbacks']}</div>
                <div class="stat-label">Callbacks Conectados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number disconnected">{stats['disconnected_callbacks']}</div>
                <div class="stat-label">Callbacks Desconectados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['connection_rate']:.1f}%</div>
                <div class="stat-label">Tasa de Conexión</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['total_keyboard_files']}</div>
                <div class="stat-label">Archivos de Teclado</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['total_handler_files']}</div>
                <div class="stat-label">Archivos de Handlers</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{stats['orphaned_handler_files']}</div>
                <div class="stat-label">Handlers Huérfanos</div>
            </div>
        </div>
        
        <div class="content">
"""

        # Connection status alerts
        if stats['disconnected_callbacks'] > 0:
            html += f"""
            <div class="alert alert-warning">
                <strong>⚠️ Atención:</strong> Se encontraron {stats['disconnected_callbacks']} callbacks sin handlers correspondientes. 
                Esto puede causar errores cuando los usuarios interactúen con esos botones.
            </div>
"""

        if stats['connection_rate'] >= 90:
            html += """
            <div class="alert alert-success">
                <strong>✅ Excelente:</strong> La mayoría de los callbacks están correctamente conectados.
            </div>
"""
        elif stats['connection_rate'] >= 70:
            html += """
            <div class="alert alert-warning">
                <strong>⚠️ Advertencia:</strong> Algunos callbacks necesitan atención.
            </div>
"""
        else:
            html += """
            <div class="alert alert-danger">
                <strong>🚨 Crítico:</strong> Muchos callbacks están desconectados. Se requiere atención inmediata.
            </div>
"""

        # Keyboard groups section
        html += """
            <div class="section">
                <h2>📋 Estado por Archivo de Teclado</h2>
"""

        for keyboard_file, mappings in sorted(keyboard_groups.items()):
            connected_count = sum(1 for m in mappings if m.is_connected)
            total_count = len(mappings)
            
            html += f"""
                <div class="keyboard-group">
                    <div class="keyboard-title">
                        📄 {keyboard_file} 
                        <span style="color: #666; font-size: 0.9em;">
                            ({connected_count}/{total_count} conectados)
                        </span>
                    </div>
"""
            
            for mapping in sorted(mappings, key=lambda x: (not x.is_connected, x.callback_data)):
                status_class = "status-connected" if mapping.is_connected else "status-disconnected"
                status_text = "✅ Conectado" if mapping.is_connected else "❌ Desconectado"
                
                if mapping.is_dynamic:
                    status_class = "status-dynamic"
                    status_text = "🔄 Dinámico"
                
                handler_info = ""
                if mapping.handler_file:
                    handler_info = f"<div class='handler-info'>📂 {mapping.handler_file}</div>"
                
                html += f"""
                    <div class="callback-item">
                        <div>
                            <div class="callback-name">{mapping.callback_data}</div>
                            {handler_info}
                        </div>
                        <div class="callback-status {status_class}">{status_text}</div>
                    </div>
"""
            
            html += "</div>"

        # Disconnected callbacks table
        if disconnected_mappings:
            html += """
            <div class="section">
                <h2>❌ Callbacks Desconectados (Requieren Atención)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Callback Data</th>
                            <th>Archivo de Teclado</th>
                            <th>Tipo</th>
                            <th>Prioridad</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for mapping in sorted(disconnected_mappings, key=lambda x: x.callback_data):
                priority = "🔴 Alta" if "admin_" in mapping.callback_data else "🟡 Media"
                callback_type = "🔄 Dinámico" if mapping.is_dynamic else "📍 Estático"
                
                html += f"""
                        <tr>
                            <td><code>{mapping.callback_data}</code></td>
                            <td>{mapping.keyboard_file}</td>
                            <td>{callback_type}</td>
                            <td>{priority}</td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
"""

        # Summary and recommendations
        html += """
            <div class="section">
                <h2>📊 Resumen y Recomendaciones</h2>
"""

        if disconnected_mappings:
            html += """
                <h3>🔧 Acciones Recomendadas:</h3>
                <ul>
                    <li><strong>Implementar handlers faltantes:</strong> Los callbacks desconectados necesitan handlers correspondientes.</li>
                    <li><strong>Verificar nombres de callbacks:</strong> Algunos pueden tener errores tipográficos.</li>
                    <li><strong>Revisar lógica de routing:</strong> Algunos handlers pueden existir pero usar patrones diferentes.</li>
                    <li><strong>Testear funcionalidad:</strong> Probar todos los botones del menú de administración.</li>
                </ul>
"""

        if stats['orphaned_handler_files']:
            html += f"""
                <h3>🗂️ Archivos de Handlers sin Usar:</h3>
                <ul>
"""
            for orphaned_file in stats['orphaned_files_list']:
                html += f"                    <li><code>{orphaned_file}</code></li>"
            
            html += """
                </ul>
                <p><em>Estos archivos pueden contener handlers obsoletos o usar patrones de naming diferentes.</em></p>
"""

        html += f"""
                <h3>📈 Estado General:</h3>
                <p>El sistema de menús tiene una tasa de conexión del <strong>{stats['connection_rate']:.1f}%</strong>. 
                {'🎉 ¡Excelente trabajo!' if stats['connection_rate'] >= 90 else 
                 '👍 Buen estado, pero hay mejoras posibles.' if stats['connection_rate'] >= 70 else 
                 '⚠️ Necesita atención para evitar errores de usuario.'}</p>
            </div>
        </div>
        
        <div class="timestamp">
            📅 Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def run_validation(self):
        """Run complete menu validation"""
        print("🚀 Iniciando validación de menús de administración...")
        print("=" * 50)
        
        self.scan_admin_keyboards()
        self.scan_admin_handlers()
        self.match_callbacks_to_handlers()
        
        stats = self.generate_statistics()
        
        print(f"\n📊 RESULTADOS DE VALIDACIÓN:")
        print(f"📋 Total de callbacks encontrados: {stats['total_callbacks']}")
        print(f"✅ Callbacks conectados: {stats['connected_callbacks']}")
        print(f"❌ Callbacks desconectados: {stats['disconnected_callbacks']}")
        print(f"📈 Tasa de conexión: {stats['connection_rate']:.1f}%")
        
        # Generate reports
        html_content = self.generate_html_report()
        json_content = self.generate_json_report()
        
        # Save HTML report
        html_report_path = self.base_path / "menu_validation_report.html"
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save JSON report
        json_report_path = self.base_path / "menu_validation_report.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte HTML generado: {html_report_path}")
        print(f"📄 Reporte JSON generado: {json_report_path}")
        
        # Show disconnected callbacks
        disconnected = [m for m in self.callback_mappings if not m.is_connected]
        if disconnected:
            print(f"\n❌ CALLBACKS DESCONECTADOS ({len(disconnected)}):")
            for mapping in disconnected:
                print(f"  • {mapping.callback_data} (en {mapping.keyboard_file})")
        
        print(f"\n{'✅ VALIDACIÓN COMPLETADA EXITOSAMENTE' if stats['connection_rate'] >= 90 else '⚠️ VALIDACIÓN COMPLETADA CON ADVERTENCIAS'}")
        return stats


def main():
    """Main function"""
    validator = MenuValidator()
    try:
        stats = validator.run_validation()
        return 0 if stats['connection_rate'] >= 90 else 1
    except Exception as e:
        print(f"❌ Error durante la validación: {e}")
        return 1


if __name__ == "__main__":
    exit(main())