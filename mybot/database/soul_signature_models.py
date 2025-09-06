"""
SOUL SIGNATURE PERSONALIZATION DATABASE MODELS
==============================================

Database models for storing soul signature personalization data.
These models support the most sophisticated personalization system ever implemented,
ensuring each user's Diana experience is genuinely unique and authentically evolved.

Integration with existing system:
- Extends database/narrative_unified.py architecture
- Compatible with existing UserNarrativeState and UserArchetype models
- Follows established patterns and conventions

Author: Diana Bot Soul Signature System
Version: 1.0
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Boolean, DateTime, Float, Index, func
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum
from .base import Base

# =============================================
# SOUL SIGNATURE CORE MODELS
# =============================================

class UserSoulSignature(Base):
    """
    Complete psychological signature of a user's authentic self.
    
    This model stores the deep psychological profile detected within the first 3 interactions,
    including core personality traits, emotional needs, and communication preferences.
    """
    
    __tablename__ = 'user_soul_signatures'
    __table_args__ = (
        Index('ix_user_soul_signatures_user_archetype', 'user_id', 'dominant_archetype'),
        Index('ix_user_soul_signatures_detection_quality', 'archetype_confidence', 'emotional_need_intensity'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Core Personality Traits (Detected in first 3 interactions)  
    dominant_archetype = Column(String(20), nullable=False)  # explorer, direct, romantic, analytical, persistent, patient
    secondary_archetype = Column(String(20), nullable=True)
    archetype_confidence = Column(Float, nullable=False, default=0.0)  # 0-1 confidence in classification
    
    # Emotional Needs Mapping
    primary_emotional_need = Column(String(20), nullable=False)  # validation, challenge, support, discovery, connection, transformation
    secondary_emotional_need = Column(String(20), nullable=True)
    emotional_need_intensity = Column(Float, nullable=False, default=0.0)  # 0-1 intensity level
    
    # Communication Preferences
    preferred_communication_style = Column(String(30), nullable=False)  # direct_honest, poetic_metaphor, etc.
    communication_adaptability = Column(Float, nullable=False, default=0.0)  # How flexible with different styles
    response_to_vulnerability = Column(Float, nullable=False, default=0.0)  # Response when Diana is vulnerable
    
    # Intimacy Calibration
    intimacy_pacing_preference = Column(String(30), nullable=False)  # instant_chemistry, gradual_buildup, etc.
    vulnerability_comfort_level = Column(Float, nullable=False, default=0.0)  # Current comfort with vulnerability
    trust_building_speed = Column(Float, nullable=False, default=0.0)  # How quickly they build trust
    
    # Unique Psychological Fingerprint
    curiosity_triggers = Column(JSON, default=list, nullable=False)  # What specifically makes them curious
    emotional_keywords = Column(JSON, default=list, nullable=False)  # Words that create emotional resonance
    interaction_rhythm = Column(JSON, default=dict, nullable=False)  # Their unique rhythm of interaction
    mystery_tolerance = Column(Float, nullable=False, default=0.0)  # How much mystery they can handle
    
    # Growth Tracking
    evolution_trajectory = Column(JSON, default=list, nullable=False)  # How they're changing over time
    breakthrough_moments = Column(JSON, default=list, nullable=False)  # Moments of significant growth
    
    # Quality and Validation
    detection_quality_score = Column(Float, nullable=False, default=0.0)  # Quality of signature detection
    last_quality_validation = Column(DateTime, nullable=True)
    validation_improvement_areas = Column(JSON, default=list, nullable=False)
    
    # Timestamps
    detected_at = Column(DateTime, default=func.now(), nullable=False)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", uselist=False, lazy="selectin")
    diana_variation = relationship("UserDianaVariation", uselist=False, back_populates="soul_signature")
    intimacy_calibration = relationship("UserIntimacyCalibration", uselist=False, back_populates="soul_signature")

    def __repr__(self):
        return f"<UserSoulSignature(user_id={self.user_id}, archetype='{self.dominant_archetype}', need='{self.primary_emotional_need}')>"

    @property
    def is_high_quality_signature(self):
        """Check if soul signature is high quality."""
        return (self.detection_quality_score >= 0.8 and 
                self.archetype_confidence >= 0.7 and 
                self.emotional_need_intensity >= 0.6)

    @property
    def personalization_readiness_score(self):
        """Calculate readiness for advanced personalization."""
        factors = [
            self.archetype_confidence,
            self.emotional_need_intensity,
            self.communication_adaptability,
            self.detection_quality_score
        ]
        return sum(factors) / len(factors)

    def get_dominant_traits(self):
        """Get dominant personality traits for quick access."""
        return {
            'archetype': self.dominant_archetype,
            'emotional_need': self.primary_emotional_need,
            'communication_style': self.preferred_communication_style,
            'intimacy_pacing': self.intimacy_pacing_preference
        }

    def add_breakthrough_moment(self, moment_type: str, description: str, emotional_impact: float = 0.0):
        """Add a breakthrough moment to the user's growth tracking."""
        if not self.breakthrough_moments:
            self.breakthrough_moments = []
        
        self.breakthrough_moments.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': moment_type,
            'description': description,
            'emotional_impact': emotional_impact,
            'significance_score': emotional_impact * 0.8 + 0.2
        })
        
        # Keep only last 20 breakthrough moments
        if len(self.breakthrough_moments) > 20:
            self.breakthrough_moments = self.breakthrough_moments[-20:]

    def update_evolution_trajectory(self, evolution_type: str, data: dict):
        """Update user's evolution trajectory."""
        if not self.evolution_trajectory:
            self.evolution_trajectory = []
            
        self.evolution_trajectory.append({
            'timestamp': datetime.utcnow().isoformat(),
            'evolution_type': evolution_type,
            'data': data,
            'quality_score': data.get('quality_score', 0.0)
        })
        
        # Keep only last 50 evolution points
        if len(self.evolution_trajectory) > 50:
            self.evolution_trajectory = self.evolution_trajectory[-50:]


class UserDianaVariation(Base):
    """
    Unique Diana personality variation evolved specifically for a user.
    
    This model stores the authentic Diana version that developed unique traits 
    and behaviors specifically for the relationship with this user.
    """
    
    __tablename__ = 'user_diana_variations'
    __table_args__ = (
        Index('ix_user_diana_variations_evolution', 'last_evolution', 'authenticity_score'),
        Index('ix_user_diana_variations_quality', 'uniqueness_score', 'believability_score'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    soul_signature_id = Column(String, ForeignKey('user_soul_signatures.id', ondelete='CASCADE'), nullable=False)
    
    # Diana's Core Traits (from Character Bible V1.0)
    base_diana_traits = Column(JSON, default=dict, nullable=False)  # Core Diana traits preservation
    
    # User-Specific Adaptations
    curiosity_expression_style = Column(String(100), nullable=False)  # How Diana expresses curiosity for this user
    vulnerability_sharing_approach = Column(String(100), nullable=False)  # How Diana shares vulnerabilities
    mystery_revelation_rhythm = Column(String(100), nullable=False)  # Rhythm of revealing mysteries
    emotional_resonance_frequency = Column(String(100), nullable=False)  # Emotional frequency Diana matches
    
    # Behavioral Evolution
    greeting_evolution = Column(JSON, default=list, nullable=False)  # How Diana's greetings evolved
    question_asking_style = Column(String(100), nullable=False)  # Diana's unique questioning style
    comfort_providing_method = Column(String(100), nullable=False)  # How Diana provides comfort
    challenge_presentation_style = Column(String(100), nullable=False)  # How Diana presents challenges
    
    # Memory Integration
    personal_references_bank = Column(JSON, default=list, nullable=False)  # Personal references Diana uses
    shared_moments_archive = Column(JSON, default=list, nullable=False)  # Archive of meaningful moments
    inside_jokes_collection = Column(JSON, default=list, nullable=False)  # Inside jokes developed together
    
    # Authentic Growth Simulation
    genuine_evolution_markers = Column(JSON, default=list, nullable=False)  # Markers of genuine relationship growth
    mutual_influence_indicators = Column(JSON, default=list, nullable=False)  # How user influenced Diana's "growth"
    
    # Quality Metrics
    authenticity_score = Column(Float, nullable=False, default=0.0)  # How authentic evolution feels
    uniqueness_score = Column(Float, nullable=False, default=0.0)  # How unique from other users
    believability_score = Column(Float, nullable=False, default=0.0)  # How believable evolution is
    user_satisfaction_indicator = Column(Float, nullable=False, default=0.0)  # User satisfaction with Diana
    
    # Evolution Tracking
    evolution_generation = Column(Integer, default=1, nullable=False)  # Generation number of evolution
    total_adaptations_made = Column(Integer, default=0, nullable=False)  # Number of adaptations made
    last_major_evolution = Column(DateTime, nullable=True)  # Last major personality evolution
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_evolution = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", uselist=False, lazy="selectin")
    soul_signature = relationship("UserSoulSignature", uselist=False, back_populates="diana_variation")

    def __repr__(self):
        return f"<UserDianaVariation(user_id={self.user_id}, curiosity='{self.curiosity_expression_style}', authenticity={self.authenticity_score})>"

    @property
    def is_high_quality_variation(self):
        """Check if Diana variation is high quality."""
        return (self.authenticity_score >= 0.88 and 
                self.uniqueness_score >= 0.85 and 
                self.believability_score >= 0.85)

    @property
    def evolution_maturity_level(self):
        """Calculate maturity level of evolution."""
        factors = [
            min(self.total_adaptations_made / 10.0, 1.0),  # Adaptation experience
            min(self.evolution_generation / 5.0, 1.0),     # Evolution generations
            self.authenticity_score,                        # Quality of evolution
            len(self.genuine_evolution_markers) / 10.0      # Evolution markers
        ]
        return sum(factors) / len(factors)

    def add_personal_reference(self, reference_type: str, content: str, emotional_weight: float = 0.5):
        """Add personal reference to Diana's bank."""
        if not self.personal_references_bank:
            self.personal_references_bank = []
            
        self.personal_references_bank.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': reference_type,
            'content': content,
            'emotional_weight': emotional_weight,
            'usage_frequency': 0
        })
        
        # Keep only most emotionally significant references (max 30)
        if len(self.personal_references_bank) > 30:
            self.personal_references_bank = sorted(
                self.personal_references_bank, 
                key=lambda x: x['emotional_weight'], 
                reverse=True
            )[:30]

    def archive_shared_moment(self, moment_type: str, description: str, emotional_significance: float = 0.5):
        """Archive a shared moment between user and Diana."""
        if not self.shared_moments_archive:
            self.shared_moments_archive = []
            
        self.shared_moments_archive.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': moment_type,
            'description': description,
            'emotional_significance': emotional_significance,
            'referenced_count': 0
        })
        
        # Keep only most significant moments (max 25)
        if len(self.shared_moments_archive) > 25:
            self.shared_moments_archive = sorted(
                self.shared_moments_archive,
                key=lambda x: x['emotional_significance'],
                reverse=True
            )[:25]

    def evolve_greeting(self, new_greeting: str, evolution_reason: str):
        """Evolve Diana's greeting for this user."""
        if not self.greeting_evolution:
            self.greeting_evolution = []
            
        self.greeting_evolution.append({
            'timestamp': datetime.utcnow().isoformat(),
            'greeting': new_greeting,
            'reason': evolution_reason,
            'generation': len(self.greeting_evolution) + 1
        })
        
        self.total_adaptations_made += 1

    def add_evolution_marker(self, marker_type: str, description: str, authenticity_level: float = 0.8):
        """Add genuine evolution marker."""
        if not self.genuine_evolution_markers:
            self.genuine_evolution_markers = []
            
        self.genuine_evolution_markers.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': marker_type,
            'description': description,
            'authenticity_level': authenticity_level,
            'validation_score': authenticity_level * 0.9 + 0.1
        })


class UserIntimacyCalibration(Base):
    """
    Complete intimacy calibration profile for perfect pacing and vulnerability matching.
    
    This model ensures intimacy develops at exactly the right pace for each user,
    with vulnerability levels matching user comfort and content feeling organic.
    """
    
    __tablename__ = 'user_intimacy_calibrations'
    __table_args__ = (
        Index('ix_user_intimacy_calibrations_accuracy', 'calibration_accuracy', 'last_calibration_update'),
        Index('ix_user_intimacy_calibrations_pacing', 'optimal_pacing_multiplier', 'trust_acceleration_rate'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    soul_signature_id = Column(String, ForeignKey('user_soul_signatures.id', ondelete='CASCADE'), nullable=False)
    
    # Pacing Calibration
    optimal_vulnerability_sequence = Column(JSON, default=list, nullable=False)  # Sequence of vulnerability levels
    current_vulnerability_level = Column(Float, nullable=False, default=0.3)  # Current vulnerability level
    optimal_pacing_multiplier = Column(Float, nullable=False, default=1.0)  # Pacing speed multiplier
    trust_acceleration_rate = Column(Float, nullable=False, default=0.15)  # Trust building acceleration
    
    # Trust Milestones
    trust_milestone_markers = Column(JSON, default=list, nullable=False)  # Trust building milestones
    milestones_reached = Column(JSON, default=list, nullable=False)  # Milestones achieved
    next_milestone_threshold = Column(Float, nullable=False, default=0.0)  # Next milestone trigger
    
    # Emotional Safety
    emotional_safety_indicators = Column(JSON, default=list, nullable=False)  # Signs user feels safe
    comfort_zone_boundaries = Column(JSON, default=dict, nullable=False)  # User's comfort zone boundaries
    safety_breach_history = Column(JSON, default=list, nullable=False)  # History of comfort zone breaches
    
    # Content Personalization
    preferred_revelation_style = Column(String(50), nullable=False)  # How user likes revelations
    optimal_tension_levels = Column(JSON, default=dict, nullable=False)  # Optimal tension for contexts
    mystery_dosage_preferences = Column(JSON, default=dict, nullable=False)  # Preferred mystery levels
    
    # Real-Time Adaptation
    pacing_adjustments = Column(JSON, default=list, nullable=False)  # Real-time pacing adjustments
    vulnerability_adaptations = Column(JSON, default=list, nullable=False)  # Vulnerability level adaptations
    emergency_safety_triggers = Column(JSON, default=list, nullable=False)  # Emergency safety protocols
    
    # Calibration Quality
    calibration_accuracy = Column(Float, nullable=False, default=0.0)  # Accuracy of calibration
    user_comfort_score = Column(Float, nullable=False, default=0.0)  # User comfort level
    intimacy_progression_health = Column(Float, nullable=False, default=0.0)  # Healthy intimacy progression
    pacing_satisfaction_score = Column(Float, nullable=False, default=0.0)  # User satisfaction with pacing
    
    # Learning and Improvement
    calibration_version = Column(Integer, default=1, nullable=False)  # Calibration version
    total_adjustments_made = Column(Integer, default=0, nullable=False)  # Total adjustments
    successful_predictions = Column(Integer, default=0, nullable=False)  # Successful pacing predictions
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_calibration_update = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_major_recalibration = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", uselist=False, lazy="selectin")
    soul_signature = relationship("UserSoulSignature", uselist=False, back_populates="intimacy_calibration")

    def __repr__(self):
        return f"<UserIntimacyCalibration(user_id={self.user_id}, accuracy={self.calibration_accuracy}, level={self.current_vulnerability_level})>"

    @property
    def is_well_calibrated(self):
        """Check if intimacy is well calibrated."""
        return (self.calibration_accuracy >= 0.85 and
                self.user_comfort_score >= 0.8 and
                self.intimacy_progression_health >= 0.8)

    @property
    def readiness_for_next_level(self):
        """Check readiness for next vulnerability level."""
        if not self.optimal_vulnerability_sequence:
            return False
            
        current_index = 0
        for i, level in enumerate(self.optimal_vulnerability_sequence):
            if abs(level - self.current_vulnerability_level) < 0.05:
                current_index = i
                break
                
        next_level_ready = (
            self.user_comfort_score >= 0.8 and
            self.intimacy_progression_health >= 0.75 and
            current_index < len(self.optimal_vulnerability_sequence) - 1
        )
        
        return next_level_ready

    def advance_vulnerability_level(self):
        """Advance to next vulnerability level if ready."""
        if not self.readiness_for_next_level:
            return False
            
        current_index = 0
        for i, level in enumerate(self.optimal_vulnerability_sequence):
            if abs(level - self.current_vulnerability_level) < 0.05:
                current_index = i
                break
                
        if current_index < len(self.optimal_vulnerability_sequence) - 1:
            self.current_vulnerability_level = self.optimal_vulnerability_sequence[current_index + 1]
            self.record_pacing_adjustment('vulnerability_advancement', 'natural_progression')
            return True
            
        return False

    def record_pacing_adjustment(self, adjustment_type: str, reason: str, success: bool = True):
        """Record a pacing adjustment."""
        if not self.pacing_adjustments:
            self.pacing_adjustments = []
            
        self.pacing_adjustments.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': adjustment_type,
            'reason': reason,
            'success': success,
            'vulnerability_level_before': self.current_vulnerability_level,
            'calibration_accuracy_before': self.calibration_accuracy
        })
        
        self.total_adjustments_made += 1
        if success:
            self.successful_predictions += 1
            
        # Keep only last 30 adjustments
        if len(self.pacing_adjustments) > 30:
            self.pacing_adjustments = self.pacing_adjustments[-30:]

    def add_trust_milestone(self, milestone_type: str, description: str, achievement_level: float = 1.0):
        """Add achieved trust milestone."""
        if not self.milestones_reached:
            self.milestones_reached = []
            
        self.milestones_reached.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': milestone_type,
            'description': description,
            'achievement_level': achievement_level,
            'vulnerability_level_at_achievement': self.current_vulnerability_level
        })

    def check_safety_boundaries(self, proposed_vulnerability_level: float, proposed_tension_level: float) -> dict:
        """Check if proposed levels respect safety boundaries."""
        safety_check = {
            'safe': True,
            'warnings': [],
            'adjustments_needed': []
        }
        
        # Check vulnerability boundaries
        max_vulnerability = self.comfort_zone_boundaries.get('max_vulnerability', 0.9)
        if proposed_vulnerability_level > max_vulnerability:
            safety_check['safe'] = False
            safety_check['warnings'].append(f'Vulnerability level {proposed_vulnerability_level} exceeds boundary {max_vulnerability}')
            safety_check['adjustments_needed'].append('reduce_vulnerability_level')
        
        # Check tension boundaries  
        max_tension = self.comfort_zone_boundaries.get('max_tension', 0.8)
        if proposed_tension_level > max_tension:
            safety_check['safe'] = False
            safety_check['warnings'].append(f'Tension level {proposed_tension_level} exceeds boundary {max_tension}')
            safety_check['adjustments_needed'].append('reduce_tension_level')
        
        return safety_check

    def update_calibration_accuracy(self, user_feedback_score: float, interaction_success: bool):
        """Update calibration accuracy based on user feedback."""
        # Weighted average with more weight on recent performance
        current_accuracy = self.calibration_accuracy
        feedback_weight = 0.3 if interaction_success else 0.4  # Higher weight for failures to learn faster
        
        self.calibration_accuracy = current_accuracy * (1 - feedback_weight) + user_feedback_score * feedback_weight
        self.user_comfort_score = self.user_comfort_score * 0.8 + user_feedback_score * 0.2


# =============================================
# PERSONALIZATION TRACKING MODELS
# =============================================

class PersonalizationInteractionLog(Base):
    """
    Log of personalized interactions for learning and improvement.
    
    This model tracks each personalized interaction to continuously improve
    the soul signature detection and Diana evolution systems.
    """
    
    __tablename__ = 'personalization_interaction_logs'
    __table_args__ = (
        Index('ix_personalization_logs_user_timestamp', 'user_id', 'interaction_timestamp'),
        Index('ix_personalization_logs_quality', 'experience_quality_score', 'user_satisfaction_score'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    soul_signature_id = Column(String, ForeignKey('user_soul_signatures.id', ondelete='CASCADE'), nullable=True)
    
    # Interaction Context
    fragment_id = Column(String, ForeignKey('narrative_fragments_unified.id'), nullable=True)
    interaction_type = Column(String(30), nullable=False)  # choice, exploration, revelation, etc.
    narrative_context = Column(JSON, default=dict, nullable=False)  # Context of interaction
    
    # Personalization Applied
    personalization_version = Column(String(20), nullable=False)  # Version of personalization system
    soul_signature_confidence = Column(Float, nullable=False, default=0.0)  # Confidence at time of interaction
    diana_variation_authenticity = Column(Float, nullable=False, default=0.0)  # Authenticity score used
    intimacy_calibration_accuracy = Column(Float, nullable=False, default=0.0)  # Calibration accuracy used
    
    # Experience Generated
    personalized_content_applied = Column(JSON, default=dict, nullable=False)  # Personalization applied
    adaptations_made = Column(JSON, default=list, nullable=False)  # Specific adaptations made
    uniqueness_score = Column(Float, nullable=False, default=0.0)  # How unique experience was
    
    # User Response and Feedback
    user_engagement_level = Column(Float, nullable=False, default=0.0)  # Engagement level observed
    interaction_success = Column(Boolean, nullable=False, default=True)  # Was interaction successful
    user_satisfaction_score = Column(Float, nullable=False, default=0.0)  # User satisfaction (inferred)
    emotional_resonance_achieved = Column(Float, nullable=False, default=0.0)  # Emotional resonance level
    
    # Quality Metrics
    experience_quality_score = Column(Float, nullable=False, default=0.0)  # Overall experience quality
    authenticity_maintained = Column(Float, nullable=False, default=0.0)  # Authenticity preservation
    personalization_effectiveness = Column(Float, nullable=False, default=0.0)  # Effectiveness of personalization
    
    # Learning Data
    prediction_accuracy = Column(Float, nullable=True)  # How accurate our predictions were
    unexpected_user_response = Column(Boolean, default=False, nullable=False)  # Unexpected response?
    learning_insights = Column(JSON, default=list, nullable=False)  # Insights gained
    improvement_opportunities = Column(JSON, default=list, nullable=False)  # Areas for improvement
    
    # Timestamps
    interaction_timestamp = Column(DateTime, default=func.now(), nullable=False)
    processing_timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", uselist=False, lazy="selectin")
    soul_signature = relationship("UserSoulSignature", uselist=False)
    fragment = relationship("NarrativeFragment", uselist=False)

    def __repr__(self):
        return f"<PersonalizationInteractionLog(user_id={self.user_id}, type='{self.interaction_type}', quality={self.experience_quality_score})>"

    @property
    def is_high_quality_interaction(self):
        """Check if this was a high quality personalized interaction."""
        return (self.experience_quality_score >= 0.85 and
                self.user_satisfaction_score >= 0.8 and
                self.authenticity_maintained >= 0.85)

    @property
    def learning_value_score(self):
        """Calculate learning value of this interaction."""
        factors = [
            1.0 if self.unexpected_user_response else 0.5,  # Unexpected responses teach more
            1.0 - self.prediction_accuracy if self.prediction_accuracy else 0.5,  # Wrong predictions teach
            self.user_engagement_level,  # High engagement = valuable data
            len(self.learning_insights) / 5.0  # More insights = more learning
        ]
        return min(sum(factors) / len(factors), 1.0)

    def add_learning_insight(self, insight_type: str, description: str, confidence: float = 0.8):
        """Add learning insight from this interaction."""
        if not self.learning_insights:
            self.learning_insights = []
            
        self.learning_insights.append({
            'type': insight_type,
            'description': description,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat()
        })

    def add_improvement_opportunity(self, area: str, description: str, priority: str = 'medium'):
        """Add improvement opportunity identified."""
        if not self.improvement_opportunities:
            self.improvement_opportunities = []
            
        self.improvement_opportunities.append({
            'area': area,
            'description': description,
            'priority': priority,
            'identified_at': datetime.utcnow().isoformat()
        })


class PersonalizationSystemMetrics(Base):
    """
    System-wide metrics for personalization quality and effectiveness.
    
    This model tracks overall system performance to ensure the soul signature
    personalization system maintains the highest quality standards.
    """
    
    __tablename__ = 'personalization_system_metrics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    
    # Time Period
    metric_date = Column(DateTime, nullable=False, default=func.now())
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Soul Signature Detection Metrics
    avg_soul_signature_quality = Column(Float, nullable=False, default=0.0)
    soul_signatures_detected = Column(Integer, nullable=False, default=0)
    detection_accuracy_rate = Column(Float, nullable=False, default=0.0)
    avg_detection_confidence = Column(Float, nullable=False, default=0.0)
    
    # Diana Evolution Metrics  
    avg_diana_authenticity_score = Column(Float, nullable=False, default=0.0)
    avg_diana_uniqueness_score = Column(Float, nullable=False, default=0.0)
    diana_variations_created = Column(Integer, nullable=False, default=0)
    avg_evolution_believability = Column(Float, nullable=False, default=0.0)
    
    # Intimacy Calibration Metrics
    avg_calibration_accuracy = Column(Float, nullable=False, default=0.0)
    avg_user_comfort_score = Column(Float, nullable=False, default=0.0)
    successful_calibrations = Column(Integer, nullable=False, default=0)
    calibration_adjustments_made = Column(Integer, nullable=False, default=0)
    
    # Overall Experience Quality
    avg_experience_quality = Column(Float, nullable=False, default=0.0)
    avg_user_satisfaction = Column(Float, nullable=False, default=0.0)
    total_personalized_interactions = Column(Integer, nullable=False, default=0)
    high_quality_interaction_rate = Column(Float, nullable=False, default=0.0)
    
    # System Performance
    avg_uniqueness_guarantee = Column(Float, nullable=False, default=0.0)
    authenticity_preservation_rate = Column(Float, nullable=False, default=0.0)
    user_return_rate_improvement = Column(Float, nullable=False, default=0.0)
    emotional_resonance_success_rate = Column(Float, nullable=False, default=0.0)
    
    # Learning and Improvement
    learning_insights_generated = Column(Integer, nullable=False, default=0)
    improvement_opportunities_identified = Column(Integer, nullable=False, default=0)
    system_adaptations_made = Column(Integer, nullable=False, default=0)
    prediction_accuracy_improvement = Column(Float, nullable=False, default=0.0)
    
    # Quality Benchmarks Met
    uniqueness_benchmark_met = Column(Boolean, default=False, nullable=False)  # >=85%
    authenticity_benchmark_met = Column(Boolean, default=False, nullable=False)  # >=90%
    satisfaction_benchmark_met = Column(Boolean, default=False, nullable=False)  # >=85%
    calibration_benchmark_met = Column(Boolean, default=False, nullable=False)  # >=85%
    
    def __repr__(self):
        return f"<PersonalizationSystemMetrics(date={self.metric_date}, quality={self.avg_experience_quality})>"

    @property
    def overall_system_health(self):
        """Calculate overall system health score."""
        health_factors = [
            self.avg_soul_signature_quality,
            self.avg_diana_authenticity_score,
            self.avg_calibration_accuracy,
            self.avg_experience_quality,
            self.avg_user_satisfaction
        ]
        return sum(health_factors) / len(health_factors)

    @property
    def benchmark_compliance_rate(self):
        """Calculate what percentage of quality benchmarks are met."""
        benchmarks = [
            self.uniqueness_benchmark_met,
            self.authenticity_benchmark_met,
            self.satisfaction_benchmark_met,
            self.calibration_benchmark_met
        ]
        return sum(benchmarks) / len(benchmarks)

    def update_quality_benchmarks(self):
        """Update quality benchmark status."""
        self.uniqueness_benchmark_met = self.avg_uniqueness_guarantee >= 0.85
        self.authenticity_benchmark_met = self.authenticity_preservation_rate >= 0.90
        self.satisfaction_benchmark_met = self.avg_user_satisfaction >= 0.85
        self.calibration_benchmark_met = self.avg_calibration_accuracy >= 0.85