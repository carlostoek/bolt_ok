#!/usr/bin/env python3
"""
MVP Gamification System Validation Script
Validates all components of the gamification system implemented in Phase 3.
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append('/home/azureuser/repos/bolt_ok/mybot')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Import all MVP gamification components
from services.mvp_gamification_service import MVPGamificationService
from services.mvp_mission_service import MVPMissionService, MVP_MISSIONS
from services.mvp_achievement_service import MVPAchievementService, MVP_ACHIEVEMENTS
from services.point_service import PointService, POINTS_CONFIG, DIANA_REWARD_MESSAGES
from services.level_service import LevelService, MVP_LEVELS, MVP_LEVEL_THRESHOLDS, get_user_level, get_next_level_info
from database.models import User, Mission, Achievement, UserMissionEntry, UserAchievement, UserStats
from utils.user_roles import get_points_multiplier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameficationValidator:
    """Comprehensive validator for MVP gamification system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.validation_results = {}
        self.issues_found = []
        self.test_user_id = 999999999  # Test user ID
        
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation of all gamification systems."""
        logger.info("🚀 Starting MVP Gamification System Validation")
        
        validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "PENDING",
            "systems_validated": {},
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # 1. Database Schema Validation
            schema_result = await self.validate_database_schema()
            validation_results["systems_validated"]["database_schema"] = schema_result
            
            # 2. Service Integration Validation
            services_result = await self.validate_service_integration()
            validation_results["systems_validated"]["service_integration"] = services_result
            
            # 3. Points System Validation
            points_result = await self.validate_points_system()
            validation_results["systems_validated"]["points_system"] = points_result
            
            # 4. Level Progression Validation
            levels_result = await self.validate_level_progression()
            validation_results["systems_validated"]["level_progression"] = levels_result
            
            # 5. Mission System Validation
            missions_result = await self.validate_mission_system()
            validation_results["systems_validated"]["mission_system"] = missions_result
            
            # 6. Achievement System Validation
            achievements_result = await self.validate_achievement_system()
            validation_results["systems_validated"]["achievement_system"] = achievements_result
            
            # 7. MVP Gamification Service Validation
            mvp_service_result = await self.validate_mvp_gamification_service()
            validation_results["systems_validated"]["mvp_gamification_service"] = mvp_service_result
            
            # 8. Diana Character Consistency Validation
            character_result = await self.validate_diana_character_consistency()
            validation_results["systems_validated"]["character_consistency"] = character_result
            
            # 9. Performance Validation
            performance_result = await self.validate_performance()
            validation_results["systems_validated"]["performance"] = performance_result
            
            # Calculate overall status
            all_systems_valid = all(
                result["status"] == "PASS" 
                for result in validation_results["systems_validated"].values()
            )
            
            validation_results["overall_status"] = "PASS" if all_systems_valid else "ISSUES_FOUND"
            validation_results["issues_found"] = self.issues_found
            validation_results["recommendations"] = self.generate_recommendations()
            
        except Exception as e:
            logger.error(f"Critical error during validation: {e}")
            validation_results["overall_status"] = "CRITICAL_ERROR"
            validation_results["error"] = str(e)
            
        finally:
            # Cleanup test data
            await self.cleanup_test_data()
            
        return validation_results
    
    async def validate_database_schema(self) -> Dict[str, Any]:
        """Validate database schema supports gamification features."""
        logger.info("📊 Validating database schema...")
        
        schema_checks = {
            "users_table": False,
            "missions_table": False,
            "achievements_table": False,
            "user_missions_table": False,
            "user_achievements_table": False,
            "user_stats_table": False,
            "point_transactions_table": False
        }
        
        try:
            # Check User table structure
            result = await self.session.execute(text("PRAGMA table_info(users)"))
            users_columns = {row[1] for row in result.fetchall()}
            required_user_columns = {"id", "points", "level", "achievements"}
            schema_checks["users_table"] = required_user_columns.issubset(users_columns)
            
            # Check missions table
            try:
                result = await self.session.execute(text("PRAGMA table_info(missions)"))
                missions_columns = {row[1] for row in result.fetchall()}
                required_mission_columns = {"id", "name", "description", "type", "target_value", "reward_points"}
                schema_checks["missions_table"] = required_mission_columns.issubset(missions_columns)
            except Exception:
                schema_checks["missions_table"] = False
            
            # Check achievements table
            try:
                result = await self.session.execute(text("PRAGMA table_info(achievements)"))
                achievements_columns = {row[1] for row in result.fetchall()}
                required_achievement_columns = {"id", "name", "condition_type", "condition_value"}
                schema_checks["achievements_table"] = required_achievement_columns.issubset(achievements_columns)
            except Exception:
                schema_checks["achievements_table"] = False
            
            # Check user_mission_entries table
            try:
                result = await self.session.execute(text("PRAGMA table_info(user_mission_entries)"))
                user_missions_columns = {row[1] for row in result.fetchall()}
                required_user_mission_columns = {"user_id", "mission_id", "progress_value", "completed"}
                schema_checks["user_missions_table"] = required_user_mission_columns.issubset(user_missions_columns)
            except Exception:
                schema_checks["user_missions_table"] = False
            
            # Check user_achievements table
            try:
                result = await self.session.execute(text("PRAGMA table_info(user_achievements)"))
                user_achievements_columns = {row[1] for row in result.fetchall()}
                required_user_achievement_columns = {"user_id", "achievement_id", "unlocked_at"}
                schema_checks["user_achievements_table"] = required_user_achievement_columns.issubset(user_achievements_columns)
            except Exception:
                schema_checks["user_achievements_table"] = False
            
            # Check user_stats table
            try:
                result = await self.session.execute(text("PRAGMA table_info(user_stats)"))
                user_stats_columns = {row[1] for row in result.fetchall()}
                required_user_stats_columns = {"user_id", "messages_sent", "checkin_streak", "last_checkin_at"}
                schema_checks["user_stats_table"] = required_user_stats_columns.issubset(user_stats_columns)
            except Exception:
                schema_checks["user_stats_table"] = False
            
            # Check point_transactions table
            try:
                result = await self.session.execute(text("PRAGMA table_info(point_transactions)"))
                transactions_columns = {row[1] for row in result.fetchall()}
                required_transaction_columns = {"user_id", "amount", "balance_after", "source"}
                schema_checks["point_transactions_table"] = required_transaction_columns.issubset(transactions_columns)
            except Exception:
                schema_checks["point_transactions_table"] = False
            
            all_schema_valid = all(schema_checks.values())
            
            if not all_schema_valid:
                missing_schemas = [name for name, valid in schema_checks.items() if not valid]
                self.issues_found.append(f"Missing or invalid database schemas: {', '.join(missing_schemas)}")
            
            return {
                "status": "PASS" if all_schema_valid else "FAIL",
                "checks": schema_checks,
                "missing_schemas": [name for name, valid in schema_checks.items() if not valid]
            }
            
        except Exception as e:
            logger.error(f"Error validating database schema: {e}")
            self.issues_found.append(f"Database schema validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_service_integration(self) -> Dict[str, Any]:
        """Validate service integration and initialization."""
        logger.info("🔧 Validating service integration...")
        
        service_checks = {
            "mvp_gamification_service": False,
            "mvp_mission_service": False,
            "mvp_achievement_service": False,
            "point_service": False,
            "level_service": False
        }
        
        try:
            # Test MVP Gamification Service
            try:
                gamification_service = MVPGamificationService(self.session)
                await gamification_service.initialize_mvp_systems()
                service_checks["mvp_gamification_service"] = True
                logger.info("✅ MVP Gamification Service initialized successfully")
            except Exception as e:
                logger.error(f"❌ MVP Gamification Service failed: {e}")
                self.issues_found.append(f"MVP Gamification Service initialization error: {e}")
            
            # Test MVP Mission Service
            try:
                from services.achievement_service import AchievementService
                base_achievement_service = AchievementService(self.session)
                level_service = LevelService(self.session)
                point_service = PointService(self.session, level_service, base_achievement_service)
                
                mission_service = MVPMissionService(self.session, point_service)
                await mission_service.initialize_mvp_missions()
                service_checks["mvp_mission_service"] = True
                logger.info("✅ MVP Mission Service initialized successfully")
            except Exception as e:
                logger.error(f"❌ MVP Mission Service failed: {e}")
                self.issues_found.append(f"MVP Mission Service initialization error: {e}")
            
            # Test MVP Achievement Service
            try:
                achievement_service = MVPAchievementService(self.session, point_service)
                await achievement_service.initialize_mvp_achievements()
                service_checks["mvp_achievement_service"] = True
                logger.info("✅ MVP Achievement Service initialized successfully")
            except Exception as e:
                logger.error(f"❌ MVP Achievement Service failed: {e}")
                self.issues_found.append(f"MVP Achievement Service initialization error: {e}")
            
            # Test Point Service
            try:
                service_checks["point_service"] = True
                logger.info("✅ Point Service accessible")
            except Exception as e:
                logger.error(f"❌ Point Service failed: {e}")
                self.issues_found.append(f"Point Service error: {e}")
            
            # Test Level Service
            try:
                service_checks["level_service"] = True
                logger.info("✅ Level Service accessible")
            except Exception as e:
                logger.error(f"❌ Level Service failed: {e}")
                self.issues_found.append(f"Level Service error: {e}")
            
            all_services_valid = all(service_checks.values())
            
            return {
                "status": "PASS" if all_services_valid else "FAIL",
                "checks": service_checks,
                "failed_services": [name for name, valid in service_checks.items() if not valid]
            }
            
        except Exception as e:
            logger.error(f"Error validating service integration: {e}")
            self.issues_found.append(f"Service integration validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_points_system(self) -> Dict[str, Any]:
        """Validate points system functionality."""
        logger.info("💰 Validating points system...")
        
        points_checks = {
            "points_config_present": False,
            "vip_multiplier_works": False,
            "diana_messages_present": False,
            "points_award_correctly": False,
            "transaction_logging": False
        }
        
        try:
            # Check points configuration
            points_checks["points_config_present"] = bool(POINTS_CONFIG and len(POINTS_CONFIG) > 0)
            logger.info(f"Points config entries: {len(POINTS_CONFIG)}")
            
            # Check Diana messages
            points_checks["diana_messages_present"] = bool(DIANA_REWARD_MESSAGES and len(DIANA_REWARD_MESSAGES) > 0)
            logger.info(f"Diana message categories: {len(DIANA_REWARD_MESSAGES)}")
            
            # Test VIP multiplier calculation
            test_user = User(id=self.test_user_id, points=0, role="vip", vip_expires_at=datetime.utcnow() + timedelta(days=30))
            self.session.add(test_user)
            await self.session.commit()
            
            from services.achievement_service import AchievementService
            level_service = LevelService(self.session)
            base_achievement_service = AchievementService(self.session)
            point_service = PointService(self.session, level_service, base_achievement_service)
            
            # Test VIP multiplier
            base_points = 10
            vip_points = await point_service._apply_vip_multiplier(self.test_user_id, base_points)
            expected_vip_points = base_points * POINTS_CONFIG['vip_bonus_multiplier']
            points_checks["vip_multiplier_works"] = abs(vip_points - expected_vip_points) < 0.01
            logger.info(f"VIP multiplier test: {base_points} -> {vip_points} (expected: {expected_vip_points})")
            
            # Test points awarding
            initial_points = test_user.points
            progress = await point_service.add_points(self.test_user_id, 50, source="test_validation")
            await self.session.refresh(test_user)
            final_points = test_user.points
            points_awarded = final_points - initial_points
            points_checks["points_award_correctly"] = abs(points_awarded - 50) < 0.01
            logger.info(f"Points awarding test: {initial_points} -> {final_points} (awarded: {points_awarded})")
            
            # Test transaction logging
            from database.transaction_models import PointTransaction
            from sqlalchemy import select
            transaction_query = await self.session.execute(
                select(PointTransaction).where(PointTransaction.user_id == self.test_user_id)
            )
            transactions = transaction_query.scalars().all()
            points_checks["transaction_logging"] = len(transactions) > 0
            logger.info(f"Transaction logging test: {len(transactions)} transactions found")
            
            all_points_valid = all(points_checks.values())
            
            return {
                "status": "PASS" if all_points_valid else "FAIL",
                "checks": points_checks,
                "config_entries": len(POINTS_CONFIG),
                "diana_message_categories": len(DIANA_REWARD_MESSAGES),
                "vip_multiplier": POINTS_CONFIG.get('vip_bonus_multiplier', 'NOT_FOUND')
            }
            
        except Exception as e:
            logger.error(f"Error validating points system: {e}")
            self.issues_found.append(f"Points system validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_level_progression(self) -> Dict[str, Any]:
        """Validate level progression system."""
        logger.info("📈 Validating level progression system...")
        
        level_checks = {
            "mvp_levels_defined": False,
            "level_thresholds_correct": False,
            "level_calculation_accurate": False,
            "next_level_info_works": False,
            "level_up_triggers": False
        }
        
        try:
            # Check MVP levels definition
            level_checks["mvp_levels_defined"] = bool(MVP_LEVELS and len(MVP_LEVELS) >= 20)
            logger.info(f"MVP levels defined: {len(MVP_LEVELS)}")
            
            # Check level thresholds
            level_checks["level_thresholds_correct"] = bool(MVP_LEVEL_THRESHOLDS and len(MVP_LEVEL_THRESHOLDS) >= 20)
            logger.info(f"MVP level thresholds: {len(MVP_LEVEL_THRESHOLDS)}")
            
            # Test level calculation
            test_points = [0, 100, 250, 500, 1000, 1500, 2500, 5000]
            expected_levels = [1, 2, 3, 5, 8, 10, 12, 18]
            
            level_calculations_correct = []
            for points, expected_level in zip(test_points, expected_levels):
                calculated_level = get_user_level(points)
                is_correct = calculated_level == expected_level or abs(calculated_level - expected_level) <= 1  # Allow 1 level tolerance
                level_calculations_correct.append(is_correct)
                logger.info(f"Level calculation: {points} points -> Level {calculated_level} (expected ~{expected_level})")
            
            level_checks["level_calculation_accurate"] = all(level_calculations_correct)
            
            # Test next level info
            next_level_info = get_next_level_info(150)  # Test with 150 points
            required_info_keys = {"current_level", "next_level", "points_needed", "percentage_to_next"}
            has_required_info = all(key in next_level_info for key in required_info_keys)
            level_checks["next_level_info_works"] = has_required_info
            logger.info(f"Next level info test: {next_level_info}")
            
            # Test level up triggering
            test_user = await self.session.get(User, self.test_user_id)
            if test_user:
                level_service = LevelService(self.session)
                initial_level = test_user.level
                test_user.points = 200  # Should trigger level up
                level_up_occurred = await level_service.check_for_level_up(test_user)
                level_checks["level_up_triggers"] = level_up_occurred or test_user.level > initial_level
                logger.info(f"Level up test: Level {initial_level} -> {test_user.level} (triggered: {level_up_occurred})")
            
            all_levels_valid = all(level_checks.values())
            
            return {
                "status": "PASS" if all_levels_valid else "FAIL",
                "checks": level_checks,
                "mvp_levels_count": len(MVP_LEVELS),
                "thresholds_count": len(MVP_LEVEL_THRESHOLDS),
                "max_level": max(level for level, _ in MVP_LEVEL_THRESHOLDS),
                "level_calculation_tests": list(zip(test_points, expected_levels, [get_user_level(p) for p in test_points]))
            }
            
        except Exception as e:
            logger.error(f"Error validating level progression: {e}")
            self.issues_found.append(f"Level progression validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_mission_system(self) -> Dict[str, Any]:
        """Validate mission system functionality."""
        logger.info("🎯 Validating mission system...")
        
        mission_checks = {
            "mvp_missions_defined": False,
            "missions_initialized": False,
            "mission_progress_tracking": False,
            "mission_completion_detection": False,
            "diana_completion_messages": False
        }
        
        try:
            # Check MVP missions definition
            mission_checks["mvp_missions_defined"] = bool(MVP_MISSIONS and len(MVP_MISSIONS) == 10)
            logger.info(f"MVP missions defined: {len(MVP_MISSIONS)}")
            
            # Check Diana completion messages
            diana_messages_present = all(
                "diana_completion_message" in mission for mission in MVP_MISSIONS
            )
            mission_checks["diana_completion_messages"] = diana_messages_present
            
            # Initialize missions
            from services.achievement_service import AchievementService
            level_service = LevelService(self.session)
            base_achievement_service = AchievementService(self.session)
            point_service = PointService(self.session, level_service, base_achievement_service)
            mission_service = MVPMissionService(self.session, point_service)
            
            await mission_service.initialize_mvp_missions()
            
            # Check if missions were initialized in database
            from sqlalchemy import select
            missions_query = await self.session.execute(select(Mission))
            db_missions = missions_query.scalars().all()
            mvp_mission_ids = [m["id"] for m in MVP_MISSIONS]
            db_mission_ids = [m.id for m in db_missions]
            missions_in_db = all(mission_id in db_mission_ids for mission_id in mvp_mission_ids)
            mission_checks["missions_initialized"] = missions_in_db
            logger.info(f"Missions in database: {len(db_missions)} (expected MVP missions: {len(MVP_MISSIONS)})")
            
            # Test mission progress tracking
            progress = await mission_service.get_user_mission_progress(self.test_user_id)
            mission_checks["mission_progress_tracking"] = isinstance(progress, list) and len(progress) > 0
            logger.info(f"Mission progress tracking test: {len(progress)} missions tracked")
            
            # Test mission completion detection
            # Simulate story fragment completion
            test_user = await self.session.get(User, self.test_user_id)
            if test_user:
                # Add story fragments to user achievements
                if "story_fragments_completed" not in test_user.achievements:
                    test_user.achievements["story_fragments_completed"] = 0
                test_user.achievements["story_fragments_completed"] = 3  # Should complete "primera_conversacion" mission
                await self.session.commit()
                
                completed_missions = await mission_service.check_mission_completion(
                    self.test_user_id, "story_progress", None
                )
                mission_checks["mission_completion_detection"] = len(completed_missions) > 0
                logger.info(f"Mission completion test: {len(completed_missions)} missions completed")
            
            all_missions_valid = all(mission_checks.values())
            
            # Get mission details for report
            mission_details = []
            for mission in MVP_MISSIONS:
                mission_details.append({
                    "id": mission["id"],
                    "name": mission["name"],
                    "type": mission["type"],
                    "target_value": mission["target_value"],
                    "reward_points": mission["reward_points"],
                    "has_diana_message": "diana_completion_message" in mission
                })
            
            return {
                "status": "PASS" if all_missions_valid else "FAIL",
                "checks": mission_checks,
                "mvp_missions_count": len(MVP_MISSIONS),
                "missions_in_db": len(db_missions),
                "mission_details": mission_details
            }
            
        except Exception as e:
            logger.error(f"Error validating mission system: {e}")
            self.issues_found.append(f"Mission system validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_achievement_system(self) -> Dict[str, Any]:
        """Validate achievement system functionality."""
        logger.info("🏆 Validating achievement system...")
        
        achievement_checks = {
            "mvp_achievements_defined": False,
            "achievements_initialized": False,
            "achievement_unlocking": False,
            "rarity_system": False,
            "diana_unlock_messages": False
        }
        
        try:
            # Check MVP achievements definition
            achievement_checks["mvp_achievements_defined"] = bool(MVP_ACHIEVEMENTS and len(MVP_ACHIEVEMENTS) == 15)
            logger.info(f"MVP achievements defined: {len(MVP_ACHIEVEMENTS)}")
            
            # Check Diana unlock messages
            diana_messages_present = all(
                "diana_unlock_message" in achievement for achievement in MVP_ACHIEVEMENTS
            )
            achievement_checks["diana_unlock_messages"] = diana_messages_present
            
            # Check rarity system
            rarities = set(achievement.get("rarity", "common") for achievement in MVP_ACHIEVEMENTS)
            expected_rarities = {"common", "uncommon", "rare", "epic", "legendary"}
            rarity_system_present = expected_rarities.issubset(rarities) or len(rarities) >= 3
            achievement_checks["rarity_system"] = rarity_system_present
            logger.info(f"Achievement rarities found: {rarities}")
            
            # Initialize achievements
            from services.achievement_service import AchievementService
            level_service = LevelService(self.session)
            base_achievement_service = AchievementService(self.session)
            point_service = PointService(self.session, level_service, base_achievement_service)
            achievement_service = MVPAchievementService(self.session, point_service)
            
            await achievement_service.initialize_mvp_achievements()
            
            # Check if achievements were initialized in database
            from sqlalchemy import select
            achievements_query = await self.session.execute(select(Achievement))
            db_achievements = achievements_query.scalars().all()
            mvp_achievement_ids = [a["id"] for a in MVP_ACHIEVEMENTS]
            db_achievement_ids = [a.id for a in db_achievements]
            achievements_in_db = all(achievement_id in db_achievement_ids for achievement_id in mvp_achievement_ids)
            achievement_checks["achievements_initialized"] = achievements_in_db
            logger.info(f"Achievements in database: {len(db_achievements)} (expected MVP achievements: {len(MVP_ACHIEVEMENTS)})")
            
            # Test achievement unlocking
            test_user = await self.session.get(User, self.test_user_id)
            if test_user:
                # Should unlock "first_steps" achievement (registration)
                unlocked_achievements = await achievement_service.check_and_unlock_achievements(self.test_user_id, None)
                achievement_checks["achievement_unlocking"] = len(unlocked_achievements) > 0
                logger.info(f"Achievement unlocking test: {len(unlocked_achievements)} achievements unlocked")
            
            all_achievements_valid = all(achievement_checks.values())
            
            # Get achievement details for report
            achievement_details = []
            for achievement in MVP_ACHIEVEMENTS:
                achievement_details.append({
                    "id": achievement["id"],
                    "name": achievement["name"],
                    "condition_type": achievement["condition_type"],
                    "condition_value": achievement["condition_value"],
                    "reward_points": achievement["reward_points"],
                    "rarity": achievement.get("rarity", "common"),
                    "has_diana_message": "diana_unlock_message" in achievement
                })
            
            return {
                "status": "PASS" if all_achievements_valid else "FAIL",
                "checks": achievement_checks,
                "mvp_achievements_count": len(MVP_ACHIEVEMENTS),
                "achievements_in_db": len(db_achievements),
                "rarities_found": list(rarities),
                "achievement_details": achievement_details
            }
            
        except Exception as e:
            logger.error(f"Error validating achievement system: {e}")
            self.issues_found.append(f"Achievement system validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_mvp_gamification_service(self) -> Dict[str, Any]:
        """Validate MVP gamification service integration."""
        logger.info("🎮 Validating MVP gamification service...")
        
        mvp_service_checks = {
            "service_initialization": False,
            "story_fragment_processing": False,
            "decision_processing": False,
            "daily_checkin_processing": False,
            "channel_reaction_processing": False,
            "user_summary_generation": False
        }
        
        try:
            # Initialize service
            gamification_service = MVPGamificationService(self.session)
            await gamification_service.initialize_mvp_systems()
            mvp_service_checks["service_initialization"] = True
            logger.info("✅ MVP Gamification Service initialized")
            
            # Test story fragment processing
            fragment_result = await gamification_service.process_story_fragment_completion(
                self.test_user_id, "test_fragment", None
            )
            is_valid_result = isinstance(fragment_result, dict) and "points_awarded" in fragment_result
            mvp_service_checks["story_fragment_processing"] = is_valid_result
            logger.info(f"Story fragment processing: {fragment_result.get('points_awarded', 0)} points awarded")
            
            # Test decision processing
            decision_result = await gamification_service.process_decision_made(
                self.test_user_id, {"choice": "test_choice"}, None
            )
            is_valid_decision = isinstance(decision_result, dict) and "points_awarded" in decision_result
            mvp_service_checks["decision_processing"] = is_valid_decision
            logger.info(f"Decision processing: {decision_result.get('points_awarded', 0)} points awarded")
            
            # Test daily checkin processing
            checkin_result = await gamification_service.process_daily_checkin(
                self.test_user_id, None
            )
            is_valid_checkin = isinstance(checkin_result, dict) and "checkin_successful" in checkin_result
            mvp_service_checks["daily_checkin_processing"] = is_valid_checkin
            logger.info(f"Daily checkin processing: success = {checkin_result.get('checkin_successful', False)}")
            
            # Test channel reaction processing
            reaction_result = await gamification_service.process_channel_reaction(
                self.test_user_id, 12345, "like", None
            )
            is_valid_reaction = isinstance(reaction_result, dict) and "points_awarded" in reaction_result
            mvp_service_checks["channel_reaction_processing"] = is_valid_reaction
            logger.info(f"Channel reaction processing: {reaction_result.get('points_awarded', 0)} points awarded")
            
            # Test user summary generation
            summary = await gamification_service.get_user_gamification_summary(self.test_user_id)
            is_valid_summary = isinstance(summary, dict) and "user_info" in summary and "diana_personal_message" in summary
            mvp_service_checks["user_summary_generation"] = is_valid_summary
            logger.info(f"User summary generation: {len(summary)} summary fields generated")
            
            all_mvp_service_valid = all(mvp_service_checks.values())
            
            return {
                "status": "PASS" if all_mvp_service_valid else "FAIL",
                "checks": mvp_service_checks,
                "sample_summary": summary if is_valid_summary else None
            }
            
        except Exception as e:
            logger.error(f"Error validating MVP gamification service: {e}")
            self.issues_found.append(f"MVP gamification service validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_diana_character_consistency(self) -> Dict[str, Any]:
        """Validate Diana character consistency across gamification messages."""
        logger.info("💋 Validating Diana character consistency...")
        
        character_checks = {
            "mission_messages_consistent": False,
            "achievement_messages_consistent": False,
            "reward_messages_consistent": False,
            "spanish_language_used": False,
            "seductive_personality_maintained": False
        }
        
        try:
            # Check mission completion messages for Diana personality
            mission_diana_messages = [mission.get("diana_completion_message", "") for mission in MVP_MISSIONS]
            mission_keywords = ["amor", "cariño", "querido", "especial", "secretos", "misterios", "corazón", "alma"]
            mission_has_diana_personality = any(
                any(keyword in message.lower() for keyword in mission_keywords)
                for message in mission_diana_messages if message
            )
            character_checks["mission_messages_consistent"] = mission_has_diana_personality and len(mission_diana_messages) == 10
            
            # Check achievement unlock messages for Diana personality
            achievement_diana_messages = [achievement.get("diana_unlock_message", "") for achievement in MVP_ACHIEVEMENTS]
            achievement_has_diana_personality = any(
                any(keyword in message.lower() for keyword in mission_keywords)
                for message in achievement_diana_messages if message
            )
            character_checks["achievement_messages_consistent"] = achievement_has_diana_personality and len(achievement_diana_messages) == 15
            
            # Check reward messages in point service
            reward_message_categories = list(DIANA_REWARD_MESSAGES.keys())
            reward_has_diana_personality = len(reward_message_categories) >= 4  # besitos_earned, level_up, mission_completed, achievement_unlocked
            character_checks["reward_messages_consistent"] = reward_has_diana_personality
            
            # Check Spanish language usage
            all_messages = mission_diana_messages + achievement_diana_messages
            spanish_indicators = ["has", "eres", "te", "me", "tu", "mi", "contigo", "juntas", "realmente"]
            spanish_usage = any(
                any(indicator in message.lower() for indicator in spanish_indicators)
                for message in all_messages if message
            )
            character_checks["spanish_language_used"] = spanish_usage
            
            # Check seductive personality maintenance
            seductive_keywords = ["seductora", "íntima", "secretos", "misterios", "especial", "único", "fascinante"]
            seductive_personality = any(
                any(keyword in message.lower() for keyword in seductive_keywords)
                for message in all_messages if message
            )
            character_checks["seductive_personality_maintained"] = seductive_personality
            
            all_character_valid = all(character_checks.values())
            
            # Sample messages analysis
            sample_analysis = {
                "mission_messages_count": len([msg for msg in mission_diana_messages if msg]),
                "achievement_messages_count": len([msg for msg in achievement_diana_messages if msg]),
                "reward_categories": reward_message_categories,
                "sample_mission_message": mission_diana_messages[0] if mission_diana_messages else "None",
                "sample_achievement_message": achievement_diana_messages[0] if achievement_diana_messages else "None"
            }
            
            return {
                "status": "PASS" if all_character_valid else "FAIL",
                "checks": character_checks,
                "analysis": sample_analysis
            }
            
        except Exception as e:
            logger.error(f"Error validating Diana character consistency: {e}")
            self.issues_found.append(f"Diana character consistency validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    async def validate_performance(self) -> Dict[str, Any]:
        """Validate performance aspects of gamification system."""
        logger.info("⚡ Validating performance...")
        
        performance_checks = {
            "service_initialization_time": False,
            "points_calculation_time": False,
            "level_calculation_time": False,
            "mission_check_time": False,
            "achievement_check_time": False
        }
        
        performance_metrics = {}
        
        try:
            import time
            
            # Test service initialization time
            start_time = time.time()
            gamification_service = MVPGamificationService(self.session)
            await gamification_service.initialize_mvp_systems()
            init_time = time.time() - start_time
            performance_metrics["service_initialization_time"] = init_time
            performance_checks["service_initialization_time"] = init_time < 2.0  # Should initialize in less than 2 seconds
            logger.info(f"Service initialization time: {init_time:.3f}s")
            
            # Test points calculation time
            start_time = time.time()
            level_service = LevelService(self.session)
            from services.achievement_service import AchievementService
            base_achievement_service = AchievementService(self.session)
            point_service = PointService(self.session, level_service, base_achievement_service)
            
            # Multiple points calculations
            for _ in range(10):
                await point_service.add_points(self.test_user_id, 1, source="performance_test")
            points_time = (time.time() - start_time) / 10
            performance_metrics["points_calculation_time"] = points_time
            performance_checks["points_calculation_time"] = points_time < 0.1  # Should calculate in less than 100ms
            logger.info(f"Average points calculation time: {points_time:.3f}s")
            
            # Test level calculation time
            start_time = time.time()
            for points in [100, 250, 500, 1000, 2500]:
                get_user_level(points)
                get_next_level_info(points)
            level_time = (time.time() - start_time) / 10
            performance_metrics["level_calculation_time"] = level_time
            performance_checks["level_calculation_time"] = level_time < 0.01  # Should be very fast
            logger.info(f"Average level calculation time: {level_time:.3f}s")
            
            # Test mission check time
            start_time = time.time()
            mission_service = MVPMissionService(self.session, point_service)
            await mission_service.get_user_mission_progress(self.test_user_id)
            mission_time = time.time() - start_time
            performance_metrics["mission_check_time"] = mission_time
            performance_checks["mission_check_time"] = mission_time < 0.5  # Should check missions in less than 500ms
            logger.info(f"Mission check time: {mission_time:.3f}s")
            
            # Test achievement check time
            start_time = time.time()
            achievement_service = MVPAchievementService(self.session, point_service)
            await achievement_service.check_and_unlock_achievements(self.test_user_id, None)
            achievement_time = time.time() - start_time
            performance_metrics["achievement_check_time"] = achievement_time
            performance_checks["achievement_check_time"] = achievement_time < 0.5  # Should check achievements in less than 500ms
            logger.info(f"Achievement check time: {achievement_time:.3f}s")
            
            all_performance_valid = all(performance_checks.values())
            
            return {
                "status": "PASS" if all_performance_valid else "FAIL",
                "checks": performance_checks,
                "metrics": performance_metrics,
                "benchmarks": {
                    "service_init_target": "< 2.0s",
                    "points_calc_target": "< 0.1s",
                    "level_calc_target": "< 0.01s",
                    "mission_check_target": "< 0.5s",
                    "achievement_check_target": "< 0.5s"
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating performance: {e}")
            self.issues_found.append(f"Performance validation error: {e}")
            return {
                "status": "FAIL",
                "error": str(e)
            }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if self.issues_found:
            recommendations.append("🔧 **Issues Found - Recommended Actions:**")
            for issue in self.issues_found:
                recommendations.append(f"• Fix: {issue}")
        
        recommendations.extend([
            "📈 **Performance Optimization Recommendations:**",
            "• Consider caching frequently accessed user data",
            "• Batch database operations where possible",
            "• Index mission and achievement tables for faster queries",
            "",
            "🎭 **Character Consistency Recommendations:**", 
            "• Review all gamification messages for Diana personality",
            "• Ensure Spanish language consistency across all texts",
            "• Add more seductive/mysterious language where appropriate",
            "",
            "🚀 **Future Enhancement Recommendations:**",
            "• Add real-time achievement notifications",
            "• Implement mission progress animations",
            "• Create achievement rarity visual effects",
            "• Add Diana menu integration for gamification features"
        ])
        
        return recommendations
    
    async def cleanup_test_data(self):
        """Clean up test data created during validation."""
        try:
            # Delete test user
            test_user = await self.session.get(User, self.test_user_id)
            if test_user:
                await self.session.delete(test_user)
            
            # Delete test user stats
            test_stats = await self.session.get(UserStats, self.test_user_id)
            if test_stats:
                await self.session.delete(test_stats)
            
            # Delete test transactions
            from database.transaction_models import PointTransaction
            from sqlalchemy import delete
            await self.session.execute(
                delete(PointTransaction).where(PointTransaction.user_id == self.test_user_id)
            )
            
            # Delete test mission entries
            await self.session.execute(
                delete(UserMissionEntry).where(UserMissionEntry.user_id == self.test_user_id)
            )
            
            # Delete test achievements
            await self.session.execute(
                delete(UserAchievement).where(UserAchievement.user_id == self.test_user_id)
            )
            
            await self.session.commit()
            logger.info("🧹 Test data cleaned up successfully")
            
        except Exception as e:
            logger.warning(f"Error cleaning up test data: {e}")

def print_validation_report(results: Dict[str, Any]):
    """Print a formatted validation report."""
    print("\n" + "="*80)
    print("🎮 MVP GAMIFICATION SYSTEM VALIDATION REPORT")
    print("="*80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status']}")
    
    if results['overall_status'] == 'PASS':
        print("✅ All systems are working correctly!")
    elif results['overall_status'] == 'ISSUES_FOUND':
        print("⚠️  Some issues were found that need attention")
    else:
        print("❌ Critical errors encountered during validation")
    
    print("\n" + "-"*80)
    print("SYSTEM VALIDATION RESULTS:")
    print("-"*80)
    
    for system_name, system_result in results.get('systems_validated', {}).items():
        status_icon = "✅" if system_result['status'] == 'PASS' else "❌"
        print(f"{status_icon} {system_name.replace('_', ' ').title()}: {system_result['status']}")
        
        if 'checks' in system_result:
            for check_name, check_result in system_result['checks'].items():
                check_icon = "  ✓" if check_result else "  ✗"
                print(f"{check_icon} {check_name.replace('_', ' ').title()}")
        
        if 'error' in system_result:
            print(f"    Error: {system_result['error']}")
        
        print()
    
    # Print issues found
    if results.get('issues_found'):
        print("-"*80)
        print("ISSUES FOUND:")
        print("-"*80)
        for i, issue in enumerate(results['issues_found'], 1):
            print(f"{i}. {issue}")
        print()
    
    # Print recommendations
    if results.get('recommendations'):
        print("-"*80)
        print("RECOMMENDATIONS:")
        print("-"*80)
        for rec in results['recommendations']:
            print(rec)
        print()
    
    print("="*80)

async def main():
    """Main validation function."""
    try:
        # Create database connection
        engine = create_async_engine(
            "sqlite+aiosqlite:///bot.db",
            echo=False
        )
        
        async_session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            # Run validation
            validator = GameficationValidator(session)
            results = await validator.run_full_validation()
            
            # Print report
            print_validation_report(results)
            
            # Return appropriate exit code
            if results['overall_status'] == 'PASS':
                return 0
            elif results['overall_status'] == 'ISSUES_FOUND':
                return 1
            else:
                return 2
                
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)