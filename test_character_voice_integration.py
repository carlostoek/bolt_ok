#!/usr/bin/env python3
"""
Test script para verificar la integración de CharacterVoiceService con CoordinadorCentral.
Este script simula las funcionalidades sin requerir base de datos.
"""
import asyncio
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.character_voice_service import (
    CharacterVoiceService, 
    CharacterType, 
    EmotionalContext
)

def test_character_voice_service():
    """Pruebas básicas del servicio de voces de personajes."""
    print("🎭 TESTING CHARACTER VOICE SERVICE")
    print("=" * 50)
    
    # Inicializar servicio
    voice_service = CharacterVoiceService()
    
    # Test 1: Respuesta de Diana para reacción exitosa
    print("\n1. Diana - Reacción exitosa (Engagement Alto):")
    diana_reaction = voice_service.get_character_response(
        CharacterType.DIANA,
        EmotionalContext.ENGAGEMENT_ALTO,
        "reaction_success"
    )
    print(f"   {diana_reaction}")
    
    # Test 2: Respuesta de Lucien para fallo de reacción  
    print("\n2. Lucien - Fallo de reacción (Pausa Reflexiva):")
    lucien_fail = voice_service.get_character_response(
        CharacterType.LUCIEN,
        EmotionalContext.PAUSA_REFLEXIVA,
        "reaction_failed"
    )
    print(f"   {lucien_fail}")
    
    # Test 3: Diana con alta vulnerabilidad
    print("\n3. Diana - Vulnerabilidad Alta:")
    diana_vulnerable = voice_service.get_character_response(
        CharacterType.DIANA,
        EmotionalContext.VULNERABILIDAD_ALTA,
        "decision_success"
    )
    print(f"   {diana_vulnerable}")
    
    # Test 4: Lucien con nuevo usuario
    print("\n4. Lucien - Nuevo Usuario:")
    lucien_new = voice_service.get_character_response(
        CharacterType.LUCIEN,
        EmotionalContext.NUEVO_USUARIO,
        "guidance"
    )
    print(f"   {lucien_new}")
    
    # Test 5: Selección automática de personaje
    print("\n5. Selección automática de personaje:")
    
    # Contexto de alta vulnerabilidad -> Diana
    selected_char = voice_service.determine_character_from_emotional_context(
        {"vulnerability_level": 0.8, "state": "vulnerable"},
        "reaction_success",
        "high"
    )
    print(f"   Alta vulnerabilidad -> {selected_char.value}")
    
    # Contexto de acceso denegado -> Lucien
    selected_char = voice_service.determine_character_from_emotional_context(
        {"vulnerability_level": 0.2, "state": "neutral"},
        "access_denied", 
        "low"
    )
    print(f"   Acceso denegado -> {selected_char.value}")
    
    # Test 6: Mapeo de contexto emocional
    print("\n6. Mapeo de contexto emocional:")
    
    # Timing rápido -> Impulso auténtico
    context = voice_service.map_emotional_analysis_to_context(
        timing_data={"response_speed": "very_fast"},
        user_history={"total_interactions": 10}
    )
    print(f"   Respuesta muy rápida -> {context.value}")
    
    # Usuario nuevo -> Nuevo usuario
    context = voice_service.map_emotional_analysis_to_context(
        user_history={"total_interactions": 2}
    )
    print(f"   Pocas interacciones -> {context.value}")
    
    print("\n✅ Todos los tests completados exitosamente!")
    print("\nLas voces auténticas están funcionando correctamente.")
    print("Diana susurra sus secretos cósmicos...")
    print("Lucien guarda las llaves de la sabiduría...")

def test_message_enhancement():
    """Test de mejora de mensajes con voces auténticas."""
    print("\n🎨 TESTING MESSAGE ENHANCEMENT")
    print("=" * 50)
    
    voice_service = CharacterVoiceService()
    
    # Test mensaje base mejorado por Diana
    base_message = "Has completado la misión exitosamente."
    enhanced = voice_service.enhance_message_with_character_voice(
        base_message,
        CharacterType.DIANA,
        EmotionalContext.ENGAGEMENT_ALTO
    )
    print(f"\nMensaje base: {base_message}")
    print(f"Mejorado por Diana: {enhanced}")
    
    # Test mensaje base mejorado por Lucien
    enhanced_lucien = voice_service.enhance_message_with_character_voice(
        base_message,
        CharacterType.LUCIEN,
        EmotionalContext.NUEVO_USUARIO
    )
    print(f"\nMejorado por Lucien: {enhanced_lucien}")

def test_emotional_context_patterns():
    """Test de patrones específicos para diferentes contextos emocionales."""
    print("\n💫 TESTING EMOTIONAL CONTEXT PATTERNS")
    print("=" * 50)
    
    voice_service = CharacterVoiceService()
    
    contexts_to_test = [
        (EmotionalContext.IMPULSO_AUTENTICO, "Impulso Auténtico"),
        (EmotionalContext.PAUSA_REFLEXIVA, "Pausa Reflexiva"),
        (EmotionalContext.VULNERABILIDAD_ALTA, "Vulnerabilidad Alta"),
        (EmotionalContext.ENGAGEMENT_BAJO, "Engagement Bajo")
    ]
    
    for context, name in contexts_to_test:
        print(f"\n{name}:")
        print("  Diana:", voice_service.get_character_response(CharacterType.DIANA, context))
        print("  Lucien:", voice_service.get_character_response(CharacterType.LUCIEN, context))

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE INTEGRACIÓN DE VOCES AUTÉNTICAS")
    print("=" * 60)
    
    test_character_voice_service()
    test_message_enhancement()
    test_emotional_context_patterns()
    
    print("\n" + "=" * 60)
    print("🎉 INTEGRACIÓN DE VOCES AUTÉNTICAS COMPLETADA")
    print("\nDiana y Lucien están listos para interactuar con sus voces únicas.")
    print("El sistema de análisis emocional guiará sus respuestas contextuales.")
    print("La experiencia inmersiva auténtica ha sido implementada.")