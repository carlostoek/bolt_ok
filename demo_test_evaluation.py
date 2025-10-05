#!/usr/bin/env python3
"""
Demo del Sistema de Test de Evaluación Emocional
Muestra el funcionamiento del sistema completamente aislado.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

# Simulación de clases para demostración
class MockSession:
    """Mock de sesión de base de datos para demo."""
    pass

class MockCoordinadorCentral:
    """Mock del CoordinadorCentral para demostrar el flujo."""
    
    def __init__(self, session):
        self.session = session
        # Simular servicios disponibles
        self.emotional_analysis = True
        self.character_voice = True
    
    async def ejecutar_flujo(self, user_id: int, accion, **kwargs) -> Dict[str, Any]:
        """Simula el flujo de evaluación emocional."""
        action_type = kwargs.get("action_type", "start_test")
        
        if action_type == "start_test":
            return {
                "success": True,
                "action": "test_started",
                "message": "¡Bienvenido al test de evaluación emocional! Descubre tu perfil único.",
                "test_active": True
            }
        
        elif action_type == "process_response":
            response_time = kwargs.get("response_time", 0)
            option_selected = kwargs.get("option_selected", "unknown")
            
            # Clasificar usuario según timing
            user_type = self._classify_user_by_response_time(response_time)
            
            # Generar mensaje personalizado
            profile_message = self._generate_profile_message(user_type)
            
            return {
                "success": True,
                "action": "test_completed",
                "message": f"Diana: Tu respuesta revela tu naturaleza auténtica...\n\n{profile_message}",
                "user_type": user_type,
                "response_time": response_time,
                "option_selected": option_selected,
                "emotional_context": {
                    "success": True,
                    "timing_pattern": "rapid_fire" if response_time < 5 else "normal",
                    "emotional_indicators": ["high_engagement"] if response_time < 3 else ["deliberate_response"]
                }
            }
    
    def _classify_user_by_response_time(self, response_time: float) -> str:
        """Clasifica al usuario según su tiempo de respuesta."""
        if response_time < 3:
            return "impulso_autentico"
        elif response_time <= 15:
            return "pausa_reflexiva"
        elif response_time <= 60:
            return "contemplacion"
        else:
            return "abandono"
    
    def _generate_profile_message(self, user_type: str) -> str:
        """Genera mensaje del perfil detectado."""
        messages = {
            "impulso_autentico": (
                "🔥 **IMPULSO AUTÉNTICO**\n\n"
                "Respondes desde el corazón, sin filtros. Tu naturaleza espontánea "
                "te lleva a conectar de manera genuina y directa. Eres de quienes "
                "viven el momento con intensidad."
            ),
            "pausa_reflexiva": (
                "💭 **PAUSA REFLEXIVA**\n\n"
                "Tomas tiempo para procesar antes de responder. Esta cualidad te "
                "permite tomar decisiones más conscientes y conectar de manera "
                "profunda con tus emociones."
            ),
            "contemplacion": (
                "🌙 **CONTEMPLACIÓN**\n\n"
                "Tu mente busca comprender profundamente antes de actuar. Este "
                "enfoque reflexivo te permite acceder a capas más profundas de "
                "comprensión y conexión emocional."
            ),
            "abandono": (
                "🌊 **ABANDONO**\n\n"
                "Tiendes a alejarte cuando sientes presión. Esto puede indicar "
                "que necesitas espacios seguros para explorar y conectar a tu "
                "propio ritmo, sin prisas."
            )
        }
        return messages.get(user_type, messages["pausa_reflexiva"])

# Simulador de tipos de usuario
async def simulate_user_responses():
    """Simula diferentes tipos de respuesta de usuarios."""
    session = MockSession()
    coordinador = MockCoordinadorCentral(session)
    
    print("=" * 60)
    print("🧠 DEMO: SISTEMA DE TEST DE EVALUACIÓN EMOCIONAL")
    print("=" * 60)
    print()
    
    # Simular diferentes usuarios
    usuarios_test = [
        {"id": 1001, "name": "Usuario Impulsivo", "delay": 1.5},
        {"id": 1002, "name": "Usuario Reflexivo", "delay": 8.0},
        {"id": 1003, "name": "Usuario Contemplativo", "delay": 35.0},
        {"id": 1004, "name": "Usuario que Abandona", "delay": 75.0},
    ]
    
    for usuario in usuarios_test:
        print(f"👤 {usuario['name']} (ID: {usuario['id']})")
        print("-" * 50)
        
        # 1. Iniciar test
        result_start = await coordinador.ejecutar_flujo(
            usuario['id'], 
            "TEST_EVALUACION_EMOCIONAL",
            action_type="start_test"
        )
        
        if result_start["success"]:
            print(f"📋 Inicio: {result_start['message']}")
            print(f"⏰ Simulando respuesta en {usuario['delay']} segundos...")
            
            # Simular tiempo de respuesta
            await asyncio.sleep(0.1)  # Simular brevemente para demo
            
            # 2. Procesar respuesta
            result_response = await coordinador.ejecutar_flujo(
                usuario['id'],
                "TEST_EVALUACION_EMOCIONAL", 
                action_type="process_response",
                response_time=usuario['delay'],
                option_selected="option_a"
            )
            
            if result_response["success"]:
                print(f"📊 Resultado:")
                print(f"   • Tipo: {result_response['user_type']}")
                print(f"   • Tiempo: {result_response['response_time']} segundos")
                print(f"📝 Mensaje:")
                for line in result_response['message'].split('\n'):
                    print(f"   {line}")
        
        print()
        await asyncio.sleep(0.5)  # Pausa entre usuarios

async def demonstrate_integration():
    """Demuestra la integración con el sistema existente."""
    print("=" * 60)
    print("🔗 INTEGRACIÓN CON SISTEMA EXISTENTE")
    print("=" * 60)
    print()
    
    print("✅ COMPONENTES IMPLEMENTADOS:")
    print("   • CoordinadorCentral: Enum TEST_EVALUACION_EMOCIONAL agregado")
    print("   • Flujo _flujo_test_evaluacion_emocional() implementado")
    print("   • EmotionalAnalysisService: Análisis de timing integrado")
    print("   • CharacterVoiceService: Respuestas auténticas de Diana")
    print()
    
    print("✅ ARCHIVOS CREADOS:")
    print("   • handlers/test_evaluation_handler.py - Handler completamente aislado")
    print("   • keyboards/test_evaluation_kb.py - Teclados para el test")
    print()
    
    print("✅ COMANDO DISPONIBLE:")
    print("   /test_evaluacion - Inicia el test emocional")
    print()
    
    print("✅ FLUJO DE USUARIO:")
    print("   1. Usuario ejecuta /test_evaluacion")
    print("   2. Sistema muestra explicación y botón de confirmación")
    print("   3. Usuario ve menú con opciones A, B, C, y 'Ver perfil'")
    print("   4. Sistema mide timing de respuesta (< 3s, 3-15s, 15-60s, > 60s)")
    print("   5. EmotionalAnalysisService analiza patrones de comportamiento")
    print("   6. Diana responde con perfil personalizado y recomendaciones")
    print("   7. Usuario puede repetir test o finalizar")
    print()
    
    print("✅ CARACTERÍSTICAS TÉCNICAS:")
    print("   • Completamente aislado - no afecta funcionalidad existente")
    print("   • Integración through CoordinadorCentral - arquitectura consistente")
    print("   • Análisis emocional REAL usando EmotionalAnalysisService")
    print("   • Graceful degradation si servicios no están disponibles")
    print("   • Cache temporal para sesiones (auto-cleanup)")
    print("   • Logging detallado para monitoring")
    print()

def show_implementation_summary():
    """Muestra resumen de la implementación."""
    print("=" * 60)
    print("📋 RESUMEN DE IMPLEMENTACIÓN")
    print("=" * 60)
    print()
    
    print("🎯 OBJETIVO CUMPLIDO:")
    print("   ✅ Comando /test_evaluacion implementado")
    print("   ✅ UI con menú de 4 botones (A, B, C, Ver perfil)")
    print("   ✅ Análisis de timing de respuesta integrado")
    print("   ✅ CoordinadorCentral activando EmotionalAnalysisService")
    print("   ✅ Sistema reporta perfil según timing:")
    print("       • < 3s = Impulso Auténtico")
    print("       • 3-15s = Pausa Reflexiva") 
    print("       • 15-60s = Contemplación")
    print("       • > 60s = Abandono")
    print()
    
    print("🏗️ ARQUITECTURA:")
    print("   • Handler aislado: handlers/test_evaluation_handler.py")
    print("   • Keyboard dedicado: keyboards/test_evaluation_kb.py")
    print("   • Integración: services/coordinador_central.py")
    print("   • Enum: AccionUsuario.TEST_EVALUACION_EMOCIONAL")
    print("   • Registro: bot.py (router incluido)")
    print()
    
    print("🔒 AISLAMIENTO GARANTIZADO:")
    print("   • Sin modificación de handlers existentes")
    print("   • Sin modificación de servicios existentes")
    print("   • Solo adiciones a CoordinadorCentral")
    print("   • Graceful degradation en caso de errores")
    print()

async def main():
    """Función principal del demo."""
    print("🤖 DianaBot - Sistema de Test de Evaluación Emocional")
    print()
    
    # Simular respuestas de usuarios
    await simulate_user_responses()
    
    # Mostrar integración
    await demonstrate_integration()
    
    # Resumen de implementación
    show_implementation_summary()
    
    print("=" * 60)
    print("🎉 SISTEMA LISTO PARA USAR")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())