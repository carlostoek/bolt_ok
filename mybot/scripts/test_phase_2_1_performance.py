#!/usr/bin/env python3
"""
Phase 2.1 Performance Testing Script
Tests Enhanced User Service and Diana Menu System under load conditions.

Performance Requirements:
- User registration <3s per user
- Menu response time <1s for 95% of requests
- System stable under 100+ concurrent users
- Character consistency maintained under load
"""

import asyncio
import sys
import time
import statistics
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import services to test
from services.enhanced_user_service import EnhancedUserService
from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
from database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase21PerformanceTester:
    """Performance testing for Phase 2.1 implementation."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        
    async def setup_test_database(self):
        """Setup test database for performance testing."""
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            pool_size=20,  # Higher pool for concurrent testing
            max_overflow=50
        )
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ Performance test database setup complete")
    
    async def test_concurrent_user_registration(self, num_users: int = 100) -> Dict[str, Any]:
        """Test concurrent user registration performance."""
        logger.info(f"🚀 Testing concurrent registration with {num_users} users...")
        
        async def register_user(user_index: int) -> Dict[str, Any]:
            """Register a single user and return performance data."""
            async with self.session_factory() as session:
                user_service = EnhancedUserService(session)
                
                start_time = time.time()
                try:
                    result = await user_service.enhanced_registration(
                        telegram_id=100000 + user_index,
                        first_name=f"ConcurrentUser{user_index}",
                        last_name="Test",
                        username=f"concurrent{user_index}",
                        initial_role="free"
                    )
                    
                    registration_time = time.time() - start_time
                    
                    return {
                        "user_index": user_index,
                        "success": result.success,
                        "registration_time": registration_time,
                        "character_score": result.character_score if result.success else 0,
                        "errors": result.errors if not result.success else []
                    }
                    
                except Exception as e:
                    return {
                        "user_index": user_index,
                        "success": False,
                        "registration_time": time.time() - start_time,
                        "character_score": 0,
                        "error": str(e)
                    }
        
        # Execute concurrent registrations
        overall_start_time = time.time()
        tasks = [register_user(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        overall_time = time.time() - overall_start_time
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        error_results = [r for r in results if isinstance(r, Exception)]
        
        success_rate = (len(successful_results) / num_users) * 100
        
        # Performance metrics
        registration_times = [r["registration_time"] for r in successful_results]
        character_scores = [r["character_score"] for r in successful_results if r["character_score"] > 0]
        
        performance_data = {
            "test_name": "Concurrent User Registration",
            "num_users": num_users,
            "success_rate": success_rate,
            "overall_time": overall_time,
            "throughput_users_per_second": num_users / overall_time,
            "successful_registrations": len(successful_results),
            "failed_registrations": len(failed_results),
            "error_exceptions": len(error_results),
            "avg_registration_time": statistics.mean(registration_times) if registration_times else 0,
            "max_registration_time": max(registration_times) if registration_times else 0,
            "min_registration_time": min(registration_times) if registration_times else 0,
            "registrations_under_3s": sum(1 for t in registration_times if t < 3.0),
            "performance_requirement_met": all(t < 3.0 for t in registration_times) and success_rate >= 99.0,
            "avg_character_score": statistics.mean(character_scores) if character_scores else 0,
            "min_character_score": min(character_scores) if character_scores else 0
        }
        
        logger.info(f"Registration performance: {success_rate:.1f}% success, "
                   f"{performance_data['avg_registration_time']:.2f}s avg time")
        
        return performance_data
    
    async def test_concurrent_menu_requests(self, num_requests: int = 200) -> Dict[str, Any]:
        """Test concurrent menu request performance."""
        logger.info(f"🚀 Testing concurrent menu requests with {num_requests} requests...")
        
        # Pre-register some users for menu testing
        async with self.session_factory() as session:
            user_service = EnhancedUserService(session)
            for i in range(10):  # Pre-register 10 users
                await user_service.enhanced_registration(
                    telegram_id=200000 + i,
                    first_name=f"MenuUser{i}",
                    last_name="Test",
                    initial_role=["free", "vip", "admin"][i % 3]
                )
        
        async def make_menu_request(request_index: int) -> Dict[str, Any]:
            """Make a single menu request and return performance data."""
            async with self.session_factory() as session:
                menu_system = EnhancedDianaMenuSystem(session)
                
                # Mock update object
                class MockUpdate:
                    def __init__(self, user_id):
                        self.from_user = type('', (), {'id': user_id})()
                    async def answer(self):
                        pass
                
                user_id = 200000 + (request_index % 10)  # Rotate through pre-registered users
                role = ["free", "vip", "admin"][request_index % 3]
                mock_update = MockUpdate(user_id)
                
                start_time = time.time()
                try:
                    result = await menu_system.show_main_menu(mock_update, user_role=role)
                    response_time = time.time() - start_time
                    
                    return {
                        "request_index": request_index,
                        "success": result.success,
                        "response_time": response_time,
                        "character_score": result.character_score if result.success else 0,
                        "role": role,
                        "meets_performance_req": result.meets_performance_requirement if result.success else False,
                        "errors": result.errors if not result.success else []
                    }
                    
                except Exception as e:
                    return {
                        "request_index": request_index,
                        "success": False,
                        "response_time": time.time() - start_time,
                        "character_score": 0,
                        "role": role,
                        "meets_performance_req": False,
                        "error": str(e)
                    }
        
        # Execute concurrent menu requests
        overall_start_time = time.time()
        tasks = [make_menu_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        overall_time = time.time() - overall_start_time
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        error_results = [r for r in results if isinstance(r, Exception)]
        
        success_rate = (len(successful_results) / num_requests) * 100
        
        # Performance metrics
        response_times = [r["response_time"] for r in successful_results]
        character_scores = [r["character_score"] for r in successful_results if r["character_score"] > 0]
        fast_responses = [r for r in successful_results if r["response_time"] < 1.0]
        
        fast_percentage = (len(fast_responses) / len(successful_results)) * 100 if successful_results else 0
        
        performance_data = {
            "test_name": "Concurrent Menu Requests",
            "num_requests": num_requests,
            "success_rate": success_rate,
            "overall_time": overall_time,
            "throughput_requests_per_second": num_requests / overall_time,
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "error_exceptions": len(error_results),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "fast_responses": len(fast_responses),
            "fast_percentage": fast_percentage,
            "performance_requirement_met": fast_percentage >= 95.0 and success_rate >= 99.0,
            "avg_character_score": statistics.mean(character_scores) if character_scores else 0,
            "min_character_score": min(character_scores) if character_scores else 0
        }
        
        logger.info(f"Menu performance: {success_rate:.1f}% success, "
                   f"{fast_percentage:.1f}% under 1s, {performance_data['avg_response_time']:.3f}s avg")
        
        return performance_data
    
    async def test_mixed_workload_stress(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Test mixed workload of registrations and menu requests."""
        logger.info(f"🚀 Testing mixed workload stress for {duration_seconds} seconds...")
        
        results = {"registrations": [], "menu_requests": []}
        start_time = time.time()
        request_counter = 0
        
        async def registration_worker():
            """Worker for continuous user registrations."""
            nonlocal request_counter
            while time.time() - start_time < duration_seconds:
                async with self.session_factory() as session:
                    user_service = EnhancedUserService(session)
                    
                    user_id = 300000 + request_counter
                    request_counter += 1
                    
                    reg_start = time.time()
                    try:
                        result = await user_service.enhanced_registration(
                            telegram_id=user_id,
                            first_name=f"StressUser{user_id}",
                            last_name="Test",
                            initial_role="free"
                        )
                        
                        results["registrations"].append({
                            "success": result.success,
                            "time": time.time() - reg_start,
                            "character_score": result.character_score if result.success else 0
                        })
                        
                    except Exception as e:
                        results["registrations"].append({
                            "success": False,
                            "time": time.time() - reg_start,
                            "error": str(e)
                        })
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        async def menu_worker():
            """Worker for continuous menu requests."""
            nonlocal request_counter
            while time.time() - start_time < duration_seconds:
                async with self.session_factory() as session:
                    menu_system = EnhancedDianaMenuSystem(session)
                    
                    # Mock update
                    class MockUpdate:
                        def __init__(self, user_id):
                            self.from_user = type('', (), {'id': user_id})()
                        async def answer(self):
                            pass
                    
                    user_id = 300000 + (request_counter % 100)
                    mock_update = MockUpdate(user_id)
                    
                    menu_start = time.time()
                    try:
                        result = await menu_system.show_main_menu(mock_update, user_role="free")
                        
                        results["menu_requests"].append({
                            "success": result.success,
                            "time": time.time() - menu_start,
                            "character_score": result.character_score if result.success else 0
                        })
                        
                    except Exception as e:
                        results["menu_requests"].append({
                            "success": False,
                            "time": time.time() - menu_start,
                            "error": str(e)
                        })
                
                await asyncio.sleep(0.05)  # Faster menu requests
        
        # Run workers concurrently
        await asyncio.gather(
            registration_worker(),
            menu_worker(),
            return_exceptions=True
        )
        
        total_time = time.time() - start_time
        
        # Analyze mixed workload results
        reg_successes = sum(1 for r in results["registrations"] if r.get("success"))
        menu_successes = sum(1 for r in results["menu_requests"] if r.get("success"))
        
        reg_times = [r["time"] for r in results["registrations"] if r.get("success")]
        menu_times = [r["time"] for r in results["menu_requests"] if r.get("success")]
        
        performance_data = {
            "test_name": "Mixed Workload Stress Test",
            "duration_seconds": duration_seconds,
            "total_registrations": len(results["registrations"]),
            "successful_registrations": reg_successes,
            "registration_success_rate": (reg_successes / len(results["registrations"])) * 100 if results["registrations"] else 0,
            "avg_registration_time": statistics.mean(reg_times) if reg_times else 0,
            "total_menu_requests": len(results["menu_requests"]),
            "successful_menu_requests": menu_successes,
            "menu_success_rate": (menu_successes / len(results["menu_requests"])) * 100 if results["menu_requests"] else 0,
            "avg_menu_time": statistics.mean(menu_times) if menu_times else 0,
            "fast_menu_requests": sum(1 for t in menu_times if t < 1.0),
            "fast_menu_percentage": (sum(1 for t in menu_times if t < 1.0) / len(menu_times)) * 100 if menu_times else 0,
            "total_throughput": (len(results["registrations"]) + len(results["menu_requests"])) / total_time,
            "system_stable": reg_successes > 0 and menu_successes > 0  # System handled both workloads
        }
        
        logger.info(f"Mixed workload: {performance_data['total_throughput']:.1f} ops/sec, "
                   f"reg={performance_data['registration_success_rate']:.1f}% success, "
                   f"menu={performance_data['menu_success_rate']:.1f}% success")
        
        return performance_data
    
    async def run_all_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests."""
        logger.info("🚀 Starting Phase 2.1 Performance Testing")
        
        await self.setup_test_database()
        
        # Run performance tests
        tests = [
            ("concurrent_registration", self.test_concurrent_user_registration(100)),
            ("concurrent_menu", self.test_concurrent_menu_requests(200)),
            ("mixed_workload", self.test_mixed_workload_stress(30))  # Shorter for CI
        ]
        
        results = {}
        overall_start = time.time()
        
        for test_name, test_coro in tests:
            try:
                logger.info(f"Running {test_name}...")
                test_start = time.time()
                result = await test_coro
                test_duration = time.time() - test_start
                result["test_duration"] = test_duration
                results[test_name] = result
                
            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                results[test_name] = {
                    "test_name": test_name,
                    "error": str(e),
                    "performance_requirement_met": False
                }
        
        overall_duration = time.time() - overall_start
        
        # Overall assessment
        all_requirements_met = all(
            result.get("performance_requirement_met", False) 
            for result in results.values()
        )
        
        summary = {
            "performance_test_suite": "Phase 2.1 - User System & Diana Menu",
            "test_timestamp": datetime.now().isoformat(),
            "overall_duration": overall_duration,
            "all_performance_requirements_met": all_requirements_met,
            "individual_test_results": results
        }
        
        return summary
    
    async def cleanup(self):
        """Cleanup test resources."""
        if self.engine:
            await self.engine.dispose()
        logger.info("✅ Performance test cleanup complete")

async def main():
    """Main performance testing execution."""
    tester = Phase21PerformanceTester()
    
    try:
        results = await tester.run_all_performance_tests()
        
        # Print performance summary
        print("\n" + "="*80)
        print("PHASE 2.1 PERFORMANCE TEST RESULTS")
        print("="*80)
        print(f"Overall Status: {'✅ ALL REQUIREMENTS MET' if results['all_performance_requirements_met'] else '❌ PERFORMANCE ISSUES'}")
        print(f"Total Test Duration: {results['overall_duration']:.1f}s")
        print(f"Test Timestamp: {results['test_timestamp']}")
        
        print("\n" + "-"*50)
        print("INDIVIDUAL TEST RESULTS:")
        print("-"*50)
        
        for test_name, result in results["individual_test_results"].items():
            if "error" in result:
                print(f"\n❌ {result.get('test_name', test_name)} - ERROR")
                print(f"   Error: {result['error']}")
                continue
            
            status = "✅ PASS" if result.get("performance_requirement_met", False) else "❌ FAIL"
            print(f"\n{status} {result.get('test_name', test_name)}")
            print(f"   Duration: {result.get('test_duration', 0):.1f}s")
            
            # Print relevant metrics based on test type
            if "registration" in test_name.lower():
                print(f"   Success Rate: {result.get('success_rate', 0):.1f}%")
                print(f"   Avg Registration Time: {result.get('avg_registration_time', 0):.3f}s")
                print(f"   Throughput: {result.get('throughput_users_per_second', 0):.1f} users/sec")
                
            elif "menu" in test_name.lower():
                print(f"   Success Rate: {result.get('success_rate', 0):.1f}%")
                print(f"   Fast Responses (<1s): {result.get('fast_percentage', 0):.1f}%")
                print(f"   Avg Response Time: {result.get('avg_response_time', 0):.3f}s")
                print(f"   Throughput: {result.get('throughput_requests_per_second', 0):.1f} req/sec")
                
            elif "mixed" in test_name.lower():
                print(f"   Registration Success: {result.get('registration_success_rate', 0):.1f}%")
                print(f"   Menu Success: {result.get('menu_success_rate', 0):.1f}%")
                print(f"   System Stable: {'Yes' if result.get('system_stable', False) else 'No'}")
                print(f"   Total Throughput: {result.get('total_throughput', 0):.1f} ops/sec")
            
            # Character consistency
            if "avg_character_score" in result:
                print(f"   Avg Character Score: {result['avg_character_score']:.1f}")
        
        print("\n" + "="*80)
        
        if results['all_performance_requirements_met']:
            print("🎉 Phase 2.1 Performance Requirements MET - Ready for Production!")
            return 0
        else:
            print("⚠️  Phase 2.1 Performance Issues Detected - Optimization Required")
            return 1
            
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        print(f"❌ Performance testing failed: {e}")
        return 1
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)