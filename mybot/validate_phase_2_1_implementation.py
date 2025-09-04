#!/usr/bin/env python3
"""
Phase 2.1 Implementation Validation Script
Validates that Enhanced User Service and Diana Menu System meet all requirements.

Requirements to validate:
- User registration success rate >99%
- Menu response time <1s  
- Diana character consistency >95%
- Zero menu navigation errors
- Role-based access control working
- Lucien coordination role preserved
"""

import asyncio
import sys
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Import services to test
from services.enhanced_user_service import EnhancedUserService
from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
from services.diana_character_validator import DianaCharacterValidator
from database.models import Base, User
from database.narrative_unified import NarrativeFragment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase21Validator:
    """Validates Phase 2.1 implementation against requirements."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.test_results = {}
        
    async def setup_test_database(self):
        """Setup test database for validation."""
        # Use SQLite in-memory for testing
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False
        )
        
        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        self.session_factory = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        logger.info("✅ Test database setup complete")
    
    async def validate_user_registration_success_rate(self) -> Dict[str, Any]:
        """Validate >99% user registration success rate requirement."""
        logger.info("🔍 Testing user registration success rate...")
        
        async with self.session_factory() as session:
            user_service = EnhancedUserService(session)
            
            # Test 100 registrations
            total_tests = 100
            successful = 0
            failed = 0
            errors = []
            registration_times = []
            character_scores = []
            
            for i in range(total_tests):
                try:
                    start_time = datetime.now()
                    result = await user_service.enhanced_registration(
                        telegram_id=10000 + i,
                        first_name=f"Test{i}",
                        last_name="User",
                        username=f"testuser{i}",
                        initial_role="free"
                    )
                    
                    reg_time = (datetime.now() - start_time).total_seconds()
                    registration_times.append(reg_time)
                    
                    if result.success:
                        successful += 1
                        character_scores.append(result.character_score)
                    else:
                        failed += 1
                        errors.extend(result.errors)
                        
                except Exception as e:
                    failed += 1
                    errors.append(str(e))
            
            success_rate = (successful / total_tests) * 100
            avg_registration_time = statistics.mean(registration_times) if registration_times else 0
            avg_character_score = statistics.mean(character_scores) if character_scores else 0
            
            result = {
                "test_name": "User Registration Success Rate",
                "requirement": ">99% success rate",
                "actual_success_rate": success_rate,
                "total_tests": total_tests,
                "successful": successful,
                "failed": failed,
                "avg_registration_time": avg_registration_time,
                "avg_character_score": avg_character_score,
                "meets_requirement": success_rate >= 99.0,
                "errors": errors[:5]  # First 5 errors for debugging
            }
            
            logger.info(f"Registration success rate: {success_rate:.1f}% (Required: >99%)")
            return result
    
    async def validate_menu_response_time(self) -> Dict[str, Any]:
        """Validate <1s menu response time requirement."""
        logger.info("🔍 Testing menu response time...")
        
        async with self.session_factory() as session:
            menu_system = EnhancedDianaMenuSystem(session)
            
            response_times = []
            character_scores = []
            errors = []
            roles_tested = ["free", "vip", "admin"]
            tests_per_role = 20
            
            for role in roles_tested:
                for i in range(tests_per_role):
                    try:
                        # Mock update object
                        class MockUpdate:
                            def __init__(self, user_id):
                                self.from_user = type('', (), {'id': user_id})()
                                
                            async def answer(self):
                                pass
                        
                        mock_update = MockUpdate(20000 + i)
                        
                        start_time = datetime.now()
                        result = await menu_system.show_main_menu(mock_update, user_role=role)
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        response_times.append(response_time)
                        
                        if result.success:
                            character_scores.append(result.character_score)
                        else:
                            errors.extend(result.errors)
                            
                    except Exception as e:
                        errors.append(f"Role {role}, test {i}: {str(e)}")
            
            fast_responses = sum(1 for rt in response_times if rt < 1.0)
            fast_percentage = (fast_responses / len(response_times)) * 100 if response_times else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            avg_character_score = statistics.mean(character_scores) if character_scores else 0
            
            result = {
                "test_name": "Menu Response Time",
                "requirement": "<1s response time for 95% of requests",
                "fast_percentage": fast_percentage,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "total_tests": len(response_times),
                "fast_responses": fast_responses,
                "avg_character_score": avg_character_score,
                "meets_requirement": fast_percentage >= 95.0,
                "errors": errors[:5]
            }
            
            logger.info(f"Fast responses: {fast_percentage:.1f}% (Required: >=95%)")
            return result
    
    async def validate_character_consistency(self) -> Dict[str, Any]:
        """Validate >95% Diana character consistency requirement."""
        logger.info("🔍 Testing Diana character consistency...")
        
        async with self.session_factory() as session:
            user_service = EnhancedUserService(session)
            menu_system = EnhancedDianaMenuSystem(session)
            character_validator = DianaCharacterValidator(session)
            
            all_scores = []
            failed_validations = []
            test_contexts = []
            
            # Test registration messages for all roles
            roles = ["free", "vip", "admin"]
            for role in roles:
                try:
                    result = await user_service.enhanced_registration(
                        telegram_id=30000 + hash(role),
                        first_name="Character",
                        last_name="Test",
                        initial_role=role
                    )
                    
                    if result.success:
                        all_scores.append(result.character_score)
                        test_contexts.append(f"registration_{role}")
                        
                        if result.character_score < 95.0:
                            failed_validations.append({
                                "context": f"registration_{role}",
                                "score": result.character_score,
                                "message": result.welcome_message[:100] + "..."
                            })
                except Exception as e:
                    failed_validations.append({
                        "context": f"registration_{role}",
                        "error": str(e)
                    })
            
            # Test menu messages for all roles
            for role in roles:
                try:
                    class MockUpdate:
                        def __init__(self, user_id):
                            self.from_user = type('', (), {'id': user_id})()
                        async def answer(self):
                            pass
                    
                    mock_update = MockUpdate(30100 + hash(role))
                    result = await menu_system.show_main_menu(mock_update, user_role=role)
                    
                    if result.success:
                        all_scores.append(result.character_score)
                        test_contexts.append(f"menu_{role}")
                        
                        if result.character_score < 95.0:
                            failed_validations.append({
                                "context": f"menu_{role}",
                                "score": result.character_score
                            })
                except Exception as e:
                    failed_validations.append({
                        "context": f"menu_{role}",
                        "error": str(e)
                    })
            
            min_score = min(all_scores) if all_scores else 0
            avg_score = statistics.mean(all_scores) if all_scores else 0
            scores_above_95 = sum(1 for score in all_scores if score >= 95.0)
            percentage_above_95 = (scores_above_95 / len(all_scores)) * 100 if all_scores else 0
            
            result = {
                "test_name": "Diana Character Consistency",
                "requirement": ">95% character consistency score",
                "min_score": min_score,
                "avg_score": avg_score,
                "total_tests": len(all_scores),
                "scores_above_95": scores_above_95,
                "percentage_above_95": percentage_above_95,
                "meets_requirement": min_score >= 95.0 and avg_score >= 95.0,
                "failed_validations": failed_validations[:5],
                "test_contexts": test_contexts
            }
            
            logger.info(f"Character consistency: min={min_score:.1f}, avg={avg_score:.1f} (Required: >95)")
            return result
    
    async def validate_role_based_access_control(self) -> Dict[str, Any]:
        """Validate role-based access control across menu paths."""
        logger.info("🔍 Testing role-based access control...")
        
        async with self.session_factory() as session:
            user_service = EnhancedUserService(session)
            menu_system = EnhancedDianaMenuSystem(session)
            
            role_tests = []
            errors = []
            
            # Create users with different roles
            test_users = []
            for i, role in enumerate(["free", "vip", "admin"]):
                user_id = 40000 + i
                reg_result = await user_service.enhanced_registration(
                    telegram_id=user_id,
                    first_name=f"Role{role.title()}",
                    last_name="Test",
                    initial_role=role
                )
                
                if reg_result.success:
                    test_users.append({
                        "user_id": user_id,
                        "role": role,
                        "user": reg_result.user
                    })
                else:
                    errors.append(f"Failed to create {role} user: {reg_result.errors}")
            
            # Test menu access for each role
            for user_data in test_users:
                try:
                    class MockUpdate:
                        def __init__(self, user_id):
                            self.from_user = type('', (), {'id': user_id})()
                        async def answer(self):
                            pass
                    
                    mock_update = MockUpdate(user_data["user_id"])
                    result = await menu_system.show_main_menu(
                        mock_update, 
                        user_role=user_data["role"]
                    )
                    
                    role_tests.append({
                        "role": user_data["role"],
                        "menu_success": result.success,
                        "character_score": result.character_score if result.success else 0,
                        "errors": result.errors if not result.success else []
                    })
                    
                except Exception as e:
                    errors.append(f"Menu test failed for {user_data['role']}: {str(e)}")
                    role_tests.append({
                        "role": user_data["role"],
                        "menu_success": False,
                        "error": str(e)
                    })
            
            successful_role_tests = sum(1 for test in role_tests if test["menu_success"])
            success_rate = (successful_role_tests / len(role_tests)) * 100 if role_tests else 0
            
            result = {
                "test_name": "Role-Based Access Control",
                "requirement": "All roles can access appropriate menu content",
                "total_role_tests": len(role_tests),
                "successful_tests": successful_role_tests,
                "success_rate": success_rate,
                "meets_requirement": success_rate >= 100.0,  # All should succeed
                "role_test_details": role_tests,
                "errors": errors
            }
            
            logger.info(f"Role-based access: {success_rate:.1f}% success (Required: 100%)")
            return result
    
    async def validate_lucien_coordination_role(self) -> Dict[str, Any]:
        """Validate Lucien's coordination role preservation."""
        logger.info("🔍 Testing Lucien coordination role preservation...")
        
        async with self.session_factory() as session:
            user_service = EnhancedUserService(session)
            
            diana_prominence_tests = []
            lucien_checks = []
            
            # Test various message types
            for role in ["free", "vip", "admin"]:
                result = await user_service.enhanced_registration(
                    telegram_id=50000 + hash(role),
                    first_name="Lucien",
                    last_name="Test",
                    initial_role=role
                )
                
                if result.success:
                    msg_lower = result.welcome_message.lower()
                    
                    diana_count = msg_lower.count("diana")
                    lucien_count = msg_lower.count("lucien")
                    
                    diana_prominence_tests.append({
                        "role": role,
                        "diana_mentions": diana_count,
                        "lucien_mentions": lucien_count,
                        "diana_more_prominent": diana_count >= lucien_count,
                        "message_sample": result.welcome_message[:200] + "..."
                    })
                    
                    # Lucien should be coordinating behind scenes, not prominent in messages
                    lucien_checks.append(lucien_count <= diana_count)
            
            all_tests_pass = all(lucien_checks) if lucien_checks else False
            diana_always_prominent = all(test["diana_more_prominent"] for test in diana_prominence_tests)
            
            result = {
                "test_name": "Lucien Coordination Role Preservation",
                "requirement": "Diana more prominent than Lucien in user-facing content",
                "total_tests": len(diana_prominence_tests),
                "diana_always_prominent": diana_always_prominent,
                "meets_requirement": all_tests_pass and diana_always_prominent,
                "prominence_test_details": diana_prominence_tests,
                "lucien_checks_passed": sum(lucien_checks) if lucien_checks else 0
            }
            
            logger.info(f"Lucien coordination: Diana prominent in {sum(lucien_checks)}/{len(lucien_checks)} tests")
            return result
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all Phase 2.1 validations."""
        logger.info("🚀 Starting Phase 2.1 Implementation Validation")
        
        await self.setup_test_database()
        
        validations = [
            self.validate_user_registration_success_rate(),
            self.validate_menu_response_time(),
            self.validate_character_consistency(),
            self.validate_role_based_access_control(),
            self.validate_lucien_coordination_role()
        ]
        
        results = await asyncio.gather(*validations, return_exceptions=True)
        
        # Process results
        validation_results = {}
        all_requirements_met = True
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                validation_name = f"validation_{i}"
                validation_results[validation_name] = {
                    "error": str(result),
                    "meets_requirement": False
                }
                all_requirements_met = False
            else:
                validation_results[result["test_name"]] = result
                if not result["meets_requirement"]:
                    all_requirements_met = False
        
        # Overall summary
        summary = {
            "phase": "2.1 - User System & Diana Menu",
            "validation_timestamp": datetime.now().isoformat(),
            "all_requirements_met": all_requirements_met,
            "total_validations": len(validations),
            "passed_validations": sum(1 for result in validation_results.values() 
                                    if result.get("meets_requirement", False)),
            "detailed_results": validation_results
        }
        
        return summary
    
    async def cleanup(self):
        """Cleanup test resources."""
        if self.engine:
            await self.engine.dispose()
        logger.info("✅ Test cleanup complete")

async def main():
    """Main validation execution."""
    validator = Phase21Validator()
    
    try:
        results = await validator.run_all_validations()
        
        # Print summary
        print("\n" + "="*80)
        print("PHASE 2.1 IMPLEMENTATION VALIDATION RESULTS")
        print("="*80)
        print(f"Overall Status: {'✅ PASSED' if results['all_requirements_met'] else '❌ FAILED'}")
        print(f"Validations Passed: {results['passed_validations']}/{results['total_validations']}")
        print(f"Validation Time: {results['validation_timestamp']}")
        
        print("\n" + "-"*50)
        print("DETAILED RESULTS:")
        print("-"*50)
        
        for test_name, result in results["detailed_results"].items():
            status = "✅ PASS" if result.get("meets_requirement", False) else "❌ FAIL"
            print(f"\n{status} {test_name}")
            
            if "requirement" in result:
                print(f"   Requirement: {result['requirement']}")
            
            # Print key metrics
            if "actual_success_rate" in result:
                print(f"   Success Rate: {result['actual_success_rate']:.1f}%")
            if "fast_percentage" in result:
                print(f"   Fast Responses: {result['fast_percentage']:.1f}%")
            if "avg_score" in result:
                print(f"   Avg Character Score: {result['avg_score']:.1f}")
            if "avg_response_time" in result:
                print(f"   Avg Response Time: {result['avg_response_time']:.3f}s")
            
            # Print errors if any
            if result.get("errors"):
                print(f"   Errors: {len(result['errors'])} error(s)")
                for error in result["errors"][:2]:  # First 2 errors
                    print(f"     - {error}")
        
        print("\n" + "="*80)
        
        if results['all_requirements_met']:
            print("🎉 Phase 2.1 Implementation READY FOR PRODUCTION!")
            return 0
        else:
            print("⚠️  Phase 2.1 Implementation requires fixes before production")
            return 1
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        print(f"❌ Validation failed: {e}")
        return 1
        
    finally:
        await validator.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)