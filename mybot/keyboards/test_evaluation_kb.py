"""
Keyboard para el sistema de test de evaluación emocional.
Completamente aislado y sin dependencias de otros módulos.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_test_evaluation_menu_kb() -> InlineKeyboardMarkup:
    """
    Genera el menú principal del test de evaluación emocional.
    
    Returns:
        InlineKeyboardMarkup: Teclado con opciones del test
    """
    builder = InlineKeyboardBuilder()
    
    # Opciones del test emocional - diseñadas para medir timing de respuesta
    builder.button(
        text="🌹 Opción A", 
        callback_data="test_eval:option_a"
    )
    builder.button(
        text="💫 Opción B", 
        callback_data="test_eval:option_b"
    )
    builder.button(
        text="🔥 Opción C", 
        callback_data="test_eval:option_c"
    )
    builder.button(
        text="📊 Ver mi perfil", 
        callback_data="test_eval:view_profile"
    )
    
    # Organizar en 2x2 para facilitar la selección rápida
    builder.adjust(2, 2)
    
    return builder.as_markup()


def get_test_results_kb(user_type: str) -> InlineKeyboardMarkup:
    """
    Genera teclado para mostrar resultados del test.
    
    Args:
        user_type: Tipo de usuario detectado
        
    Returns:
        InlineKeyboardMarkup: Teclado con opciones post-test
    """
    builder = InlineKeyboardBuilder()
    
    # Opción para repetir el test
    builder.button(
        text="🔄 Repetir Test", 
        callback_data="test_eval:restart"
    )
    
    # Opción para salir
    builder.button(
        text="✨ Finalizar", 
        callback_data="test_eval:finish"
    )
    
    builder.adjust(2)
    
    return builder.as_markup()


def get_test_confirmation_kb() -> InlineKeyboardMarkup:
    """
    Genera teclado de confirmación para iniciar el test.
    
    Returns:
        InlineKeyboardMarkup: Teclado de confirmación
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🚀 Comenzar Test", 
        callback_data="test_eval:start_confirmed"
    )
    builder.button(
        text="❌ Cancelar", 
        callback_data="test_eval:cancel"
    )
    
    builder.adjust(2)
    
    return builder.as_markup()


def create_dynamic_test_kb(
    test_stage: str, 
    context: Dict[str, Any] = None
) -> InlineKeyboardMarkup:
    """
    Crea teclado dinámico según la etapa del test.
    
    Args:
        test_stage: Etapa actual del test
        context: Contexto adicional para personalización
        
    Returns:
        InlineKeyboardMarkup: Teclado personalizado
    """
    if context is None:
        context = {}
    
    builder = InlineKeyboardBuilder()
    
    if test_stage == "initial":
        return get_test_confirmation_kb()
    elif test_stage == "active":
        return get_test_evaluation_menu_kb()
    elif test_stage == "results":
        user_type = context.get("user_type", "unknown")
        return get_test_results_kb(user_type)
    else:
        # Fallback a menú principal
        return get_test_evaluation_menu_kb()


# Funciones de utilidad para el manejo de callbacks

def parse_test_callback(callback_data: str) -> Dict[str, str]:
    """
    Parsea callback_data del test emocional.
    
    Args:
        callback_data: Datos del callback (formato: "test_eval:action")
        
    Returns:
        Dict con la acción parseada
    """
    try:
        if not callback_data.startswith("test_eval:"):
            return {"action": "unknown"}
        
        action = callback_data.split(":", 1)[1]
        return {"action": action}
        
    except Exception as e:
        logger.warning(f"Error parseando callback del test: {callback_data} - {e}")
        return {"action": "unknown"}


def get_option_display_text(option: str) -> str:
    """
    Convierte opciones del test a texto descriptivo.
    
    Args:
        option: Opción seleccionada (option_a, option_b, etc.)
        
    Returns:
        String con texto descriptivo de la opción
    """
    option_texts = {
        "option_a": "Opción A - Respuesta Intuitiva",
        "option_b": "Opción B - Respuesta Equilibrada", 
        "option_c": "Opción C - Respuesta Analítica",
        "view_profile": "Consulta de Perfil Actual"
    }
    
    return option_texts.get(option, f"Opción: {option}")