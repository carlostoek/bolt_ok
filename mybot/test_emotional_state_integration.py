#!/usr/bin/env python3
"""
Script de prueba rápida para verificar la integración del sistema de estados emocionales.
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import User
from database.emotional_state_models import UserEmotionalState, EmotionalStateHistory
from services.emotional_state_service import EmotionalStateService
from services.interfaces.emotional_state_interface import EmotionalState
from services.coordinador_central import CoordinadorCentral, AccionUsuario

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_emotional_state_integration():
    """Test básico de integración del sistema de estados emocionales."""
    
    # Crear engine de prueba en memoria
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Crear factory de sesiones
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        try:
            # 1. Crear usuario de prueba
            test_user = User(
                id=123456789,
                username="testuser",
                first_name="Test",
                points=0.0
            )
            session.add(test_user)
            await session.commit()
            logger.info("✅ Usuario de prueba creado")
            
            # 2. Probar servicio de estados emocionales
            emotional_service = EmotionalStateService(session)
            
            # 2.1. Obtener estado inicial (debe crear uno neutral)
            initial_context = await emotional_service.get_user_emotional_state(test_user.id)
            assert initial_context.primary_state == EmotionalState.NEUTRAL
            assert initial_context.intensity == 0.0
            logger.info("✅ Estado emocional inicial creado correctamente")
            
            # 2.2. Actualizar estado emocional
            updated_context = await emotional_service.update_emotional_state(
                test_user.id, 
                EmotionalState.EXCITED, 
                0.8, 
                "test_trigger"
            )
            assert updated_context.primary_state == EmotionalState.EXCITED
            assert updated_context.intensity == 0.8
            logger.info("✅ Estado emocional actualizado correctamente")
            
            # 2.3. Probar análisis de interacción
            interaction_data = {
                "type": "fragment_completion",
                "completion_time": 25,  # Rápido
                "user_choice": "positive_option"
            }
            inferred_emotion = await emotional_service.analyze_interaction_emotion(
                test_user.id, interaction_data
            )
            assert inferred_emotion in [EmotionalState.EXCITED, EmotionalState.ENGAGED]
            logger.info(f"✅ Análisis de interacción: {inferred_emotion.value}")
            
            # 2.4. Obtener tono recomendado
            recommended_tone = await emotional_service.get_recommended_content_tone(test_user.id)
            assert isinstance(recommended_tone, str)
            logger.info(f"✅ Tono recomendado: {recommended_tone}")
            
            # 3. Probar integración con CoordinadorCentral
            coordinador = CoordinadorCentral(session)
            
            # 3.1. Ejecutar flujo de análisis emocional
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
                interaction_data=interaction_data
            )
            
            assert result["success"] == True
            assert "emotion_changed" in result
            assert "recommended_tone" in result
            logger.info("✅ Integración con CoordinadorCentral funciona correctamente")
            
            # 4. Verificar datos en base de datos
            # 4.1. Verificar estado emocional guardado
            from sqlalchemy import select
            db_state_result = await session.execute(
                select(UserEmotionalState).where(UserEmotionalState.user_id == test_user.id)
            )
            db_state = db_state_result.scalar_one()
            assert db_state is not None
            logger.info("✅ Estado emocional guardado en base de datos")
            
            # 4.2. Verificar historial
            history_result = await session.execute(
                select(EmotionalStateHistory).where(EmotionalStateHistory.user_id == test_user.id)
            )
            history_entries = history_result.scalars().all()
            assert len(history_entries) >= 1
            logger.info(f"✅ Historial emocional creado: {len(history_entries)} entradas")
            
            logger.info("🎉 ¡Todas las pruebas de integración pasaron exitosamente!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en prueba de integración: {e}")
            raise
        finally:
            await session.close()
            await engine.dispose()

if __name__ == "__main__":
    try:
        result = asyncio.run(test_emotional_state_integration())
        print("\n" + "="*60)
        print("✅ SISTEMA DE ESTADOS EMOCIONALES IMPLEMENTADO CORRECTAMENTE")
        print("="*60)
        print("Features implementadas:")
        print("  • Interfaz IEmotionalStateManager")
        print("  • Servicio EmotionalStateService")
        print("  • Modelos de base de datos (UserEmotionalState, EmotionalStateHistory)")
        print("  • Integración con CoordinadorCentral")
        print("  • Análisis automático de emociones basado en interacciones")
        print("  • Recomendaciones de tono para contenido personalizado")
        print("  • Persistencia completa de estados y historial")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Error en la implementación: {e}")
        exit(1)