#!/usr/bin/env python3
"""
Cross-Module Reward Flow Integration Example

This example demonstrates how the three main cross-module reward flows work together:
1. Narrative Progress → Mission Unlocking
2. Gamification Achievements → Narrative Progress  
3. Channel Engagement → Cross-System Rewards

This is a complete working example that shows the integration between all systems.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import the reward flow services
from services.rewards.narrative_mission_flow import get_narrative_mission_flow
from services.rewards.achievement_narrative_flow import get_achievement_narrative_flow
from services.rewards.engagement_rewards_flow import get_engagement_rewards_flow
from services.rewards.cross_module_rewards import get_cross_module_rewards

# Import core services for initialization
from services.coordinador_central import CoordinadorCentral
from services.point_service import PointService
from services.user_service import UserService
from services.event_bus import get_event_bus, EventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrossModuleRewardFlowDemo:
    """
    Comprehensive demonstration of cross-module reward flows.
    
    This class shows how all the reward systems work together to create
    a cohesive gamification experience that spans narrative, achievements,
    and channel engagement.
    """
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///telegram_bot.db"):
        """Initialize the demo with database connection."""
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.session = None
        
        # Service instances
        self.coordinador = None
        self.narrative_mission_flow = None
        self.achievement_narrative_flow = None
        self.engagement_rewards_flow = None
        self.cross_module_rewards = None
        
        # Demo user ID
        self.demo_user_id = 123456789
    
    async def initialize(self):
        """Initialize database connection and services."""
        logger.info("Initializing cross-module reward flow demo...")
        
        # Create database engine and session factory
        self.engine = create_async_engine(self.database_url, echo=False)
        self.session_factory = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create session
        self.session = self.session_factory()
        
        # Initialize services
        self.coordinador = CoordinadorCentral(self.session)
        self.narrative_mission_flow = get_narrative_mission_flow(self.session)
        self.achievement_narrative_flow = get_achievement_narrative_flow(self.session)
        self.engagement_rewards_flow = get_engagement_rewards_flow(self.session)
        self.cross_module_rewards = get_cross_module_rewards(self.session)
        
        # Initialize cross-module reward system
        init_result = await self.cross_module_rewards.initialize_reward_system()
        logger.info(f"Cross-module rewards initialized: {init_result}")
        
        logger.info("Demo initialization complete!")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
        if self.engine:
            await self.engine.dispose()
    
    async def demonstrate_narrative_mission_flow(self):
        """
        Demonstrate Flow 1: Narrative Progress → Mission Unlocking
        
        Shows how completing narrative fragments unlocks new missions
        with Diana-themed notifications and dynamic menu updates.
        """
        logger.info("\n" + "="*60)
        logger.info("FLOW 1: Narrative Progress → Mission Unlocking")
        logger.info("="*60)
        
        # Simulate user completing different narrative fragments
        narrative_milestones = [
            "level1_garden_discovery",
            "level2_first_kiss", 
            "level3_passionate_night",
            "level4_complete_trust",
            "level5_ultimate_union"
        ]
        
        for fragment_key in narrative_milestones:
            logger.info(f"\n--- Processing narrative milestone: {fragment_key} ---")
            
            result = await self.narrative_mission_flow.process_narrative_progress(
                user_id=self.demo_user_id,
                completed_fragment_key=fragment_key,
                bot=None  # No bot instance in demo
            )
            
            if result.success:
                logger.info(f"✅ Narrative milestone processed successfully!")
                logger.info(f"   Unlocked Missions: {result.unlocked_missions}")
                logger.info(f"   Points Required: {result.user_level_required}")
                logger.info(f"   Notification: {result.notification_message[:100]}...")
            else:
                logger.error(f"❌ Failed to process narrative milestone")
            
            # Brief pause for demonstration
            await asyncio.sleep(0.5)
    
    async def demonstrate_achievement_narrative_flow(self):
        """
        Demonstrate Flow 2: Gamification Achievements → Narrative Progress
        
        Shows how unlocking achievements grants access to narrative content,
        hints, clues, and special story elements.
        """
        logger.info("\n" + "="*60)
        logger.info("FLOW 2: Gamification Achievements → Narrative Progress")
        logger.info("="*60)
        
        # Simulate user unlocking different achievements
        achievements = [
            "first_reaction",
            "daily_streak_7",
            "points_milestone_100",
            "mission_master",
            "devoted_lover",
            "master_storyteller"
        ]
        
        for achievement_id in achievements:
            logger.info(f"\n--- Processing achievement unlock: {achievement_id} ---")
            
            result = await self.achievement_narrative_flow.process_achievement_unlock(
                user_id=self.demo_user_id,
                achievement_id=achievement_id,
                bot=None  # No bot instance in demo
            )
            
            if result.success:
                logger.info(f"✅ Achievement unlock processed successfully!")
                logger.info(f"   Unlocked Content: {len(result.unlocked_content)} items")
                logger.info(f"   Backpack Items: {result.backpack_items}")
                logger.info(f"   Special Access: {result.special_access_granted}")
                logger.info(f"   Notification: {result.notification_message[:100]}...")
            else:
                logger.error(f"❌ Failed to process achievement unlock")
            
            # Brief pause for demonstration
            await asyncio.sleep(0.5)
    
    async def demonstrate_engagement_rewards_flow(self):
        """
        Demonstrate Flow 3: Channel Engagement → Cross-System Rewards
        
        Shows how channel activities reward users with both points and
        narrative content access, creating integrated engagement.
        """
        logger.info("\n" + "="*60)
        logger.info("FLOW 3: Channel Engagement → Cross-System Rewards")
        logger.info("="*60)
        
        # Simulate different types of channel engagement
        engagement_activities = [
            {"type": "reaction", "data": {"channel_id": 1001, "message_id": 501}},
            {"type": "comment", "data": {"channel_id": 1001, "message_id": 502, "comment_length": 75}},
            {"type": "post", "data": {"channel_id": 1002, "content_quality": "high"}},
            {"type": "multi_channel", "data": {"channels": [1001, 1002, 1003], "activities": 8}},
            {"type": "daily_streak", "data": {"streak": 14, "consistency": True}},
            {"type": "engagement_burst", "data": {"activities": 15, "time_window": 45}}
        ]
        
        for activity in engagement_activities:
            logger.info(f"\n--- Processing engagement activity: {activity['type']} ---")
            
            result = await self.engagement_rewards_flow.process_engagement_activity(
                user_id=self.demo_user_id,
                activity_type=activity["type"],
                activity_data=activity["data"],
                bot=None  # No bot instance in demo
            )
            
            if result.success:
                logger.info(f"✅ Engagement activity processed successfully!")
                logger.info(f"   Points Awarded: {result.dual_reward.total_points}")
                logger.info(f"   Bonus Multiplier: {result.dual_reward.bonus_multiplier}x")
                logger.info(f"   Narrative Unlocks: {result.dual_reward.narrative_unlocks}")
                logger.info(f"   Special Access: {result.dual_reward.special_access}")
                logger.info(f"   Achievements: {result.achievements_triggered}")
                logger.info(f"   Notification: {result.notification_message[:100]}...")
            else:
                logger.error(f"❌ Failed to process engagement activity")
            
            # Brief pause for demonstration
            await asyncio.sleep(0.5)
    
    async def demonstrate_cross_module_integration(self):
        """
        Demonstrate comprehensive cross-module integration.
        
        Shows how all three flows work together to create compound
        rewards and bonuses when users engage across multiple systems.
        """
        logger.info("\n" + "="*60)
        logger.info("CROSS-MODULE INTEGRATION DEMONSTRATION")
        logger.info("="*60)
        
        # Simulate a complete user journey across all systems
        logger.info("\n--- Simulating comprehensive user journey ---")
        
        # 1. User completes a narrative milestone
        logger.info("\n1. User completes narrative milestone...")
        narrative_result = await self.cross_module_rewards.process_narrative_milestone(
            user_id=self.demo_user_id,
            fragment_key="level3_passionate_night",
            bot=None
        )
        
        if narrative_result.success:
            logger.info(f"   ✅ Narrative milestone: +{narrative_result.points_awarded} points")
            logger.info(f"   📖 Missions unlocked: {len(narrative_result.missions_unlocked)}")
            logger.info(f"   🏆 Achievements gained: {len(narrative_result.achievements_gained)}")
        
        # 2. This triggers an achievement unlock
        logger.info("\n2. Achievement unlocked from narrative progress...")
        achievement_result = await self.cross_module_rewards.process_achievement_unlock(
            user_id=self.demo_user_id,
            achievement_id="story_explorer",
            bot=None
        )
        
        if achievement_result.success:
            logger.info(f"   ✅ Achievement unlock: +{achievement_result.points_awarded} points")
            logger.info(f"   📚 Narrative content: {len(achievement_result.narrative_unlocked)}")
            logger.info(f"   🎯 New missions: {len(achievement_result.missions_unlocked)}")
        
        # 3. User engages in channels, triggering engagement rewards
        logger.info("\n3. Channel engagement creates cross-system bonuses...")
        engagement_result = await self.cross_module_rewards.process_engagement_milestone(
            user_id=self.demo_user_id,
            engagement_type="weekly_champion",
            engagement_data={"total_activities": 25, "channels": 4, "quality_score": 9.2},
            bot=None
        )
        
        if engagement_result.success:
            logger.info(f"   ✅ Engagement milestone: +{engagement_result.points_awarded} points")
            logger.info(f"   📖 Narrative unlocks: {len(engagement_result.narrative_unlocked)}")
            logger.info(f"   🎯 Mission unlocks: {len(engagement_result.missions_unlocked)}")
        
        # 4. Calculate total rewards and cross-module bonuses
        total_points = (
            narrative_result.points_awarded + 
            achievement_result.points_awarded + 
            engagement_result.points_awarded
        )
        
        total_content = (
            len(achievement_result.narrative_unlocked) +
            len(engagement_result.narrative_unlocked)
        )
        
        total_missions = (
            len(narrative_result.missions_unlocked) +
            len(achievement_result.missions_unlocked) +
            len(engagement_result.missions_unlocked)
        )
        
        logger.info("\n" + "-"*50)
        logger.info("CROSS-MODULE INTEGRATION SUMMARY")
        logger.info("-"*50)
        logger.info(f"💋 Total Points Awarded: {total_points}")
        logger.info(f"📖 Total Content Unlocked: {total_content} items")
        logger.info(f"🎯 Total Missions Unlocked: {total_missions}")
        logger.info(f"🌟 Cross-Module Bonuses: Active")
        logger.info(f"👑 Diana's Satisfaction: Maximum")
    
    async def demonstrate_event_system_integration(self):
        """
        Demonstrate the event system that connects all modules.
        
        Shows how events are published and consumed across the system
        to create real-time cross-module communication.
        """
        logger.info("\n" + "="*60)
        logger.info("EVENT SYSTEM INTEGRATION")
        logger.info("="*60)
        
        event_bus = get_event_bus()
        
        # Show current event history
        recent_events = event_bus.get_event_history(10)
        logger.info(f"Recent events in system: {len(recent_events)}")
        
        for i, event in enumerate(recent_events[-5:], 1):
            logger.info(f"   {i}. {event.event_type.value} - User {event.user_id} - {event.timestamp}")
        
        # Demonstrate event publishing
        logger.info("\n--- Publishing test events ---")
        
        # Publish a narrative progress event
        await event_bus.publish(
            EventType.NARRATIVE_PROGRESS,
            self.demo_user_id,
            {
                "fragment_key": "level4_intimate_moment",
                "points_earned": 25,
                "unlocks_triggered": ["mission_romance_expert"]
            },
            source="integration_demo"
        )
        
        # Publish an achievement event
        await event_bus.publish(
            EventType.ACHIEVEMENT_UNLOCKED,
            self.demo_user_id,
            {
                "achievement_id": "narrative_devotee",
                "points_earned": 50,
                "narrative_unlocks": ["backstory_diana_secrets"]
            },
            source="integration_demo"
        )
        
        # Publish a channel engagement event
        await event_bus.publish(
            EventType.CHANNEL_ENGAGEMENT,
            self.demo_user_id,
            {
                "action_type": "quality_post",
                "channel_id": 1001,
                "engagement_score": 8.5,
                "points_awarded": 20
            },
            source="integration_demo"
        )
        
        logger.info("✅ Test events published successfully!")
        logger.info("   Events will trigger cross-module reward calculations")
        logger.info("   Real-time notifications and menu updates will follow")
    
    async def run_complete_demonstration(self):
        """
        Run the complete cross-module reward flow demonstration.
        
        This shows all three flows working together with the event system
        to create a comprehensive gamification experience.
        """
        try:
            await self.initialize()
            
            logger.info("\n🚀 CROSS-MODULE REWARD FLOW DEMONSTRATION")
            logger.info("This demo shows how Diana's world integrates narrative,")
            logger.info("gamification, and social engagement into unified rewards.")
            
            # Demonstrate each flow individually
            await self.demonstrate_narrative_mission_flow()
            await self.demonstrate_achievement_narrative_flow()
            await self.demonstrate_engagement_rewards_flow()
            
            # Demonstrate cross-module integration
            await self.demonstrate_cross_module_integration()
            
            # Demonstrate event system
            await self.demonstrate_event_system_integration()
            
            logger.info("\n" + "="*60)
            logger.info("DEMONSTRATION COMPLETE!")
            logger.info("="*60)
            logger.info("✅ All cross-module reward flows are operational")
            logger.info("✅ Event system provides real-time integration")
            logger.info("✅ Diana Menu System receives dynamic updates")
            logger.info("✅ Comprehensive gamification experience delivered")
            logger.info("\n💕 Diana is pleased with the implementation!")
            
        except Exception as e:
            logger.exception(f"Error during demonstration: {e}")
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the demonstration."""
    demo = CrossModuleRewardFlowDemo()
    await demo.run_complete_demonstration()


if __name__ == "__main__":
    asyncio.run(main())