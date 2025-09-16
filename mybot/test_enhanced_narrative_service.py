#!/usr/bin/env python3
"""
Test script for Task 20: Enhanced NarrativeService with Analytics Integration
Tests the comprehensive analytics tracking and context-aware narrative responses.
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import DatabaseManager
from services.narrative_service import NarrativeService
from database.models import User
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState, FragmentAnalytics, UserJourneyAnalytics
from sqlalchemy import select

class TestEnhancedNarrativeService:
    """Test suite for the enhanced narrative service with analytics."""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.test_user_id = 999999  # Use a test user ID

    async def setup_test_data(self, session):
        """Set up test data for narrative testing."""
        print("Setting up test data...")

        # Create test user
        test_user = User(
            id=self.test_user_id,
            username="test_user",
            first_name="Test",
            points=50
        )
        session.add(test_user)

        # Create test story fragments
        start_fragment = StoryFragment(
            key="test_start",
            text="Welcome to the test narrative. This is the beginning of your journey.",
            character="Lucien",
            reward_besitos=5
        )
        session.add(start_fragment)

        middle_fragment = StoryFragment(
            key="test_middle",
            text="You've made your first choice and arrived here. What will you do next?",
            character="Diana",
            reward_besitos=10
        )
        session.add(middle_fragment)

        end_fragment = StoryFragment(
            key="test_end",
            text="This is the conclusion of your test journey. Well done!",
            character="Lucien",
            reward_besitos=15
        )
        session.add(end_fragment)

        await session.flush()

        # Create test narrative choices
        choice1 = NarrativeChoice(
            source_fragment_id=start_fragment.id,
            destination_fragment_key="test_middle",
            text="Continue the adventure"
        )
        session.add(choice1)

        choice2 = NarrativeChoice(
            source_fragment_id=middle_fragment.id,
            destination_fragment_key="test_end",
            text="Reach the conclusion"
        )
        session.add(choice2)

        await session.commit()
        print("Test data setup complete!")

        return {
            "start_fragment": start_fragment,
            "middle_fragment": middle_fragment,
            "end_fragment": end_fragment,
            "choice1": choice1,
            "choice2": choice2
        }

    async def cleanup_test_data(self, session):
        """Clean up test data."""
        print("Cleaning up test data...")

        # Clean up analytics data
        await session.execute(
            "DELETE FROM fragment_analytics WHERE fragment_key LIKE 'test_%'"
        )
        await session.execute(
            f"DELETE FROM user_journey_analytics WHERE user_id = {self.test_user_id}"
        )
        await session.execute(
            f"DELETE FROM user_narrative_states WHERE user_id = {self.test_user_id}"
        )

        # Clean up narrative data
        await session.execute(
            "DELETE FROM narrative_choices WHERE destination_fragment_key LIKE 'test_%'"
        )
        await session.execute(
            "DELETE FROM story_fragments WHERE key LIKE 'test_%'"
        )

        # Clean up user
        await session.execute(f"DELETE FROM users WHERE id = {self.test_user_id}")

        await session.commit()
        print("Cleanup complete!")

    async def test_basic_narrative_with_analytics(self, session, narrative_service):
        """Test basic narrative flow with analytics tracking."""
        print("\n=== Testing Basic Narrative Flow with Analytics ===")

        # Start narrative
        fragment = await narrative_service.start_narrative(self.test_user_id)
        assert fragment is not None, "Failed to start narrative"
        assert fragment.key == "test_start", f"Expected test_start, got {fragment.key}"
        print(f"✓ Started narrative at fragment: {fragment.key}")

        # Check that analytics were created
        journey = await narrative_service._get_user_journey_analytics(self.test_user_id)
        assert journey is not None, "User journey analytics not created"
        assert journey.engagement_level == "new", f"Expected 'new' engagement level, got {journey.engagement_level}"
        print("✓ User journey analytics created successfully")

        # Get fragment analytics
        fragment_analytics = await narrative_service._get_or_create_fragment_analytics("test_start")
        assert fragment_analytics.view_count >= 1, "Fragment view count not tracked"
        print("✓ Fragment analytics tracking working")

        return fragment

    async def test_choice_tracking_and_progression(self, session, narrative_service):
        """Test choice tracking and fragment progression analytics."""
        print("\n=== Testing Choice Tracking and Progression ===")

        # Get current fragment and choices
        current_fragment = await narrative_service.get_user_current_fragment(self.test_user_id)
        assert current_fragment is not None, "Could not get current fragment"

        # Get available choices
        choices = await narrative_service._get_fragment_choices(current_fragment.id)
        assert len(choices) > 0, "No choices available"
        print(f"✓ Found {len(choices)} choices for fragment {current_fragment.key}")

        # Simulate some time passing for session tracking
        time.sleep(1)

        # Make a choice
        next_fragment = await narrative_service.process_user_decision(self.test_user_id, 0)
        assert next_fragment is not None, "Failed to process decision"
        assert next_fragment.key == "test_middle", f"Expected test_middle, got {next_fragment.key}"
        print(f"✓ Successfully progressed to fragment: {next_fragment.key}")

        # Verify choice was tracked in analytics
        journey = await narrative_service._get_user_journey_analytics(self.test_user_id)
        assert len(journey.choices_made) >= 1, "Choice not recorded in journey analytics"
        assert journey.fragments_completed >= 1, "Fragment completion not tracked"
        print("✓ Choice and progression tracking verified")

        # Verify fragment analytics were updated
        start_analytics = await narrative_service._get_or_create_fragment_analytics("test_start")
        assert start_analytics.completion_count >= 1, "Fragment completion not tracked"
        print("✓ Fragment completion analytics updated")

        return next_fragment

    async def test_contextual_narrative_response(self, session, narrative_service):
        """Test context-aware narrative responses."""
        print("\n=== Testing Context-Aware Narrative Responses ===")

        current_fragment = await narrative_service.get_user_current_fragment(self.test_user_id)
        assert current_fragment is not None, "Could not get current fragment"

        # Get contextual response
        contextual_response = await narrative_service.get_contextual_narrative_response(
            self.test_user_id, current_fragment
        )

        assert "fragment" in contextual_response, "Fragment not in contextual response"
        assert "context" in contextual_response, "Context not in contextual response"
        assert "personalization" in contextual_response, "Personalization not in contextual response"

        context = contextual_response["context"]
        assert "is_returning_visitor" in context, "Returning visitor status not tracked"
        assert "character_familiarity" in context, "Character familiarity not tracked"
        print("✓ Context-aware response generated successfully")

        personalization = contextual_response["personalization"]
        assert "suggested_tone" in personalization, "Narrative tone suggestion not provided"
        assert "reference_previous_choices" in personalization, "Previous choices not referenced"
        print("✓ Personalization features working")

        # Check character familiarity
        char_familiarity = context["character_familiarity"]
        assert "level" in char_familiarity, "Character familiarity level not provided"
        assert "interactions" in char_familiarity, "Character interaction count not provided"
        print(f"✓ Character familiarity: {char_familiarity['level']} ({char_familiarity['interactions']} interactions)")

        return contextual_response

    async def test_user_analytics_summary(self, session, narrative_service):
        """Test comprehensive user analytics summary."""
        print("\n=== Testing User Analytics Summary ===")

        # Get narrative stats with analytics
        stats = await narrative_service.get_user_narrative_stats(self.test_user_id)
        assert "current_fragment" in stats, "Current fragment not in stats"
        assert "fragments_visited" in stats, "Fragments visited not tracked"
        assert "analytics" in stats, "Analytics data not included in stats"

        analytics = stats["analytics"]
        assert "engagement_level" in analytics, "Engagement level not tracked"
        assert "exploration_score" in analytics, "Exploration score not calculated"
        assert "total_time_spent" in analytics, "Total time not tracked"
        assert "character_interactions" in analytics, "Character interactions not tracked"

        print(f"✓ User analytics summary complete:")
        print(f"  - Engagement level: {analytics['engagement_level']}")
        print(f"  - Exploration score: {analytics['exploration_score']}")
        print(f"  - Total time spent: {analytics['total_time_spent']} seconds")
        print(f"  - Character interactions: {analytics['character_interactions']}")

        return stats

    async def test_advanced_progression_tracking(self, session, narrative_service):
        """Test advanced progression and complete the narrative."""
        print("\n=== Testing Advanced Progression Tracking ===")

        # Complete the narrative journey
        current_fragment = await narrative_service.get_user_current_fragment(self.test_user_id)
        choices = await narrative_service._get_fragment_choices(current_fragment.id)

        if len(choices) > 0:
            # Simulate time for session tracking
            time.sleep(1)

            final_fragment = await narrative_service.process_user_decision(self.test_user_id, 0)
            assert final_fragment is not None, "Failed to complete narrative"
            assert final_fragment.key == "test_end", f"Expected test_end, got {final_fragment.key}"
            print(f"✓ Completed narrative at fragment: {final_fragment.key}")

            # Verify comprehensive journey tracking
            journey = await narrative_service._get_user_journey_analytics(self.test_user_id)
            assert len(journey.choices_made) >= 2, "Multiple choices not tracked"
            assert journey.fragments_completed >= 2, "Multiple fragment completions not tracked"
            assert len(journey.progression_path) >= 2, "Progression path not complete"
            assert journey.engagement_level != "new", "Engagement level not updated"

            print("✓ Advanced progression tracking verified")
            print(f"  - Choices made: {len(journey.choices_made)}")
            print(f"  - Fragments completed: {journey.fragments_completed}")
            print(f"  - Progression path: {journey.progression_path}")
            print(f"  - Engagement level: {journey.engagement_level}")

            return journey

        return None

    async def run_comprehensive_test(self):
        """Run the complete test suite."""
        print("Starting Enhanced Narrative Service Test Suite")
        print("=" * 60)

        try:
            # Initialize database session
            async with self.db_manager.get_session() as session:
                # Clean up any existing test data
                await self.cleanup_test_data(session)

                # Set up test data
                test_data = await self.setup_test_data(session)

                # Initialize narrative service with analytics enabled
                narrative_service = NarrativeService(session, analytics_enabled=True)

                try:
                    # Run all tests
                    await self.test_basic_narrative_with_analytics(session, narrative_service)
                    await self.test_choice_tracking_and_progression(session, narrative_service)
                    await self.test_contextual_narrative_response(session, narrative_service)
                    await self.test_user_analytics_summary(session, narrative_service)
                    await self.test_advanced_progression_tracking(session, narrative_service)

                    print("\n" + "=" * 60)
                    print("🎉 ALL TESTS PASSED! Enhanced Narrative Service working correctly!")
                    print("✓ Analytics integration functioning")
                    print("✓ Context-aware responses implemented")
                    print("✓ User journey tracking operational")
                    print("✓ Real-time analytics collection working")
                    print("=" * 60)

                finally:
                    # Clean up test data
                    await self.cleanup_test_data(session)

        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        return True

async def main():
    """Main test execution function."""
    tester = TestEnhancedNarrativeService()
    success = await tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)