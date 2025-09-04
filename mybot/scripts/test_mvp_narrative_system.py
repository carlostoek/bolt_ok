#!/usr/bin/env python3
"""
Test MVP Narrative System Implementation
Simple validation script to test the MVP narrative system functionality.
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import create_async_session
from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
from services.mvp_narrative_progression_service import MVPNarrativeProgressionService

async def test_fragment_definitions():
    """Test fragment definitions are valid."""
    print("🧪 Testing fragment definitions...")
    
    async with create_async_session() as session:
        service = MVPNarrativeFragmentService(session)
        
        # Get fragment definitions
        fragments = service._get_mvp_fragment_definitions()
        
        print(f"  ✅ Found {len(fragments)} fragment definitions")
        
        # Test structure
        levels = {}
        for fragment in fragments:
            level = fragment['storyline_level']
            if level not in levels:
                levels[level] = []
            levels[level].append(fragment)
            
            # Validate required fields
            required_fields = ['id', 'title', 'content', 'fragment_type', 'storyline_level', 'tier_classification']
            for field in required_fields:
                assert field in fragment, f"Missing field {field} in fragment {fragment.get('id')}"
        
        print(f"  ✅ Level 1 (Los Kinkys): {len(levels.get(1, []))} fragments")
        print(f"  ✅ Level 2 (Observadores): {len(levels.get(2, []))} fragments") 
        print(f"  ✅ Level 3 (Comprensores): {len(levels.get(3, []))} fragments")
        
        # Validate progression logic
        for level, frags in levels.items():
            for fragment in frags:
                if fragment['fragment_type'] == 'DECISION':
                    assert 'choices' in fragment, f"Decision fragment {fragment['id']} missing choices"
                    assert len(fragment['choices']) > 0, f"Decision fragment {fragment['id']} has no choices"
                    
                    for choice in fragment['choices']:
                        assert 'text' in choice, f"Choice missing text in {fragment['id']}"
        
        return True

async def test_service_initialization():
    """Test service can be initialized properly."""
    print("🧪 Testing service initialization...")
    
    try:
        async with create_async_session() as session:
            fragment_service = MVPNarrativeFragmentService(session)
            progression_service = MVPNarrativeProgressionService(session)
            
            print("  ✅ Fragment service initialized")
            print("  ✅ Progression service initialized")
            
            # Test cache initialization
            assert hasattr(fragment_service, '_fragment_cache')
            assert hasattr(fragment_service, '_cache_ttl')
            
            print("  ✅ Caching system ready")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Service initialization failed: {e}")
        return False

async def test_character_consistency():
    """Test character consistency in fragment content."""
    print("🧪 Testing character consistency...")
    
    async with create_async_session() as session:
        service = MVPNarrativeFragmentService(session)
        fragments = service._get_mvp_fragment_definitions()
        
        diana_elements = ['diana', 'querido', 'secreto', 'misterio', 'alma']
        consistency_scores = []
        
        for fragment in fragments:
            content = fragment['content'].lower()
            
            # Check for Diana personality elements
            element_count = sum(1 for element in diana_elements if element in content)
            consistency_score = (element_count / len(diana_elements)) * 100
            consistency_scores.append(consistency_score)
            
            # Check personality weight requirement
            personality_weight = fragment.get('diana_personality_weight', 0)
            meets_requirement = personality_weight >= 95
            
            status = "✅" if meets_requirement else "❌"
            print(f"  {status} {fragment['id']}: Personality weight {personality_weight}%")
        
        avg_consistency = sum(consistency_scores) / len(consistency_scores)
        print(f"  📊 Average character consistency: {avg_consistency:.1f}%")
        
        return avg_consistency >= 70  # Reasonable threshold for element presence

async def test_performance_simulation():
    """Test performance characteristics."""
    print("🧪 Testing performance simulation...")
    
    async with create_async_session() as session:
        fragment_service = MVPNarrativeFragmentService(session)
        progression_service = MVPNarrativeProgressionService(session)
        
        # Test fragment retrieval performance
        retrieval_times = []
        for i in range(3):
            start_time = time.time()
            
            # Simulate fragment operations
            fragments = fragment_service._get_mvp_fragment_definitions()
            test_fragment = fragments[0] if fragments else None
            
            end_time = time.time()
            retrieval_time = (end_time - start_time) * 1000  # Convert to ms
            retrieval_times.append(retrieval_time)
        
        avg_retrieval_time = sum(retrieval_times) / len(retrieval_times)
        meets_requirement = avg_retrieval_time < 500
        
        status = "✅" if meets_requirement else "❌"
        print(f"  {status} Fragment operations: {avg_retrieval_time:.2f}ms (target: <500ms)")
        
        # Test progress calculation performance
        progress_times = []
        for i in range(3):
            start_time = time.time()
            
            # Simulate progress calculation
            test_progress = {
                'current_level': 1,
                'fragments_completed': 2,
                'total_mvp_fragments': 8
            }
            completion_pct = progression_service._calculate_mvp_completion(test_progress)
            
            end_time = time.time()
            progress_time = (end_time - start_time) * 1000
            progress_times.append(progress_time)
        
        avg_progress_time = sum(progress_times) / len(progress_times)
        progress_meets_requirement = avg_progress_time < 100  # Should be very fast
        
        status = "✅" if progress_meets_requirement else "❌"
        print(f"  {status} Progress calculation: {avg_progress_time:.2f}ms (target: <100ms)")
        
        return meets_requirement and progress_meets_requirement

async def test_narrative_flow_logic():
    """Test narrative flow and progression logic."""
    print("🧪 Testing narrative flow logic...")
    
    async with create_async_session() as session:
        service = MVPNarrativeFragmentService(session)
        fragments = service._get_mvp_fragment_definitions()
        
        # Create fragment lookup
        fragment_map = {f['id']: f for f in fragments}
        
        # Test progression paths
        start_fragment = fragment_map.get('diana_l1_f1_umbral')
        if not start_fragment:
            print("  ❌ Start fragment not found")
            return False
        
        print(f"  ✅ Start fragment: {start_fragment['id']}")
        
        # Test choice progression
        if start_fragment['fragment_type'] == 'DECISION':
            choice = start_fragment['choices'][0]
            next_fragment_id = choice.get('next_fragment_id')
            next_fragment = fragment_map.get(next_fragment_id)
            
            if next_fragment:
                print(f"  ✅ Choice leads to: {next_fragment['id']}")
            else:
                print(f"  ❌ Invalid next fragment: {next_fragment_id}")
                return False
        
        # Test level progression
        level_counts = {}
        for fragment in fragments:
            level = fragment['storyline_level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        expected_counts = {1: 3, 2: 3, 3: 2}  # MVP structure
        for level, expected_count in expected_counts.items():
            actual_count = level_counts.get(level, 0)
            if actual_count == expected_count:
                print(f"  ✅ Level {level}: {actual_count} fragments (expected: {expected_count})")
            else:
                print(f"  ❌ Level {level}: {actual_count} fragments (expected: {expected_count})")
                return False
        
        return True

async def run_all_tests():
    """Run all tests and provide summary."""
    print("🚀 Starting MVP Narrative System Tests...\n")
    
    tests = [
        ("Fragment Definitions", test_fragment_definitions),
        ("Service Initialization", test_service_initialization),
        ("Character Consistency", test_character_consistency),
        ("Performance Simulation", test_performance_simulation),
        ("Narrative Flow Logic", test_narrative_flow_logic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            result = await test_func()
            results.append((test_name, result, None))
            
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"Result: {status}")
            
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"Result: ❌ ERROR - {e}")
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if error:
            print(f"    Error: {error}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MVP Narrative System ready for deployment.")
        return True
    else:
        print(f"⚠️ {total - passed} test(s) failed. Review issues before deployment.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)