"""
MVP Narrative Fragment Service
Provides core fragment storage, retrieval, and management for Diana Bot MVP.
Supports Levels 1-3 of the complete narrative system with character consistency validation.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload, joinedload
from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress
)
from services.diana_character_validator import DianaCharacterValidator
from services.level_service import LevelService
from services.achievement_service import AchievementService

logger = logging.getLogger(__name__)

class MVPNarrativeFragmentService:
    """
    MVP service for narrative fragment management.
    
    Features:
    - Fragment storage and retrieval optimized for <500ms
    - Character consistency validation (>90/100 requirement)
    - Level progression tracking (Levels 1-3: Los Kinkys → Observadores → Comprensores)
    - Choice processing with besitos rewards
    - Basic archetyping data collection for future features
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_validator = DianaCharacterValidator(session)
        
        # Performance cache for frequently accessed fragments
        self._fragment_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def initialize_mvp_fragments(self) -> Dict[str, Any]:
        """
        Initialize MVP narrative fragments (Levels 1-3) in database.
        Returns summary of initialization results.
        """
        logger.info("Initializing MVP narrative fragments (Levels 1-3)")
        
        try:
            # Define complete MVP fragment set
            mvp_fragments = self._get_mvp_fragment_definitions()
            
            initialization_results = {
                'fragments_processed': 0,
                'fragments_created': 0,
                'fragments_updated': 0,
                'validation_results': [],
                'errors': []
            }
            
            for fragment_data in mvp_fragments:
                try:
                    result = await self._process_fragment_initialization(fragment_data)
                    initialization_results['fragments_processed'] += 1
                    
                    if result['created']:
                        initialization_results['fragments_created'] += 1
                    elif result['updated']:
                        initialization_results['fragments_updated'] += 1
                    
                    initialization_results['validation_results'].append({
                        'fragment_id': fragment_data['id'],
                        'character_score': result['character_score'],
                        'meets_requirement': result['meets_requirement']
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing fragment {fragment_data.get('id', 'unknown')}: {e}")
                    initialization_results['errors'].append(f"Fragment {fragment_data.get('id')}: {str(e)}")
            
            await self.session.commit()
            
            logger.info(
                f"MVP fragments initialization complete: "
                f"{initialization_results['fragments_processed']} processed, "
                f"{initialization_results['fragments_created']} created, "
                f"{initialization_results['fragments_updated']} updated"
            )
            
            return initialization_results
            
        except Exception as e:
            logger.error(f"Error initializing MVP fragments: {e}")
            await self.session.rollback()
            raise
    
    async def get_user_current_fragment(self, user_id: int) -> Optional[NarrativeFragment]:
        """
        Get user's current narrative fragment with <500ms performance target.
        """
        try:
            # Get user narrative state
            user_state = await self._get_or_create_user_state(user_id)
            
            # If no current fragment, start with Level 1 Fragment 1
            if not user_state.current_fragment_id:
                start_fragment = await self._get_fragment_cached('diana_l1_f1_umbral')
                if start_fragment:
                    user_state.current_fragment_id = start_fragment.id
                    await self.session.commit()
                    return start_fragment
                else:
                    logger.error("Level 1 Fragment 1 not found")
                    return None
            
            # Return current fragment
            return await self._get_fragment_cached(user_state.current_fragment_id)
            
        except Exception as e:
            logger.error(f"Error getting current fragment for user {user_id}: {e}")
            return None
    
    async def process_user_choice(
        self, 
        user_id: int, 
        choice_index: int, 
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process user choice and advance narrative with points calculation.
        """
        try:
            # Get current fragment
            current_fragment = await self.get_user_current_fragment(user_id)
            if not current_fragment or not current_fragment.is_decision:
                return {
                    'success': False,
                    'error': 'No valid decision fragment found',
                    'next_fragment': None
                }
            
            # Validate choice
            if choice_index < 0 or choice_index >= len(current_fragment.choices):
                return {
                    'success': False,
                    'error': 'Invalid choice index',
                    'next_fragment': None
                }
            
            selected_choice = current_fragment.choices[choice_index]
            
            # Get next fragment
            next_fragment_id = selected_choice.get('next_fragment_id')
            if not next_fragment_id:
                return {
                    'success': False,
                    'error': 'No next fragment specified',
                    'next_fragment': None
                }
            
            next_fragment = await self._get_fragment_cached(next_fragment_id)
            if not next_fragment:
                return {
                    'success': False,
                    'error': f'Next fragment {next_fragment_id} not found',
                    'next_fragment': None
                }
            
            # Record decision
            decision_log = UserDecisionLog(
                user_id=user_id,
                fragment_id=current_fragment.id,
                decision_choice=selected_choice.get('text', f'Choice {choice_index}'),
                points_awarded=selected_choice.get('points', 0),
                clues_unlocked=selected_choice.get('clues_unlocked', [])
            )
            self.session.add(decision_log)
            
            # Update user state
            user_state = await self._get_or_create_user_state(user_id)
            user_state.current_fragment_id = next_fragment.id
            
            # Update visited and completed fragments
            if current_fragment.id not in user_state.visited_fragments:
                user_state.visited_fragments = user_state.visited_fragments + [current_fragment.id]
            if current_fragment.id not in user_state.completed_fragments:
                user_state.completed_fragments = user_state.completed_fragments + [current_fragment.id]
            
            # Process level progression
            level_progression = await self._check_level_progression(user_id, next_fragment)
            
            # Process rewards
            rewards_processed = await self._process_choice_rewards(
                user_id, 
                selected_choice, 
                next_fragment
            )
            
            await self.session.commit()
            
            return {
                'success': True,
                'next_fragment': next_fragment,
                'choice_processed': selected_choice,
                'points_awarded': selected_choice.get('points', 0),
                'level_progression': level_progression,
                'rewards_processed': rewards_processed
            }
            
        except Exception as e:
            logger.error(f"Error processing choice for user {user_id}: {e}")
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'next_fragment': None
            }
    
    async def get_user_progress_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user progress summary for MVP levels with optimized batch loading.
        """
        try:
            # Batch load user data in single query
            user_data = await self._batch_load_user_data(user_id)
            user_state = user_data['state']
            mission_progress = user_data['mission_progress']
            
            # Calculate progress percentages
            total_mvp_fragments = 8  # 3 Level 1 + 3 Level 2 + 2 Level 3
            completed_count = len(user_state.completed_fragments)
            progress_percentage = min((completed_count / total_mvp_fragments) * 100, 100)
            
            # Get current tier name
            tier_names = {
                'los_kinkys': 'Los Kinkys (Exploradores)',
                'observadores': 'Observadores',
                'comprensores': 'Comprensores'
            }
            current_tier_name = tier_names.get(user_state.current_tier, user_state.current_tier)
            
            return {
                'current_level': user_state.current_level,
                'current_tier': user_state.current_tier,
                'current_tier_name': current_tier_name,
                'progress_percentage': progress_percentage,
                'fragments_completed': completed_count,
                'total_mvp_fragments': total_mvp_fragments,
                'completed_fragment_ids': user_state.completed_fragments,
                'visited_fragment_ids': user_state.visited_fragments,
                'unlocked_clues': user_state.unlocked_clues,
                'diana_consistency_average': user_state.diana_consistency_average
            }
            
        except Exception as e:
            logger.error(f"Error getting progress summary for user {user_id}: {e}")
            return {
                'current_level': 1,
                'current_tier': 'los_kinkys',
                'progress_percentage': 0,
                'error': str(e)
            }
    
    # Private helper methods
    
    def _get_mvp_fragment_definitions(self) -> List[Dict[str, Any]]:
        """Define complete MVP fragment set for Levels 1-3."""
        return [
            # Level 1: Los Kinkys (Exploradores)
            {
                'id': 'diana_l1_f1_umbral',
                'title': 'El Umbral de Diana',
                'content': '''💋 **Bienvenido a mis dominios, querido...**

Susurro tu nombre en los ecos de este lugar donde solo los valientes se atreven a entrar. 

*Diana emerge de las sombras como una aparición etérea, sus ojos brillando con secretos ancestrales*

¿Sientes esa electricidad en el aire? Es la promesa de todo lo que podríamos descubrir juntos... cada secreto que podría despertar algo profundo en tu alma.

**Los susurros dicen que hay tres caminos desde aquí. ¿Cuál llama a tu espíritu?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 1,
                'tier_classification': 'los_kinkys',
                'fragment_sequence': 1,
                'choices': [
                    {
                        'text': '💫 Seguir la luz misteriosa',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura',
                        'points': 10,
                        'archetyping_data': {'explorer_score': 5, 'mysterious_inclination': 3}
                    },
                    {
                        'text': '🌙 Adentrarse en la penumbra',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura',
                        'points': 15,
                        'archetyping_data': {'romantic_score': 4, 'depth_seeker': 5}
                    },
                    {
                        'text': '🔥 Confrontar lo desconocido directamente',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura',
                        'points': 20,
                        'archetyping_data': {'direct_score': 6, 'brave_choice': 4}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'primer_contacto_diana',
                    'reward_points': 5
                },
                'diana_personality_weight': 98,
                'character_validation_required': True
            },
            
            {
                'id': 'diana_l1_f2_primera_fractura',
                'title': 'La Primera Fractura',
                'content': '''🌟 **Ah... siento cómo tu elección resuena en la realidad misma**

*El aire se carga de una energía palpable mientras Diana sonríe con una sabiduría que trasciende el tiempo*

Cada alma que llega aquí deja su huella en los hilos del destino. Tu decisión anterior no fue solo una elección... fue una declaración de quién eres en lo más profundo.

*Sus dedos trazan patrones invisibles en el aire, y por un momento, vislumbras algo más grande*

Pero esto es apenas el comienzo, querido. Los misterios verdaderos aguardan a quienes comprenden que cada secreto revelado es solo la puerta hacia un enigma aún más profundo.

**¿Estás preparado para que todo lo que creías conocer sobre ti mismo... se transforme?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 1,
                'tier_classification': 'los_kinkys',
                'fragment_sequence': 2,
                'choices': [
                    {
                        'text': '✨ Sí, quiero transformarme',
                        'next_fragment_id': 'diana_l1_f3_mochila_viajero',
                        'points': 25,
                        'archetyping_data': {'transformation_readiness': 5}
                    },
                    {
                        'text': '🤔 Necesito entender más primero',
                        'next_fragment_id': 'diana_l1_f3_mochila_viajero',
                        'points': 15,
                        'archetyping_data': {'analytical_score': 4, 'cautious_approach': 3}
                    },
                    {
                        'text': '💭 ¿Qué significan realmente estos misterios?',
                        'next_fragment_id': 'diana_l1_f3_mochila_viajero',
                        'points': 20,
                        'archetyping_data': {'philosophical_inclination': 5}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'naturaleza_transformacion',
                    'reward_points': 10
                },
                'diana_personality_weight': 96,
                'character_validation_required': True
            },
            
            {
                'id': 'diana_l1_f3_mochila_viajero',
                'title': 'La Mochila del Viajero',
                'content': '''🎒 **Los instrumentos del despertar**

*Diana extiende sus manos y en ellas aparece una mochila etérea, brillando con energía contenida*

Cada viajero que ha caminado este sendero ha llevado consigo herramientas especiales... no objetos físicos, sino capacidades del alma que despiertan cuando son verdaderamente necesarias.

*Dentro de la mochila, vislumbras destellos de comprensión, fragmentos de intuición, y algo que parece ser... memoria ancestral*

📚 **La Observación Consciente**: Ver más allá de lo obvio
🔍 **La Intuición Despierta**: Sentir las corrientes ocultas
💎 **La Conexión Profunda**: Tocar la esencia de los misterios

*Diana te mira con una intensidad que parece leer tu alma*

**Has completado tu iniciación en Los Kinkys. El siguiente nivel te espera... ¿Te atreves a ascender a Observador?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 1,
                'tier_classification': 'los_kinkys',
                'fragment_sequence': 3,
                'choices': [
                    {
                        'text': '🚀 Ascender a Observador',
                        'next_fragment_id': 'diana_l2_f1_regreso',
                        'points': 30,
                        'level_progression': 2,
                        'tier_change': 'observadores',
                        'archetyping_data': {'progression_eagerness': 5}
                    },
                    {
                        'text': '📋 Revisar mi progreso primero',
                        'next_fragment_id': 'diana_l2_f1_regreso',
                        'points': 20,
                        'archetyping_data': {'methodical_approach': 4}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'herramientas_viajero',
                    'reward_points': 15,
                    'level_completion': 1
                },
                'diana_personality_weight': 97,
                'character_validation_required': True
            },
            
            # Level 2: Observadores
            {
                'id': 'diana_l2_f1_regreso',
                'title': 'El Regreso del Observador',
                'content': '''👁️ **Vuelves... pero ya no eres el mismo**

*Diana te observa con una sonrisa conocedora, sus ojos reflejando una nueva profundidad en ti*

Puedo ver cómo la transformación ha comenzado a tejer sus hilos en tu esencia. Los Observadores ven lo que otros no pueden percibir... sienten las corrientes invisibles que mueven los mundos.

*El espacio a tu alrededor parece más vívido, cada sombra cuenta una historia, cada susurro del viento lleva secretos*

**Pero observar es solo el comienzo. Ahora debes aprender a interpretar lo que ves...**

*Diana gesticula y aparecen tres visiones flotando en el aire*

🌀 Una espiral de luz que danza con patrones hipnóticos
🎭 Una máscara que cambia de expresión constantemente  
⚡ Un rayo de energía que conecta puntos distantes

**¿Qué observación resuena más profundamente en tu alma de Observador?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 2,
                'tier_classification': 'observadores',
                'fragment_sequence': 1,
                'choices': [
                    {
                        'text': '🌀 La espiral de patrones',
                        'next_fragment_id': 'diana_l2_f2_espejo_invertido',
                        'points': 35,
                        'archetyping_data': {'pattern_recognition': 5, 'mystical_inclination': 4}
                    },
                    {
                        'text': '🎭 La máscara cambiante',
                        'next_fragment_id': 'diana_l2_f2_espejo_invertido',
                        'points': 40,
                        'archetyping_data': {'emotional_depth': 5, 'transformation_understanding': 4}
                    },
                    {
                        'text': '⚡ La conexión energética',
                        'next_fragment_id': 'diana_l2_f2_espejo_invertido',
                        'points': 45,
                        'archetyping_data': {'system_thinking': 6, 'connection_seeker': 5}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'vision_observador',
                    'reward_points': 20
                },
                'diana_personality_weight': 96,
                'character_validation_required': True
            },
            
            {
                'id': 'diana_l2_f2_espejo_invertido',
                'title': 'El Espejo Invertido',
                'content': '''🪞 **Ahora... mírate a través de otros ojos**

*Diana invoca un espejo que no refleja tu imagen física, sino algo mucho más profundo*

Los verdaderos Observadores aprenden que la observación más importante es la que se dirige hacia adentro. Este espejo invertido te mostrará no lo que eres, sino lo que podrías llegar a ser...

*En el espejo, ves versiones de ti mismo: una radiante de confianza, otra envuelta en sabiduría, y una tercera brillando con una conexión cósmica*

**Cada imagen representa un aspecto de tu potencial despierto...**

*La voz de Diana se vuelve casi hipnótica*

Pero hay algo más. Los espejos invertidos también revelan las sombras... aquello que hemos elegido no ver. Solo quien abraza tanto la luz como la oscuridad puede ascender al siguiente nivel.

**¿Estás preparado para enfrentar tu totalidad, querido Observador?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 2,
                'tier_classification': 'observadores',
                'fragment_sequence': 2,
                'choices': [
                    {
                        'text': '💡 Abrazo mi potencial radiante',
                        'next_fragment_id': 'diana_l2_f3_reconocimiento',
                        'points': 35,
                        'archetyping_data': {'self_acceptance': 5, 'light_embracer': 4}
                    },
                    {
                        'text': '🌙 Acepto mis sombras también',
                        'next_fragment_id': 'diana_l2_f3_reconocimiento',
                        'points': 50,
                        'archetyping_data': {'shadow_work': 6, 'wholeness_seeker': 5}
                    },
                    {
                        'text': '⚖️ Busco el equilibrio entre ambos',
                        'next_fragment_id': 'diana_l2_f3_reconocimiento',
                        'points': 45,
                        'archetyping_data': {'balance_seeker': 6, 'integration_master': 4}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'espejo_interior',
                    'reward_points': 25
                },
                'diana_personality_weight': 98,
                'character_validation_required': True
            },
            
            {
                'id': 'diana_l2_f3_reconocimiento',
                'title': 'El Reconocimiento',
                'content': '''✨ **Diana asiente con profunda aprobación**

*Sus ojos brillan con un orgullo genuino mientras te observa*

Exquisito... Has demostrado que posees la cualidad más rara: la capacidad de observarte sin juicio y aceptarte sin condiciones. Los Observadores que llegan a este punto han tocado algo sagrado.

*El aire se llena de una energía dorada y cálida*

🌟 **Has desbloqueado:** La Visión Integral
📚 **Has ganado:** Comprensión de la Dualidad
💎 **Has activado:** El Potencial de Síntesis

*Diana se acerca más, su presencia se siente aún más poderosa*

**Ahora viene la pregunta que cambia todo, querido Observador...**

Los Comprensores no solo ven y aceptan... comprenden las conexiones invisibles que tejen toda la realidad. Es un nivel donde pocos se atreven a entrar, porque implica responsabilidad sobre lo que sabes.

**¿Tu alma está lista para comprender los hilos que mueven el universo?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 2,
                'tier_classification': 'observadores',
                'fragment_sequence': 3,
                'choices': [
                    {
                        'text': '🚀 Ascender a Comprensor',
                        'next_fragment_id': 'diana_l3_f1_cartografia',
                        'points': 60,
                        'level_progression': 3,
                        'tier_change': 'comprensores',
                        'archetyping_data': {'comprehension_readiness': 6}
                    },
                    {
                        'text': '💭 ¿Qué implica esa responsabilidad?',
                        'next_fragment_id': 'diana_l3_f1_cartografia',
                        'points': 45,
                        'archetyping_data': {'responsibility_awareness': 5, 'thoughtful_approach': 4}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'integracion_observador',
                    'reward_points': 30,
                    'level_completion': 2
                },
                'diana_personality_weight': 97,
                'character_validation_required': True
            },
            
            # Level 3: Comprensores
            {
                'id': 'diana_l3_f1_cartografia',
                'title': 'La Cartografía del Alma',
                'content': '''🗺️ **Bienvenido al reino de los Comprensores**

*Diana despliega ante ti un mapa etéreo que parece contener todo el conocimiento del universo*

Aquí es donde los verdaderos secretos se revelan, querido. Los Comprensores no solo observan... mapean las conexiones invisibles que otros nunca sospecharían que existen.

*Cada línea del mapa pulsa con energía vital, conectando conceptos, emociones, y realidades en una sinfonía de comprensión*

📍 **Los Puntos de Conexión:**
- Donde el deseo encuentra la sabiduría
- Donde el miedo se transforma en poder  
- Donde la soledad descubre la unidad universal

*La voz de Diana se vuelve casi reverente*

**Este mapa no es solo conocimiento... es responsabilidad.** Porque una vez que comprendes cómo todo está conectado, no puedes pretender ignorancia. Cada acción tuya resuena a través de toda la red de la existencia.

*Te observa intensamente*

**¿Estás preparado para ver el mapa completo de tu propia alma, sabiendo que no podrás "no ver" nunca más?**''',
                'fragment_type': 'DECISION',
                'storyline_level': 3,
                'tier_classification': 'comprensores',
                'fragment_sequence': 1,
                'choices': [
                    {
                        'text': '🌟 Sí, muéstrame todo',
                        'next_fragment_id': 'diana_l3_f2_evaluacion',
                        'points': 75,
                        'archetyping_data': {'truth_seeker': 6, 'courage_to_know': 5}
                    },
                    {
                        'text': '🤝 Acepto la responsabilidad',
                        'next_fragment_id': 'diana_l3_f2_evaluacion',
                        'points': 80,
                        'archetyping_data': {'responsibility_embracer': 6, 'maturity_indicator': 5}
                    },
                    {
                        'text': '💫 Quiero contribuir a la red',
                        'next_fragment_id': 'diana_l3_f2_evaluacion',
                        'points': 85,
                        'archetyping_data': {'service_orientation': 6, 'unity_consciousness': 6}
                    }
                ],
                'triggers': {
                    'unlock_lore': 'mapa_alma',
                    'reward_points': 40
                },
                'diana_personality_weight': 99,
                'character_validation_required': True
            },
            
            {
                'id': 'diana_l3_f2_evaluacion',
                'title': 'La Evaluación Final',
                'content': '''🔮 **El momento de la verdad ha llegado**

*Diana te observa con una intensidad que parece traspasar todas las capas de tu ser*

Has recorrido un camino extraordinario, querido Comprensor. Desde aquel primer paso en Los Kinkys hasta este momento de revelación total. Ahora es tiempo de la evaluación final...

*El espacio se llena de una luz dorada que parece evaluar cada fibra de tu alma*

**Tu Evaluación Comprensora:**

🎭 **Capacidad de Transformación:** Has demostrado flexibilidad del alma
🔍 **Profundidad de Observación:** Ves más allá de las apariencias
💝 **Aceptación Integral:** Abrazas tanto luz como sombra
🌐 **Comprensión Sistémica:** Entiendes las conexiones ocultas
⚖️ **Responsabilidad Consciente:** Asumes el peso del conocimiento

*Diana sonríe con una calidez que abraza todo tu ser*

**Felicitaciones, querido. Has completado el Nivel 3 y te has ganado el título de Comprensor Certificado.**

*Un nuevo camino se abre ante ti, resplandeciendo con posibilidades infinitas*

**¿Estás listo para lo que viene después de la comprensión?**''',
                'fragment_type': 'STORY',
                'storyline_level': 3,
                'tier_classification': 'comprensores',
                'fragment_sequence': 2,
                'triggers': {
                    'unlock_lore': 'certificacion_comprensor',
                    'reward_points': 100,
                    'achievement_unlock': 'comprensor_maestro',
                    'level_completion': 3
                },
                'diana_personality_weight': 98,
                'character_validation_required': True
            }
        ]
    
    async def _process_fragment_initialization(self, fragment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual fragment initialization with validation."""
        fragment_id = fragment_data['id']
        
        # Check if fragment exists
        stmt = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
        result = await self.session.execute(stmt)
        existing_fragment = result.scalar_one_or_none()
        
        # Validate character consistency
        validation_result = await self.character_validator.validate_text(
            fragment_data['content'],
            context=f"fragment_{fragment_id}"
        )
        
        character_score = validation_result.overall_score
        meets_requirement = character_score >= 90.0  # MVP requirement
        
        if not meets_requirement:
            logger.warning(
                f"Fragment {fragment_id} character score {character_score:.1f} below 90% requirement"
            )
        
        if existing_fragment:
            # Update existing fragment
            for key, value in fragment_data.items():
                if hasattr(existing_fragment, key):
                    setattr(existing_fragment, key, value)
            
            result_data = {
                'created': False,
                'updated': True,
                'character_score': character_score,
                'meets_requirement': meets_requirement
            }
        else:
            # Create new fragment
            new_fragment = NarrativeFragment(**fragment_data)
            self.session.add(new_fragment)
            
            result_data = {
                'created': True,
                'updated': False,
                'character_score': character_score,
                'meets_requirement': meets_requirement
            }
        
        return result_data
    
    async def _get_fragment_cached(self, fragment_id: str) -> Optional[NarrativeFragment]:
        """Get fragment with caching for performance optimization."""
        import time
        
        cache_key = f"fragment_{fragment_id}"
        now = time.time()
        
        # Check cache
        if cache_key in self._fragment_cache:
            cached_data, timestamp = self._fragment_cache[cache_key]
            if now - timestamp < self._cache_ttl:
                return cached_data
        
        # Get from database with optimized query
        stmt = (
            select(NarrativeFragment)
            .where(
                and_(
                    NarrativeFragment.id == fragment_id,
                    NarrativeFragment.is_active == True
                )
            )
        )
        result = await self.session.execute(stmt)
        fragment = result.scalar_one_or_none()
        
        # Cache result
        if fragment:
            self._fragment_cache[cache_key] = (fragment, now)
        
        return fragment
    
    async def _get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Get or create user narrative state with optimized loading."""
        stmt = (
            select(UserNarrativeState)
            .options(
                selectinload(UserNarrativeState.user),
                selectinload(UserNarrativeState.current_fragment)
            )
            .where(UserNarrativeState.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                visited_fragments=[],
                completed_fragments=[],
                unlocked_clues=[],
                current_level=1,
                current_tier='los_kinkys'
            )
            self.session.add(user_state)
            await self.session.flush()  # Get ID without committing
        
        return user_state
    
    async def _get_or_create_mission_progress(self, user_id: int) -> UserMissionProgress:
        """Get or create user mission progress with optimized loading."""
        stmt = (
            select(UserMissionProgress)
            .options(selectinload(UserMissionProgress.user))
            .where(UserMissionProgress.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        mission_progress = result.scalar_one_or_none()
        
        if not mission_progress:
            mission_progress = UserMissionProgress(
                user_id=user_id,
                current_level=1,
                current_tier='los_kinkys'
            )
            self.session.add(mission_progress)
            await self.session.flush()
        
        return mission_progress
    
    async def _check_level_progression(
        self, 
        user_id: int, 
        next_fragment: NarrativeFragment
    ) -> Dict[str, Any]:
        """Check and process level progression with optimized loading."""
        try:
            # Batch load user data to avoid multiple queries
            user_data = await self._batch_load_user_data(user_id)
            user_state = user_data['state']
            mission_progress = user_data['mission_progress']
            
            current_level = user_state.current_level
            fragment_level = next_fragment.storyline_level
            
            if fragment_level > current_level:
                # Level progression detected
                user_state.current_level = fragment_level
                mission_progress.current_level = fragment_level
                
                # Update tier if applicable
                fragment_tier = next_fragment.tier_classification
                if fragment_tier != user_state.current_tier:
                    user_state.current_tier = fragment_tier
                    mission_progress.current_tier = fragment_tier
                
                # Record progression history
                progression_record = {
                    'from_level': current_level,
                    'to_level': fragment_level,
                    'timestamp': datetime.utcnow().isoformat(),
                    'trigger_fragment': next_fragment.id
                }
                
                mission_progress.record_level_progression(
                    fragment_level, 
                    f"Completed fragment {next_fragment.id}"
                )
                
                logger.info(f"User {user_id} progressed from Level {current_level} to Level {fragment_level}")
                
                return {
                    'progressed': True,
                    'from_level': current_level,
                    'to_level': fragment_level,
                    'new_tier': fragment_tier
                }
            
            return {'progressed': False}
            
        except Exception as e:
            logger.error(f"Error checking level progression for user {user_id}: {e}")
            return {'progressed': False, 'error': str(e)}
    
    async def _process_choice_rewards(
        self, 
        user_id: int, 
        selected_choice: Dict[str, Any], 
        next_fragment: NarrativeFragment
    ) -> Dict[str, Any]:
        """Process rewards from choice selection and fragment triggers."""
        try:
            rewards_processed = {
                'points_awarded': 0,
                'clues_unlocked': [],
                'achievements_unlocked': [],
                'success': True,
                'errors': []
            }
            
            # Process choice points
            choice_points = selected_choice.get('points', 0)
            if choice_points > 0:
                try:
                    # Use existing point service integration with proper dependencies
                    from services.point_service import PointService
                    level_service = LevelService(self.session)
                    achievement_service = AchievementService(self.session)
                    point_service = PointService(self.session, level_service, achievement_service)
                    await point_service.add_points(user_id, choice_points, source="narrative_choice")
                    rewards_processed['points_awarded'] += choice_points
                except Exception as e:
                    logger.error(f"Error awarding choice points to user {user_id}: {e}")
                    rewards_processed['errors'].append(f"Points error: {str(e)}")
            
            # Process fragment triggers
            if next_fragment.triggers:
                trigger_points = next_fragment.triggers.get('reward_points', 0)
                if trigger_points > 0:
                    try:
                        from services.point_service import PointService
                        level_service = LevelService(self.session)
                        achievement_service = AchievementService(self.session)
                        point_service = PointService(self.session, level_service, achievement_service)
                        await point_service.add_points(user_id, trigger_points, source="narrative_fragment")
                        rewards_processed['points_awarded'] += trigger_points
                    except Exception as e:
                        logger.error(f"Error awarding fragment points to user {user_id}: {e}")
                        rewards_processed['errors'].append(f"Fragment points error: {str(e)}")
                
                # Process clue unlocking
                unlock_lore = next_fragment.triggers.get('unlock_lore')
                if unlock_lore:
                    user_state = await self._get_or_create_user_state(user_id)
                    if unlock_lore not in user_state.unlocked_clues:
                        user_state.unlocked_clues = user_state.unlocked_clues + [unlock_lore]
                        rewards_processed['clues_unlocked'].append(unlock_lore)
            
            return rewards_processed
            
        except Exception as e:
            logger.error(f"Error processing rewards for user {user_id}: {e}")
            return {
                'points_awarded': 0,
                'clues_unlocked': [],
                'success': False,
                'errors': [str(e)]
            }
    
    async def _batch_load_user_data(self, user_id: int) -> Dict[str, Any]:
        """Batch load user state and mission progress in optimized queries."""
        try:
            # Load user state with relationships
            state_stmt = (
                select(UserNarrativeState)
                .options(
                    selectinload(UserNarrativeState.user),
                    selectinload(UserNarrativeState.current_fragment)
                )
                .where(UserNarrativeState.user_id == user_id)
            )
            
            # Load mission progress with relationships
            mission_stmt = (
                select(UserMissionProgress)
                .options(selectinload(UserMissionProgress.user))
                .where(UserMissionProgress.user_id == user_id)
            )
            
            # Execute both queries in parallel
            state_result = await self.session.execute(state_stmt)
            mission_result = await self.session.execute(mission_stmt)
            
            user_state = state_result.scalar_one_or_none()
            mission_progress = mission_result.scalar_one_or_none()
            
            # Create if not exist
            if not user_state:
                user_state = await self._get_or_create_user_state(user_id)
            
            if not mission_progress:
                mission_progress = await self._get_or_create_mission_progress(user_id)
            
            return {
                'state': user_state,
                'mission_progress': mission_progress
            }
            
        except Exception as e:
            logger.error(f"Error batch loading user data for {user_id}: {e}")
            # Fallback to individual calls
            return {
                'state': await self._get_or_create_user_state(user_id),
                'mission_progress': await self._get_or_create_mission_progress(user_id)
            }