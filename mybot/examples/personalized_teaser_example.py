"""
Personalized Teaser Content System - Usage Example
Task 21: Implementation demonstration

This example shows how to use the personalized teaser system
to generate contextually appropriate and personalized content
for item-restricted narrative paths.
"""
import asyncio
import logging
from datetime import datetime

# Example usage without full database setup
logging.basicConfig(level=logging.INFO)


class PersonalizedTeaserExample:
    """Example implementation of personalized teaser generation."""

    def __init__(self):
        self.archetype_strategies = {
            "explorer": self._create_explorer_teaser,
            "direct": self._create_direct_teaser,
            "poet": self._create_poet_teaser,
            "analytic": self._create_analytic_teaser,
            "patient": self._create_patient_teaser
        }

    def _create_explorer_teaser(self, fragment_key: str, restriction_amount: int) -> dict:
        """Example Explorer archetype teaser."""
        return {
            "content": f"Un sendero inexplorado se abre ante ti en '{fragment_key}'...\n\n"
                      f"¿Qué secretos esconde este fragmento?\n"
                      f"Tu espíritu aventurero ha encontrado una puerta hacia lo inexplorado.",
            "archetype_approach": "discovery_focused",
            "character_suggestion": "diana",
            "motivation_type": "curiosity_driven"
        }

    def _create_direct_teaser(self, fragment_key: str, restriction_amount: int) -> dict:
        """Example Direct archetype teaser."""
        return {
            "content": f"Acceso directo a '{fragment_key}' disponible con los recursos adecuados.\n\n"
                      f"La solución es simple y directa.\n"
                      f"Inversión requerida: {restriction_amount} besitos. Resultado inmediato garantizado.",
            "archetype_approach": "efficiency_focused",
            "character_suggestion": "lucien",
            "motivation_type": "solution_oriented"
        }

    def _create_poet_teaser(self, fragment_key: str, restriction_amount: int) -> dict:
        """Example Poet archetype teaser."""
        return {
            "content": f"En '{fragment_key}' habitan palabras aún no escritas, esperando tu toque para cobrar vida.\n\n"
                      f"La belleza de lo no revelado tiene su propio encanto.\n"
                      f"Los momentos más hermosos nacen del anhelo cultivado con paciencia.",
            "archetype_approach": "aesthetic_focused",
            "character_suggestion": "diana",
            "motivation_type": "aesthetic_appreciation"
        }

    def _create_analytic_teaser(self, fragment_key: str, restriction_amount: int) -> dict:
        """Example Analytic archetype teaser."""
        return {
            "content": f"Análisis de '{fragment_key}': Contenido de alta relevancia identificado.\n\n"
                      f"El análisis histórico sugiere que el contenido restringido ofrece valor diferenciado.\n"
                      f"Análisis de costo-beneficio: {restriction_amount} besitos por acceso a contenido diferenciado.",
            "archetype_approach": "logic_focused",
            "character_suggestion": "lucien",
            "motivation_type": "optimization_driven"
        }

    def _create_patient_teaser(self, fragment_key: str, restriction_amount: int) -> dict:
        """Example Patient archetype teaser."""
        return {
            "content": f"'{fragment_key}' permanece en calma, esperando el momento adecuado para revelarse.\n\n"
                      f"Los tesoros más valiosos se revelan solo a quienes saben cultivar la paciencia.\n"
                      f"La contemplación previa enriquece exponencialmente la experiencia final.",
            "archetype_approach": "patience_focused",
            "character_suggestion": "diana",
            "motivation_type": "patience_rewarded"
        }

    def generate_example_teaser(self, archetype: str, fragment_key: str, restriction_amount: int) -> dict:
        """Generate an example teaser for the given archetype."""
        strategy = self.archetype_strategies.get(archetype, self._create_explorer_teaser)
        base_teaser = strategy(fragment_key, restriction_amount)

        # Simulate character voice enhancement
        character = base_teaser["character_suggestion"]
        if character == "diana":
            enhanced_content = f"*{base_teaser['content']}*\n\n*Diana susurra con voz íntima...*"
        else:
            enhanced_content = f"{base_teaser['content']}\n\n*Lucien añade con elegancia:* \"La elección es tuya.\""

        return {
            "teaser_content": enhanced_content,
            "archetype": archetype,
            "character": character,
            "approach": base_teaser["archetype_approach"],
            "motivation_type": base_teaser["motivation_type"],
            "restriction_info": {
                "type": "besitos",
                "amount_needed": restriction_amount,
                "fragment_key": fragment_key
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    def demonstrate_personalization(self):
        """Demonstrate personalization across different archetypes."""
        print("🎭 PERSONALIZED TEASER CONTENT SYSTEM DEMONSTRATION")
        print("=" * 60)

        # Test scenario
        fragment_key = "secret_garden"
        restriction_amount = 50

        print(f"Scenario: User wants to access '{fragment_key}' but needs {restriction_amount} besitos\n")

        archetypes = ["explorer", "direct", "poet", "analytic", "patient"]

        for archetype in archetypes:
            print(f"👤 USER ARCHETYPE: {archetype.upper()}")
            print("-" * 40)

            teaser = self.generate_example_teaser(archetype, fragment_key, restriction_amount)

            print(f"Character: {teaser['character'].title()}")
            print(f"Approach: {teaser['approach']}")
            print(f"Motivation: {teaser['motivation_type']}")
            print("\nTeaser Content:")
            print(teaser['teaser_content'])
            print("\n" + "=" * 60 + "\n")

    def demonstrate_character_adaptation(self):
        """Demonstrate how character voice adapts teasers."""
        print("🎪 CHARACTER VOICE ADAPTATION DEMONSTRATION")
        print("=" * 60)

        fragment_key = "forbidden_memories"
        restriction_amount = 75

        # Same archetype, different characters
        base_teaser = self._create_explorer_teaser(fragment_key, restriction_amount)

        print("Base Teaser Content:")
        print(base_teaser['content'])
        print("\n" + "-" * 40)

        # Diana's delivery
        print("✨ DIANA'S DELIVERY:")
        diana_teaser = f"*{base_teaser['content']}*\n\n" + \
                      "*Diana te toma de la mano y susurra:* \"En tus pausas leo más que en tus certezas...\""
        print(diana_teaser)

        print("\n" + "-" * 40)

        # Lucien's delivery
        print("🎩 LUCIEN'S DELIVERY:")
        lucien_teaser = f"{base_teaser['content']}\n\n" + \
                       "*Lucien observa con elegancia:* \"Soy el custodio de lo que aún no estás listo para escuchar.\""
        print(lucien_teaser)

        print("\n" + "=" * 60 + "\n")

    def demonstrate_purchase_motivation(self):
        """Demonstrate purchase motivation integration."""
        print("🛍️ PURCHASE MOTIVATION INTEGRATION")
        print("=" * 60)

        scenarios = [
            {"archetype": "direct", "points_needed": 25, "current_points": 30},
            {"archetype": "explorer", "points_needed": 50, "current_points": 15},
            {"archetype": "poet", "points_needed": 30, "current_points": 45}
        ]

        for scenario in scenarios:
            archetype = scenario["archetype"]
            points_needed = scenario["points_needed"]
            current_points = scenario["current_points"]
            shortfall = max(0, points_needed - current_points)

            print(f"👤 Archetype: {archetype.upper()}")
            print(f"💰 Current Points: {current_points}")
            print(f"💎 Points Needed: {points_needed}")
            print(f"📊 Shortfall: {shortfall}")

            if shortfall > 0:
                motivation_messages = {
                    "direct": f"Solución directa: {shortfall} besitos adicionales desbloquean acceso inmediato.",
                    "explorer": "Nuevos horizontes esperan ser explorados con los recursos adecuados.",
                    "poet": "La belleza completa de esta narrativa merece tu inversión emocional."
                }

                print(f"🎯 Motivation: {motivation_messages.get(archetype, 'Generic motivation')}")
                print("📦 Suggested Items:")
                print("   • 📖 Diario Secreto (50 besitos) - Contenido exclusivo")
                print("   • 💝 Regalo Especial (30 besitos) - Sorpresa narrativa")
            else:
                print("✅ User has sufficient points!")

            print("\n" + "-" * 40 + "\n")

    async def run_demonstration(self):
        """Run complete demonstration."""
        print("🚀 STARTING PERSONALIZED TEASER SYSTEM DEMONSTRATION\n")

        self.demonstrate_personalization()
        self.demonstrate_character_adaptation()
        self.demonstrate_purchase_motivation()

        print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("\nKey Features Demonstrated:")
        print("• ✅ User archetype-based personalization")
        print("• ✅ Character-authentic voice integration")
        print("• ✅ Purchase motivation with shop integration")
        print("• ✅ Contextual content adaptation")
        print("• ✅ Multi-layered personalization approach")


async def main():
    """Main demonstration runner."""
    example = PersonalizedTeaserExample()
    await example.run_demonstration()


if __name__ == "__main__":
    asyncio.run(main())