"""
ArchetypeClassifier - User Personality Archetype Detection and Classification
Implements the 5-archetype system: Explorer, Direct, Poet, Analytic, Patient
"""
import logging
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from enum import Enum

try:
    from .emotional_analysis_service import EmotionalAnalysisService
    from .analytics_service import AnalyticsService
    from ..database.models import User, UserStats, ButtonReaction
    from ..database.emotional_models import ArchetypeClassification, UserEmotionalProfile, EmotionalInteraction
except ImportError:
    # Fallback to absolute imports
    from services.emotional_analysis_service import EmotionalAnalysisService
    from services.analytics_service import AnalyticsService
    from database.models import User, UserStats, ButtonReaction
    from database.emotional_models import ArchetypeClassification, UserEmotionalProfile, EmotionalInteraction

logger = logging.getLogger(__name__)

class UserArchetype(Enum):
    """User personality archetypes for personalized responses."""
    EXPLORER_DEEP = "explorer_deep"
    DIRECT_AUTHENTIC = "direct_authentic"
    POET_DESIRE = "poet_desire"
    ANALYTIC_EMPATHIC = "analytic_empathic"
    PERSISTENT_PATIENT = "persistent_patient"

class ArchetypeClassifier:
    """
    Service for detecting and classifying user personality archetypes
    based on interaction patterns, response timing, and linguistic analysis.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.emotional_service = EmotionalAnalysisService(session)
        self.analytics_service = AnalyticsService(session)

        # Archetype behavioral patterns for classification
        self.archetype_patterns = self._initialize_archetype_patterns()

        # Cache for recent classifications
        self._classification_cache = {}
        self._cache_timeout = timedelta(hours=1)

    def _initialize_archetype_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize archetype behavioral pattern definitions."""
        return {
            UserArchetype.EXPLORER_DEEP.value: {
                "response_time_patterns": {
                    "min": 15.0, "max": 45.0, "preferred": 25.0,
                    "consistency_threshold": 0.7
                },
                "linguistic_markers": [
                    "understand", "deeper", "layers", "complexity", "patterns",
                    "meaning", "explore", "discover", "beneath", "significance",
                    "fascinating", "intriguing", "profound", "nuanced"
                ],
                "behavioral_indicators": [
                    "depth_seeking", "pattern_recognition", "contemplative_processing",
                    "revisitation_patterns", "analytical_curiosity", "thoughtful_engagement"
                ],
                "emotional_traits": {
                    "vulnerability_progression": 0.6,
                    "authenticity_preference": 0.8,
                    "complexity_tolerance": 0.9,
                    "patience_level": 0.8
                }
            },
            UserArchetype.DIRECT_AUTHENTIC.value: {
                "response_time_patterns": {
                    "min": 1.0, "max": 8.0, "preferred": 4.0,
                    "consistency_threshold": 0.8
                },
                "linguistic_markers": [
                    "honest", "real", "genuine", "truth", "authentic", "direct",
                    "straightforward", "clear", "simple", "honest", "plain",
                    "no games", "real talk", "cut through", "straight up"
                ],
                "behavioral_indicators": [
                    "immediate_response", "emotional_directness", "authenticity_seeking",
                    "no_pretense", "clear_communication", "genuine_expression"
                ],
                "emotional_traits": {
                    "vulnerability_progression": 0.8,
                    "authenticity_preference": 0.95,
                    "complexity_tolerance": 0.4,
                    "patience_level": 0.3
                }
            },
            UserArchetype.POET_DESIRE.value: {
                "response_time_patterns": {
                    "min": 12.0, "max": 35.0, "preferred": 22.0,
                    "consistency_threshold": 0.6
                },
                "linguistic_markers": [
                    "beautiful", "poetry", "whisper", "touch", "feeling", "soul",
                    "aesthetic", "elegant", "graceful", "delicate", "sensual",
                    "longing", "desire", "beauty", "art", "metaphor", "imagery"
                ],
                "behavioral_indicators": [
                    "aesthetic_appreciation", "metaphorical_thinking", "sensual_language",
                    "beauty_focus", "artistic_expression", "emotional_aesthetics"
                ],
                "emotional_traits": {
                    "vulnerability_progression": 0.7,
                    "authenticity_preference": 0.7,
                    "complexity_tolerance": 0.8,
                    "patience_level": 0.9
                }
            },
            UserArchetype.ANALYTIC_EMPATHIC.value: {
                "response_time_patterns": {
                    "min": 20.0, "max": 50.0, "preferred": 32.0,
                    "consistency_threshold": 0.75
                },
                "linguistic_markers": [
                    "understand", "analyze", "recognize", "paradox", "complexity",
                    "perspective", "insight", "wisdom", "empathy", "balance",
                    "nuance", "sophisticated", "comprehend", "integrate"
                ],
                "behavioral_indicators": [
                    "analytical_thinking", "empathetic_understanding", "paradox_acceptance",
                    "sophisticated_analysis", "emotional_intelligence", "wise_perspective"
                ],
                "emotional_traits": {
                    "vulnerability_progression": 0.6,
                    "authenticity_preference": 0.8,
                    "complexity_tolerance": 0.95,
                    "patience_level": 0.9
                }
            },
            UserArchetype.PERSISTENT_PATIENT.value: {
                "response_time_patterns": {
                    "min": 8.0, "max": 25.0, "preferred": 15.0,
                    "consistency_threshold": 0.85
                },
                "linguistic_markers": [
                    "patient", "wait", "time", "journey", "process", "build",
                    "persistent", "devoted", "commitment", "steady", "gradual",
                    "worth waiting", "take time", "step by step", "long term"
                ],
                "behavioral_indicators": [
                    "consistent_engagement", "long_term_thinking", "patience_demonstration",
                    "commitment_signals", "steady_progression", "loyalty_indicators"
                ],
                "emotional_traits": {
                    "vulnerability_progression": 0.5,
                    "authenticity_preference": 0.7,
                    "complexity_tolerance": 0.6,
                    "patience_level": 0.95
                }
            }
        }

    async def classify_user(
        self,
        user_id: int,
        conversation_data: List[Dict[str, Any]],
        force_reclassify: bool = False
    ) -> Dict[str, Any]:
        """
        Classify user's personality archetype based on interaction patterns.

        Args:
            user_id: User ID to classify
            conversation_data: List of user responses and interactions
            force_reclassify: Force new classification even if cached

        Returns:
            Dict with classification results and confidence scores
        """
        try:
            # Check cache first
            cache_key = f"classify_{user_id}"
            if not force_reclassify and self._is_cache_valid(cache_key):
                return self._classification_cache[cache_key]

            # Validate input data
            if not conversation_data or len(conversation_data) < 2:
                return {
                    "classification_status": "insufficient_data",
                    "primary_archetype": None,
                    "confidence_score": 0.0,
                    "recommended_action": "gather_more_data",
                    "data_points_needed": max(2, 5 - len(conversation_data))
                }

            # Analyze user behavior patterns
            timing_analysis = await self._analyze_response_timing(conversation_data)
            linguistic_analysis = await self._analyze_linguistic_patterns(conversation_data)
            behavioral_analysis = await self._analyze_behavioral_indicators(user_id, conversation_data)

            # Calculate archetype scores
            archetype_scores = {}
            for archetype in UserArchetype:
                score = await self._calculate_archetype_score(
                    archetype.value,
                    timing_analysis,
                    linguistic_analysis,
                    behavioral_analysis
                )
                archetype_scores[archetype.value] = score

            # Determine primary archetype and confidence
            primary_archetype, confidence = self._determine_primary_archetype(archetype_scores)

            # Analyze for mixed traits
            secondary_archetypes = self._identify_secondary_archetypes(archetype_scores, confidence)

            # Check for artificial behavior patterns
            authenticity_analysis = self._analyze_authenticity(conversation_data)

            result = {
                "classification_status": "success" if confidence > 0.6 else "low_confidence",
                "primary_archetype": primary_archetype,
                "confidence_score": confidence,
                "archetype_scores": archetype_scores,
                "secondary_archetypes": secondary_archetypes,
                "key_traits": self._extract_key_traits(primary_archetype, archetype_scores),
                "classification_type": "mixed_traits" if len(secondary_archetypes) > 0 else "clear_classification",
                "timing_analysis": timing_analysis,
                "linguistic_analysis": linguistic_analysis,
                "behavioral_analysis": behavioral_analysis,
                "authenticity_analysis": authenticity_analysis,
                "classified_at": datetime.utcnow().isoformat()
            }

            # Cache result
            self._cache_classification(cache_key, result)

            # Store in database if high confidence
            if confidence > 0.7:
                await self._store_archetype_classification(user_id, result)

            return result

        except Exception as e:
            logger.error(f"Error classifying user {user_id}: {str(e)}")
            return {
                "classification_status": "error",
                "primary_archetype": None,
                "confidence_score": 0.0,
                "error": str(e)
            }

    async def _analyze_response_timing(
        self,
        conversation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user response timing patterns."""
        response_times = [
            item.get("response_time", 10.0)
            for item in conversation_data
            if item.get("response_time")
        ]

        if not response_times:
            return {"pattern": "no_timing_data", "consistency": 0.0}

        # Calculate timing statistics
        avg_time = sum(response_times) / len(response_times)
        variance = sum((t - avg_time) ** 2 for t in response_times) / len(response_times)
        consistency = max(0.0, 1.0 - (variance / max(avg_time ** 2, 1)))

        # Categorize timing pattern
        if avg_time < 5:
            pattern = "immediate"
        elif avg_time < 15:
            pattern = "quick"
        elif avg_time < 30:
            pattern = "thoughtful"
        else:
            pattern = "contemplative"

        return {
            "pattern": pattern,
            "average_time": avg_time,
            "consistency": consistency,
            "response_count": len(response_times),
            "time_distribution": {
                "min": min(response_times),
                "max": max(response_times),
                "variance": variance
            }
        }

    async def _analyze_linguistic_patterns(
        self,
        conversation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze linguistic patterns in user responses."""
        all_text = " ".join([
            item.get("response", "").lower()
            for item in conversation_data
            if item.get("response")
        ])

        if not all_text.strip():
            return {"markers_found": {}, "total_markers": 0}

        # Find archetype-specific linguistic markers
        markers_found = {}
        for archetype, patterns in self.archetype_patterns.items():
            markers = patterns["linguistic_markers"]
            found_markers = []

            for marker in markers:
                if marker.lower() in all_text:
                    # Count occurrences
                    count = len(re.findall(r'\b' + re.escape(marker.lower()) + r'\b', all_text))
                    if count > 0:
                        found_markers.append({"marker": marker, "count": count})

            markers_found[archetype] = found_markers

        # Calculate linguistic complexity
        word_count = len(all_text.split())
        avg_word_length = sum(len(word) for word in all_text.split()) / max(word_count, 1)

        return {
            "markers_found": markers_found,
            "total_markers": sum(len(markers) for markers in markers_found.values()),
            "linguistic_complexity": {
                "word_count": word_count,
                "average_word_length": avg_word_length,
                "sentence_count": len([s for s in all_text.split('.') if s.strip()])
            }
        }

    async def _analyze_behavioral_indicators(
        self,
        user_id: int,
        conversation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze behavioral indicators from conversation data."""

        # Extract behavioral markers if provided
        all_behavioral_markers = []
        for item in conversation_data:
            markers = item.get("behavioral_markers", [])
            if isinstance(markers, list):
                all_behavioral_markers.extend(markers)

        # Get engagement patterns if provided
        engagement_patterns = [
            item.get("engagement_pattern", "neutral")
            for item in conversation_data
            if item.get("engagement_pattern")
        ]

        # Analyze consistency in behavioral patterns
        behavioral_consistency = self._calculate_behavioral_consistency(all_behavioral_markers)

        return {
            "behavioral_markers": all_behavioral_markers,
            "engagement_patterns": engagement_patterns,
            "behavioral_consistency": behavioral_consistency,
            "marker_frequency": self._count_marker_frequency(all_behavioral_markers)
        }

    def _calculate_behavioral_consistency(self, markers: List[str]) -> float:
        """Calculate consistency of behavioral markers."""
        if not markers:
            return 0.0

        # Group markers by archetype alignment
        archetype_alignment = {}
        for archetype, patterns in self.archetype_patterns.items():
            alignment_count = 0
            for marker in markers:
                if marker in patterns["behavioral_indicators"]:
                    alignment_count += 1
            archetype_alignment[archetype] = alignment_count

        # Calculate consistency as concentration in one archetype
        total_markers = len(markers)
        max_alignment = max(archetype_alignment.values()) if archetype_alignment else 0

        return max_alignment / max(total_markers, 1)

    def _count_marker_frequency(self, markers: List[str]) -> Dict[str, int]:
        """Count frequency of behavioral markers."""
        frequency = {}
        for marker in markers:
            frequency[marker] = frequency.get(marker, 0) + 1
        return frequency

    async def _calculate_archetype_score(
        self,
        archetype: str,
        timing_analysis: Dict[str, Any],
        linguistic_analysis: Dict[str, Any],
        behavioral_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall score for a specific archetype."""

        patterns = self.archetype_patterns.get(archetype, {})
        if not patterns:
            return 0.0

        score_components = []

        # Timing score
        timing_score = self._calculate_timing_score(archetype, timing_analysis)
        score_components.append(("timing", timing_score, 0.3))

        # Linguistic score
        linguistic_score = self._calculate_linguistic_score(archetype, linguistic_analysis)
        score_components.append(("linguistic", linguistic_score, 0.4))

        # Behavioral score
        behavioral_score = self._calculate_behavioral_score(archetype, behavioral_analysis)
        score_components.append(("behavioral", behavioral_score, 0.3))

        # Weighted average
        total_score = sum(score * weight for _, score, weight in score_components)

        return min(1.0, max(0.0, total_score))

    def _calculate_timing_score(self, archetype: str, timing_analysis: Dict[str, Any]) -> float:
        """Calculate timing alignment score for archetype."""
        patterns = self.archetype_patterns.get(archetype, {})
        timing_patterns = patterns.get("response_time_patterns", {})

        avg_time = timing_analysis.get("average_time", 10.0)
        consistency = timing_analysis.get("consistency", 0.0)

        # Score based on timing preference
        preferred_time = timing_patterns.get("preferred", 10.0)
        min_time = timing_patterns.get("min", 1.0)
        max_time = timing_patterns.get("max", 60.0)
        consistency_threshold = timing_patterns.get("consistency_threshold", 0.5)

        # Time alignment score
        if min_time <= avg_time <= max_time:
            time_diff = abs(avg_time - preferred_time)
            time_range = max_time - min_time
            time_score = 1.0 - (time_diff / time_range)
        else:
            time_score = 0.0

        # Consistency score
        consistency_score = 1.0 if consistency >= consistency_threshold else consistency / consistency_threshold

        return (time_score * 0.7 + consistency_score * 0.3)

    def _calculate_linguistic_score(self, archetype: str, linguistic_analysis: Dict[str, Any]) -> float:
        """Calculate linguistic alignment score for archetype."""
        markers_found = linguistic_analysis.get("markers_found", {})
        archetype_markers = markers_found.get(archetype, [])

        if not archetype_markers:
            return 0.0

        # Score based on number and frequency of markers found
        total_marker_count = sum(marker["count"] for marker in archetype_markers)
        unique_markers = len(archetype_markers)

        # Normalize scores
        marker_count_score = min(1.0, total_marker_count / 10.0)  # Max at 10 occurrences
        diversity_score = min(1.0, unique_markers / 5.0)  # Max at 5 different markers

        return (marker_count_score * 0.6 + diversity_score * 0.4)

    def _calculate_behavioral_score(self, archetype: str, behavioral_analysis: Dict[str, Any]) -> float:
        """Calculate behavioral alignment score for archetype."""
        patterns = self.archetype_patterns.get(archetype, {})
        expected_indicators = patterns.get("behavioral_indicators", [])

        found_markers = behavioral_analysis.get("behavioral_markers", [])

        if not found_markers or not expected_indicators:
            return 0.0

        # Calculate overlap between found markers and expected indicators
        matches = sum(1 for marker in found_markers if marker in expected_indicators)
        overlap_score = matches / len(expected_indicators)

        # Bonus for consistency
        consistency = behavioral_analysis.get("behavioral_consistency", 0.0)

        return (overlap_score * 0.8 + consistency * 0.2)

    def _determine_primary_archetype(self, archetype_scores: Dict[str, float]) -> Tuple[str, float]:
        """Determine primary archetype and confidence from scores."""
        if not archetype_scores:
            return None, 0.0

        # Find highest scoring archetype
        primary_archetype = max(archetype_scores.items(), key=lambda x: x[1])
        archetype_name, top_score = primary_archetype

        # Calculate confidence based on score separation
        sorted_scores = sorted(archetype_scores.values(), reverse=True)

        if len(sorted_scores) < 2:
            confidence = top_score
        else:
            score_separation = sorted_scores[0] - sorted_scores[1]
            confidence = min(1.0, top_score + score_separation)

        return archetype_name, confidence

    def _identify_secondary_archetypes(
        self,
        archetype_scores: Dict[str, float],
        primary_confidence: float
    ) -> List[str]:
        """Identify secondary archetypes if confidence is mixed."""
        if primary_confidence > 0.8:
            return []

        # Find archetypes with significant scores
        secondary = []
        sorted_archetypes = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)

        for archetype, score in sorted_archetypes[1:]:
            if score > 0.4:  # Significant secondary score
                secondary.append(archetype)

        return secondary

    def _extract_key_traits(self, primary_archetype: str, archetype_scores: Dict[str, float]) -> Dict[str, float]:
        """Extract key personality traits from classification."""
        if not primary_archetype:
            return {}

        patterns = self.archetype_patterns.get(primary_archetype, {})
        emotional_traits = patterns.get("emotional_traits", {})

        # Adjust traits based on archetype score
        archetype_score = archetype_scores.get(primary_archetype, 0.0)

        key_traits = {}
        for trait, base_value in emotional_traits.items():
            # Scale trait strength by archetype confidence
            adjusted_value = base_value * archetype_score
            key_traits[trait] = round(adjusted_value, 2)

        # Add archetype-specific traits
        archetype_specific_traits = self._get_archetype_specific_traits(primary_archetype, archetype_score)
        key_traits.update(archetype_specific_traits)

        return key_traits

    def _get_archetype_specific_traits(self, archetype: str, score: float) -> Dict[str, float]:
        """Get traits specific to each archetype."""
        trait_mapping = {
            UserArchetype.EXPLORER_DEEP.value: {
                "depth_seeking": score * 0.9,
                "pattern_recognition": score * 0.8,
                "thoughtful_engagement": score * 0.85
            },
            UserArchetype.DIRECT_AUTHENTIC.value: {
                "directness": score * 0.95,
                "authenticity": score * 0.9,
                "emotional_clarity": score * 0.8
            },
            UserArchetype.POET_DESIRE.value: {
                "aesthetic_sensitivity": score * 0.9,
                "metaphorical_thinking": score * 0.85,
                "beauty_appreciation": score * 0.8
            },
            UserArchetype.ANALYTIC_EMPATHIC.value: {
                "analytical_thinking": score * 0.9,
                "empathetic_understanding": score * 0.85,
                "paradox_acceptance": score * 0.8
            },
            UserArchetype.PERSISTENT_PATIENT.value: {
                "persistence": score * 0.9,
                "patience": score * 0.95,
                "commitment": score * 0.85
            }
        }

        return trait_mapping.get(archetype, {})

    def _analyze_authenticity(self, conversation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze authenticity indicators in conversation data."""

        # Check for artificial behavior flags
        artificial_flags = {
            "too_consistent_timing": False,
            "generic_language": False,
            "lack_of_genuine_markers": False,
            "repetitive_patterns": False
        }

        response_times = [item.get("response_time", 0) for item in conversation_data if item.get("response_time")]
        responses = [item.get("response", "") for item in conversation_data if item.get("response")]

        # Check timing consistency (too perfect = suspicious)
        if len(response_times) >= 3:
            time_variance = sum((t - sum(response_times)/len(response_times))**2 for t in response_times) / len(response_times)
            if time_variance < 0.5:  # Very consistent timing
                artificial_flags["too_consistent_timing"] = True

        # Check for generic language patterns
        generic_phrases = [
            "this is exactly what", "precisely what", "perfect in every way",
            "exactly as intended", "this is perfect"
        ]

        generic_count = sum(1 for response in responses for phrase in generic_phrases if phrase in response.lower())
        if generic_count > len(responses) * 0.3:
            artificial_flags["generic_language"] = True

        # Check for genuine emotional markers
        genuine_markers = [
            "i feel", "this touches", "i'm surprised", "unexpected", "confusing",
            "i don't know", "maybe", "perhaps", "i think", "seems like"
        ]

        genuine_count = sum(1 for response in responses for marker in genuine_markers if marker in response.lower())
        if genuine_count == 0 and len(responses) > 2:
            artificial_flags["lack_of_genuine_markers"] = True

        # Calculate overall authenticity score
        authenticity_score = 1.0 - (sum(artificial_flags.values()) * 0.25)

        return {
            "artificial_behavior_flags": artificial_flags,
            "overall_authenticity_score": max(0.0, authenticity_score),
            "genuine_markers_found": genuine_count,
            "analysis_confidence": min(0.9, len(conversation_data) * 0.2)
        }

    async def get_user_archetype(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get stored archetype classification for a user."""
        try:
            # Check database first
            result = await self.session.execute(
                select(ArchetypeClassification).where(ArchetypeClassification.user_id == user_id)
            )
            classification = result.scalar_one_or_none()

            if classification:
                return {
                    "primary_archetype": classification.primary_archetype,
                    "confidence": classification.archetype_confidence,
                    "secondary_traits": json.loads(classification.secondary_traits or "[]"),
                    "last_updated": classification.updated_at.isoformat(),
                    "stability": classification.archetype_stability
                }

            return None

        except Exception as e:
            logger.error(f"Error getting user archetype for {user_id}: {str(e)}")
            return None

    async def _store_archetype_classification(self, user_id: int, result: Dict[str, Any]) -> None:
        """Store archetype classification in database."""
        try:
            # Check if classification exists
            existing = await self.session.execute(
                select(ArchetypeClassification).where(ArchetypeClassification.user_id == user_id)
            )
            classification = existing.scalar_one_or_none()

            if classification:
                # Update existing
                old_archetype = classification.primary_archetype
                new_archetype = result["primary_archetype"]

                classification.primary_archetype = new_archetype
                classification.archetype_confidence = result["confidence_score"]
                classification.secondary_traits = json.dumps(result.get("secondary_archetypes", []))
                classification.updated_at = datetime.utcnow()

                # Track archetype changes for stability
                if old_archetype != new_archetype:
                    classification.last_classification_change = datetime.utcnow()
                    classification.archetype_stability = max(0.0, classification.archetype_stability - 0.1)
                else:
                    classification.archetype_stability = min(1.0, classification.archetype_stability + 0.05)
            else:
                # Create new
                classification = ArchetypeClassification(
                    user_id=user_id,
                    primary_archetype=result["primary_archetype"],
                    archetype_confidence=result["confidence_score"],
                    secondary_traits=json.dumps(result.get("secondary_archetypes", [])),
                    archetype_stability=0.7  # Initial stability
                )
                self.session.add(classification)

            await self.session.commit()

        except Exception as e:
            logger.error(f"Error storing archetype classification for {user_id}: {str(e)}")
            await self.session.rollback()

    async def analyze_archetype_evolution(
        self,
        user_id: int,
        classification_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze how a user's archetype has evolved over time."""
        try:
            if len(classification_history) < 2:
                return {
                    "evolution_detected": False,
                    "reason": "insufficient_history"
                }

            # Extract archetype sequence
            archetype_sequence = [result["primary_archetype"] for result in classification_history]
            confidence_sequence = [result["confidence_score"] for result in classification_history]

            # Detect evolution patterns
            unique_archetypes = set(archetype_sequence)
            evolution_detected = len(unique_archetypes) > 1

            if not evolution_detected:
                return {
                    "evolution_detected": False,
                    "final_archetype": archetype_sequence[-1],
                    "stability_score": sum(confidence_sequence) / len(confidence_sequence),
                    "evolution_type": "stable"
                }

            # Analyze evolution type
            evolution_type = self._classify_evolution_pattern(archetype_sequence)

            # Calculate evolution coherence
            coherence_score = self._calculate_evolution_coherence(archetype_sequence)

            return {
                "evolution_detected": True,
                "evolution_type": evolution_type,
                "final_archetype": archetype_sequence[-1],
                "archetype_sequence": archetype_sequence,
                "evolution_coherence_score": coherence_score,
                "confidence_progression": confidence_sequence,
                "unique_archetypes_count": len(unique_archetypes)
            }

        except Exception as e:
            logger.error(f"Error analyzing archetype evolution for {user_id}: {str(e)}")
            return {"evolution_detected": False, "error": str(e)}

    def _classify_evolution_pattern(self, sequence: List[str]) -> str:
        """Classify the type of archetype evolution pattern."""
        if len(sequence) < 2:
            return "stable"

        # Check for natural progression patterns
        natural_progressions = {
            ("explorer_cautious", "explorer_deep"): "natural_deepening",
            ("direct_authentic", "analytic_empathic"): "intellectual_growth",
            ("poet_desire", "analytic_empathic"): "aesthetic_to_analytical",
            ("persistent_patient", "explorer_deep"): "patience_to_exploration"
        }

        for i in range(len(sequence) - 1):
            transition = (sequence[i], sequence[i + 1])
            if transition in natural_progressions:
                return natural_progressions[transition]

        # Check for erratic changes
        changes = sum(1 for i in range(1, len(sequence)) if sequence[i] != sequence[i-1])
        if changes > len(sequence) / 2:
            return "erratic"

        return "gradual_shift"

    def _calculate_evolution_coherence(self, sequence: List[str]) -> float:
        """Calculate how coherent the archetype evolution is."""
        if len(sequence) < 2:
            return 1.0

        # Define archetype relationships (how logically one can evolve into another)
        relationship_matrix = {
            "explorer_deep": {"analytic_empathic": 0.8, "poet_desire": 0.6, "persistent_patient": 0.7},
            "direct_authentic": {"analytic_empathic": 0.7, "explorer_deep": 0.5},
            "poet_desire": {"analytic_empathic": 0.8, "explorer_deep": 0.6},
            "analytic_empathic": {"explorer_deep": 0.8, "poet_desire": 0.7},
            "persistent_patient": {"explorer_deep": 0.8, "analytic_empathic": 0.6}
        }

        coherence_scores = []
        for i in range(len(sequence) - 1):
            from_archetype = sequence[i]
            to_archetype = sequence[i + 1]

            if from_archetype == to_archetype:
                coherence_scores.append(1.0)  # Staying the same is perfectly coherent
            else:
                relationship_score = relationship_matrix.get(from_archetype, {}).get(to_archetype, 0.3)
                coherence_scores.append(relationship_score)

        return sum(coherence_scores) / len(coherence_scores)

    async def analyze_archetype_stability(
        self,
        user_id: int,
        recent_classifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze stability of archetype classification over time."""
        try:
            if len(recent_classifications) < 3:
                return {
                    "stability_score": 0.5,
                    "consistency_flags": {"insufficient_data": True},
                    "recommended_action": "gather_more_data"
                }

            # Extract recent archetypes and confidences
            recent_archetypes = [cls["primary_archetype"] for cls in recent_classifications]
            recent_confidences = [cls["confidence_score"] for cls in recent_classifications]

            # Calculate stability metrics
            unique_archetypes = set(recent_archetypes)
            archetype_consistency = 1.0 - (len(unique_archetypes) - 1) / len(recent_archetypes)

            confidence_consistency = 1.0 - (max(recent_confidences) - min(recent_confidences))

            # Overall stability score
            stability_score = (archetype_consistency * 0.7 + confidence_consistency * 0.3)

            # Identify consistency flags
            consistency_flags = {
                "stable": stability_score > 0.8,
                "minor_fluctuation": 0.6 < stability_score <= 0.8,
                "erratic_behavior": stability_score < 0.3,
                "insufficient_data": False
            }

            # Recommend action
            if stability_score > 0.8:
                recommended_action = "classification_reliable"
            elif stability_score > 0.6:
                recommended_action = "monitor_trends"
            else:
                recommended_action = "requires_observation"

            return {
                "stability_score": stability_score,
                "archetype_consistency": archetype_consistency,
                "confidence_consistency": confidence_consistency,
                "consistency_flags": consistency_flags,
                "recommended_action": recommended_action,
                "analysis_period": len(recent_classifications)
            }

        except Exception as e:
            logger.error(f"Error analyzing archetype stability for {user_id}: {str(e)}")
            return {
                "stability_score": 0.0,
                "consistency_flags": {"error": True},
                "recommended_action": "requires_observation"
            }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached classification is still valid."""
        if cache_key not in self._classification_cache:
            return False

        cached_item = self._classification_cache[cache_key]
        cache_time = cached_item.get("cached_at", datetime.min)

        if isinstance(cache_time, str):
            cache_time = datetime.fromisoformat(cache_time)

        age = datetime.utcnow() - cache_time
        return age < self._cache_timeout

    def _cache_classification(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache classification result."""
        result["cached_at"] = datetime.utcnow()
        self._classification_cache[cache_key] = result

        # Basic cache cleanup
        if len(self._classification_cache) > 100:
            oldest_key = min(
                self._classification_cache.keys(),
                key=lambda k: self._classification_cache[k].get("cached_at", datetime.min)
            )
            del self._classification_cache[oldest_key]