# utils/keyboard_utils.py
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from database.models import User
from utils.messages import BOT_MESSAGES







# Continuación del archivo utils/keyboard_utils.py - MENÚS FALTANTES ACTUALIZADOS











# Funciones helper para mensajes con la guía de estilo aplicada
def get_admin_main_message() -> str:
    """Mensaje principal del panel de administración."""
    return """
⚙️ **PANEL DE ADMINISTRACIÓN**

┌─────────────────────────────────┐
│        CENTRO DE CONTROL        │
├─────────────────────────────────┤
│ 👥 Gestión de usuarios          │
│ 🎯 Contenido y misiones         │
│ 📊 Estadísticas del bot         │
│ 🔧 Configuración avanzada       │
└─────────────────────────────────┘

🎛️ **¿Qué deseas administrar?**
"""


def get_user_profile_message(username: str, besitos: int, level: int, streak: int, vip_status: str) -> str:
    """Mensaje del perfil de usuario con formato elegante."""
    level_emoji = "🌱" if level <= 10 else "🌿" if level <= 25 else "🌳" if level <= 50 else "🏆" if level <= 100 else "💎"
    vip_badge = "💎" if vip_status == "vip" else "👑" if vip_status == "premium" else "⚡" if vip_status == "admin" else "🤍"
    
    return f"""
🏆 **TU PERFIL EN EL DIVÁN**

┌─────────────────────────────────┐
│  {vip_badge} {username}                    │
├─────────────────────────────────┤
│ {level_emoji} Nivel {level}                    │
│ 💋 {besitos:,} besitos             │
│ 🔥 Racha: {streak} días            │
│ 💎 Estado: {vip_status.title()}           │
└─────────────────────────────────┘

🌟 **¡Sigue coleccionando besitos y subiendo de nivel!**
"""


def get_missions_header_message(completed_today: int, total_available: int) -> str:
    """Mensaje de cabecera para la sección de misiones."""
    progress_bar = "█" * (completed_today * 10 // max(total_available, 1)) + "░" * (10 - (completed_today * 10 // max(total_available, 1)))
    
    return f"""
🎯 **CENTRO DE MISIONES**

┌─────────────────────────────────┐
│        PROGRESO DIARIO          │
├─────────────────────────────────┤
│ ✅ Completadas: {completed_today}/{total_available}           │
│ 📊 Progreso: {progress_bar}     │
│ 🎁 Besitos ganados hoy: +{completed_today * 50}    │
└─────────────────────────────────┘

🎮 **Misiones disponibles:**
"""
