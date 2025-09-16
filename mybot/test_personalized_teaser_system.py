"""
Test script for the Personalized Teaser Content System
Task 21 implementation verification

This script tests the integration of user archetype analysis,
character voice patterns, and shop item relationships to create
compelling personalized teasers.
"""
import asyncio
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required services and models
from services.personalized_teaser_service import PersonalizedTeaserService
from services.narrative_service import NarrativeService
from services.user_experience_service import UserExperienceService
from services.character_voice_service import CharacterVoiceService
from database.models import User
from database.narrative_models import StoryFragment, UserNarrativeState
from database.emotional_models import UserEmotionalProfile, ArchetypeClassification


class PersonalizedTeaserSystemTest:
    """Test suite for the personalized teaser system."""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///test.db"):
        self.database_url = database_url
        self.engine = None
        self.session_maker = None

    async def setup(self):
        """Set up test environment."""
        try:
            self.engine = create_async_engine(self.database_url, echo=False)
            self.session_maker = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("Test environment set up successfully")
        except Exception as e:
            logger.error(f"Error setting up test environment: {e}")
            raise

    async def cleanup(self):
        """Clean up test environment."""
        if self.engine:
            await self.engine.dispose()

    async def create_test_data(self, session: AsyncSession):
        """Create test data for scenarios."""
        try:
            # Create test user
            test_user = User(
                id=99999,
                username="test_user_teaser",
                points=25,
                level=2,
                role="user"
            )
            session.add(test_user)

            # Create test emotional profile with different archetypes
            profiles = [
                (99999, ArchetypeClassification.EXPLORER, 0.8),
                (99998, ArchetypeClassification.DIRECT, 0.7),
                (99997, ArchetypeClassification.POET, 0.9),
                (99996, ArchetypeClassification.ANALYTIC, 0.8),
                (99995, ArchetypeClassification.PATIENT, 0.6)
            ]

            for user_id, archetype, confidence in profiles:
                if user_id != 99999:  # Create additional users
                    user = User(
                        id=user_id,
                        username=f"test_user_{user_id}",
                        points=30,
                        level=1,
                        role="user"
                    )
                    session.add(user)

                profile = UserEmotionalProfile(
                    user_id=user_id,
                    archetype_classification=archetype,
                    archetype_confidence=confidence,
                    vulnerability_level=0.5,
                    authenticity_score=0.7
                )
                session.add(profile)

            # Create test story fragment with restrictions
            test_fragment = StoryFragment(
                id=9999,
                key="test_restricted_content",
                text="This is exclusive content that requires points to access.",
                character="Diana",
                level=2,
                min_besitos=50,  # More than test user has
                reward_besitos=10
            )
            session.add(test_fragment)

            # Create VIP-only fragment
            vip_fragment = StoryFragment(
                id=9998,
                key="test_vip_content",
                text="Exclusive VIP content for premium members.",
                character="Lucien",
                level=3,
                required_role="vip",
                reward_besitos=20
            )
            session.add(vip_fragment)

            await session.commit()
            logger.info("Test data created successfully")

        except Exception as e:
            logger.error(f"Error creating test data: {e}")
            await session.rollback()
            raise

    async def test_archetype_personalization(self, session: AsyncSession):
        """Test that different archetypes get different teasers."""
        logger.info("Testing archetype-based personalization...")

        teaser_service = PersonalizedTeaserService(session)

        # Get the test fragment
        fragment = await session.get(StoryFragment, 9999)
        if not fragment:
            logger.error("Test fragment not found")
            return False

        archetype_results = {}

        # Test each archetype
        for user_id in [99999, 99998, 99997, 99996, 99995]:
            try:
                teaser_result = await teaser_service.generate_personalized_teaser(
                    user_id=user_id,
                    restricted_fragment=fragment,
                    restriction_type="besitos",
                    restriction_amount=50
                )

                archetype = teaser_result.get("archetype", "unknown")
                teaser_content = teaser_result.get("teaser_content", "")

                archetype_results[archetype] = {
                    "content_length": len(teaser_content),
                    "has_purchase_motivation": teaser_result.get("purchase_motivation") is not None,
                    "character": teaser_result.get("character"),
                    "sample_content": teaser_content[:100] + "..." if len(teaser_content) > 100 else teaser_content
                }

                logger.info(f"Archetype {archetype}: Generated {len(teaser_content)} chars, "
                          f"Character: {teaser_result.get('character')}")

            except Exception as e:
                logger.error(f"Error testing archetype for user {user_id}: {e}")

        # Verify different archetypes got different approaches
        unique_approaches = set()
        for archetype, data in archetype_results.items():
            approach_signature = f"{data['character']}_{data['content_length']//50}"
            unique_approaches.add(approach_signature)

        success = len(unique_approaches) >= 3  # At least 3 different approaches
        logger.info(f"Archetype personalization test: {'PASSED' if success else 'FAILED'}")
        logger.info(f"Generated {len(unique_approaches)} unique approach signatures from {len(archetype_results)} archetypes")

        return success

    async def test_character_voice_integration(self, session: AsyncSession):
        """Test character voice integration."""
        logger.info("Testing character voice integration...")

        teaser_service = PersonalizedTeaserService(session)
        fragment = await session.get(StoryFragment, 9999)

        try:
            # Test Diana fragment
            diana_teaser = await teaser_service.generate_personalized_teaser(
                user_id=99999,
                restricted_fragment=fragment,
                restriction_type="besitos",
                restriction_amount=50
            )

            # Test Lucien fragment (VIP)
            vip_fragment = await session.get(StoryFragment, 9998)
            lucien_teaser = await teaser_service.generate_personalized_teaser(
                user_id=99999,
                restricted_fragment=vip_fragment,
                restriction_type="vip",
                restriction_amount=0
            )

            # Verify character-specific elements
            diana_has_character_voice = "*" in diana_teaser.get("teaser_content", "")
            lucien_has_character_voice = "*" in lucien_teaser.get("teaser_content", "")

            success = diana_has_character_voice and lucien_has_character_voice

            logger.info(f"Diana teaser has character voice: {diana_has_character_voice}")
            logger.info(f"Lucien teaser has character voice: {lucien_has_character_voice}")
            logger.info(f"Character voice integration test: {'PASSED' if success else 'FAILED'}")

            return success

        except Exception as e:
            logger.error(f"Error testing character voice integration: {e}")
            return False

    async def test_shop_integration(self, session: AsyncSession):
        """Test shop integration for purchase motivation."""
        logger.info("Testing shop integration...")

        teaser_service = PersonalizedTeaserService(session)
        fragment = await session.get(StoryFragment, 9999)

        try:
            teaser_result = await teaser_service.generate_personalized_teaser(
                user_id=99999,
                restricted_fragment=fragment,
                restriction_type="besitos",
                restriction_amount=50
            )

            purchase_motivation = teaser_result.get("purchase_motivation")
            has_motivation = purchase_motivation is not None
            has_points_calculation = False
            has_relevant_items = False

            if purchase_motivation:
                has_points_calculation = "points_needed" in purchase_motivation
                has_relevant_items = len(purchase_motivation.get("relevant_items", [])) > 0

            success = has_motivation and has_points_calculation

            logger.info(f"Has purchase motivation: {has_motivation}")
            logger.info(f"Has points calculation: {has_points_calculation}")
            logger.info(f"Has relevant items: {has_relevant_items}")
            logger.info(f"Shop integration test: {'PASSED' if success else 'FAILED'}")

            return success

        except Exception as e:
            logger.error(f"Error testing shop integration: {e}")
            return False

    async def test_narrative_service_integration(self, session: AsyncSession):
        """Test integration with narrative service."""
        logger.info("Testing narrative service integration...")

        try:
            narrative_service = NarrativeService(session)

            # Test contextual teaser generation
            fragment = await session.get(StoryFragment, 9999)
            teasers = await narrative_service._get_contextual_teasers(99999, fragment)

            has_personalized_teasers = "personalized_teasers" in teasers
            personalized_count = len(teasers.get("personalized_teasers", []))

            success = has_personalized_teasers and personalized_count > 0

            logger.info(f"Has personalized teasers: {has_personalized_teasers}")
            logger.info(f"Personalized teaser count: {personalized_count}")
            logger.info(f"Narrative service integration test: {'PASSED' if success else 'FAILED'}")

            return success

        except Exception as e:
            logger.error(f"Error testing narrative service integration: {e}")
            return False

    async def test_user_experience_service_integration(self, session: AsyncSession):
        """Test integration with user experience service."""
        logger.info("Testing user experience service integration...")

        try:
            character_voice_service = CharacterVoiceService()
            ux_service = UserExperienceService(session, character_voice_service)

            # Test personalized teaser generation
            teaser_content = await ux_service.generate_personalized_teaser_content(
                user_id=99999,
                restricted_content_key="test_restricted_content"
            )

            has_content = len(teaser_content) > 50
            has_personalization = "espíritu" in teaser_content or "misterio" in teaser_content

            success = has_content and has_personalization

            logger.info(f"Generated teaser length: {len(teaser_content)}")
            logger.info(f"Has personalization elements: {has_personalization}")
            logger.info(f"User experience service integration test: {'PASSED' if success else 'FAILED'}")

            return success

        except Exception as e:
            logger.error(f"Error testing user experience service integration: {e}")
            return False

    async def run_all_tests(self):
        """Run complete test suite."""
        logger.info("Starting Personalized Teaser System Test Suite...")

        await self.setup()

        async with self.session_maker() as session:
            try:
                await self.create_test_data(session)

                tests = [
                    ("Archetype Personalization", self.test_archetype_personalization),
                    ("Character Voice Integration", self.test_character_voice_integration),
                    ("Shop Integration", self.test_shop_integration),
                    ("Narrative Service Integration", self.test_narrative_service_integration),
                    ("User Experience Service Integration", self.test_user_experience_service_integration)
                ]

                results = {}
                for test_name, test_func in tests:
                    logger.info(f"\n{'='*50}")
                    logger.info(f"Running: {test_name}")
                    logger.info(f"{'='*50}")

                    try:
                        result = await test_func(session)
                        results[test_name] = result
                    except Exception as e:
                        logger.error(f"Test {test_name} failed with exception: {e}")
                        results[test_name] = False

                # Summary
                logger.info(f"\n{'='*50}")
                logger.info("TEST RESULTS SUMMARY")
                logger.info(f"{'='*50}")

                passed = sum(results.values())
                total = len(results)

                for test_name, result in results.items():
                    status = "PASSED" if result else "FAILED"
                    logger.info(f"{test_name}: {status}")

                logger.info(f"\nOverall: {passed}/{total} tests passed")

                if passed == total:
                    logger.info("🎉 All tests passed! Personalized Teaser System is working correctly.")
                else:
                    logger.warning(f"⚠️  {total - passed} test(s) failed. Please review the implementation.")

                return passed == total

            except Exception as e:
                logger.error(f"Error running test suite: {e}")
                return False
            finally:
                await self.cleanup()


async def main():
    """Main test runner."""
    # Use the actual database URL from your environment
    database_url = "sqlite+aiosqlite:///./bot_database.db"

    test_suite = PersonalizedTeaserSystemTest(database_url)
    success = await test_suite.run_all_tests()

    exit_code = 0 if success else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)