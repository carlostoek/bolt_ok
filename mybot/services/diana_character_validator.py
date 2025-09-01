"""
Diana Character Consistency Validation Framework

This framework ensures Diana maintains her mysterious, seductive personality 
across all interactions while providing automated testing and scoring capabilities.

Character Profile:
- Mysterious: Never reveals too much, always maintains intrigue  
- Seductive: Subtle charm and allure in interactions
- Emotionally Complex: Deep emotional layers, not simple responses
- Intellectually Engaging: Stimulates curiosity and thought
"""

import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

class DianaPersonalityTrait(Enum):
    """Diana's core personality traits for validation."""
    MYSTERIOUS = "mysterious"
    SEDUCTIVE = "seductive" 
    EMOTIONALLY_COMPLEX = "emotionally_complex"
    INTELLECTUALLY_ENGAGING = "intellectually_engaging"

@dataclass
class CharacterValidationResult:
    """Result of character consistency validation."""
    overall_score: float
    trait_scores: Dict[DianaPersonalityTrait, float]
    violations: List[str]
    recommendations: List[str]
    meets_threshold: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "trait_scores": {trait.value: score for trait, score in self.trait_scores.items()},
            "violations": self.violations,
            "recommendations": self.recommendations,
            "meets_threshold": self.meets_threshold
        }

class DianaCharacterValidator:
    """
    Validates Diana's character consistency across all interactions.
    Provides automated scoring based on personality traits.
    """
    
    # Minimum score threshold for character consistency (95/100 required)
    MIN_CONSISTENCY_SCORE = 95.0
    
    # Weight distribution for personality traits
    TRAIT_WEIGHTS = {
        DianaPersonalityTrait.MYSTERIOUS: 0.25,
        DianaPersonalityTrait.SEDUCTIVE: 0.25,
        DianaPersonalityTrait.EMOTIONALLY_COMPLEX: 0.25,
        DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: 0.25
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mysterious_patterns = self._load_mysterious_patterns()
        self.seductive_patterns = self._load_seductive_patterns()
        self.emotional_patterns = self._load_emotional_patterns()
        self.intellectual_patterns = self._load_intellectual_patterns()
        self.violation_patterns = self._load_violation_patterns()
    
    def _load_mysterious_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate mysterious personality."""
        return {
            "positive_indicators": [
                r"secretos?\s+que",
                r"misterio",
                r"enigma", 
                r"oculto",
                r"susurra",
                r"insinúa",
                r"sugiere",
                r"pistas?",
                r"indicios?",
                r"sombras?",
                r"velos?",
                r"no todo lo que",
                r"¿acaso sabes",
                r"tal vez",
                r"quizás",
                r"...\.\.",  # Ellipsis indicating trailing off
                r"¿será que",
                r"hay más de lo que",
                r"entre líneas"
            ],
            "sentence_structures": [
                r"[A-Z][^.!?]*\.\.\.[^.!?]*[.!?]",  # Sentences with ellipsis
                r"¿[^?]+\?\.\.\.",  # Questions trailing off
                r"[^.!?]*susurr[a-z]+[^.!?]*[.!?]",  # Whispering
                r"[^.!?]*insinú[a-z]+[^.!?]*[.!?]"   # Insinuating
            ]
        }
    
    def _load_seductive_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate seductive personality."""
        return {
            "positive_indicators": [
                r"💋",
                r"encanto",
                r"seductor[a]?",
                r"tentador[a]?", 
                r"irresistible",
                r"fascinan?t?e",
                r"cautivador[a]?",
                r"hechizo",
                r"embrujo",
                r"magnetism[o]?",
                r"atractiv[o|a]",
                r"sensual",
                r"provocativ[o|a]",
                r"sugerente",
                r"coqueto",
                r"encantador[a]?",
                r"mi querido",
                r"cariño",
                r"tesoro"
            ],
            "tone_indicators": [
                r"[^.!?]*susurra[^.!?]*[.!?]",
                r"[^.!?]*murmura[^.!?]*[.!?]",
                r"con una sonrisa",
                r"guiña el ojo",
                r"sonríe pícara"
            ]
        }
    
    def _load_emotional_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate emotional complexity."""
        return {
            "positive_indicators": [
                r"sentimientos?",
                r"emociones?",
                r"corazón",
                r"alma",
                r"profundidad",
                r"vulnerabilidad", 
                r"melancolía",
                r"nostalgia",
                r"anhelo",
                r"deseo",
                r"esperanza",
                r"temor",
                r"inquietud",
                r"turbación",
                r"conflicto interno",
                r"dilema"
            ],
            "complexity_indicators": [
                r"por un lado.*por otro",
                r"aunque.*sin embargo",
                r"mezcla de",
                r"entre.*y",
                r"tanto.*como",
                r"contradicción",
                r"paradoja"
            ]
        }
    
    def _load_intellectual_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate intellectual engagement."""
        return {
            "positive_indicators": [
                r"filosofía",
                r"reflexión",
                r"contemplar?",
                r"meditar?",
                r"analizar?",
                r"interpretar?",
                r"significado",
                r"comprensión",
                r"sabiduría",
                r"conocimiento",
                r"perspectiva",
                r"dimensión",
                r"complejidad",
                r"profundizar?",
                r"explorar?",
                r"descubrir?",
                r"revelar?"
            ],
            "engagement_patterns": [
                r"¿has pensado en",
                r"¿te has preguntado",
                r"considera esto",
                r"imagina que",
                r"reflexiona sobre",
                r"¿qué opinas de",
                r"¿cómo interpretas"
            ]
        }
    
    def _load_violation_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that violate Diana's character."""
        return {
            "too_direct": [
                r"directamente",
                r"sin rodeos",
                r"claramente",
                r"obviamente",
                r"evidentemente",
                r"^[A-Z][^.!?]*\.$",  # Too simple, direct statements
            ],
            "too_casual": [
                r"\bhola\b",
                r"\bokay\b", 
                r"\bgenial\b",
                r"\bperfecto\b",
                r"jaja",
                r"jeje",
                r"emoticons?",
                r"😀|😁|😂|🤣|😃|😄"  # Too cheerful emojis
            ],
            "technical_language": [
                r"sistema",
                r"configuración",
                r"parámetros?",
                r"opciones?",
                r"settings?",
                r"menú",
                r"botón"
            ],
            "robotic_responses": [
                r"^(sí|no), [a-z]",
                r"proceso completado",
                r"operación exitosa",
                r"error en",
                r"comando ejecutado"
            ]
        }
    
    async def validate_text(self, text: str, context: Optional[str] = None) -> CharacterValidationResult:
        """
        Validate character consistency of a text.
        
        Args:
            text: The text to validate
            context: Optional context (e.g., "narrative_fragment", "menu_response")
            
        Returns:
            CharacterValidationResult with scores and recommendations
        """
        if not text or not text.strip():
            return CharacterValidationResult(
                overall_score=0.0,
                trait_scores={trait: 0.0 for trait in DianaPersonalityTrait},
                violations=["Empty or whitespace-only text"],
                recommendations=["Provide substantive content for Diana"],
                meets_threshold=False
            )
        
        # Calculate scores for each personality trait
        trait_scores = {}
        violations = []
        recommendations = []
        
        # Validate mysterious trait
        mysterious_score = self._validate_mysterious_trait(text)
        trait_scores[DianaPersonalityTrait.MYSTERIOUS] = mysterious_score
        if mysterious_score < 15.0:  # Below 60% of max 25 points
            violations.append(f"Insufficient mysterious quality (score: {mysterious_score:.1f}/25)")
            recommendations.append("Add more mystery - use ellipsis, suggestions, hints rather than direct statements")
        
        # Validate seductive trait
        seductive_score = self._validate_seductive_trait(text)
        trait_scores[DianaPersonalityTrait.SEDUCTIVE] = seductive_score
        if seductive_score < 15.0:
            violations.append(f"Insufficient seductive charm (score: {seductive_score:.1f}/25)")
            recommendations.append("Include subtle charm - use enticing language and emotional connection")
        
        # Validate emotional complexity
        emotional_score = self._validate_emotional_trait(text)
        trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX] = emotional_score
        if emotional_score < 15.0:
            violations.append(f"Insufficient emotional depth (score: {emotional_score:.1f}/25)")
            recommendations.append("Add emotional layers - show inner conflict, deeper feelings, vulnerability")
        
        # Validate intellectual engagement
        intellectual_score = self._validate_intellectual_trait(text)
        trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING] = intellectual_score
        if intellectual_score < 15.0:
            violations.append(f"Insufficient intellectual stimulation (score: {intellectual_score:.1f}/25)")
            recommendations.append("Engage the mind - pose questions, invite reflection, offer deeper perspectives")
        
        # Check for character violations
        violation_penalty = self._check_character_violations(text)
        for trait in trait_scores:
            trait_scores[trait] = max(0, trait_scores[trait] - violation_penalty)
        
        # Calculate overall score
        overall_score = sum(
            trait_scores[trait] * self.TRAIT_WEIGHTS[trait] 
            for trait in DianaPersonalityTrait
        )
        
        # Additional context-specific validation
        if context:
            context_violations, context_recommendations = self._validate_context_specific(text, context)
            violations.extend(context_violations)
            recommendations.extend(context_recommendations)
        
        return CharacterValidationResult(
            overall_score=overall_score,
            trait_scores=trait_scores,
            violations=violations,
            recommendations=recommendations,
            meets_threshold=overall_score >= self.MIN_CONSISTENCY_SCORE
        )
    
    def _validate_mysterious_trait(self, text: str) -> float:
        """Validate mysterious personality trait (0-25 points)."""
        score = 0.0
        text_lower = text.lower()
        
        # Check for mysterious language patterns
        for pattern in self.mysterious_patterns["positive_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.0
        
        # Check for mysterious sentence structures
        for pattern in self.mysterious_patterns["sentence_structures"]:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            score += matches * 3.0
        
        # Bonus for indirect communication style
        if "..." in text:
            score += 2.0
        if re.search(r"\?[^?]*\?", text):  # Multiple questions suggest curiosity/mystery
            score += 2.0
        
        return min(score, 25.0)
    
    def _validate_seductive_trait(self, text: str) -> float:
        """Validate seductive personality trait (0-25 points)."""
        score = 0.0
        text_lower = text.lower()
        
        # Check for seductive language
        for pattern in self.seductive_patterns["positive_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.5
        
        # Check for seductive tone
        for pattern in self.seductive_patterns["tone_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 3.0
        
        # Check for personal, intimate language
        if re.search(r"\btu\b|\bte\b|\bti\b", text_lower):  # Personal pronouns
            score += 1.0
        if re.search(r"contigo|conmigo", text_lower):  # Intimate prepositions
            score += 2.0
        
        return min(score, 25.0)
    
    def _validate_emotional_trait(self, text: str) -> float:
        """Validate emotional complexity trait (0-25 points)."""
        score = 0.0
        text_lower = text.lower()
        
        # Check for emotional vocabulary
        for pattern in self.emotional_patterns["positive_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.0
        
        # Check for complexity indicators
        for pattern in self.emotional_patterns["complexity_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 4.0
        
        # Bonus for emotional depth
        emotional_words = len(re.findall(r"siento|sientes|sentir|emoción|corazón|alma", text_lower))
        score += emotional_words * 1.5
        
        return min(score, 25.0)
    
    def _validate_intellectual_trait(self, text: str) -> float:
        """Validate intellectual engagement trait (0-25 points)."""
        score = 0.0
        text_lower = text.lower()
        
        # Check for intellectual vocabulary
        for pattern in self.intellectual_patterns["positive_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.0
        
        # Check for engagement patterns
        for pattern in self.intellectual_patterns["engagement_patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 3.5
        
        # Bonus for thought-provoking content
        question_count = len(re.findall(r"\?", text))
        score += min(question_count * 1.0, 5.0)  # Max 5 points for questions
        
        return min(score, 25.0)
    
    def _check_character_violations(self, text: str) -> float:
        """Check for patterns that violate Diana's character. Returns penalty points."""
        penalty = 0.0
        text_lower = text.lower()
        
        # Check each violation category
        for category, patterns in self.violation_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                penalty += matches * 3.0  # 3 point penalty per violation
        
        return penalty
    
    def _validate_context_specific(self, text: str, context: str) -> Tuple[List[str], List[str]]:
        """Perform context-specific validation."""
        violations = []
        recommendations = []
        
        if context == "narrative_fragment":
            if len(text) < 50:
                violations.append("Narrative fragment too short for meaningful character development")
                recommendations.append("Expand narrative content to allow Diana's personality to emerge")
            
            if not re.search(r'[.!?].*[.!?]', text):  # At least two sentences
                violations.append("Narrative lacks sufficient development")
                recommendations.append("Use multiple sentences to build atmospheric tension")
        
        elif context == "menu_response":
            if re.search(r'^[A-Z][a-z\s]*$', text.strip()):  # Simple title case
                violations.append("Menu text too plain and direct")
                recommendations.append("Add Diana's personality even to menu options")
        
        elif context == "error_message":
            if re.search(r'error|fallo|problema', text.lower()):
                violations.append("Error message too technical")
                recommendations.append("Frame errors as mysterious interruptions or intriguing pauses")
        
        return violations, recommendations
    
    async def validate_narrative_fragment(self, fragment) -> CharacterValidationResult:
        """Validate a narrative fragment for character consistency."""
        if not fragment:
            return CharacterValidationResult(
                overall_score=0.0,
                trait_scores={trait: 0.0 for trait in DianaPersonalityTrait},
                violations=["No fragment provided"],
                recommendations=["Provide a valid narrative fragment"],
                meets_threshold=False
            )
        
        # Combine title and content for validation
        full_text = f"{fragment.title}\n\n{fragment.content}"
        
        # Also validate choices if present
        if hasattr(fragment, 'choices') and fragment.choices:
            for i, choice in enumerate(fragment.choices):
                choice_text = choice.get('text', '')
                full_text += f"\n{choice_text}"
        
        return await self.validate_text(full_text, context="narrative_fragment")
    
    async def validate_user_interaction(self, interaction_text: str, interaction_type: str) -> CharacterValidationResult:
        """Validate user interaction for character consistency."""
        context_map = {
            "menu": "menu_response",
            "error": "error_message", 
            "notification": "notification",
            "greeting": "greeting"
        }
        
        context = context_map.get(interaction_type, "general_interaction")
        return await self.validate_text(interaction_text, context=context)
    
    async def batch_validate_content(self, content_list: List[Tuple[str, str]]) -> Dict[str, CharacterValidationResult]:
        """
        Validate multiple pieces of content in batch.
        
        Args:
            content_list: List of tuples (content_id, text_content)
            
        Returns:
            Dictionary mapping content_id to CharacterValidationResult
        """
        results = {}
        
        for content_id, text in content_list:
            try:
                result = await self.validate_text(text)
                results[content_id] = result
            except Exception as e:
                logger.error(f"Error validating content {content_id}: {e}")
                results[content_id] = CharacterValidationResult(
                    overall_score=0.0,
                    trait_scores={trait: 0.0 for trait in DianaPersonalityTrait},
                    violations=[f"Validation error: {str(e)}"],
                    recommendations=["Fix validation errors and retry"],
                    meets_threshold=False
                )
        
        return results
    
    def generate_character_report(self, results: List[CharacterValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive character consistency report."""
        if not results:
            return {"error": "No validation results provided"}
        
        # Calculate aggregate statistics
        total_score = sum(r.overall_score for r in results) / len(results)
        passing_percentage = (len([r for r in results if r.meets_threshold]) / len(results)) * 100
        
        # Aggregate trait scores
        trait_averages = {}
        for trait in DianaPersonalityTrait:
            trait_sum = sum(r.trait_scores.get(trait, 0) for r in results)
            trait_averages[trait.value] = trait_sum / len(results)
        
        # Collect common violations
        all_violations = []
        for result in results:
            all_violations.extend(result.violations)
        
        violation_frequency = {}
        for violation in all_violations:
            violation_frequency[violation] = violation_frequency.get(violation, 0) + 1
        
        # Most common violations
        common_violations = sorted(
            violation_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "summary": {
                "average_score": total_score,
                "passing_percentage": passing_percentage,
                "total_validations": len(results),
                "passing_validations": len([r for r in results if r.meets_threshold]),
                "meets_mvp_requirement": passing_percentage >= 95.0
            },
            "trait_performance": trait_averages,
            "common_violations": [{"violation": v, "frequency": f} for v, f in common_violations],
            "recommendations": self._generate_improvement_recommendations(trait_averages, common_violations)
        }
    
    def _generate_improvement_recommendations(self, trait_averages: Dict[str, float], common_violations: List[Tuple[str, int]]) -> List[str]:
        """Generate improvement recommendations based on analysis."""
        recommendations = []
        
        # Check trait performance
        for trait_name, score in trait_averages.items():
            if score < 20.0:  # Less than 80% of max score
                trait = DianaPersonalityTrait(trait_name)
                if trait == DianaPersonalityTrait.MYSTERIOUS:
                    recommendations.append("Increase mystery: Use more ellipsis, indirect language, and hints")
                elif trait == DianaPersonalityTrait.SEDUCTIVE:
                    recommendations.append("Enhance charm: Add more intimate language and emotional connection")
                elif trait == DianaPersonalityTrait.EMOTIONALLY_COMPLEX:
                    recommendations.append("Deepen emotions: Show inner conflicts and vulnerability")
                elif trait == DianaPersonalityTrait.INTELLECTUALLY_ENGAGING:
                    recommendations.append("Stimulate minds: Pose more questions and philosophical thoughts")
        
        # Address common violations
        if common_violations:
            most_common = common_violations[0][0]
            if "direct" in most_common.lower():
                recommendations.append("Reduce directness: Use more subtle, suggestive language")
            if "casual" in most_common.lower():
                recommendations.append("Elevate tone: Avoid casual language and maintain sophistication")
            if "technical" in most_common.lower():
                recommendations.append("Reduce technical language: Frame system interactions mysteriously")
        
        return recommendations[:5]  # Top 5 recommendations

# Convenience function for quick validation
async def validate_diana_character(text: str, session: AsyncSession, context: Optional[str] = None) -> CharacterValidationResult:
    """Quick validation function for Diana character consistency."""
    validator = DianaCharacterValidator(session)
    return await validator.validate_text(text, context)