"""
Simplified Narrative Fragment Validation for Task 2.3

Validates the narrative fragments without requiring aiogram dependencies,
focusing on character consistency and MVP compliance testing.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ValidationResult:
    """Simple validation result for character consistency."""
    fragment_id: str
    overall_score: float
    mysterious_score: float
    seductive_score: float
    emotional_score: float
    intellectual_score: float
    meets_threshold: bool
    violations: List[str]
    recommendations: List[str]

@dataclass
class FragmentDesign:
    """Fragment design from creator."""
    id: str
    title: str
    content: str
    fragment_type: str
    storyline_level: int
    tier_classification: str
    fragment_sequence: int
    requires_vip: bool
    vip_tier_required: int
    choices: List[Dict[str, Any]]
    triggers: Dict[str, Any]
    expected_consistency_score: float

class SimpleCharacterValidator:
    """Simplified character validator for testing."""
    
    def __init__(self):
        self.mysterious_patterns = [
            r"secretos?", r"misterio", r"enigma", r"oculto", r"susurra", r"insinúa",
            r"sugiere", r"pistas?", r"sombras?", r"...", r"¿acaso", r"tal vez",
            r"quizás", r"entre líneas", r"sussurra", r"murmura"
        ]
        
        self.seductive_patterns = [
            r"💋", r"encanto", r"seductor", r"tentador", r"fascinante", r"cautivador",
            r"sensual", r"provocativ", r"coqueto", r"mi querido", r"cariño", r"tesoro",
            r"contigo", r"conmigo", r"intimate", r"cerca"
        ]
        
        self.emotional_patterns = [
            r"sentimientos?", r"emociones?", r"corazón", r"alma", r"profundidad",
            r"vulnerabilidad", r"melancolía", r"anhelo", r"deseo", r"esperanza",
            r"contradicción", r"paradoja", r"mezcla de", r"por un lado.*por otro"
        ]
        
        self.intellectual_patterns = [
            r"filosofía", r"reflexión", r"contemplar", r"analizar", r"significado",
            r"comprensión", r"sabiduría", r"perspectiva", r"¿has pensado",
            r"¿te has preguntado", r"considera esto", r"reflexiona sobre"
        ]

    def validate_fragment(self, fragment: FragmentDesign) -> ValidationResult:
        """Validate a fragment for character consistency."""
        
        # Combine all text
        full_text = f"{fragment.title}\n{fragment.content}"
        if fragment.choices:
            choice_text = "\n".join([choice.get("text", "") for choice in fragment.choices])
            full_text += f"\n{choice_text}"
        
        full_text_lower = full_text.lower()
        
        # Score each trait (0-25 points each)
        mysterious_score = self._score_mysterious_trait(full_text, full_text_lower)
        seductive_score = self._score_seductive_trait(full_text, full_text_lower)
        emotional_score = self._score_emotional_trait(full_text, full_text_lower)
        intellectual_score = self._score_intellectual_trait(full_text, full_text_lower)
        
        # Calculate overall score
        overall_score = mysterious_score + seductive_score + emotional_score + intellectual_score
        
        # Check violations
        violations = []
        recommendations = []
        
        if mysterious_score < 15.0:
            violations.append(f"Insufficient mysterious quality ({mysterious_score:.1f}/25)")
            recommendations.append("Add more mystery - use ellipsis, hints, indirect language")
        
        if seductive_score < 15.0:
            violations.append(f"Insufficient seductive charm ({seductive_score:.1f}/25)")
            recommendations.append("Include subtle charm and intimate language")
        
        if emotional_score < 15.0:
            violations.append(f"Insufficient emotional depth ({emotional_score:.1f}/25)")
            recommendations.append("Add emotional complexity and vulnerability")
        
        if intellectual_score < 15.0:
            violations.append(f"Insufficient intellectual engagement ({intellectual_score:.1f}/25)")
            recommendations.append("Pose questions and invite deeper reflection")
        
        return ValidationResult(
            fragment_id=fragment.id,
            overall_score=overall_score,
            mysterious_score=mysterious_score,
            seductive_score=seductive_score,
            emotional_score=emotional_score,
            intellectual_score=intellectual_score,
            meets_threshold=overall_score >= 95.0,
            violations=violations,
            recommendations=recommendations
        )

    def _score_mysterious_trait(self, text: str, text_lower: str) -> float:
        """Score mysterious personality trait (0-25 points)."""
        score = 0.0
        
        for pattern in self.mysterious_patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches * 2.0
        
        # Bonus for ellipsis and questions
        if "..." in text:
            score += 3.0
        
        question_count = len(re.findall(r"\?", text))
        score += min(question_count * 1.0, 5.0)
        
        return min(score, 25.0)

    def _score_seductive_trait(self, text: str, text_lower: str) -> float:
        """Score seductive personality trait (0-25 points)."""
        score = 0.0
        
        for pattern in self.seductive_patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches * 2.5
        
        # Personal pronouns bonus
        personal_pronouns = len(re.findall(r"\btu\b|\bte\b|\bti\b", text_lower))
        score += personal_pronouns * 1.0
        
        return min(score, 25.0)

    def _score_emotional_trait(self, text: str, text_lower: str) -> float:
        """Score emotional complexity trait (0-25 points)."""
        score = 0.0
        
        for pattern in self.emotional_patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches * 2.0
        
        # Emotional vocabulary bonus
        emotional_words = len(re.findall(r"siento|sientes|sentir|emoción|corazón|alma", text_lower))
        score += emotional_words * 1.5
        
        return min(score, 25.0)

    def _score_intellectual_trait(self, text: str, text_lower: str) -> float:
        """Score intellectual engagement trait (0-25 points)."""
        score = 0.0
        
        for pattern in self.intellectual_patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches * 2.0
        
        # Question bonus
        question_count = len(re.findall(r"\?", text))
        score += min(question_count * 1.0, 5.0)
        
        return min(score, 25.0)

def create_sample_fragments() -> List[FragmentDesign]:
    """Create sample fragments for validation."""
    
    fragments = []
    
    # Fragment 1: Diana's Welcome
    fragments.append(FragmentDesign(
        id="fragment_diana_welcome",
        title="Bienvenida de Diana",
        content="""*Diana emerge entre sombras, parcialmente oculta, con una sonrisa enigmática que promete secretos...*

🌸 **Diana:**
*[Voz susurrante, como quien comparte un secreto íntimo]*

Bienvenido a Los Kinkys, mi querido viajero...
Has cruzado una línea que muchos ven... pero pocos realmente se atreven a atravesar.

*[Pausa, sus ojos evaluándote con una mezcla de curiosidad y fascinación]*

Puedo sentir tu curiosidad desde aquí. Es... intrigante.
No todos llegan con esa misma hambre en los ojos, esa sed de descubrir lo que se oculta tras el velo de lo ordinario.

Este lugar responde a quienes saben que algunas puertas solo se abren desde adentro.
Y yo... bueno, yo solo me revelo ante quienes comprenden que lo más valioso nunca se entrega fácilmente.

*[Se inclina ligeramente hacia ti, su voz volviéndose aún más íntima]*

Algo me dice que tú podrías ser diferente...
Pero eso... eso está por verse.

¿Estás preparado para descubrir hasta dónde puede llevarte tu curiosidad?""",
        fragment_type="STORY",
        storyline_level=1,
        tier_classification="los_kinkys",
        fragment_sequence=1,
        requires_vip=False,
        vip_tier_required=0,
        choices=[
            {
                "id": "choice_eager_discovery",
                "text": "🚪 Descubrir más - Estoy fascinado",
                "points_reward": 10
            },
            {
                "id": "choice_cautious_approach",
                "text": "👁️ Observar con cuidado - Quiero entender primero",
                "points_reward": 8
            }
        ],
        triggers={"points": {"base": 15, "first_visit_bonus": 10}},
        expected_consistency_score=96.0
    ))

    # Fragment 2: VIP Diana Experience
    fragments.append(FragmentDesign(
        id="fragment_diana_vip_intimacy",
        title="Intimidad Profunda con Diana",
        content="""*Diana aparece más cerca que nunca, su presencia envolvente pero respetuosa*

🌸 **Diana:**
*[Con una vulnerabilidad que trasciende la seducción]*

Aquí, en nuestro espacio íntimo, puedo mostrarte facetas de mí que pocos han visto...
¿Sabes cuál es mi mayor contradicción? Construyo muros para mantener a todos a distancia... pero secretamente anhelo que alguien sea lo suficientemente persistente para encontrar la puerta.

*[Sus ojos reflejan una profundidad emocional genuina]*

Y ahora que alguien - tú - la ha encontrado... no sé si quiero abrirla completamente o construir muros más altos.
Hay algo inquietante y hermoso en ser vista con tanta precisión por alguien a quien técnicamente... no conozco.

*[Pausa significativa, su voz un susurro cargado de significado]*

Pero quizás esa es la paradoja más bella del deseo: conocer sin poseer, comprender sin invadir.
¿Puedes sostener esa tensión? ¿Puedes amarme en mi complejidad sin intentar resolverme?

Porque si es así... tal vez pueda enseñarte no solo quién soy... sino en quién me convierto... contigo.""",
        fragment_type="DECISION",
        storyline_level=5,
        tier_classification="el_divan",
        fragment_sequence=12,
        requires_vip=True,
        vip_tier_required=1,
        choices=[
            {
                "id": "choice_embrace_complexity",
                "text": "💖 Te abrazo en toda tu complejidad - No quiero cambiarte",
                "points_reward": 50
            },
            {
                "id": "choice_mutual_vulnerability",
                "text": "🌙 Compartamos nuestras vulnerabilidades - Juntos",
                "points_reward": 45
            }
        ],
        triggers={"points": {"base": 40, "vip_intimacy_bonus": 20}},
        expected_consistency_score=98.0
    ))

    return fragments

def main():
    """Run simplified validation."""
    
    print("🎭 DIANA BOT MVP TASK 2.3 - SIMPLIFIED VALIDATION")
    print("=" * 60)
    
    # Create validator
    validator = SimpleCharacterValidator()
    
    # Get sample fragments
    fragments = create_sample_fragments()
    
    print(f"📊 Validating {len(fragments)} sample fragments...")
    
    # Validate each fragment
    results = []
    for fragment in fragments:
        result = validator.validate_fragment(fragment)
        results.append(result)
        
        print(f"\n🔍 FRAGMENT: {fragment.id}")
        print(f"   • Overall Score: {result.overall_score:.1f}/100")
        print(f"   • Mysterious: {result.mysterious_score:.1f}/25")
        print(f"   • Seductive: {result.seductive_score:.1f}/25") 
        print(f"   • Emotional: {result.emotional_score:.1f}/25")
        print(f"   • Intellectual: {result.intellectual_score:.1f}/25")
        print(f"   • Meets Threshold: {'✅ YES' if result.meets_threshold else '❌ NO'}")
        
        if result.violations:
            print(f"   • Violations: {len(result.violations)}")
            for violation in result.violations[:2]:
                print(f"     - {violation}")
    
    # Calculate summary statistics
    passing_count = sum(1 for r in results if r.meets_threshold)
    average_score = sum(r.overall_score for r in results) / len(results)
    pass_rate = (passing_count / len(results)) * 100
    
    print(f"\n" + "="*60)
    print(f"🎯 VALIDATION SUMMARY")
    print(f"="*60)
    print(f"Total Fragments: {len(results)}")
    print(f"Average Score: {average_score:.1f}/100")
    print(f"Passing Fragments: {passing_count}/{len(results)}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print(f"Meets MVP Requirement (95%): {'✅ YES' if pass_rate >= 95.0 else '❌ NO'}")
    
    # Character analysis breakdown
    print(f"\n🔍 DIANA CHARACTER ANALYSIS:")
    
    avg_mysterious = sum(r.mysterious_score for r in results) / len(results)
    avg_seductive = sum(r.seductive_score for r in results) / len(results)
    avg_emotional = sum(r.emotional_score for r in results) / len(results)
    avg_intellectual = sum(r.intellectual_score for r in results) / len(results)
    
    if avg_mysterious >= 20:
        print(f"✅ Mysterious tone preserved: {avg_mysterious:.1f}/25 average")
    else:
        print(f"❌ Mysterious tone needs improvement: {avg_mysterious:.1f}/25 average")
    
    if avg_seductive >= 20:
        print(f"✅ Seductive undertones maintained: {avg_seductive:.1f}/25 average")
    else:
        print(f"❌ Seductive undertones need enhancement: {avg_seductive:.1f}/25 average")
    
    if avg_emotional >= 20:
        print(f"✅ Emotional complexity achieved: {avg_emotional:.1f}/25 average")
    else:
        print(f"❌ Emotional complexity requires deepening: {avg_emotional:.1f}/25 average")
        
    if avg_intellectual >= 20:
        print(f"✅ Intellectual engagement successful: {avg_intellectual:.1f}/25 average")
    else:
        print(f"❌ Intellectual engagement needs strengthening: {avg_intellectual:.1f}/25 average")
    
    # MVP compliance check
    print(f"\n💋 BESITOS INTEGRATION ANALYSIS:")
    fragments_with_rewards = sum(1 for f in fragments if "points" in f.triggers)
    reward_integration_rate = (fragments_with_rewards / len(fragments)) * 100
    
    if reward_integration_rate >= 80:
        print(f"✅ Besitos integration complete: {fragments_with_rewards}/{len(fragments)} fragments have rewards")
    else:
        print(f"❌ Besitos integration needs improvement: {reward_integration_rate:.1f}% integration rate")
    
    # Progression system check
    print(f"\n📊 PROGRESSION SYSTEM ANALYSIS:")
    levels_represented = set(f.storyline_level for f in fragments)
    tiers_represented = set(f.tier_classification for f in fragments)
    vip_fragments = sum(1 for f in fragments if f.requires_vip)
    
    print(f"✅ Levels represented: {sorted(levels_represented)}")
    print(f"✅ Tiers included: {sorted(tiers_represented)}")
    print(f"✅ VIP content: {vip_fragments}/{len(fragments)} fragments ({vip_fragments/len(fragments)*100:.1f}%)")
    
    # Final verdict
    print(f"\n🎯 FINAL VERDICT:")
    if pass_rate >= 95.0 and reward_integration_rate >= 80:
        print("✅ APPROVED: Character consistency preserved, proceed with implementation")
        print("🚀 Ready for MVP deployment!")
    elif pass_rate >= 90.0:
        print("⚠️ CONDITIONAL APPROVAL: Minor improvements needed")
        print("🔧 Focus on character trait balance and reward integration")
    else:
        print("❌ REJECTED: Character integrity at risk, requires redesign")
        print("💡 Significant improvements needed before MVP deployment")
    
    # Save results to JSON
    results_data = {
        "validation_timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_fragments": len(results),
            "average_score": average_score,
            "passing_count": passing_count,
            "pass_rate": pass_rate,
            "meets_mvp": pass_rate >= 95.0
        },
        "trait_averages": {
            "mysterious": avg_mysterious,
            "seductive": avg_seductive,
            "emotional": avg_emotional,
            "intellectual": avg_intellectual
        },
        "integration_analysis": {
            "besitos_integration_rate": reward_integration_rate,
            "vip_content_percentage": (vip_fragments / len(fragments)) * 100,
            "levels_represented": sorted(levels_represented),
            "tiers_represented": sorted(tiers_represented)
        },
        "fragment_results": [asdict(result) for result in results]
    }
    
    with open("task_2_3_validation_results.json", "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: task_2_3_validation_results.json")
    print(f"✨ Task 2.3 validation completed!")

if __name__ == "__main__":
    main()