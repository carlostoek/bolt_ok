#!/usr/bin/env python3
"""
Script para testing manual del sistema de evaluación emocional.
Simula interacciones de usuario y muestra responses de Diana/Lucien.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the mybot directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_session_factory
from services.coordinador_central import CoordinadorCentral, AccionUsuario

async def test_emotional_system():
    """
    Test manual del sistema de evaluación emocional.
    """
    print("🧪 TESTING SISTEMA DE EVALUACIÓN EMOCIONAL")
    print("=" * 50)
    
    # Initialize database session
    session_factory = get_session_factory()
    async with session_factory() as session:
        coordinador = CoordinadorCentral(session)
        
        # Test user ID (use your admin ID)
        test_user_id = 1280444712
        
        print(f"🔬 Testing con usuario: {test_user_id}")
        print()
        
        # Test 1: Reacción rápida (impulso auténtico)
        print("📱 TEST 1: REACCIÓN RÁPIDA (Impulso Auténtico)")
        print("-" * 30)
        
        result1 = await coordinador.ejecutar_flujo(
            test_user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001468184215,  # Your VIP channel ID
            reaction_type="❤️"
        )
        
        print("✅ Response:")
        print(f"   Success: {result1['success']}")
        print(f"   Message: {result1['message']}")
        if 'emotional_context' in result1:
            print(f"   Emotional Context: {result1['emotional_context']}")
        print()
        
        # Test 2: Simulación de pausa reflexiva
        print("🤔 TEST 2: REACCIÓN CON PAUSA (Reflexión)")
        print("-" * 30)
        
        # Simulate delay to trigger "pausa reflexiva"
        await asyncio.sleep(2)
        
        result2 = await coordinador.ejecutar_flujo(
            test_user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12346,
            channel_id=-1001468184215,
            reaction_type="🔥"
        )
        
        print("✅ Response:")
        print(f"   Success: {result2['success']}")
        print(f"   Message: {result2['message']}")
        if 'emotional_context' in result2:
            print(f"   Emotional Context: {result2['emotional_context']}")
        print()
        
        # Test 3: Verificar engagement
        print("💫 TEST 3: VERIFICACIÓN ENGAGEMENT DIARIO")
        print("-" * 30)
        
        result3 = await coordinador.ejecutar_flujo(
            test_user_id,
            AccionUsuario.VERIFICAR_ENGAGEMENT
        )
        
        print("✅ Response:")
        print(f"   Success: {result3['success']}")
        print(f"   Message: {result3['message']}")
        if 'emotional_context' in result3:
            print(f"   Emotional Context: {result3['emotional_context']}")
        print()
        
        # Test 4: Participación en canal
        print("👥 TEST 4: PARTICIPACIÓN EN CANAL")
        print("-" * 30)
        
        result4 = await coordinador.ejecutar_flujo(
            test_user_id,
            AccionUsuario.PARTICIPAR_CANAL,
            channel_id=-1001468184215,
            action_type="message"
        )
        
        print("✅ Response:")
        print(f"   Success: {result4['success']}")
        print(f"   Message: {result4['message']}")
        if 'emotional_context' in result4:
            print(f"   Emotional Context: {result4['emotional_context']}")
        print()

        # Test 5: Check emotional analysis service status
        print("🔍 TEST 5: EMOTIONAL ANALYSIS SERVICE STATUS")
        print("-" * 30)
        
        if coordinador.emotional_analysis:
            print("✅ EmotionalAnalysisService: DISPONIBLE")
            
            # Test direct emotional analysis
            try:
                timing_analysis = await coordinador.emotional_analysis.analyze_response_timing(
                    test_user_id, 
                    datetime.now()
                )
                print(f"   Timing Analysis: {timing_analysis}")
                
            except Exception as e:
                print(f"   Error en análisis directo: {str(e)}")
        else:
            print("❌ EmotionalAnalysisService: NO DISPONIBLE")
        
        print()
        
        # Test 6: Character voice service
        print("🎭 TEST 6: CHARACTER VOICE SERVICE")
        print("-" * 30)
        
        if coordinador.character_voice:
            print("✅ CharacterVoiceService: DISPONIBLE")
            
            # Test character selection
            diana_response = coordinador.character_voice.get_diana_response(
                "high_vulnerability", 
                "pausa_reflexiva"
            )
            print(f"   Diana Response: {diana_response}")
            
            lucien_response = coordinador.character_voice.get_lucien_response(
                "low_vulnerability",
                "impulso_autentico" 
            )
            print(f"   Lucien Response: {lucien_response}")
        else:
            print("❌ CharacterVoiceService: NO DISPONIBLE")
            
        print()
        print("🎉 TESTING COMPLETADO")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_emotional_system())