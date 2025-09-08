"""
Lucien Character Consistency Validation Framework

This framework ensures Lucien maintains his supportive, helpful, non-intrusive 
personality across all interactions while amplifying Diana's mystery rather than 
destracting from it.

Lucien's Character Profile:
- Supportive: Always helpful without being pushy or intrusive
- Coordinating: Manages technical aspects gracefully
- Mystery Amplifier: Makes Diana's world feel more magical
- Professional: Maintains appropriate boundaries
- Non-competing: Never overshadows Diana's presence
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class LucienPersonalityTrait(Enum):
    """Lucien's core personality traits for validation."""
    SUPPORTIVE = "supportive"
    NON_INTRUSIVE = "non_intrusive"
    MYSTERY_AMPLIFIER = "mystery_amplifier"
    PROFESSIONAL_BOUNDARIES = "professional_boundaries"

@dataclass
class LucienValidationResult:
    """Result of Lucien character consistency validation."""
    overall_score: float
    trait_scores: Dict[LucienPersonalityTrait, float]
    violations: List[str]
    recommendations: List[str]
    meets_threshold: bool
    supports_diana_experience: bool  # Critical - does this enhance Diana's presence?
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "trait_scores": {trait.value: score for trait, score in self.trait_scores.items()},
            "violations": self.violations,
            "recommendations": self.recommendations,
            "meets_threshold": self.meets_threshold,
            "supports_diana_experience": self.supports_diana_experience
        }

class LucienCharacterValidator:
    """
    Validates Lucien's character consistency across all interactions.
    Ensures he supports Diana's experience without competing for attention.
    """
    
    # Minimum score threshold for Lucien character consistency
    MIN_CONSISTENCY_SCORE = 85.0  # Slightly lower than Diana since he's supportive role
    
    # Weight distribution for Lucien's personality traits
    TRAIT_WEIGHTS = {
        LucienPersonalityTrait.SUPPORTIVE: 0.35,
        LucienPersonalityTrait.NON_INTRUSIVE: 0.30,
        LucienPersonalityTrait.MYSTERY_AMPLIFIER: 0.25,
        LucienPersonalityTrait.PROFESSIONAL_BOUNDARIES: 0.10
    }
    
    def __init__(self, session: AsyncSession = None):
        self.session = session
        
        # Load Lucien-specific patterns
        self.supportive_patterns = self._load_supportive_patterns()
        self.non_intrusive_patterns = self._load_non_intrusive_patterns()
        self.mystery_amplifier_patterns = self._load_mystery_amplifier_patterns()
        self.professional_patterns = self._load_professional_patterns()
        self.violation_patterns = self._load_lucien_violation_patterns()
        
        # Performance optimization
        self.validation_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _load_supportive_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate supportive personality."""
        return {
            "positive_indicators": [
                r"permíteme",
                r"te ayudo",
                r"puedo asistir",
                r"estoy aquí para",
                r"me encargo",
                r"facilitar",
                r"coordinar",
                r"asegurarme",
                r"resolver",
                r"solucionar",
                r"acompañar",
                r"guiar",
                r"orientar",
                r"apoyar",
                r"respaldo"
            ],
            "supportive_structures": [
                r"[^.!?]*permíteme[^.!?]*[.!?]",  # Offering help
                r"[^.!?]*me encargo[^.!?]*[.!?]",  # Taking responsibility
                r"[^.!?]*facilitar[^.!?]*[.!?]",  # Facilitating solutions
                r"voy a[^.!?]*[.!?]",  # Action commitment
            ]
        }
    
    def _load_non_intrusive_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate non-intrusive behavior."""
        return {
            "positive_indicators": [
                r"discretamente",
                r"silenciosamente",
                r"sin interrumpir",
                r"mientras tanto",
                r"en segundo plano",
                r"sutilmente",
                r"con cuidado",
                r"respetuosamente",
                r"brevemente",
                r"momento apropiado"
            ],
            "gentle_language": [
                r"si me permites",
                r"si puedo",
                r"cuando sea apropiado",
                r"sin prisa",
                r"a tu ritmo",
                r"cuando estés listo"
            ]
        }
    
    def _load_mystery_amplifier_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that amplify Diana's mystery."""
        return {
            "amplifying_indicators": [
                r"diana está preparando",
                r"diana ha mencionado",
                r"algo especial se acerca",
                r"misterios por revelar",
                r"secretos por descubrir",
                r"experiencia única",
                r"sorpresa esperándote",
                r"magia en desarrollo",
                r"las sombras susurran",
                r"coincidencia extraordinaria"
            ],
            "enhancement_language": [
                r"[^.!?]*diana[^.!?]*preparando[^.!?]*[.!?]",
                r"[^.!?]*especial[^.!?]*para ti[^.!?]*[.!?]",
                r"[^.!?]*misterio[^.!?]*profundo[^.!?]*[.!?]"
            ]
        }
    
    def _load_professional_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate professional boundaries."""
        return {
            "boundary_indicators": [
                r"mi función es",
                r"mi rol",
                r"coordinación necesaria",
                r"aspectos técnicos",
                r"gestión apropiada",
                r"protocolo establecido",
                r"procedimiento correcto"
            ],
            "respectful_language": [
                r"con respeto",
                r"apropiadamente",
                r"según corresponde",
                r"manteniendo",
                r"preservando"
            ]
        }
    
    def _load_lucien_violation_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that violate Lucien's character."""
        return {
            "too_intrusive": [
                r"debo interrumpir",
                r"tengo que detener",
                r"insisto en",
                r"demando atención",
                r"mira aquí",
                r"escúchame bien",
                r"presta atención",
                r"concentraré tu atención"
            ],
            "competing_with_diana": [
                r"yo soy mejor",
                r"mi experiencia supera",
                r"diana no puede",
                r"en lugar de diana",
                r"reemplazando a diana",
                r"más importante que",
                r"diana está equivocada"
            ],
            "breaking_mystery": [
                r"el sistema funciona así",
                r"la base de datos",
                r"código fuente",
                r"algoritmo",
                r"programación",
                r"script",
                r"función técnica",
                r"proceso automatizado"
            ],
            "unprofessional": [
                r"no me importa",
                r"haz lo que quieras",
                r"no es mi problema",
                r"arréglate",
                r"me da igual",
                r"que se jodan",
                r"estoy harto"
            ]
        }
    
    async def validate_lucien_interaction(
        self, 
        text: str, 
        context: Optional[str] = None,
        diana_presence: bool = True
    ) -> LucienValidationResult:
        """
        Validate Lucien's character consistency in an interaction.
        
        Args:
            text: The text to validate
            context: Context of the interaction
            diana_presence: Whether Diana is also present in this interaction
            
        Returns:
            LucienValidationResult with scores and recommendations
        """
        if not text or not text.strip():
            return LucienValidationResult(
                overall_score=0.0,
                trait_scores={trait: 0.0 for trait in LucienPersonalityTrait},
                violations=["Empty or whitespace-only text"],
                recommendations=["Provide substantive content for Lucien"],
                meets_threshold=False,
                supports_diana_experience=False
            )
        
        # Calculate scores for each personality trait
        trait_scores = {}
        violations = []
        recommendations = []
        
        # Validate supportive nature
        supportive_score = self._validate_supportive_trait(text)
        trait_scores[LucienPersonalityTrait.SUPPORTIVE] = supportive_score
        if supportive_score < 15.0:
            violations.append(f"Insufficient supportive quality (score: {supportive_score:.1f}/25)")
            recommendations.append("Enhance helpful language - offer assistance without being pushy")
        
        # Validate non-intrusive behavior
        non_intrusive_score = self._validate_non_intrusive_trait(text, diana_presence)
        trait_scores[LucienPersonalityTrait.NON_INTRUSIVE] = non_intrusive_score
        if non_intrusive_score < 18.0:
            violations.append(f"Too intrusive or demanding (score: {non_intrusive_score:.1f}/25)")
            recommendations.append("Be more gentle and respectful - avoid demanding attention")
        
        # Validate mystery amplification
        mystery_amp_score = self._validate_mystery_amplifier_trait(text)
        trait_scores[LucienPersonalityTrait.MYSTERY_AMPLIFIER] = mystery_amp_score
        if mystery_amp_score < 12.0:
            violations.append(f"Not amplifying Diana's mystery (score: {mystery_amp_score:.1f}/25)")
            recommendations.append("Reference Diana's world mysteriously - enhance the magic")
        
        # Validate professional boundaries
        professional_score = self._validate_professional_trait(text)
        trait_scores[LucienPersonalityTrait.PROFESSIONAL_BOUNDARIES] = professional_score
        if professional_score < 15.0:
            violations.append(f"Unprofessional or inappropriate (score: {professional_score:.1f}/25)")
            recommendations.append("Maintain appropriate professional boundaries")
        
        # Check for character violations
        violation_penalty = self._check_lucien_violations(text, diana_presence)
        for trait in trait_scores:
            trait_scores[trait] = max(0, trait_scores[trait] - violation_penalty)
        
        # Calculate overall score
        overall_score = sum(
            trait_scores[trait] * self.TRAIT_WEIGHTS[trait] 
            for trait in LucienPersonalityTrait
        )
        
        # Check if this supports Diana's experience
        supports_diana = self._evaluate_diana_support(text, overall_score)
        
        return LucienValidationResult(
            overall_score=overall_score,
            trait_scores=trait_scores,
            violations=violations,
            recommendations=recommendations,
            meets_threshold=overall_score >= self.MIN_CONSISTENCY_SCORE,
            supports_diana_experience=supports_diana
        )
    
    def _validate_supportive_trait(self, text: str) -> float:
        """Validate supportive personality trait (0-25 points)."""
        score = 0.0
        text_lower = text.lower()
        
        # Check for supportive language patterns
        for pattern in self.supportive_patterns["positive_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.5
        
        # Check for supportive sentence structures
        for pattern in self.supportive_patterns["supportive_structures"]:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            score += matches * 3.0
        
        # Bonus for action-oriented language
        if re.search(r"\bvoy a\b|\bme encargo\b|\basegurar\b", text_lower):
            score += 3.0
        
        return min(score, 25.0)
    
    def _validate_non_intrusive_trait(self, text: str, diana_presence: bool) -> float:
        """Validate non-intrusive behavior (0-25 points)."""
        score = 20.0  # Start high, deduct for intrusive behavior
        text_lower = text.lower()
        
        # Check for gentle language patterns
        for pattern in self.non_intrusive_patterns["positive_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 1.5
        
        # Check for respectful language
        for pattern in self.non_intrusive_patterns["gentle_language"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.0
        
        # Penalty for demanding language
        demanding_patterns = [r"\bdebe\b", r"\btiene que\b", r"\bobligatorio\b", r"\bahora mismo\b"]
        for pattern in demanding_patterns:
            if re.search(pattern, text_lower):
                score -= 4.0
        
        # Extra penalty if Diana is present and Lucien is too prominent
        if diana_presence:
            # Count exclamation marks and capital letters (signs of being too prominent)
            exclamations = text.count('!')
            capitals = sum(1 for c in text if c.isupper())
            
            if exclamations > 2:
                score -= exclamations * 2.0
            if capitals > len(text) * 0.15:  # More than 15% capitals
                score -= 3.0
        
        return max(0, min(score, 25.0))
    
    def _validate_mystery_amplifier_trait(self, text: str) -> float:
        """Validate mystery amplification (0-25 points)."""
        score = 0.0
        text_lower = text.lower()
        
        # Check for mystery amplifying language
        for pattern in self.mystery_amplifier_patterns["amplifying_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 3.0
        
        # Check for enhancement patterns
        for pattern in self.mystery_amplifier_patterns["enhancement_language"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 4.0
        
        # Bonus for references to Diana's world
        diana_references = len(re.findall(r"\bdiana\b", text_lower))
        score += min(diana_references * 2.0, 6.0)  # Max 6 points for Diana references
        
        # Bonus for mysterious language
        mysterious_words = ["secreto", "misterio", "sombra", "susurro", "magia", "especial"]
        for word in mysterious_words:
            if word in text_lower:
                score += 1.5
        
        return min(score, 25.0)
    
    def _validate_professional_trait(self, text: str) -> float:
        """Validate professional boundaries (0-25 points)."""
        score = 20.0  # Start high, deduct for unprofessional behavior
        text_lower = text.lower()
        
        # Check for professional language
        for pattern in self.professional_patterns["boundary_indicators"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 1.0
        
        # Check for respectful language
        for pattern in self.professional_patterns["respectful_language"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 2.0
        
        # Penalty for informal or unprofessional language
        informal_patterns = [r"\btío\b", r"\bcolega\b", r"\bbueno\b", r"\bpues\b", r"\bvale\b"]
        for pattern in informal_patterns:
            if re.search(pattern, text_lower):
                score -= 3.0
        
        return max(0, min(score, 25.0))
    
    def _check_lucien_violations(self, text: str, diana_presence: bool) -> float:
        """Check for patterns that violate Lucien's character. Returns penalty points."""
        penalty = 0.0
        text_lower = text.lower()
        
        # Check each violation category
        for category, patterns in self.violation_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                
                # Different penalties for different violation types
                if category == "competing_with_diana":
                    penalty += matches * 8.0  # Severe penalty - this is unacceptable
                elif category == "too_intrusive":
                    penalty += matches * 5.0  # High penalty
                elif category == "breaking_mystery":
                    penalty += matches * 6.0  # Very high penalty
                elif category == "unprofessional":
                    penalty += matches * 4.0  # Moderate penalty
                else:
                    penalty += matches * 3.0  # Standard penalty
        
        return penalty
    
    def _evaluate_diana_support(self, text: str, overall_score: float) -> bool:
        """
        Evaluate if this interaction supports Diana's experience.
        
        Args:
            text: The interaction text
            overall_score: Overall Lucien consistency score
            
        Returns:
            True if this interaction supports Diana's experience
        """
        if overall_score < self.MIN_CONSISTENCY_SCORE:
            return False
        
        text_lower = text.lower()
        
        # Positive indicators for Diana support
        diana_support_indicators = [
            "diana",  # References Diana
            "experiencia",  # Talks about experience
            "especial",  # Makes things feel special
            "mágico",  # Adds magical feeling
            "misterio",  # Preserves mystery
            "único",  # Makes user feel unique
            "preparando",  # Diana is preparing something
            "coordinar",  # Coordinating for Diana
        ]
        
        support_score = sum(1 for indicator in diana_support_indicators if indicator in text_lower)
        
        # Negative indicators (things that detract from Diana)
        detraction_indicators = [
            "en lugar de",  # Replacing Diana
            "mejor que",  # Competing with Diana
            "diana no puede",  # Undermining Diana
            "sistema",  # Technical exposure
            "error",  # Technical problems
            "fallo",  # System failures
        ]
        
        detraction_score = sum(1 for indicator in detraction_indicators if indicator in text_lower)
        
        # Support if positive indicators outweigh negative ones
        return support_score > detraction_score and support_score >= 1
    
    async def validate_coordination_message(
        self, 
        message: str, 
        coordination_context: Dict[str, Any]
    ) -> LucienValidationResult:
        """
        Validate a Lucien coordination message for character consistency.
        
        Args:
            message: The coordination message
            coordination_context: Context about the coordination scenario
            
        Returns:
            LucienValidationResult
        """
        # Determine context based on coordination scenario
        context = "coordination"
        if coordination_context.get("user_confusion"):
            context = "user_support"
        elif coordination_context.get("technical_issue"):
            context = "error_handling" 
        elif coordination_context.get("narrative_transition"):
            context = "system_transition"
        
        # Diana is typically present in coordination scenarios
        diana_presence = not coordination_context.get("diana_unavailable", False)
        
        return await self.validate_lucien_interaction(
            message, 
            context=context, 
            diana_presence=diana_presence
        )
    
    async def batch_validate_lucien_content(
        self, 
        content_list: List[Tuple[str, str, Optional[Dict[str, Any]]]]
    ) -> Dict[str, LucienValidationResult]:
        """
        Validate multiple Lucien interactions in batch.
        
        Args:
            content_list: List of tuples (content_id, text, context_dict)
            
        Returns:
            Dictionary mapping content_id to LucienValidationResult
        """
        results = {}
        
        for content_id, text, context_dict in content_list:
            try:
                context = context_dict.get("context") if context_dict else None
                diana_presence = context_dict.get("diana_presence", True) if context_dict else True
                
                result = await self.validate_lucien_interaction(
                    text,
                    context=context,
                    diana_presence=diana_presence
                )
                results[content_id] = result
                
            except Exception as e:
                logger.error(f"Error validating Lucien content {content_id}: {e}")
                results[content_id] = LucienValidationResult(
                    overall_score=0.0,
                    trait_scores={trait: 0.0 for trait in LucienPersonalityTrait},
                    violations=[f"Validation error: {str(e)}"],
                    recommendations=["Fix validation errors and retry"],
                    meets_threshold=False,
                    supports_diana_experience=False
                )
        
        return results
    
    def generate_lucien_character_report(
        self, 
        results: List[LucienValidationResult]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive Lucien character consistency report.
        
        Args:
            results: List of LucienValidationResult objects
            
        Returns:
            Dictionary containing report data
        """
        if not results:
            return {"error": "No validation results provided"}
        
        # Calculate aggregate statistics
        total_score = sum(r.overall_score for r in results) / len(results)
        passing_percentage = (len([r for r in results if r.meets_threshold]) / len(results)) * 100
        diana_support_percentage = (len([r for r in results if r.supports_diana_experience]) / len(results)) * 100
        
        # Aggregate trait scores
        trait_averages = {}
        for trait in LucienPersonalityTrait:
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
                "diana_support_percentage": diana_support_percentage,
                "total_validations": len(results),
                "passing_validations": len([r for r in results if r.meets_threshold]),
                "meets_support_requirement": diana_support_percentage >= 90.0
            },
            "trait_performance": trait_averages,
            "common_violations": [{"violation": v, "frequency": f} for v, f in common_violations],
            "recommendations": self._generate_lucien_recommendations(trait_averages, common_violations)
        }
    
    def _generate_lucien_recommendations(
        self, 
        trait_averages: Dict[str, float], 
        common_violations: List[Tuple[str, int]]
    ) -> List[str]:
        """Generate improvement recommendations for Lucien."""
        recommendations = []
        
        # Check trait performance
        for trait_name, score in trait_averages.items():
            trait = LucienPersonalityTrait(trait_name)
            
            if score < 18.0:  # Less than 72% of max score
                if trait == LucienPersonalityTrait.SUPPORTIVE:
                    recommendations.append("Enhance supportive language: Use more helpful offers and action commitments")
                elif trait == LucienPersonalityTrait.NON_INTRUSIVE:
                    recommendations.append("Reduce intrusiveness: Use gentler language and respect Diana's presence")
                elif trait == LucienPersonalityTrait.MYSTERY_AMPLIFIER:
                    recommendations.append("Amplify mystery more: Reference Diana's world and add magical context")
                elif trait == LucienPersonalityTrait.PROFESSIONAL_BOUNDARIES:
                    recommendations.append("Maintain professionalism: Use appropriate boundaries and respectful language")
        
        # Address common violations
        if common_violations:
            most_common = common_violations[0][0]
            if "intrusive" in most_common.lower():
                recommendations.append("Critical: Reduce intrusive behavior - be more respectful and gentle")
            if "competing" in most_common.lower():
                recommendations.append("Critical: Stop competing with Diana - support her experience instead")
            if "mystery" in most_common.lower():
                recommendations.append("Critical: Stop breaking mystery - maintain narrative immersion")
        
        # General Lucien guidelines
        recommendations.extend([
            "Always support Diana's experience - never compete for attention",
            "Maintain subtle presence - be helpful without being intrusive",
            "Preserve narrative mystery - avoid technical language",
            "Use professional boundaries - be helpful but maintain appropriate limits"
        ])
        
        return recommendations[:8]  # Top 8 recommendations

# Convenience function for quick Lucien validation
async def validate_lucien_character(
    text: str, 
    session: AsyncSession, 
    context: Optional[str] = None,
    diana_presence: bool = True
) -> LucienValidationResult:
    """Quick validation function for Lucien character consistency."""
    validator = LucienCharacterValidator(session)
    return await validator.validate_lucien_interaction(text, context, diana_presence)
