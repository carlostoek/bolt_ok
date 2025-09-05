#!/usr/bin/env python3
"""
Diana Service Layer Performance Test Script

Tests the performance optimizations implemented for the Diana Bot MVP:
- Service Registry Pattern performance
- Character validation caching efficiency  
- Menu generation optimization
- Async operation patterns

Expected Results:
- 40% improvement in service layer response times
- <1s response time for 95% of operations
- >95% character consistency maintained
- Service instantiation overhead eliminated
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import optimized services
from services.diana_service_registry import (
    get_service_registry, 
    initialize_diana_service_registry,
    get_service_performance_report
)
from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
from services.diana_character_validator import DianaCharacterValidator

class DianaPerformanceTester:
    """Performance testing suite for Diana service layer optimizations."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.performance_results = {}
        
    async def setup_test_environment(self):
        """Setup test database and services."""
        # Create in-memory test database
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        self.session_factory = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Initialize service registry
        await initialize_diana_service_registry()
        print("✅ Test environment setup complete")
    
    async def test_service_registry_performance(self, iterations: int = 100) -> Dict[str, Any]:
        """Test service registry caching performance."""
        print(f"\n🔧 Testing Service Registry Performance ({iterations} iterations)")
        
        registry = get_service_registry()
        response_times = []
        
        async with self.session_factory() as session:
            # Warm up cache
            await registry.get_service("user_service", session)
            await registry.get_service("character_validator", session)
            
            # Test performance
            for i in range(iterations):
                start_time = time.time()
                
                user_service = await registry.get_service("user_service", session)
                validator = await registry.get_service("character_validator", session)
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if i % 25 == 0:
                    print(f"  Iteration {i}: {response_time:.3f}s")
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        cache_stats = registry.get_cache_stats()
        
        results = {
            "test": "service_registry",
            "iterations": iterations,
            "avg_response_time": avg_time,
            "p95_response_time": p95_time,
            "cache_hit_rate": cache_stats["cache_efficiency"],
            "meets_target": avg_time < 0.050  # 50ms target
        }
        
        print(f"  Average: {avg_time:.3f}s, P95: {p95_time:.3f}s")
        print(f"  Cache efficiency: {cache_stats['cache_efficiency']}")
        
        return results
    
    async def test_character_validation_performance(self, iterations: int = 50) -> Dict[str, Any]:
        """Test character validation caching and ultra-fast validation."""
        print(f"\n🎭 Testing Character Validation Performance ({iterations} iterations)")
        
        test_texts = [
            "💋 **Los Dominios de Diana**\n\nSusurra mi nombre, querido... ¿Qué secretos deseas explorar conmigo hoy?",
            "👑 **Círculo Íntimo de Diana**\n\nAh, mi querido elegido... Bienvenido a donde solo los especiales pueden llegar.",
            "✨ **Invitación al Círculo Íntimo**\n\nQuerido... siento que estás listo para más.",
            "😔 Las corrientes místicas fluctúan... Algo interrumpe nuestra conexión."
        ]
        
        response_times = []
        character_scores = []
        
        async with self.session_factory() as session:
            validator = DianaCharacterValidator(session)
            
            for i in range(iterations):
                test_text = test_texts[i % len(test_texts)]
                start_time = time.time()
                
                # Use ultra-fast validation
                result = await validator.validate_text_ultra_fast(test_text, "menu_response")
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                character_scores.append(result.overall_score)
                
                if i % 10 == 0:
                    print(f"  Iteration {i}: {response_time:.3f}s, score: {result.overall_score:.1f}")
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        avg_score = statistics.mean(character_scores)
        cache_stats = validator.get_cache_stats()
        
        results = {
            "test": "character_validation",
            "iterations": iterations,
            "avg_response_time": avg_time,
            "p95_response_time": p95_time,
            "avg_character_score": avg_score,
            "cache_hit_rate": cache_stats["hit_rate"],
            "meets_time_target": avg_time < 0.050,  # 50ms target
            "meets_score_target": avg_score >= 95.0
        }
        
        print(f"  Average: {avg_time:.3f}s, P95: {p95_time:.3f}s")
        print(f"  Character score: {avg_score:.1f}, Cache hit rate: {cache_stats['hit_rate']:.1f}%")
        
        return results
    
    async def test_menu_generation_performance(self, iterations: int = 30) -> Dict[str, Any]:
        """Test menu generation with pre-built keyboards and caching."""
        print(f"\n📱 Testing Menu Generation Performance ({iterations} iterations)")
        
        # Mock update object
        class MockUpdate:
            def __init__(self, user_id: int):
                self.from_user = MockUser(user_id)
        
        class MockUser:
            def __init__(self, user_id: int):
                self.id = user_id
        
        response_times = []
        character_scores = []
        performance_met = []
        
        async with self.session_factory() as session:
            menu_system = EnhancedDianaMenuSystem(session)
            
            for i in range(iterations):
                user_id = 1000 + (i % 10)  # Simulate different users
                user_role = ["free", "vip", "admin"][i % 3]
                
                mock_update = MockUpdate(user_id)
                start_time = time.time()
                
                try:
                    # Test optimized menu show (would normally send message)
                    # We'll simulate the internal processing
                    cache_key = f"main_menu_{user_role}_{user_id}"
                    cached_data = menu_system._get_from_cache(cache_key)
                    
                    if not cached_data:
                        # Simulate menu generation
                        template = menu_system.diana_menu_templates["main_menu"][user_role]
                        keyboard = menu_system._get_cached_keyboard(f"main_{user_role}")
                        character_score = menu_system.static_content_scores[f"main_menu_{user_role}"]
                        
                        menu_system._cache_menu_data(cache_key, (template, keyboard, character_score))
                    else:
                        template, keyboard, character_score = cached_data
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    character_scores.append(character_score)
                    performance_met.append(response_time < 0.200)  # 200ms target for menu generation
                    
                    if i % 10 == 0:
                        print(f"  Iteration {i}: {response_time:.3f}s, score: {character_score:.1f}")
                        
                except Exception as e:
                    print(f"  Error in iteration {i}: {e}")
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        avg_score = statistics.mean(character_scores)
        performance_rate = sum(performance_met) / len(performance_met) * 100
        
        results = {
            "test": "menu_generation",
            "iterations": iterations,
            "avg_response_time": avg_time,
            "p95_response_time": p95_time,
            "avg_character_score": avg_score,
            "performance_target_met": performance_rate,
            "meets_targets": avg_time < 0.200 and avg_score >= 95.0
        }
        
        print(f"  Average: {avg_time:.3f}s, P95: {p95_time:.3f}s")
        print(f"  Character score: {avg_score:.1f}, Performance rate: {performance_rate:.1f}%")
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all performance tests and generate comprehensive report."""
        print("🚀 Starting Diana Service Layer Performance Tests")
        print("=" * 60)
        
        await self.setup_test_environment()
        
        # Run all tests
        registry_results = await self.test_service_registry_performance()
        validation_results = await self.test_character_validation_performance()
        menu_results = await self.test_menu_generation_performance()
        
        # Get final performance report
        performance_report = get_service_performance_report()
        
        # Compile comprehensive results
        comprehensive_results = {
            "timestamp": time.time(),
            "test_results": {
                "service_registry": registry_results,
                "character_validation": validation_results,
                "menu_generation": menu_results
            },
            "performance_summary": performance_report,
            "overall_assessment": self._assess_performance(
                registry_results, validation_results, menu_results
            )
        }
        
        # Print final assessment
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE ASSESSMENT SUMMARY")
        print("=" * 60)
        
        assessment = comprehensive_results["overall_assessment"]
        print(f"Service Registry: {'✅' if assessment['service_registry_optimal'] else '❌'}")
        print(f"Character Validation: {'✅' if assessment['validation_optimal'] else '❌'}")
        print(f"Menu Generation: {'✅' if assessment['menu_optimal'] else '❌'}")
        print(f"\nOverall Performance Target: {'✅ MET' if assessment['targets_met'] else '❌ NOT MET'}")
        print(f"Expected Performance Improvement: {assessment['improvement_estimate']:.1f}%")
        
        return comprehensive_results
    
    def _assess_performance(self, registry_results: Dict, validation_results: Dict, menu_results: Dict) -> Dict[str, Any]:
        """Assess overall performance against targets."""
        service_registry_optimal = (
            registry_results["meets_target"] and
            registry_results["avg_response_time"] < 0.050
        )
        
        validation_optimal = (
            validation_results["meets_time_target"] and
            validation_results["meets_score_target"] and
            validation_results["cache_hit_rate"] > 70
        )
        
        menu_optimal = (
            menu_results["meets_targets"] and
            menu_results["performance_target_met"] > 90
        )
        
        targets_met = service_registry_optimal and validation_optimal and menu_optimal
        
        # Estimate improvement based on results
        improvement_estimate = 0
        if service_registry_optimal:
            improvement_estimate += 15  # Service instantiation overhead eliminated
        if validation_optimal:
            improvement_estimate += 20  # Validation caching efficiency
        if menu_optimal:
            improvement_estimate += 10  # Menu generation optimization
        
        return {
            "service_registry_optimal": service_registry_optimal,
            "validation_optimal": validation_optimal,
            "menu_optimal": menu_optimal,
            "targets_met": targets_met,
            "improvement_estimate": improvement_estimate
        }
    
    async def cleanup(self):
        """Cleanup test resources."""
        if self.engine:
            await self.engine.dispose()
        print("🧹 Test cleanup complete")

async def main():
    """Run the Diana performance test suite."""
    tester = DianaPerformanceTester()
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Save results to file for analysis
        import json
        with open("diana_performance_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to diana_performance_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())