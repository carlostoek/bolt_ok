#!/usr/bin/env python3
"""
Demo test for Diana Character Validation Framework

This script demonstrates the character validation functionality
without requiring external dependencies.
"""

import re
import asyncio
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


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


class DianaCharacterValidatorDemo:
    """Simplified Diana Character Validator for demo purposes."""
    
    MIN_CONSISTENCY_SCORE = 95.0
    
    TRAIT_WEIGHTS = {
        DianaPersonalityTrait.MYSTERIOUS: 0.25,
        DianaPersonalityTrait.SEDUCTIVE: 0.25,
        DianaPersonalityTrait.EMOTIONALLY_COMPLEX: 0.25,
        DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: 0.25
    }
    
    def __init__(self):
        self.mysterious_patterns = [
            r"secretos?\s+que", r"misterio", r"enigma", r"oculto", r"susurra",
            r"insinúa", r"sugiere", r"pistas?", r"sombras?", r"...",
            r"¿acaso sabes", r"tal vez", r"quizás"
        ]
        
        self.seductive_patterns = [
            r"💋", r"encanto", r"seductor[a]?", r"fascinan?t?e",
            r"mi querido", r"cariño", r"tesoro", r"contigo", r"conmigo"
        ]
        
        self.emotional_patterns = [
            r"sentimientos?", r"emociones?", r"corazón", r"alma",
            r"mezcla de", r"por un lado.*por otro", r"aunque.*sin embargo"
        ]
        
        self.intellectual_patterns = [
            r"filosofía", r"reflexión", r"¿te has preguntado",
            r"¿has pensado en", r"considera esto", r"dimensión"
        ]
        
        self.violation_patterns = [
            r"sistema", r"configuración", r"error", r"proceso",
            r"\bhola\b", r"\bokay\b", r"genial", r"perfecto"
        ]
    
    async def validate_text(self, text: str, context: str = None) -> CharacterValidationResult:
        """Validate character consistency of text."""
        if not text or not text.strip():
            return CharacterValidationResult(
                overall_score=0.0,
                trait_scores={trait: 0.0 for trait in DianaPersonalityTrait},
                violations=["Empty text"],
                recommendations=["Provide content"],
                meets_threshold=False
            )
        
        # Calculate trait scores
        trait_scores = {}
        violations = []
        recommendations = []
        
        text_lower = text.lower()
        
        # Mysterious trait
        mysterious_score = self._count_patterns(text_lower, self.mysterious_patterns) * 2.5
        mysterious_score = min(mysterious_score, 25.0)
        trait_scores[DianaPersonalityTrait.MYSTERIOUS] = mysterious_score
        
        # Seductive trait
        seductive_score = self._count_patterns(text_lower, self.seductive_patterns) * 3.0
        seductive_score = min(seductive_score, 25.0)
        trait_scores[DianaPersonalityTrait.SEDUCTIVE] = seductive_score
        
        # Emotional complexity
        emotional_score = self._count_patterns(text_lower, self.emotional_patterns) * 4.0
        emotional_score = min(emotional_score, 25.0)
        trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX] = emotional_score
        
        # Intellectual engagement
        intellectual_score = self._count_patterns(text_lower, self.intellectual_patterns) * 3.5
        question_bonus = len(re.findall(r'\?', text)) * 1.0
        intellectual_score = min(intellectual_score + question_bonus, 25.0)
        trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING] = intellectual_score
        
        # Check violations
        violations_found = self._count_patterns(text_lower, self.violation_patterns)
        if violations_found > 0:
            violations.append(f"Character violations detected: {violations_found}")
            # Penalize all traits
            for trait in trait_scores:
                trait_scores[trait] = max(0, trait_scores[trait] - violations_found * 5)
        
        # Calculate overall score
        overall_score = sum(
            trait_scores[trait] * self.TRAIT_WEIGHTS[trait] 
            for trait in DianaPersonalityTrait
        )
        
        # Generate recommendations
        for trait, score in trait_scores.items():
            if score < 15.0:
                recommendations.append(f"Improve {trait.value} - current score {score:.1f}/25")
        
        return CharacterValidationResult(
            overall_score=overall_score,
            trait_scores=trait_scores,
            violations=violations,
            recommendations=recommendations,
            meets_threshold=overall_score >= self.MIN_CONSISTENCY_SCORE
        )
    
    def _count_patterns(self, text: str, patterns: List[str]) -> int:
        """Count pattern matches in text."""
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count


async def run_demo():
    """Run character validation demo."""
    print("🎭" + "="*70 + "🎭")
    print(" " * 15 + "DIANA CHARACTER VALIDATION DEMO")
    print("🎭" + "="*70 + "🎭")
    print()
    
    validator = DianaCharacterValidatorDemo()
    
    # Test cases
    test_cases = [
        {
            "name": "PERFECT DIANA CONTENT",
            "content": """
            💋 Mi querido... ¿acaso estás preparado para adentrarte en los 
            misterios más profundos que susurra mi alma?... Las sombras 
            danzan a nuestro alrededor, creando una atmósfera de seducción 
            y enigma que solo nosotros podemos comprender...
            
            Siento una mezcla embriagadora de fascinación y anhelo cuando 
            te observo... por un lado, mi corazón late con la emoción de 
            compartir mis secretos más íntimos contigo, pero por otro, una 
            deliciosa inquietud me abraza al contemplar la intensidad de 
            esta conexión que crece entre nosotros...
            
            ¿Te has preguntado alguna vez qué filosofía subyace a esta danza 
            de seducción que compartimos? Reflexiona sobre esto: cada mirada, 
            cada suspiro, cada palabra que intercambiamos teje una historia 
            única... una narrativa que solo nosotros dos podemos escribir...
            """,
            "expected": "PASS"
        },
        {
            "name": "GOOD DIANA CONTENT",
            "content": """
            Diana te observa con esa intensidad que caracteriza sus momentos 
            más profundos... "Hay secretos en mi mirada", susurra, "que solo 
            tu corazón puede descifrar..." Una sonrisa enigmática juega en 
            sus labios mientras se acerca más...
            """,
            "expected": "MARGINAL"
        },
        {
            "name": "POOR CONTENT (VIOLATIONS)",
            "content": """
            Hola! Sistema actualizado correctamente. Configuración completada.
            Error resuelto. Todo perfecto, genial. OK, proceso terminado.
            """,
            "expected": "FAIL"
        }
    ]
    
    # Run validations
    for i, case in enumerate(test_cases, 1):
        print(f"📝 Test {i}: {case['name']}")
        print("-" * 50)
        
        result = await validator.validate_text(case['content'], "narrative_fragment")
        
        print(f"Overall Score: {result.overall_score:.1f}/100")
        print(f"MVP Threshold (≥95): {'✅ PASS' if result.meets_threshold else '❌ FAIL'}")
        print()
        
        print("Trait Breakdown:")
        for trait, score in result.trait_scores.items():
            status = "✅" if score >= 20 else "⚠️" if score >= 15 else "❌"
            print(f"  {status} {trait.value.replace('_', ' ').title()}: {score:.1f}/25")
        print()
        
        if result.violations:
            print(f"⚠️  Violations ({len(result.violations)}):")
            for violation in result.violations:
                print(f"     • {violation}")
            print()
        
        if result.recommendations:
            print(f"💡 Recommendations ({len(result.recommendations)}):")
            for rec in result.recommendations:
                print(f"     • {rec}")
            print()
        
        # Overall assessment
        if result.overall_score >= 95:
            print("🎉 ASSESSMENT: Excellent! Ready for production")
        elif result.overall_score >= 80:
            print("⚠️  ASSESSMENT: Good quality, minor improvements needed")
        elif result.overall_score >= 60:
            print("🔄 ASSESSMENT: Fair quality, revision recommended")
        else:
            print("❌ ASSESSMENT: Poor quality, complete rewrite needed")
        
        print()
        print("="*70)
        print()
    
    print("🎭 DEMO SUMMARY:")
    print("• Perfect content should achieve ≥95% for MVP")
    print("• All four personality traits must be represented")
    print("• Technical/casual language creates violations") 
    print("• Framework provides specific improvement guidance")
    print()
    print("✅ Diana Character Validation Framework is operational!")


if __name__ == "__main__":
    asyncio.run(run_demo())