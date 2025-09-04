"""
Narrative Character Integrity Service

Ensures all narrative fragments maintain Diana's character consistency
and provides validation for narrative content creation and updates.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog
from .diana_character_validator import DianaCharacterValidator, CharacterValidationResult

logger = logging.getLogger(__name__)

class NarrativeCharacterIntegrityService:
    """
    Service to maintain character integrity across narrative fragments.
    Validates existing fragments and prevents character-inconsistent content.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.validator = DianaCharacterValidator(session)
        
        # Track validation results for reporting
        self.validation_cache = {}
    
    async def validate_fragment_creation(self, fragment_data: Dict[str, Any]) -> Tuple[bool, CharacterValidationResult]:
        """
        Validate fragment data before creation.
        
        Args:
            fragment_data: Dictionary containing fragment fields
            
        Returns:
            Tuple of (is_valid, validation_result)
        """
        try:
            # Construct full text for validation
            title = fragment_data.get('title', '')
            content = fragment_data.get('content', '')
            full_text = f"{title}\n\n{content}"
            
            # Add choice text if present
            choices = fragment_data.get('choices', [])
            for choice in choices:
                choice_text = choice.get('text', '') if isinstance(choice, dict) else str(choice)
                if choice_text:
                    full_text += f"\n{choice_text}"
            
            # Validate the complete fragment
            result = await self.validator.validate_text(full_text, context="narrative_fragment")
            
            # Additional narrative-specific validation
            if result.meets_threshold:
                narrative_violations = await self._validate_narrative_specific_rules(fragment_data)
                if narrative_violations:
                    result.violations.extend(narrative_violations)
                    result.recommendations.extend([
                        "Ensure fragment integrates well with Diana's narrative arc",
                        "Maintain consistency with established character dynamics"
                    ])
                    # Reduce score for narrative violations
                    result.overall_score = max(0, result.overall_score - len(narrative_violations) * 5)
                    result.meets_threshold = result.overall_score >= self.validator.MIN_CONSISTENCY_SCORE
            
            is_valid = result.meets_threshold
            
            if not is_valid:
                logger.warning(f"Fragment creation blocked - character consistency score: {result.overall_score}")
                logger.warning(f"Violations: {result.violations}")
            
            return is_valid, result
            
        except Exception as e:
            logger.error(f"Error validating fragment creation: {e}")
            error_result = CharacterValidationResult(
                overall_score=0.0,
                trait_scores={trait: 0.0 for trait in self.validator.TRAIT_WEIGHTS.keys()},
                violations=[f"Validation error: {str(e)}"],
                recommendations=["Fix validation errors and retry"],
                meets_threshold=False
            )
            return False, error_result
    
    async def validate_existing_fragment(self, fragment_id: str) -> Optional[CharacterValidationResult]:
        """
        Validate an existing narrative fragment.
        
        Args:
            fragment_id: ID of the fragment to validate
            
        Returns:
            CharacterValidationResult or None if fragment not found
        """
        try:
            # Get fragment from database
            result = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            )
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                logger.warning(f"Fragment {fragment_id} not found for validation")
                return None
            
            # Validate the fragment
            validation_result = await self.validator.validate_narrative_fragment(fragment)
            
            # Cache result for reporting
            self.validation_cache[fragment_id] = validation_result
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating existing fragment {fragment_id}: {e}")
            return None
    
    async def validate_all_active_fragments(self) -> Dict[str, CharacterValidationResult]:
        """
        Validate all active narrative fragments.
        
        Returns:
            Dictionary mapping fragment_id to CharacterValidationResult
        """
        results = {}
        
        try:
            # Get all active fragments
            query_result = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.is_active == True)
            )
            fragments = query_result.scalars().all()
            
            logger.info(f"Validating {len(fragments)} active narrative fragments")
            
            # Validate each fragment
            for fragment in fragments:
                try:
                    validation_result = await self.validator.validate_narrative_fragment(fragment)
                    results[fragment.id] = validation_result
                    
                    # Log fragments that fail validation
                    if not validation_result.meets_threshold:
                        logger.warning(f"Fragment {fragment.id} failed validation: score {validation_result.overall_score}")
                        logger.warning(f"Title: {fragment.title}")
                        logger.warning(f"Violations: {validation_result.violations}")
                        
                except Exception as e:
                    logger.error(f"Error validating fragment {fragment.id}: {e}")
                    results[fragment.id] = CharacterValidationResult(
                        overall_score=0.0,
                        trait_scores={trait: 0.0 for trait in self.validator.TRAIT_WEIGHTS.keys()},
                        violations=[f"Validation error: {str(e)}"],
                        recommendations=["Fix validation errors"],
                        meets_threshold=False
                    )
            
            # Update cache
            self.validation_cache.update(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating all fragments: {e}")
            return {}
    
    async def get_character_consistency_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive character consistency report for narrative system.
        
        Returns:
            Dictionary containing validation statistics and recommendations
        """
        try:
            # Validate all fragments if cache is empty
            if not self.validation_cache:
                await self.validate_all_active_fragments()
            
            if not self.validation_cache:
                return {"error": "No fragments found or validated"}
            
            # Generate report using validator
            results_list = list(self.validation_cache.values())
            base_report = self.validator.generate_character_report(results_list)
            
            # Add narrative-specific metrics
            failing_fragments = [
                fragment_id for fragment_id, result in self.validation_cache.items()
                if not result.meets_threshold
            ]
            
            excellent_fragments = [
                fragment_id for fragment_id, result in self.validation_cache.items()
                if result.overall_score >= 98.0
            ]
            
            # Identify most problematic fragments
            worst_fragments = sorted(
                [(fid, result.overall_score) for fid, result in self.validation_cache.items()],
                key=lambda x: x[1]
            )[:5]
            
            # Add narrative-specific sections
            base_report.update({
                "narrative_specific": {
                    "total_fragments": len(self.validation_cache),
                    "failing_fragments": len(failing_fragments),
                    "excellent_fragments": len(excellent_fragments),
                    "character_consistency_percentage": (
                        len([r for r in results_list if r.meets_threshold]) / len(results_list) * 100
                    ),
                    "average_character_score": sum(r.overall_score for r in results_list) / len(results_list),
                    "fragments_needing_attention": [
                        {"fragment_id": fid, "score": score} for fid, score in worst_fragments
                    ]
                },
                "narrative_recommendations": await self._generate_narrative_recommendations(results_list)
            })
            
            return base_report
            
        except Exception as e:
            logger.error(f"Error generating character consistency report: {e}")
            return {"error": f"Report generation failed: {str(e)}"}
    
    async def suggest_character_improvements(self, fragment_id: str) -> Dict[str, Any]:
        """
        Provide specific character improvement suggestions for a fragment.
        
        Args:
            fragment_id: ID of the fragment to improve
            
        Returns:
            Dictionary with improvement suggestions
        """
        try:
            # Get fragment validation result
            if fragment_id not in self.validation_cache:
                await self.validate_existing_fragment(fragment_id)
            
            if fragment_id not in self.validation_cache:
                return {"error": "Fragment not found or validation failed"}
            
            result = self.validation_cache[fragment_id]
            
            # Get the actual fragment for analysis
            query_result = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            )
            fragment = query_result.scalar_one_or_none()
            
            if not fragment:
                return {"error": "Fragment not found in database"}
            
            # Generate specific suggestions
            suggestions = {
                "current_score": result.overall_score,
                "meets_threshold": result.meets_threshold,
                "trait_analysis": {},
                "specific_improvements": [],
                "example_rewrites": {}
            }
            
            # Analyze each trait
            from services.diana_character_validator import DianaPersonalityTrait
            
            for trait, score in result.trait_scores.items():
                trait_name = trait.value
                suggestions["trait_analysis"][trait_name] = {
                    "current_score": score,
                    "max_score": 25.0,
                    "percentage": (score / 25.0) * 100,
                    "needs_improvement": score < 20.0
                }
                
                # Specific improvement suggestions based on trait
                if score < 20.0:
                    if trait == DianaPersonalityTrait.MYSTERIOUS:
                        suggestions["specific_improvements"].append({
                            "trait": trait_name,
                            "suggestion": "Add more mysterious elements: use ellipsis (...), indirect language, hints rather than direct statements",
                            "example": "Instead of 'Te voy a contar un secreto', try '¿Acaso estás listo para... lo que podría susurrarte?'"
                        })
                    elif trait == DianaPersonalityTrait.SEDUCTIVE:
                        suggestions["specific_improvements"].append({
                            "trait": trait_name,
                            "suggestion": "Enhance seductive charm: use intimate language, add 💋 emoji, create emotional connection",
                            "example": "Instead of 'Ven aquí', try '💋 Mi querido... ¿podrías acercarte? Tu presencia hace que mi corazón...'"
                        })
                    elif trait == DianaPersonalityTrait.EMOTIONALLY_COMPLEX:
                        suggestions["specific_improvements"].append({
                            "trait": trait_name,
                            "suggestion": "Add emotional depth: show inner conflicts, vulnerability, complex feelings",
                            "example": "Instead of 'Estoy triste', try 'Una mezcla de melancolía y esperanza abraza mi corazón, creando esta hermosa contradicción...'"
                        })
                    elif trait == DianaPersonalityTrait.INTELLECTUALLY_ENGAGING:
                        suggestions["specific_improvements"].append({
                            "trait": trait_name,
                            "suggestion": "Stimulate intellectual curiosity: pose questions, invite reflection, offer deeper perspectives",
                            "example": "Instead of 'Es interesante', try '¿Te has preguntado alguna vez qué filosofía subyace a esta experiencia?'"
                        })
            
            # Provide rewrite examples for problematic sections
            if result.overall_score < 90.0:
                suggestions["example_rewrites"] = await self._generate_rewrite_examples(fragment)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions for {fragment_id}: {e}")
            return {"error": f"Failed to generate suggestions: {str(e)}"}
    
    async def _validate_narrative_specific_rules(self, fragment_data: Dict[str, Any]) -> List[str]:
        """Validate narrative-specific rules beyond character consistency."""
        violations = []
        
        # Check fragment type consistency
        fragment_type = fragment_data.get('fragment_type', '')
        content = fragment_data.get('content', '')
        choices = fragment_data.get('choices', [])
        
        # Decision fragments should have choices
        if fragment_type == 'DECISION' and not choices:
            violations.append("Decision fragments must have choice options")
        
        # Story fragments shouldn't have too many choices
        if fragment_type == 'STORY' and len(choices) > 2:
            violations.append("Story fragments should focus on narrative, limit choices")
        
        # Check for Diana-specific narrative elements
        if fragment_type == 'STORY':
            # Story fragments should build atmosphere
            if len(content) < 100:
                violations.append("Story fragments should be substantial to build Diana's world")
            
            # Should avoid breaking character immersion
            if any(word in content.lower() for word in ['bot', 'sistema', 'programa', 'código']):
                violations.append("Avoid technical terms that break narrative immersion")
        
        # Check choice quality for decisions
        if choices:
            for i, choice in enumerate(choices):
                if isinstance(choice, dict):
                    choice_text = choice.get('text', '')
                    if len(choice_text) < 10:
                        violations.append(f"Choice {i+1} too short - choices should be meaningful")
                    
                    # Choices should maintain Diana's voice
                    if choice_text and not any(
                        indicator in choice_text.lower() 
                        for indicator in ['...', '💋', 'susurr', 'misterio', 'secreto', 'corazón']
                    ):
                        violations.append(f"Choice {i+1} lacks Diana's characteristic voice")
        
        return violations
    
    async def _generate_narrative_recommendations(self, results: List[CharacterValidationResult]) -> List[str]:
        """Generate narrative-specific recommendations."""
        recommendations = []
        
        # Calculate statistics
        total_fragments = len(results)
        failing_count = len([r for r in results if not r.meets_threshold])
        avg_score = sum(r.overall_score for r in results) / total_fragments if total_fragments > 0 else 0
        
        if failing_count > total_fragments * 0.1:  # More than 10% failing
            recommendations.append("Critical: High number of fragments failing character consistency - review content creation guidelines")
        
        if avg_score < 85.0:
            recommendations.append("Overall character consistency below target - implement character training for content creators")
        
        # Analyze common issues
        all_violations = []
        for result in results:
            all_violations.extend(result.violations)
        
        violation_counts = {}
        for violation in all_violations:
            violation_counts[violation] = violation_counts.get(violation, 0) + 1
        
        # Address most common issues
        if violation_counts:
            most_common = max(violation_counts.items(), key=lambda x: x[1])
            recommendations.append(f"Address most common issue: {most_common[0]} (appears in {most_common[1]} fragments)")
        
        # Specific narrative recommendations
        recommendations.extend([
            "Ensure all narrative fragments contribute to Diana's mysterious and seductive persona",
            "Review fragment transitions to maintain character continuity",
            "Consider adding character consistency checks to content approval workflow"
        ])
        
        return recommendations[:8]  # Top 8 recommendations
    
    async def _generate_rewrite_examples(self, fragment) -> Dict[str, str]:
        """Generate example rewrites for problematic content."""
        examples = {}
        
        # Title rewrite
        if fragment.title and len(fragment.title) < 30:
            examples["title"] = {
                "original": fragment.title,
                "improved": f"💋 {fragment.title}... ¿Listos para Descubrir sus Secretos?"
            }
        
        # Content improvement example
        if fragment.content:
            first_sentence = fragment.content.split('.')[0] + '.' if '.' in fragment.content else fragment.content[:100]
            examples["content_opening"] = {
                "original": first_sentence,
                "improved": f"💋 {first_sentence}... pero hay algo más que late en las sombras de esta historia. ¿Acaso estás preparado para lo que podría revelarte?"
            }
        
        # Choice improvements
        if hasattr(fragment, 'choices') and fragment.choices:
            for i, choice in enumerate(fragment.choices[:2]):  # Only first 2 choices
                if isinstance(choice, dict) and 'text' in choice:
                    original_text = choice['text']
                    improved_text = f"💋 {original_text}... susurrando secretos"
                    examples[f"choice_{i+1}"] = {
                        "original": original_text,
                        "improved": improved_text
                    }
        
        return examples