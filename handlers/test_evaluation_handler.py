"""
Test Evaluation Handler - Sistema de evaluación emocional completamente aislado.
Diseñado para no interferir con funcionalidad existente del bot.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession

# Imports locales aislados
from keyboards.test_evaluation_kb import (
    get_test_evaluation_menu_kb,
    get_test_results_kb, 
    get_test_confirmation_kb,
    parse_test_callback,
    get_option_display_text
)
from services.coordinador_central import CoordinadorCentral, AccionUsuario

logger = logging.getLogger(__name__)

# Router aislado para el test emocional
router = Router()

# Cache temporal para timing de respuestas (evitar deps adicionales)
_user_test_sessions: Dict[int, Dict[str, Any]] = {}


class TestEvaluationState:
    """Estado del test emocional para un usuario específico."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.started_at = datetime.utcnow()
        self.stage = "initial"  # initial, active, completed
        self.responses = []
        self.last_action_time = time.time()
    
    def record_response(self, option: str, response_time: float):
        """Registra una respuesta del usuario."""
        self.responses.append({
            "option": option,
            "response_time": response_time,
            "timestamp": datetime.utcnow()
        })
        self.last_action_time = time.time()
    
    def get_average_response_time(self) -> float:
        """Calcula tiempo promedio de respuesta."""
        if not self.responses:
            return 0.0
        return sum(r["response_time"] for r in self.responses) / len(self.responses)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte estado a diccionario."""
        return {
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "stage": self.stage,
            "responses": self.responses,
            "avg_response_time": self.get_average_response_time()
        }


@router.message(Command("test_evaluacion"))
async def cmd_test_evaluacion(message: Message, session: AsyncSession):
    """
    Comando principal para iniciar el test de evaluación emocional.
    Completamente aislado del resto del sistema.
    """
    logger.info(f"Test evaluacion command received from user {message.from_user.id}")
    await cmd_test_evaluacion_main(message, session)

@router.message(Command("test_eval"))  
async def cmd_test_eval_short(message: Message, session: AsyncSession):
    """Alias corto para el test de evaluación."""
    await cmd_test_evaluacion_main(message, session)

@router.message(Command("test_evaluation"))
async def cmd_test_evaluation_english(message: Message, session: AsyncSession):
    """Alias en inglés para el test de evaluación.""" 
    await cmd_test_evaluacion_main(message, session)

async def cmd_test_evaluacion_main(message: Message, session: AsyncSession):
    """
    Comando principal para iniciar el test de evaluación emocional.
    Completamente aislado del resto del sistema.
    """
    try:
        user_id = message.from_user.id
        logger.info(f"Test emocional iniciado por usuario {user_id}")
        
        # Crear o actualizar sesión de test
        _user_test_sessions[user_id] = TestEvaluationState(user_id)
        
        # Ejecutar flujo completo a través del CoordinadorCentral
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.TEST_EVALUACION_EMOCIONAL,
            action_type="start_test"
        )
        
        if result["success"]:
            # Mostrar mensaje de bienvenida con confirmación
            welcome_text = (
                f"✨ {result.get('message', 'Sistema emocional activado')}\n\n"
                "🔬 Test de Evaluación Emocional\n\n"
                "Este test mide tu patrón de respuesta emocional según el timing "
                "de tus decisiones. No hay respuestas correctas o incorrectas.\n\n"
                "📊 Clasificaciones:\n"
                "• &lt; 3s = Impulso Auténtico\n"
                "• 3-15s = Pausa Reflexiva\n"
                "• 15-60s = Contemplación\n"
                "• &gt; 60s = Abandono\n\n"
                "¿Estás listo para descubrir tu perfil?"
            )
            
            await message.answer(
                welcome_text,
                reply_markup=get_test_confirmation_kb()
            )
        else:
            await message.answer(
                f"❌ {result.get('message', 'Error al inicializar el test emocional.')}"
            )
            
    except Exception as e:
        logger.error(f"Error en comando test_evaluacion para usuario {user_id}: {e}")
        await message.answer(
            "❌ Error inesperado durante la inicialización del test. "
            "El sistema ha registrado el problema."
        )


@router.callback_query(lambda c: c.data and c.data.startswith("test_eval:"))
async def handle_test_evaluation_callback(callback_query: CallbackQuery, session: AsyncSession):
    """
    Handler para todos los callbacks del test emocional.
    Maneja el timing y procesa las respuestas de forma aislada.
    """
    try:
        user_id = callback_query.from_user.id
        callback_data = callback_query.data
        
        # Parsear acción del callback
        parsed = parse_test_callback(callback_data)
        action = parsed["action"]
        
        logger.info(f"Test callback recibido de usuario {user_id}: {action}")
        
        # Obtener o crear sesión de test
        if user_id not in _user_test_sessions:
            _user_test_sessions[user_id] = TestEvaluationState(user_id)
        
        test_session = _user_test_sessions[user_id]
        
        # Procesar según la acción
        if action == "start_confirmed":
            await _handle_test_start(callback_query, session, test_session)
        
        elif action in ["option_a", "option_b", "option_c", "view_profile"]:
            await _handle_test_response(callback_query, session, test_session, action)
        
        elif action == "restart":
            await _handle_test_restart(callback_query, session, test_session)
        
        elif action in ["cancel", "finish"]:
            await _handle_test_finish(callback_query, session, test_session)
        
        else:
            logger.warning(f"Acción de test no reconocida: {action}")
            await callback_query.answer("Acción no reconocida", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error en callback del test emocional: {e}")
        await callback_query.answer("Error procesando respuesta", show_alert=True)


async def _handle_test_start(
    callback_query: CallbackQuery, 
    session: AsyncSession, 
    test_session: TestEvaluationState
):
    """Maneja el inicio confirmado del test."""
    test_session.stage = "active"
    test_session.last_action_time = time.time()  # Iniciar cronómetro
    
    # Texto del test activo
    test_text = (
        "🧠 **Test Emocional Activo**\n\n"
        "Responde según tu primer impulso. El sistema está midiendo "
        "tu tiempo de respuesta para crear tu perfil emocional.\n\n"
        "**Pregunta:** En una situación íntima, tiendes a...\n\n"
        "⏱️ *Cronómetro iniciado*"
    )
    
    await callback_query.message.edit_text(
        test_text,
        reply_markup=get_test_evaluation_menu_kb()
    )
    await callback_query.answer()


async def _handle_test_response(
    callback_query: CallbackQuery,
    session: AsyncSession, 
    test_session: TestEvaluationState,
    action: str
):
    """Maneja las respuestas del usuario al test."""
    # Calcular tiempo de respuesta
    current_time = time.time()
    response_time = current_time - test_session.last_action_time
    
    # Registrar respuesta
    test_session.record_response(action, response_time)
    test_session.stage = "completed"
    
    # Procesar a través del CoordinadorCentral
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        callback_query.from_user.id,
        AccionUsuario.TEST_EVALUACION_EMOCIONAL,
        action_type="process_response",
        response_time=response_time,
        option_selected=action
    )
    
    if result["success"]:
        # Mostrar resultados del test
        user_type = result.get("user_type", "unknown")
        option_text = get_option_display_text(action)
        
        results_text = (
            f"✅ Test Completado\n\n"
            f"📝 Tu respuesta: {option_text}\n"
            f"⏱️ Tiempo: {response_time:.1f} segundos\n\n"
            f"{result['message']}"
        )
        
        await callback_query.message.edit_text(
            results_text,
            reply_markup=get_test_results_kb(user_type)
        )
        
        # Log detallado del resultado
        logger.info(
            f"Test completado - Usuario: {callback_query.from_user.id}, "
            f"Tipo: {user_type}, Tiempo: {response_time:.1f}s, Opción: {action}"
        )
    else:
        await callback_query.message.edit_text(
            f"❌ Error procesando respuesta: {result.get('message', 'Error desconocido')}"
        )
    
    await callback_query.answer()


async def _handle_test_restart(
    callback_query: CallbackQuery,
    session: AsyncSession, 
    test_session: TestEvaluationState
):
    """Maneja el reinicio del test."""
    # Reiniciar sesión
    user_id = callback_query.from_user.id
    _user_test_sessions[user_id] = TestEvaluationState(user_id)
    
    # Regresar al inicio
    welcome_text = (
        "🔄 **Test Reiniciado**\n\n"
        "Vamos a empezar de nuevo. Recuerda que el sistema mide tu "
        "tiempo de respuesta para crear tu perfil emocional.\n\n"
        "¿Listo para intentarlo otra vez?"
    )
    
    await callback_query.message.edit_text(
        welcome_text,
        reply_markup=get_test_confirmation_kb()
    )
    await callback_query.answer()


async def _handle_test_finish(
    callback_query: CallbackQuery,
    session: AsyncSession, 
    test_session: TestEvaluationState
):
    """Maneja la finalización del test."""
    user_id = callback_query.from_user.id
    
    # Limpiar sesión
    if user_id in _user_test_sessions:
        del _user_test_sessions[user_id]
    
    # Mensaje de finalización
    finish_text = (
        "✨ **Test Finalizado**\n\n"
        "Gracias por participar en la evaluación emocional. "
        "Tus resultados han sido procesados por el sistema.\n\n"
        "Puedes repetir el test en cualquier momento con /test_evaluacion"
    )
    
    await callback_query.message.edit_text(finish_text)
    await callback_query.answer()
    
    logger.info(f"Test finalizado para usuario {user_id}")


# Funciones de utilidad

def get_active_test_sessions() -> Dict[int, Dict[str, Any]]:
    """
    Retorna información de sesiones activas (para debugging/monitoring).
    
    Returns:
        Dict con información de sesiones activas
    """
    return {
        user_id: session.to_dict() 
        for user_id, session in _user_test_sessions.items()
    }


def cleanup_expired_sessions(max_age_hours: int = 2):
    """
    Limpia sesiones expiradas para evitar memory leaks.
    
    Args:
        max_age_hours: Máximo edad de sesiones en horas
    """
    current_time = datetime.utcnow()
    expired_users = []
    
    for user_id, session in _user_test_sessions.items():
        age = current_time - session.started_at
        if age.total_seconds() > max_age_hours * 3600:
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del _user_test_sessions[user_id]
        logger.debug(f"Sesión de test limpiada para usuario {user_id}")
    
    if expired_users:
        logger.info(f"Limpiadas {len(expired_users)} sesiones expiradas de test emocional")


# Auto-cleanup cada vez que se importa el módulo
import atexit
atexit.register(lambda: cleanup_expired_sessions(1))  # Limpiar al salir