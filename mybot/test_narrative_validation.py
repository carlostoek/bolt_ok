#!/usr/bin/env python3
"""
Narrative System Validation Script
Tests MVP narrative system functionality and identifies issues.
"""

import asyncio
import logging
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fragment_service_structure():
    """Test 1: Fragment Service Structure and Definitions"""
    logger.info("=== TEST 1: Fragment Service Structure ===")
    
    try:
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = MVPNarrativeFragmentService(session)
            fragments = service._get_mvp_fragment_definitions()
            
            print(f"✓ Total MVP fragments defined: {len(fragments)}")
            
            # Check fragment structure
            levels = {}
            for fragment in fragments:
                level = fragment['storyline_level']
                if level not in levels:
                    levels[level] = []
                levels[level].append(fragment)
                
            print(f"✓ Fragment levels found: {sorted(levels.keys())}")
            
            for level, level_fragments in levels.items():
                print(f"  - Level {level}: {len(level_fragments)} fragments")
                for fragment in level_fragments:
                    print(f"    • {fragment['id']} ({fragment['tier_classification']})")
            
            # Check fragment navigation chain
            fragment_links = {}
            for fragment in fragments:
                if fragment.get('choices'):
                    for choice in fragment['choices']:
                        next_id = choice.get('next_fragment_id')
                        if next_id:
                            fragment_links[fragment['id']] = next_id
                            
            print(f"✓ Fragment navigation links: {len(fragment_links)}")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Fragment service structure test failed: {e}")
        return False

async def test_fragment_initialization():
    """Test 2: Fragment Database Initialization"""
    logger.info("=== TEST 2: Fragment Database Initialization ===")
    
    try:
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = MVPNarrativeFragmentService(session)
            
            # Initialize fragments
            result = await service.initialize_mvp_fragments()
            
            print(f"✓ Fragments processed: {result['fragments_processed']}")
            print(f"✓ Fragments created: {result['fragments_created']}")
            print(f"✓ Fragments updated: {result['fragments_updated']}")
            
            # Check character validation
            validation_issues = []
            for validation in result['validation_results']:
                if not validation['meets_requirement']:
                    validation_issues.append({
                        'fragment_id': validation['fragment_id'],
                        'score': validation['character_score']
                    })
                    
            if validation_issues:
                print(f"⚠ Character validation issues found: {len(validation_issues)}")
                for issue in validation_issues:
                    print(f"  - {issue['fragment_id']}: {issue['score']:.1f}%")
            else:
                print("✓ All fragments meet character validation requirements (>90%)")
                
            if result['errors']:
                print(f"⚠ Errors during initialization: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"  - {error}")
                    
            return len(result['errors']) == 0
            
    except Exception as e:
        logger.error(f"✗ Fragment initialization test failed: {e}")
        return False

async def test_user_narrative_flow():
    """Test 3: User Narrative Flow and Progression"""
    logger.info("=== TEST 3: User Narrative Flow ===")
    
    try:
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = MVPNarrativeFragmentService(session)
            test_user_id = 999999  # Test user
            
            # Test getting starting fragment
            current_fragment = await service.get_user_current_fragment(test_user_id)
            if current_fragment:
                print(f"✓ Starting fragment retrieved: {current_fragment.id}")
                print(f"  - Title: {current_fragment.title}")
                print(f"  - Level: {current_fragment.storyline_level}")
                print(f"  - Tier: {current_fragment.tier_classification}")
                
                # Test user progress summary
                progress = await service.get_user_progress_summary(test_user_id)
                print(f"✓ User progress summary:")
                print(f"  - Current level: {progress['current_level']}")
                print(f"  - Current tier: {progress['current_tier_name']}")
                print(f"  - Progress: {progress['progress_percentage']:.1f}%")
                print(f"  - Completed fragments: {progress['fragments_completed']}")
                
                return True
            else:
                print("✗ Could not retrieve starting fragment")
                return False
                
    except Exception as e:
        logger.error(f"✗ User narrative flow test failed: {e}")
        return False

async def test_decision_tree_service():
    """Test 4: Decision Tree Service Functionality"""
    logger.info("=== TEST 4: Decision Tree Service ===")
    
    try:
        from services.mvp_decision_tree_service import MVPDecisionTreeService
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = MVPDecisionTreeService(session)
            test_user_id = 999999  # Test user
            
            # Test decision validation
            validation_result = await service.validate_decision(
                user_id=test_user_id,
                fragment_id='diana_l1_f1_umbral',
                choice_index=0
            )
            
            if validation_result['valid']:
                print("✓ Decision validation passed")
                print(f"  - Performance: {validation_result['performance_ms']}ms")
                print(f"  - Meets target (<500ms): {validation_result['meets_performance_target']}")
                
                # Test decision processing
                process_result = await service.process_decision_with_consequences(
                    user_id=test_user_id,
                    fragment_id='diana_l1_f1_umbral',
                    choice_index=0,
                    response_time_ms=100
                )
                
                if process_result['success']:
                    print("✓ Decision processing succeeded")
                    print(f"  - Next fragment: {process_result['next_fragment'].id if process_result['next_fragment'] else 'None'}")
                    print(f"  - Performance: {process_result['performance_ms']}ms")
                    return True
                else:
                    print(f"✗ Decision processing failed: {process_result.get('error')}")
                    return False
                    
            else:
                print(f"✗ Decision validation failed: {validation_result.get('error')}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Decision tree service test failed: {e}")
        return False

async def test_gamification_integration():
    """Test 5: Gamification Integration"""
    logger.info("=== TEST 5: Gamification Integration ===")
    
    try:
        from services.narrative_gamification_integration import NarrativeGamificationIntegration
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            integration = NarrativeGamificationIntegration(session)
            
            # Test initialization
            await integration.initialize_integration()
            print("✓ Gamification integration initialized")
            
            # Test fragment completion processing
            test_user_id = 999999
            result = await integration.process_narrative_fragment_completion(
                user_id=test_user_id,
                fragment_id='diana_l1_f1_umbral'
            )
            
            print("✓ Fragment completion processing tested")
            print(f"  - Diana response generated: {len(result['diana_response']) > 0}")
            print(f"  - Gamification results: {bool(result['gamification_results'])}")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Gamification integration test failed: {e}")
        return False

async def test_character_consistency():
    """Test 6: Character Consistency Validation"""
    logger.info("=== TEST 6: Character Consistency ===")
    
    try:
        from services.diana_character_validator import DianaCharacterValidator
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            validator = DianaCharacterValidator(session)
            
            # Test with a typical Diana text
            test_text = """💋 Bienvenido a mis dominios, querido...
            
Susurro tu nombre en los ecos de este lugar donde solo los valientes se atreven a entrar. 

¿Sientes esa electricidad en el aire? Es la promesa de todo lo que podríamos descubrir juntos..."""

            validation_result = await validator.validate_text(
                text=test_text,
                context="test_fragment"
            )
            
            print(f"✓ Character validation completed")
            print(f"  - Overall score: {validation_result.overall_score:.1f}%")
            print(f"  - Meets requirement (>90%): {validation_result.overall_score >= 90.0}")
            
            if hasattr(validation_result, 'detailed_scores'):
                print(f"  - Detailed scores available: {bool(validation_result.detailed_scores)}")
            
            return validation_result.overall_score >= 90.0
            
    except Exception as e:
        logger.error(f"✗ Character consistency test failed: {e}")
        return False

async def test_handler_integration():
    """Test 7: Handler Integration Check"""
    logger.info("=== TEST 7: Handler Integration ===")
    
    try:
        # Check if handlers are properly structured
        from handlers.diana_handler import router as diana_router
        from handlers.narrative_handlers import router as narrative_router
        
        print("✓ Diana handler router imported successfully")
        print("✓ Narrative handlers router imported successfully")
        
        # Check handler registration patterns
        diana_handlers = len([handler for handler in diana_router.handlers if handler])
        narrative_handlers = len([handler for handler in narrative_router.handlers if handler])
        
        print(f"✓ Diana router handlers: {diana_handlers}")
        print(f"✓ Narrative router handlers: {narrative_handlers}")
        
        return diana_handlers > 0 and narrative_handlers > 0
        
    except Exception as e:
        logger.error(f"✗ Handler integration test failed: {e}")
        return False

async def main():
    """Run all narrative system validation tests"""
    print("=" * 60)
    print("NARRATIVE SYSTEM VALIDATION")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Fragment Service Structure", test_fragment_service_structure),
        ("Fragment Database Initialization", test_fragment_initialization),
        ("User Narrative Flow", test_user_narrative_flow),
        ("Decision Tree Service", test_decision_tree_service),
        ("Gamification Integration", test_gamification_integration),
        ("Character Consistency", test_character_consistency),
        ("Handler Integration", test_handler_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            print(f"[{status}] {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"[ERROR] {test_name}: {e}")
            logger.error(f"Test {test_name} crashed: {e}", exc_info=True)
        
        print()
    
    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n⚠ ISSUES FOUND - Check failed tests above")
        return False
    else:
        print("\n✓ ALL TESTS PASSED - Narrative system is functional")
        return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation script crashed: {e}", exc_info=True)
        sys.exit(1)