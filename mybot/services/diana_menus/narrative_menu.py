"""
Diana Narrative Menu Module - Interactive Storytelling Interface
Provides immersive narrative experience with VIP content integration.
"""

import logging
from typing import Dict, Any, Optional, List
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from ..coordinador_central import CoordinadorCentral, AccionUsuario
from ..narrative_service import NarrativeService
from ..point_service import PointService
from ..level_service import LevelService
from ..achievement_service import AchievementService
from utils.message_safety import safe_edit
from utils.user_roles import get_user_role

logger = logging.getLogger(__name__)

class DianaNarrativeMenu:
    """
    Diana-themed narrative menu system providing immersive storytelling experience.
    Integrates with narrative service and handles VIP content access.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.coordinador = CoordinadorCentral(session)
        self.narrative_service = NarrativeService(session)
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        self.point_service = PointService(session, level_service, achievement_service)
        
        # Character-specific styling
        self.character_themes = {
            "diana": {
                "icon": "💋",
                "color": "passionate",
                "style": "seductive"
            },
            "lucien": {
                "icon": "🖤", 
                "color": "mysterious",
                "style": "enigmatic"
            }
        }
    
    async def show_narrative_hub(self, callback: CallbackQuery) -> None:
        """
        Central narrative hub with story progress and available content.
        """
        user_id = callback.from_user.id
        bot = callback.bot
        
        try:
            # Get narrative data
            narrative_data = await self._get_narrative_data(user_id)
            user_role = await get_user_role(bot, user_id, self.session)
            character = await self._get_active_character(user_id)
            theme = self.character_themes[character]
            
            text = f"""
📖 **CENTRO NARRATIVO - {character.upper()}**
*Tu historia personal de seducción y misterio*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

{theme['icon']} **Tu Viaje con {character.title()}**
• Capítulo actual: {narrative_data.get('current_chapter', 'Prólogo')}
• Progreso: {narrative_data.get('completion_percentage', 0)}% completado
• Última interacción: {narrative_data.get('last_interaction', 'Hace poco')}

🗝️ **Pistas Narrativas**
• Desbloqueadas: {narrative_data.get('hints_unlocked', 0)}
• Disponibles: {narrative_data.get('hints_available', 0)}
• Próxima pista: {narrative_data.get('next_hint_requirement', 'Continúa la historia')}

🔮 **Decisiones Pendientes**
• Momentos de elección: {narrative_data.get('pending_decisions', 0)}
• Impacto acumulado: {narrative_data.get('decision_impact', 'Neutral')}
• Caminos abiertos: {narrative_data.get('available_paths', 1)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **Experiencias Disponibles**
📚 Historia principal
🎒 Mochila de pistas  
🔓 Momentos especiales
{self._get_vip_content_status(user_role)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
{theme['icon']} *{character.title()} susurra: "{self._get_character_quote(character, narrative_data)}"*
            """
            
            keyboard = await self._build_narrative_hub_keyboard(user_role, narrative_data)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer(f"📖 {character.title()} te da la bienvenida...")
            
        except Exception as e:
            logger.error(f"Error showing narrative hub: {e}")
            await callback.answer("❌ Error cargando centro narrativo", show_alert=True)
    
    async def show_story_continuation(self, callback: CallbackQuery) -> None:
        """
        Show current story fragment and continuation options.
        """
        user_id = callback.from_user.id
        
        try:
            # Get current fragment using coordinador for VIP access check
            fragment_result = await self.coordinador.ejecutar_flujo(
                user_id, 
                AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="current",
                bot=callback.bot
            )
            
            if not fragment_result.get("success"):
                # Handle VIP access required
                await self._show_vip_access_required(callback, fragment_result)
                return
            
            current_fragment = fragment_result.get("fragment")
            if not current_fragment:
                await self._show_story_beginning(callback)
                return
            
            character = await self._get_active_character(user_id)
            theme = self.character_themes[character]
            
            text = f"""
📖 **{current_fragment.get('title', 'Historia Continuada')}**
*Capítulo en curso de tu historia con {character.title()}*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

{current_fragment.get('content', 'La historia continúa...')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

{theme['icon']} **{character.title()}**: *{current_fragment.get('character_dialogue', 'La historia nos llama...')}*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔮 **¿Cómo quieres continuar?**
Cada decisión moldea vuestra historia juntos...
            """
            
            keyboard = await self._build_story_continuation_keyboard(current_fragment, user_id)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("📖 Historia cargada")
            
        except Exception as e:
            logger.error(f"Error showing story continuation: {e}")
            await callback.answer("❌ Error cargando historia", show_alert=True)
    
    async def show_hints_inventory(self, callback: CallbackQuery) -> None:
        """
        Show user's collected narrative hints and clues.
        """
        user_id = callback.from_user.id
        
        try:
            # Get hints data
            hints_data = await self._get_user_hints(user_id)
            character = await self._get_active_character(user_id)
            theme = self.character_themes[character]
            
            text = f"""
🎒 **MOCHILA DE PISTAS - {character.upper()}**
*Secretos y revelaciones descubiertas*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗝️ **Tu Colección**
• Pistas desbloqueadas: {hints_data.get('total_unlocked', 0)}
• Pistas nuevas: {hints_data.get('new_hints', 0)}
• Valor narrativo: {hints_data.get('narrative_value', 0)} puntos

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📜 **Pistas Recientes**
{self._format_recent_hints(hints_data.get('recent_hints', []))}

🔍 **Pistas por Categoría**
💋 Intimidad: {hints_data.get('intimacy_hints', 0)} pistas
🎭 Personalidad: {hints_data.get('personality_hints', 0)} pistas  
🏰 Trasfondo: {hints_data.get('background_hints', 0)} pistas
🔮 Misterio: {hints_data.get('mystery_hints', 0)} pistas

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **Próximas Revelaciones**
{self._format_upcoming_hints(hints_data.get('upcoming_hints', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
{theme['icon']} *{character.title()}: "Cada pista te acerca más a conocer mi verdadero ser..."*
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("💋 Pistas de Intimidad", callback_data="hints_intimacy"),
                    InlineKeyboardButton("🎭 Pistas de Personalidad", callback_data="hints_personality")
                ],
                [
                    InlineKeyboardButton("🏰 Pistas de Trasfondo", callback_data="hints_background"),
                    InlineKeyboardButton("🔮 Pistas de Misterio", callback_data="hints_mystery")
                ],
                [
                    InlineKeyboardButton("🔍 Buscar Pistas", callback_data="hints_search"),
                    InlineKeyboardButton("📊 Estadísticas", callback_data="hints_stats")
                ],
                [
                    InlineKeyboardButton("🎯 Conseguir Más", callback_data="hints_how_to_get"),
                    InlineKeyboardButton("🔄 Actualizar", callback_data="narrative_inventory")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="user_narrative"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🎒 Mochila de pistas cargada")
            
        except Exception as e:
            logger.error(f"Error showing hints inventory: {e}")
            await callback.answer("❌ Error cargando mochila de pistas", show_alert=True)
    
    async def show_decision_center(self, callback: CallbackQuery) -> None:
        """
        Show available decisions and their potential impacts.
        """
        user_id = callback.from_user.id
        
        try:
            # Get decision data
            decisions_data = await self._get_user_decisions(user_id)
            character = await self._get_active_character(user_id)
            theme = self.character_themes[character]
            
            text = f"""
🔮 **CENTRO DE DECISIONES**
*Momentos que definirán vuestra historia*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ **Decisiones Disponibles**
• Momentos de elección: {decisions_data.get('available_decisions', 0)}
• Impacto potencial: {decisions_data.get('impact_level', 'Medio')}
• Costo en besitos: {decisions_data.get('total_cost', 0)} 💋

📊 **Tu Historial**
• Decisiones tomadas: {decisions_data.get('total_made', 0)}
• Camino principal: {decisions_data.get('main_path', 'Romántico')}
• Impacto acumulado: {decisions_data.get('cumulative_impact', 'Positivo')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 **Decisiones Pendientes**
{self._format_pending_decisions(decisions_data.get('pending_decisions', []))}

📈 **Análisis de Impacto**
• Relación con {character.title()}: {decisions_data.get('relationship_level', 'Creciendo')}
• Confianza mutua: {decisions_data.get('trust_level', 'Media')}
• Intensidad emocional: {decisions_data.get('intensity_level', 'Moderada')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 **Consejos de {character.title()}**
*"{self._get_decision_advice(character, decisions_data)}"*

━━━━━━━━━━━━━━━━━━━━━━━━━━━
{theme['icon']} *Cada elección teje el destino de vuestra historia...*
            """
            
            keyboard = await self._build_decision_center_keyboard(decisions_data, user_id)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🔮 Centro de decisiones cargado")
            
        except Exception as e:
            logger.error(f"Error showing decision center: {e}")
            await callback.answer("❌ Error cargando centro de decisiones", show_alert=True)
    
    async def show_character_selection(self, callback: CallbackQuery) -> None:
        """
        Allow user to choose their preferred character interaction.
        """
        user_id = callback.from_user.id
        
        try:
            # Get character data and user preferences
            character_data = await self._get_character_data(user_id)
            
            text = f"""
🎭 **SELECCIÓN DE PERSONAJE**
*Elige con quién quieres vivir tu próxima experiencia*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💋 **DIANA - La Seductora**
• Personalidad: Apasionada, misteriosa, seductora
• Especialidad: Romance intenso y pasión
• Historia completada: {character_data.get('diana_progress', 0)}%
• Momentos íntimos: {character_data.get('diana_intimate_moments', 0)}

🖤 **LUCIEN - El Enigma**  
• Personalidad: Misterioso, intelectual, intenso
• Especialidad: Intriga psicológica y tensión
• Historia completada: {character_data.get('lucien_progress', 0)}%
• Momentos íntimos: {character_data.get('lucien_intimate_moments', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **Tu Preferencia Actual**
Personaje principal: {character_data.get('current_character', 'Diana').title()}
Último encuentro: {character_data.get('last_interaction', 'Con Diana')}
Afinidad desarrollada: {character_data.get('affinity_level', 'Media')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **Experiencias Exclusivas**
Desbloquea contenido único con cada personaje según tu elección y progreso

━━━━━━━━━━━━━━━━━━━━━━━━━━━
*¿Con quién quieres continuar tu historia?*
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("💋 Continuar con Diana", callback_data="character_select_diana"),
                    InlineKeyboardButton("🖤 Cambiar a Lucien", callback_data="character_select_lucien")
                ],
                [
                    InlineKeyboardButton("📊 Comparar Personajes", callback_data="character_compare"),
                    InlineKeyboardButton("🎭 Momentos Especiales", callback_data="character_special_moments")
                ],
                [
                    InlineKeyboardButton("📖 Historia de Diana", callback_data="character_diana_story"),
                    InlineKeyboardButton("📖 Historia de Lucien", callback_data="character_lucien_story")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="user_narrative"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🎭 Selección de personaje")
            
        except Exception as e:
            logger.error(f"Error showing character selection: {e}")
            await callback.answer("❌ Error cargando selección de personaje", show_alert=True)
    
    # ==================== HELPER METHODS ====================
    
    async def _get_narrative_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive narrative data for user."""
        try:
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            
            # Calculate narrative statistics
            completion = await self._calculate_narrative_completion(user_id)
            
            return {
                "current_chapter": current_fragment.title if current_fragment else "Prólogo",
                "completion_percentage": completion,
                "last_interaction": "Hace 2 horas",  # Would get from interaction log
                "hints_unlocked": completion // 10,
                "hints_available": 2,  # Would calculate available hints
                "next_hint_requirement": "Completa el capítulo actual",
                "pending_decisions": 1 if completion < 100 else 0,
                "decision_impact": "Creciente",
                "available_paths": 2 if completion > 50 else 1
            }
        except Exception as e:
            logger.error(f"Error getting narrative data: {e}")
            return {}
    
    async def _get_active_character(self, user_id: int) -> str:
        """Get user's current active character."""
        try:
            # Would get from user preferences or narrative state
            return "diana"  # Default to Diana
        except Exception:
            return "diana"
    
    def _get_vip_content_status(self, user_role: str) -> str:
        """Get VIP content availability status."""
        if user_role in ["vip", "admin"]:
            return "👑 Contenido VIP desbloqueado"
        else:
            return "🔒 Contenido VIP (Requiere suscripción)"
    
    def _get_character_quote(self, character: str, narrative_data: Dict) -> str:
        """Get appropriate character quote based on progress."""
        progress = narrative_data.get("completion_percentage", 0)
        
        if character == "diana":
            if progress < 25:
                return "Apenas comenzamos a conocernos, pero ya siento la conexión..."
            elif progress < 50:
                return "Cada momento contigo revela una nueva faceta de mi ser..."
            elif progress < 75:
                return "Nuestros caminos se entrelazan de maneras que no imaginé..."
            else:
                return "Has llegado a lugares de mi corazón que creí cerrados para siempre..."
        else:
            return "Los misterios más profundos requieren de almas valientes para descubrirlos..."
    
    async def _build_narrative_hub_keyboard(self, user_role: str, narrative_data: Dict) -> List[List[InlineKeyboardButton]]:
        """Build narrative hub keyboard based on user access and progress."""
        keyboard = [
            [
                InlineKeyboardButton("📚 Continuar Historia", callback_data="narrative_continue"),
                InlineKeyboardButton("🎒 Mochila de Pistas", callback_data="narrative_inventory")
            ],
            [
                InlineKeyboardButton("🔮 Centro de Decisiones", callback_data="narrative_decisions"),
                InlineKeyboardButton("🎭 Cambiar Personaje", callback_data="narrative_character")
            ]
        ]
        
        # Add VIP content if accessible
        if user_role in ["vip", "admin"]:
            keyboard.append([
                InlineKeyboardButton("👑 Momentos VIP", callback_data="narrative_vip_content"),
                InlineKeyboardButton("💫 Experiencias Exclusivas", callback_data="narrative_exclusive")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("💎 Desbloquear VIP", callback_data="narrative_upgrade_vip")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📊 Mi Progreso", callback_data="narrative_progress"),
                InlineKeyboardButton("🔄 Actualizar", callback_data="user_narrative")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="user_menu"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ])
        
        return keyboard
    
    async def _show_vip_access_required(self, callback: CallbackQuery, result: Dict) -> None:
        """Show VIP access required message."""
        text = """
🔒 **CONTENIDO VIP REQUERIDO**

Diana te mira con deseo, pero niega suavemente con la cabeza...

💋 *"Este momento especial es solo para mis amantes más dedicados, mi amor. Algunas fantasías requieren una conexión más profunda..."*

👑 **Beneficios VIP:**
• Acceso a momentos íntimos exclusivos
• Decisiones que transforman la historia
• Contenido para adultos sin censura
• Personajes y escenarios únicos

💎 **¡Conviértete en VIP ahora!**
Desbloquea experiencias que cambiarán tu relación con Diana para siempre.
        """
        
        keyboard = [
            [
                InlineKeyboardButton("👑 Hacerse VIP", callback_data="upgrade_to_vip"),
                InlineKeyboardButton("💳 Ver Planes", callback_data="view_vip_plans")
            ],
            [
                InlineKeyboardButton("📖 Contenido Gratuito", callback_data="narrative_free_content"),
                InlineKeyboardButton("◀️ Volver", callback_data="user_narrative")
            ]
        ]
        
        await safe_edit(
            callback.message,
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("🔒 Contenido VIP requerido")
    
    async def _show_story_beginning(self, callback: CallbackQuery) -> None:
        """Show story beginning for new users."""
        text = """
📖 **EL COMIENZO DE TU HISTORIA**

Te encuentras en el umbral de una experiencia única. Diana, una mujer de belleza misteriosa y encanto magnético, acaba de cruzar tu camino...

Sus ojos te observan con una mezcla de curiosidad y provocación, como si pudiera leer los secretos más profundos de tu alma.

💋 *"Bienvenido a mi mundo,"* susurra con una sonrisa que promete aventuras que nunca imaginaste. *"¿Estás preparado para descubrir hasta dónde puede llevarnos esta historia?"*

🌟 **Esta es solo el comienzo...**
Cada decisión que tomes, cada momento que compartas, moldeará el curso de vuestra historia juntos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
¿Cómo quieres responder a Diana?
        """
        
        keyboard = [
            [
                InlineKeyboardButton("😊 'Me intrigas, Diana'", callback_data="story_begin_intrigued"),
                InlineKeyboardButton("😏 'Estoy listo para cualquier cosa'", callback_data="story_begin_ready")
            ],
            [
                InlineKeyboardButton("🤔 '¿Qué tipo de historia?'", callback_data="story_begin_curious"),
                InlineKeyboardButton("💋 'Enséñame tu mundo'", callback_data="story_begin_forward")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="user_narrative")
            ]
        ]
        
        await safe_edit(
            callback.message,
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("📖 Historia comenzando...")
    
    # Additional helper methods for formatting and data processing...
    
    def _format_recent_hints(self, hints: List[Dict]) -> str:
        """Format recent hints for display."""
        if not hints:
            return "• No hay pistas recientes"
        
        formatted = []
        for hint in hints[:3]:
            formatted.append(f"🗝️ {hint.get('title', 'Pista misteriosa')}")
            formatted.append(f"   *{hint.get('description', 'Una revelación te espera...')}*")
        
        return "\n".join(formatted)
    
    def _format_upcoming_hints(self, hints: List[Dict]) -> str:
        """Format upcoming hints for display."""
        if not hints:
            return "• Continúa la historia para más revelaciones"
        
        return "\n".join(f"🎯 {h.get('requirement', 'Requisito desconocido')}" for h in hints[:2])
    
    def _format_pending_decisions(self, decisions: List[Dict]) -> str:
        """Format pending decisions for display."""
        if not decisions:
            return "• No hay decisiones pendientes"
        
        formatted = []
        for decision in decisions[:3]:
            cost = decision.get('cost', 0)
            cost_text = f" ({cost} besitos)" if cost > 0 else ""
            formatted.append(f"🔮 {decision.get('title', 'Decisión importante')}{cost_text}")
        
        return "\n".join(formatted)
    
    def _get_decision_advice(self, character: str, decisions_data: Dict) -> str:
        """Get character-specific decision advice."""
        if character == "diana":
            return "Escucha a tu corazón, pero no olvides que algunas decisiones requieren valentía..."
        else:
            return "Las decisiones más profundas nacen de la contemplación y el entendimiento..."
    
    async def _calculate_narrative_completion(self, user_id: int) -> int:
        """Calculate narrative completion percentage."""
        try:
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            if current_fragment:
                # Simple calculation based on fragment key
                if "level1" in current_fragment.key:
                    return 20
                elif "level2" in current_fragment.key:
                    return 40
                elif "level3" in current_fragment.key:
                    return 60
                elif "level4" in current_fragment.key:
                    return 80
                elif "level5" in current_fragment.key:
                    return 100
            return 0
        except Exception:
            return 0
    
    async def _get_user_hints(self, user_id: int) -> Dict[str, Any]:
        """Get user's hint collection data."""
        # Placeholder implementation
        return {
            "total_unlocked": 8,
            "new_hints": 2,
            "narrative_value": 120,
            "recent_hints": [
                {"title": "El secreto de Diana", "description": "Sus ojos guardan memorias de vidas pasadas"},
                {"title": "La conexión", "description": "Sientes que ya os conocíais de antes"}
            ],
            "intimacy_hints": 3,
            "personality_hints": 2,
            "background_hints": 2,
            "mystery_hints": 1,
            "upcoming_hints": [
                {"requirement": "Completa el capítulo actual"},
                {"requirement": "Toma una decisión arriesgada"}
            ]
        }
    
    async def _get_user_decisions(self, user_id: int) -> Dict[str, Any]:
        """Get user's decision data."""
        # Placeholder implementation
        return {
            "available_decisions": 2,
            "impact_level": "Alto",
            "total_cost": 15,
            "total_made": 12,
            "main_path": "Romántico Intenso",
            "cumulative_impact": "Muy Positivo",
            "pending_decisions": [
                {"title": "Un momento íntimo", "cost": 10},
                {"title": "Revelar un secreto", "cost": 5}
            ],
            "relationship_level": "Profunda",
            "trust_level": "Alta",
            "intensity_level": "Intensa"
        }
    
    async def _get_character_data(self, user_id: int) -> Dict[str, Any]:
        """Get character interaction data."""
        # Placeholder implementation
        return {
            "diana_progress": 65,
            "diana_intimate_moments": 8,
            "lucien_progress": 20,
            "lucien_intimate_moments": 2,
            "current_character": "Diana",
            "last_interaction": "Con Diana hace 2 horas",
            "affinity_level": "Alta"
        }
    
    async def _build_story_continuation_keyboard(self, fragment: Dict, user_id: int) -> List[List[InlineKeyboardButton]]:
        """Build keyboard for story continuation based on fragment options."""
        keyboard = []
        
        # Add story-specific choices (would come from fragment data)
        choices = fragment.get("choices", [
            {"text": "Continuar con cautela", "id": "continue_cautious"},
            {"text": "Ser más directo", "id": "continue_direct"}
        ])
        
        for choice in choices[:4]:  # Max 4 choices
            keyboard.append([
                InlineKeyboardButton(choice["text"], callback_data=f"story_choice_{choice['id']}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📚 Historia Completa", callback_data="story_full_view"),
                InlineKeyboardButton("💾 Guardar Progreso", callback_data="story_save")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="user_narrative"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ])
        
        return keyboard
    
    async def _build_decision_center_keyboard(self, decisions_data: Dict, user_id: int) -> List[List[InlineKeyboardButton]]:
        """Build decision center keyboard."""
        keyboard = []
        
        # Add pending decisions
        pending = decisions_data.get("pending_decisions", [])
        for decision in pending[:2]:
            cost = decision.get("cost", 0)
            text = f"{decision['title']} ({cost} besitos)" if cost > 0 else decision["title"]
            keyboard.append([
                InlineKeyboardButton(text, callback_data=f"decision_make_{decision.get('id', 'unknown')}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📊 Historial Decisiones", callback_data="decisions_history"),
                InlineKeyboardButton("🎯 Impacto en Historia", callback_data="decisions_impact")
            ],
            [
                InlineKeyboardButton("💡 Consejos", callback_data="decisions_advice"),
                InlineKeyboardButton("🔄 Actualizar", callback_data="narrative_decisions")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="user_narrative"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ])
        
        return keyboard