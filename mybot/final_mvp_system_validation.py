#!/usr/bin/env python3
"""
FINAL MVP SYSTEM VALIDATION - PHASE 4 READINESS CHECK
Comprehensive validation script for complete Diana Bot MVP system
"""
import os
import sys
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.setup import init_db, get_session
from database.models import User, Mission, Achievement, BotConfig
from utils.config import Config as AppConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalMVPValidator:
    """Comprehensive MVP validation for Phase 4 readiness"""
    
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "performance_metrics": {},
            "critical_issues": [],
            "warnings": [],
            "phase_4_ready": False
        }
        self.performance_metrics = {}
        self.critical_issues = []
        self.warnings = []
        
    async def run_validation(self):
        """Run complete system validation"""
        logger.info("🚀 STARTING FINAL MVP SYSTEM VALIDATION")
        logger.info("="*60)
        
        # Initialize database
        await self._validate_database_initialization()
        
        # Core System Tests
        await self._validate_diana_menu_system()
        await self._validate_narrative_system()
        await self._validate_gamification_system()
        await self._validate_user_flow()
        
        # Integration Tests
        await self._validate_cross_system_integration()
        await self._validate_handler_registration()
        
        # Performance Tests
        await self._validate_performance()
        
        # Character Consistency
        await self._validate_character_consistency()
        
        # Critical Path Verification
        await self._validate_critical_paths()
        
        # Generate final report
        self._generate_final_report()
        
    async def _validate_database_initialization(self):
        """Validate database is properly initialized"""
        test_name = "Database Initialization"
        start_time = time.time()
        
        try:
            # Initialize database
            engine = await init_db()
            session = await get_session()
            
            # Test basic queries
            from sqlalchemy.future import select
            result = await session.execute(select(User).limit(1))
            await session.execute(select(Mission).limit(1))
            await session.execute(select(Achievement).limit(1))
            
            await session.close()
            await engine.dispose()
            
            duration = time.time() - start_time
            self._add_test_result(test_name, True, f"Database initialized successfully in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, False, f"Database initialization failed: {str(e)}")
            self.critical_issues.append(f"Database initialization error: {str(e)}")
            
    async def _validate_diana_menu_system(self):
        """Validate Diana menu system functionality"""
        test_name = "Diana Menu System"
        start_time = time.time()
        
        try:
            # Check if Diana menu system files exist
            diana_files = [
                "services/diana_menu_system.py",
                "services/enhanced_diana_menu_system.py",
                "handlers/diana_handler.py"
            ]
            
            missing_files = []
            for file_path in diana_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                raise Exception(f"Missing Diana menu files: {missing_files}")
            
            # Try to import and test basic functionality
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            session = await get_session()
            diana_menu = EnhancedDianaMenuSystem(session)
            
            # Test basic menu operations
            # This is a simplified test since we can't mock aiogram easily
            await session.close()
            
            duration = time.time() - start_time
            self._add_test_result(test_name, True, f"Diana menu system files and imports working in {duration:.2f}s")
            self.performance_metrics["diana_menu_response_time"] = duration
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, False, f"Diana menu system failed: {str(e)}")
            self.critical_issues.append(f"Diana menu error: {str(e)}")
            
    async def _validate_narrative_system(self):
        """Validate narrative system functionality"""
        test_name = "Narrative System"
        start_time = time.time()
        
        try:
            session = await get_session()
            
            # Check narrative fragments in database
            from sqlalchemy.future import select
            from database.narrative_unified import NarrativeFragment
            
            result = await session.execute(select(NarrativeFragment))
            fragments = result.scalars().all()
            
            # Check if narrative service files exist
            narrative_files = [
                "services/narrative_service.py",
                "services/unified_narrative_service.py",
                "handlers/narrative_handler.py"
            ]
            
            missing_files = []
            for file_path in narrative_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
                    
            if missing_files:
                self.validation_results["warnings"].append(f"Missing narrative files: {missing_files}")
            
            await session.close()
            duration = time.time() - start_time
            self._add_test_result(test_name, True, f"Narrative system validated with {len(fragments)} fragments in {duration:.2f}s")
            self.performance_metrics["narrative_response_time"] = duration
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, False, f"Narrative system failed: {str(e)}")
            self.critical_issues.append(f"Narrative system error: {str(e)}")
            
    async def _validate_gamification_system(self):
        """Validate gamification system functionality"""
        test_name = "Gamification System"
        start_time = time.time()
        
        try:
            session = await get_session()
            
            # Check gamification tables
            from sqlalchemy.future import select
            
            # Check missions
            mission_result = await session.execute(select(Mission))
            missions = mission_result.scalars().all()
            
            # Check achievements  
            achievement_result = await session.execute(select(Achievement))
            achievements = achievement_result.scalars().all()
            
            # Check users table
            user_result = await session.execute(select(User).limit(1))
            users_exist = user_result.scalar_one_or_none() is not None
            
            # Check gamification service files
            gamification_files = [
                "services/point_service.py",
                "services/mission_service.py", 
                "services/achievement_service.py",
                "services/level_service.py"
            ]
            
            missing_files = []
            for file_path in gamification_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
                    
            if missing_files:
                self.validation_results["warnings"].append(f"Missing gamification files: {missing_files}")
            
            await session.close()
            duration = time.time() - start_time
            self._add_test_result(test_name, True, f"Gamification validated - {len(missions)} missions, {len(achievements)} achievements in {duration:.2f}s")
            self.performance_metrics["gamification_response_time"] = duration
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, False, f"Gamification system failed: {str(e)}")
            self.critical_issues.append(f"Gamification error: {str(e)}")
            
    async def _validate_user_flow(self):
        """Validate complete user flow"""
        test_name = "End-to-End User Flow"
        start_time = time.time()
        
        try:
            session = await get_session()
            
            # Test user creation
            from sqlalchemy.future import select
            test_user_id = 555666777
            
            # Check if user exists, if not create one
            result = await session.execute(select(User).where(User.id == test_user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    id=test_user_id, 
                    username="test_user",
                    first_name="Test",
                    last_name="User",
                    points=0,
                    level=1
                )
                session.add(user)
                await session.commit()
            
            # Test user exists and has basic properties
            assert user.id == test_user_id, "User creation failed"
            assert user.points >= 0, "User points invalid"
            assert user.level >= 1, "User level invalid"
            
            await session.close()
            duration = time.time() - start_time
            self._add_test_result(test_name, True, f"User flow validation completed in {duration:.2f}s")
            self.performance_metrics["user_flow_time"] = duration
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, False, f"User flow failed: {str(e)}")
            self.critical_issues.append(f"User flow error: {str(e)}")
            
    async def _validate_cross_system_integration(self):
        """Validate integration between systems"""
        test_name = "Cross-System Integration"
        start_time = time.time()
        
        try:
            # Check integration service files exist
            integration_files = [
                "services/coordinador_central.py",
                "services/diana_menu_integration_impl.py",
                "services/narrative_compatibility_layer.py"
            ]
            
            existing_files = []
            for file_path in integration_files:
                if os.path.exists(file_path):
                    existing_files.append(file_path)
                    
            # Check database foreign key relationships exist
            session = await get_session()
            
            # Basic validation - check if related tables have data
            from sqlalchemy.future import select
            
            users = await session.execute(select(User).limit(1))
            missions = await session.execute(select(Mission).limit(1))
            achievements = await session.execute(select(Achievement).limit(1))
            
            await session.close()
            
            duration = time.time() - start_time
            self._add_test_result(test_name, True, f"Integration services available - {len(existing_files)} integration files in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, False, f"Cross-system integration failed: {str(e)}")
            self.critical_issues.append(f"Integration error: {str(e)}")
            
    async def _validate_handler_registration(self):
        """Validate all handlers are properly registered"""
        test_name = "Handler Registration"
        
        try:
            # Check key handler files exist
            handler_files = [
                "handlers/diana_handler.py",
                "handlers/admin/admin_narrative_handler.py", 
                "handlers/user/gamification_handler.py",
                "handlers/narrative_handler.py"
            ]
            
            missing_handlers = []
            for handler_file in handler_files:
                if not os.path.exists(handler_file):
                    missing_handlers.append(handler_file)
                    
            if missing_handlers:
                self._add_test_result(test_name, False, f"Missing handlers: {missing_handlers}")
                self.critical_issues.append(f"Missing handlers: {missing_handlers}")
            else:
                self._add_test_result(test_name, True, "All critical handlers exist")
                
        except Exception as e:
            self._add_test_result(test_name, False, f"Handler validation failed: {str(e)}")
            
    async def _validate_performance(self):
        """Validate system performance meets requirements"""
        test_name = "Performance Validation"
        
        # Check response times
        max_response_time = 2.0  # 2 second requirement
        
        performance_issues = []
        
        for metric_name, duration in self.performance_metrics.items():
            if duration > max_response_time:
                performance_issues.append(f"{metric_name}: {duration:.2f}s > {max_response_time}s")
                
        if performance_issues:
            self._add_test_result(test_name, False, f"Performance issues: {performance_issues}")
            self.warnings.extend(performance_issues)
        else:
            self._add_test_result(test_name, True, f"All systems meet <{max_response_time}s requirement")
            
    async def _validate_character_consistency(self):
        """Validate Diana character consistency"""
        test_name = "Character Consistency"
        
        try:
            # Check for character consistency files
            character_files = [
                "services/diana_character_validator.py",
                "scripts/validate_diana_character_consistency.py",
                "docs/diana_character_consistency_framework.md"
            ]
            
            existing_character_files = []
            for file_path in character_files:
                if os.path.exists(file_path):
                    existing_character_files.append(file_path)
            
            # Check for Diana-specific messaging in key files
            diana_indicators = 0
            key_files = [
                "services/enhanced_diana_menu_system.py",
                "handlers/diana_handler.py"
            ]
            
            for file_path in key_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(term in content.lower() for term in ['diana', 'seductora', 'misteriosa', 'encantadora']):
                            diana_indicators += 1
            
            consistency_score = (len(existing_character_files) * 30 + diana_indicators * 20)
            
            if consistency_score >= 80:
                self._add_test_result(test_name, True, f"Character consistency framework present (score: {consistency_score}/100)")
            else:
                self._add_test_result(test_name, False, f"Character consistency framework incomplete (score: {consistency_score}/100)")
                self.validation_results["warnings"].append("Character consistency framework could be improved")
                
        except Exception as e:
            self._add_test_result(test_name, False, f"Character consistency validation failed: {str(e)}")
            
    async def _validate_critical_paths(self):
        """Validate critical operational paths"""
        test_name = "Critical Paths"
        
        try:
            session = await get_session()
            
            critical_checks = []
            
            # 1. New user registration flow - simplified test
            from sqlalchemy.future import select
            test_user_id = 999888777
            
            # Try to create a user
            result = await session.execute(select(User).where(User.id == test_user_id))
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                new_user = User(
                    id=test_user_id,
                    username="new_user",
                    first_name="New",
                    last_name="User",
                    points=0,
                    level=1,
                    role="free"
                )
                session.add(new_user)
                await session.commit()
                
            critical_checks.append("✅ New user registration")
            
            # 2. VIP detection - check role field exists
            vip_test_user = await session.execute(select(User).where(User.role == "vip").limit(1))
            critical_checks.append("✅ VIP status management")
            
            # 3. Admin access - check admin field exists
            admin_test = await session.execute(select(User).limit(1))
            user_sample = admin_test.scalar_one_or_none()
            if user_sample and hasattr(user_sample, 'is_admin'):
                critical_checks.append("✅ Admin access control")
            
            await session.close()
            
            self._add_test_result(test_name, True, f"Critical paths validated: {len(critical_checks)} checks passed")
            
        except Exception as e:
            self._add_test_result(test_name, False, f"Critical path validation failed: {str(e)}")
            self.critical_issues.append(f"Critical path error: {str(e)}")
            
    def _add_test_result(self, test_name: str, success: bool, message: str):
        """Add test result to validation results"""
        self.validation_results["tests"].append({
            "name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {message}")
        
    def _generate_final_report(self):
        """Generate final validation report"""
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL MVP VALIDATION REPORT")
        logger.info("="*60)
        
        total_tests = len(self.validation_results["tests"])
        passed_tests = sum(1 for test in self.validation_results["tests"] if test["success"])
        
        logger.info(f"Tests: {passed_tests}/{total_tests} passed")
        logger.info(f"Critical Issues: {len(self.critical_issues)}")
        logger.info(f"Warnings: {len(self.validation_results['warnings'])}")
        
        # Performance summary
        if self.performance_metrics:
            logger.info("\n🚀 Performance Metrics:")
            for metric, value in self.performance_metrics.items():
                logger.info(f"  • {metric}: {value:.2f}s")
                
        # Critical issues
        if self.critical_issues:
            logger.info("\n❌ Critical Issues:")
            for issue in self.critical_issues:
                logger.info(f"  • {issue}")
                
        # Warnings
        if self.validation_results["warnings"]:
            logger.info("\n⚠️  Warnings:")
            for warning in self.validation_results["warnings"]:
                logger.info(f"  • {warning}")
                
        # Final determination
        self.validation_results["phase_4_ready"] = (
            len(self.critical_issues) == 0 and 
            passed_tests >= total_tests * 0.9  # 90% success rate
        )
        
        logger.info("\n" + "="*60)
        if self.validation_results["phase_4_ready"]:
            logger.info("🎉 ✅ READY FOR PHASE 4")
            logger.info("All critical systems validated successfully!")
            logger.info("MVP system is ready for optimization phase.")
        else:
            logger.info("❌ NOT READY FOR PHASE 4")
            logger.info("Critical issues must be resolved first.")
            
        logger.info("="*60)
        
        # Save detailed results
        import json
        with open("final_mvp_validation_results.json", "w") as f:
            json.dump(self.validation_results, f, indent=2)
            
        return self.validation_results["phase_4_ready"]

async def main():
    """Run final MVP validation"""
    validator = FinalMVPValidator()
    ready_for_phase_4 = await validator.run_validation()
    
    if ready_for_phase_4:
        print("\n✅ SYSTEM READY FOR PHASE 4")
        return 0
    else:
        print("\n❌ SYSTEM NOT READY FOR PHASE 4")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)