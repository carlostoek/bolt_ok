from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Boolean, DateTime, Index, func
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from .base import Base


class NarrativeFragment(Base):
    """Modelo unificado para fragmentos narrativos con soporte para historia, decisiones e información.
    
    Este modelo representa fragmentos narrativos que pueden ser de diferentes tipos:
    - STORY: Fragmentos de historia principal
    - DECISION: Puntos de decisión con opciones
    - INFO: Fragmentos informativos
    
    Cada fragmento puede tener requerimientos (pistas necesarias) y triggers (recompensas/pistas).
    """
    
    __tablename__ = 'narrative_fragments_unified'
    __table_args__ = (
        Index('ix_narrative_fragments_unified_type_active', 'fragment_type', 'is_active'),
        Index('ix_narrative_fragments_unified_active', 'is_active'),
    )

    # UUID primary key for global uniqueness
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Fragment type classification
    FRAGMENT_TYPES = (
        ('STORY', 'Fragmento de historia'),
        ('DECISION', 'Punto de decisión'),
        ('INFO', 'Fragmento informativo'),
    )
    fragment_type = Column(String(20), nullable=False)
    
    # Choices for decision points (JSON field)
    choices = Column(JSON, default=list, nullable=False)
    
    # Triggers for rewards and other effects (JSON field)
    triggers = Column(JSON, default=dict, nullable=False)
    
    # Required clues/pistas for unlocking this fragment
    required_clues = Column(JSON, default=list, nullable=False)
    
    # Master storyline integration
    storyline_level = Column(Integer, nullable=True)  # 1-6 level from master storyline
    tier_classification = Column(String(20), nullable=True)  # los_kinkys, el_divan, elite
    fragment_sequence = Column(Integer, nullable=True)  # 1-16 sequence in master storyline
    
    # VIP access control
    requires_vip = Column(Boolean, default=False, nullable=False)
    vip_tier_required = Column(Integer, default=0, nullable=False)  # 0=free, 1=basic, 2=premium
    
    # Mission integration
    mission_type = Column(String(30), nullable=True)  # observation, comprehension, synthesis
    validation_criteria = Column(JSON, default=dict, nullable=False)  # Criteria for mission completion
    archetyping_data = Column(JSON, default=dict, nullable=False)  # Data for user archetyping
    
    # Character consistency requirements
    diana_personality_weight = Column(Integer, default=95, nullable=False)  # Required consistency %
    lucien_appearance_logic = Column(JSON, default=dict, nullable=False)  # When Lucien should appear
    character_validation_required = Column(Boolean, default=True, nullable=False)
    
    # Performance tracking
    avg_completion_time = Column(Integer, default=0, nullable=False)  # Average time to complete in seconds
    user_satisfaction_score = Column(Integer, default=0, nullable=False)  # Average user satisfaction
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Active status
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<NarrativeFragment(id={self.id}, title='{self.title}', type='{self.fragment_type}')>"

    @property
    def is_story(self):
        """Check if fragment is a story fragment."""
        return self.fragment_type == 'STORY'

    @property
    def is_decision(self):
        """Check if fragment is a decision point."""
        return self.fragment_type == 'DECISION'

    @property
    def is_info(self):
        """Check if fragment is an info fragment."""
        return self.fragment_type == 'INFO'
    
    @property
    def is_vip_content(self):
        """Check if fragment requires VIP access."""
        return self.requires_vip
    
    @property
    def is_los_kinkys_tier(self):
        """Check if fragment belongs to Los Kinkys (free) tier."""
        return self.tier_classification == 'los_kinkys'
    
    @property
    def is_el_divan_tier(self):
        """Check if fragment belongs to El Diván (VIP) tier."""
        return self.tier_classification == 'el_divan'
    
    @property
    def is_elite_tier(self):
        """Check if fragment belongs to Elite tier."""
        return self.tier_classification == 'elite'
    
    def get_mission_type_description(self):
        """Get human-readable description of mission type."""
        mission_descriptions = {
            'observation': 'Misión de Observación - Encuentra detalles ocultos',
            'comprehension': 'Prueba de Comprensión - Demuestra tu entendimiento',
            'synthesis': 'Desafío de Síntesis - Conecta múltiples niveles de comprensión'
        }
        return mission_descriptions.get(self.mission_type, 'Experiencia Narrativa')
    
    def requires_character_validation(self):
        """Check if this fragment requires character consistency validation."""
        return self.character_validation_required and self.diana_personality_weight >= 95
    
    def get_tier_display_name(self):
        """Get display name for tier classification."""
        tier_names = {
            'los_kinkys': 'Los Kinkys (Acceso Libre)',
            'el_divan': 'El Diván (VIP)',
            'elite': 'Círculo Élite (VIP Premium)'
        }
        return tier_names.get(self.tier_classification, 'Sin Clasificar')


class UserNarrativeState(Base):
    """Estado narrativo unificado del usuario.
    
    Este modelo rastrea el progreso del usuario en el sistema narrativo unificado,
    incluyendo fragmentos visitados, completados, y pistas desbloqueadas.
    """
    
    __tablename__ = 'user_narrative_states_unified'
    
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    current_fragment_id = Column(String, ForeignKey('narrative_fragments_unified.id'), nullable=True)
    visited_fragments = Column(JSON, default=list, nullable=False)  # Lista de IDs de fragmentos visitados
    completed_fragments = Column(JSON, default=list, nullable=False)  # Lista de IDs de fragmentos completados
    unlocked_clues = Column(JSON, default=list, nullable=False)  # Lista de códigos de pistas desbloqueadas
    
    # Master storyline progression tracking
    current_level = Column(Integer, default=1, nullable=False)  # 1-6 master storyline levels
    current_tier = Column(String(20), default='los_kinkys', nullable=False)  # los_kinkys, el_divan, elite
    tier_transition_history = Column(JSON, default=list, nullable=False)
    
    # User behavior analysis for archetyping
    response_time_tracking = Column(JSON, default=list, nullable=False)  # Track response times
    interaction_patterns = Column(JSON, default=dict, nullable=False)  # Behavioral patterns
    content_engagement_depth = Column(JSON, default=dict, nullable=False)  # How deeply user engages
    
    # Character consistency tracking
    diana_interactions_validated = Column(Integer, default=0, nullable=False)
    diana_consistency_average = Column(Integer, default=0, nullable=False)  # Running average score
    character_validation_history = Column(JSON, default=list, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    user = relationship("User", backref="narrative_state_unified", uselist=False)
    current_fragment = relationship("NarrativeFragment", foreign_keys=[current_fragment_id])
    
    async def get_progress_percentage(self, session):
        """Calcula el porcentaje de progreso del usuario.
        
        Args:
            session: Sesión de base de datos SQLAlchemy
            
        Returns:
            float: Porcentaje de progreso (0-100)
        """
        from sqlalchemy import func, select
        # Contar fragmentos activos
        total_fragments_result = await session.execute(
            select(func.count(NarrativeFragment.id)).where(NarrativeFragment.is_active == True)
        )
        total_fragments = total_fragments_result.scalar()
        
        if total_fragments == 0:
            return 0
        
        completed_count = len(self.completed_fragments)
        return (completed_count / total_fragments) * 100
    
    def has_unlocked_clue(self, clue_code):
        """Verifica si el usuario ha desbloqueado una pista específica.
        
        Args:
            clue_code (str): Código de la pista a verificar
            
        Returns:
            bool: True si la pista está desbloqueada, False en caso contrario
        """
        return clue_code in self.unlocked_clues

    def has_visited_fragment(self, fragment_id):
        """Verifica si el usuario ha visitado un fragmento específico.
        
        Args:
            fragment_id (str): ID del fragmento a verificar
            
        Returns:
            bool: True si el fragmento ha sido visitado, False en caso contrario
        """
        return fragment_id in self.visited_fragments

    def has_completed_fragment(self, fragment_id):
        """Verifica si el usuario ha completado un fragmento específico.
        
        Args:
            fragment_id (str): ID del fragmento a verificar
            
        Returns:
            bool: True si el fragmento ha sido completado, False en caso contrario
        """
        return fragment_id in self.completed_fragments


class UserDecisionLog(Base):
    """Log de decisiones del usuario en el sistema narrativo unificado.
    
    Este modelo registra todas las decisiones tomadas por los usuarios para
    análisis, seguimiento de progreso y prevención de recompensas duplicadas.
    """
    
    __tablename__ = 'user_decision_log_unified'
    __table_args__ = (
        Index('ix_user_decision_log_unified_user', 'user_id'),
        Index('ix_user_decision_log_unified_time', 'made_at'),
        Index('ix_user_decision_log_unified_fragment', 'fragment_id'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    fragment_id = Column(String, ForeignKey('narrative_fragments_unified.id', ondelete='CASCADE'), nullable=False)
    decision_choice = Column(String(100), nullable=False)  # Texto de la opción elegida
    points_awarded = Column(Integer, default=0, nullable=False)
    clues_unlocked = Column(JSON, default=list, nullable=False)  # Lista de códigos de pistas desbloqueadas
    made_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relaciones
    user = relationship("User", lazy="selectin")
    fragment = relationship("NarrativeFragment", lazy="selectin")

    def __repr__(self):
        return f"<UserDecisionLog(id={self.id}, user_id={self.user_id}, fragment_id='{self.fragment_id}', choice='{self.decision_choice}')>"


class UserArchetype(Base):
    """User archetyping system for behavioral pattern recognition.
    
    Tracks user behavior patterns to classify them into archetypes:
    - Explorer: Searches for details, revisits content multiple times
    - Direct: Goes straight to the point, concise interactions
    - Romantic: Seeks emotional connection, poetic responses
    - Analytical: Reflective responses, seeks intellectual understanding
    - Persistent: Doesn't give up easily, multiple attempts
    - Patient: Takes time to respond, processes deeply
    """
    
    __tablename__ = 'user_archetypes_unified'
    __table_args__ = (
        Index('ix_user_archetypes_unified_user', 'user_id'),
        Index('ix_user_archetypes_unified_dominant', 'dominant_archetype'),
    )
    
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    # Archetype scoring system (0-100 for each type)
    explorer_score = Column(Integer, default=0, nullable=False)
    direct_score = Column(Integer, default=0, nullable=False)
    romantic_score = Column(Integer, default=0, nullable=False)
    analytical_score = Column(Integer, default=0, nullable=False)
    persistent_score = Column(Integer, default=0, nullable=False)
    patient_score = Column(Integer, default=0, nullable=False)
    
    # Dominant archetype (calculated field)
    dominant_archetype = Column(String(20), nullable=True)
    
    # Behavioral tracking metrics
    avg_response_time = Column(Integer, default=0, nullable=False)  # Average seconds to respond
    content_revisit_count = Column(Integer, default=0, nullable=False)  # How often user revisits content
    deep_exploration_sessions = Column(Integer, default=0, nullable=False)  # Sessions >10 minutes
    question_engagement_rate = Column(Integer, default=0, nullable=False)  # % of questions answered thoughtfully
    emotional_vocabulary_usage = Column(Integer, default=0, nullable=False)  # Emotional words per interaction
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    user = relationship("User", backref="archetype_unified", uselist=False)
    
    def calculate_dominant_archetype(self):
        """Calculate and update the dominant archetype based on scores."""
        scores = {
            'explorer': self.explorer_score,
            'direct': self.direct_score,
            'romantic': self.romantic_score,
            'analytical': self.analytical_score,
            'persistent': self.persistent_score,
            'patient': self.patient_score
        }
        
        if max(scores.values()) == 0:
            self.dominant_archetype = None
        else:
            self.dominant_archetype = max(scores, key=scores.get)
    
    def get_archetype_distribution(self):
        """Get archetype distribution as percentages."""
        total = sum([
            self.explorer_score, self.direct_score, self.romantic_score,
            self.analytical_score, self.persistent_score, self.patient_score
        ])
        
        if total == 0:
            return {archetype: 0 for archetype in ['explorer', 'direct', 'romantic', 'analytical', 'persistent', 'patient']}
        
        return {
            'explorer': round((self.explorer_score / total) * 100, 1),
            'direct': round((self.direct_score / total) * 100, 1),
            'romantic': round((self.romantic_score / total) * 100, 1),
            'analytical': round((self.analytical_score / total) * 100, 1),
            'persistent': round((self.persistent_score / total) * 100, 1),
            'patient': round((self.patient_score / total) * 100, 1)
        }


class UserMissionProgress(Base):
    """User mission progress tracking for the master storyline system.
    
    Tracks progress through observation, comprehension, and synthesis challenges
    mapped to the 6-level master storyline progression.
    """
    
    __tablename__ = 'user_mission_progress_unified'
    __table_args__ = (
        Index('ix_user_mission_progress_unified_user', 'user_id'),
        Index('ix_user_mission_progress_unified_level', 'current_level'),
        Index('ix_user_mission_progress_unified_tier', 'current_tier'),
    )
    
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    # Master storyline progression (1-6 levels)
    current_level = Column(Integer, default=1, nullable=False)
    current_tier = Column(String(20), default='los_kinkys', nullable=False)  # los_kinkys, el_divan, elite
    
    # Mission completion tracking
    observation_missions_completed = Column(JSON, default=list, nullable=False)
    comprehension_tests_passed = Column(JSON, default=list, nullable=False)
    synthesis_challenges_completed = Column(JSON, default=list, nullable=False)
    
    # Performance metrics
    observation_accuracy = Column(Integer, default=0, nullable=False)  # % accuracy in finding hidden details
    comprehension_depth_score = Column(Integer, default=0, nullable=False)  # Quality of understanding
    synthesis_creativity_score = Column(Integer, default=0, nullable=False)  # Ability to connect concepts
    
    # Fragment progression per tier
    los_kinkys_fragments_completed = Column(JSON, default=list, nullable=False)  # Fragments 1-8
    el_divan_fragments_completed = Column(JSON, default=list, nullable=False)    # Fragments 9-12
    elite_fragments_completed = Column(JSON, default=list, nullable=False)       # Fragments 13-16
    
    # User evaluation results
    personality_evaluation_results = Column(JSON, default=dict, nullable=False)
    emotional_maturity_score = Column(Integer, default=0, nullable=False)
    diana_comprehension_score = Column(Integer, default=0, nullable=False)  # How well they understand Diana
    
    # VIP progression tracking
    vip_access_granted = Column(Boolean, default=False, nullable=False)
    vip_tier_level = Column(Integer, default=0, nullable=False)  # 0=none, 1=basic, 2=premium
    personalized_content_unlocked = Column(JSON, default=list, nullable=False)
    
    # Special achievements
    circle_intimo_access = Column(Boolean, default=False, nullable=False)
    guardian_of_secrets_status = Column(Boolean, default=False, nullable=False)
    narrative_synthesis_completed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    level_progression_history = Column(JSON, default=list, nullable=False)  # Track progression timeline
    
    # Relations
    user = relationship("User", backref="mission_progress_unified", uselist=False)
    
    def get_overall_progress_percentage(self):
        """Calculate overall progress through the master storyline."""
        total_fragments = 16
        completed_fragments = (
            len(self.los_kinkys_fragments_completed) +
            len(self.el_divan_fragments_completed) + 
            len(self.elite_fragments_completed)
        )
        
        return min(round((completed_fragments / total_fragments) * 100, 1), 100.0)
    
    def get_tier_progress(self, tier: str):
        """Get progress percentage for a specific tier."""
        tier_mapping = {
            'los_kinkys': (self.los_kinkys_fragments_completed, 8),
            'el_divan': (self.el_divan_fragments_completed, 4),
            'elite': (self.elite_fragments_completed, 4)
        }
        
        if tier not in tier_mapping:
            return 0.0
        
        completed_list, total_count = tier_mapping[tier]
        return round((len(completed_list) / total_count) * 100, 1)
    
    def can_access_tier(self, tier: str):
        """Check if user can access a specific tier based on progression."""
        if tier == 'los_kinkys':
            return True
        elif tier == 'el_divan':
            return self.vip_access_granted and len(self.los_kinkys_fragments_completed) >= 6
        elif tier == 'elite':
            return (
                self.vip_access_granted and 
                self.vip_tier_level >= 2 and
                len(self.el_divan_fragments_completed) >= 3
            )
        return False
    
    def record_level_progression(self, new_level: int, trigger_event: str):
        """Record level progression with timestamp and trigger event."""
        if not self.level_progression_history:
            self.level_progression_history = []
        
        self.level_progression_history.append({
            'previous_level': self.current_level,
            'new_level': new_level,
            'trigger_event': trigger_event,
            'timestamp': datetime.utcnow().isoformat(),
            'tier_at_progression': self.current_tier
        })
        
        self.current_level = new_level
        self.updated_at = datetime.utcnow()


class NarrativeCharacterValidation(Base):
    """Real-time character consistency validation results.
    
    Stores validation results for narrative fragments and user interactions
    to ensure >95% Diana character consistency requirement.
    """
    
    __tablename__ = 'narrative_character_validation_unified'
    __table_args__ = (
        Index('ix_narrative_character_validation_unified_fragment', 'fragment_id'),
        Index('ix_narrative_character_validation_unified_score', 'consistency_score'),
        Index('ix_narrative_character_validation_unified_meets', 'meets_threshold'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    fragment_id = Column(String, ForeignKey('narrative_fragments_unified.id', ondelete='CASCADE'), nullable=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    
    # Validation content
    validated_content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # fragment, menu_response, error_message, etc.
    
    # Character consistency scores (0-100)
    consistency_score = Column(Integer, nullable=False)
    mysterious_score = Column(Integer, nullable=False)
    seductive_score = Column(Integer, nullable=False)
    emotional_complexity_score = Column(Integer, nullable=False)
    intellectual_engagement_score = Column(Integer, nullable=False)
    
    # Validation results
    meets_threshold = Column(Boolean, nullable=False)  # >= 95% required
    violations_detected = Column(JSON, default=list, nullable=False)
    recommendations = Column(JSON, default=list, nullable=False)
    
    # Context information
    validation_context = Column(JSON, default=dict, nullable=False)
    archetype_influence = Column(String(20), nullable=True)  # User's dominant archetype
    
    # Timestamps
    validated_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relations
    fragment = relationship("NarrativeFragment", backref="character_validations")
    user = relationship("User", lazy="selectin")
    
    def get_validation_summary(self):
        """Get summary of validation results."""
        return {
            'overall_score': self.consistency_score,
            'meets_requirement': self.meets_threshold,
            'trait_breakdown': {
                'mysterious': self.mysterious_score,
                'seductive': self.seductive_score,
                'emotional_complexity': self.emotional_complexity_score,
                'intellectual_engagement': self.intellectual_engagement_score
            },
            'violation_count': len(self.violations_detected),
            'recommendation_count': len(self.recommendations)
        }


class LucienCoordination(Base):
    """Lucien coordination system for dynamic appearance logic.
    
    Manages when and how Lucien appears/disappears based on narrative timing,
    user emotional state, and storyline progression requirements.
    """
    
    __tablename__ = 'lucien_coordination_unified'
    __table_args__ = (
        Index('ix_lucien_coordination_unified_user', 'user_id'),
        Index('ix_lucien_coordination_unified_active', 'is_active'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Current coordination state
    is_active = Column(Boolean, default=False, nullable=False)
    coordination_mode = Column(String(30), nullable=False)  # hidden, observing, guiding, transitioning
    current_role = Column(String(50), nullable=False)  # guardian, guide, coordinator, messenger
    
    # Appearance triggers and conditions
    trigger_conditions = Column(JSON, default=dict, nullable=False)
    appearance_context = Column(String(100), nullable=True)  # mission, error, transition, introduction
    planned_disappearance_at = Column(DateTime, nullable=True)
    
    # User interaction tracking
    user_emotional_state = Column(String(30), nullable=True)  # curious, confused, engaged, frustrated
    last_interaction_type = Column(String(50), nullable=True)  # decision, question, exploration
    requires_coordination = Column(Boolean, default=False, nullable=False)
    
    # Narrative context
    current_fragment_context = Column(String, nullable=True)
    narrative_phase = Column(String(30), nullable=False)  # introduction, guidance, transition, support
    diana_availability = Column(Boolean, default=True, nullable=False)  # Is Diana currently "present"
    
    # Coordination history
    appearance_history = Column(JSON, default=list, nullable=False)
    coordination_effectiveness = Column(Integer, default=50, nullable=False)  # 0-100 score
    
    # Timestamps
    activated_at = Column(DateTime, nullable=True)
    last_coordination_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    user = relationship("User", backref="lucien_coordination_unified", uselist=False)
    
    def should_appear(self, context: str, user_state: dict) -> bool:
        """Determine if Lucien should appear based on current context and user state."""
        # Don't appear if already active
        if self.is_active:
            return False
        
        # Check trigger conditions
        if not self.trigger_conditions:
            return False
        
        # Context-specific appearance logic
        if context == 'user_confusion' and user_state.get('consecutive_errors', 0) >= 2:
            return True
        elif context == 'mission_introduction' and user_state.get('new_level', False):
            return True
        elif context == 'error_handling' and user_state.get('system_error', False):
            return True
        elif context == 'narrative_transition' and user_state.get('tier_change', False):
            return True
        
        return False
    
    def record_appearance(self, context: str, trigger_reason: str):
        """Record Lucien appearance with context and reason."""
        if not self.appearance_history:
            self.appearance_history = []
        
        self.appearance_history.append({
            'appeared_at': datetime.utcnow().isoformat(),
            'context': context,
            'trigger_reason': trigger_reason,
            'coordination_mode': self.coordination_mode,
            'user_emotional_state': self.user_emotional_state
        })
        
        self.is_active = True
        self.activated_at = datetime.utcnow()
        self.last_coordination_at = datetime.utcnow()
    
    def record_disappearance(self, reason: str, effectiveness_score: int = None):
        """Record Lucien disappearance and coordination effectiveness."""
        if self.appearance_history:
            self.appearance_history[-1]['disappeared_at'] = datetime.utcnow().isoformat()
            self.appearance_history[-1]['disappearance_reason'] = reason
            if effectiveness_score is not None:
                self.appearance_history[-1]['effectiveness_score'] = effectiveness_score
        
        self.is_active = False
        self.activated_at = None
        if effectiveness_score is not None:
            self.coordination_effectiveness = effectiveness_score