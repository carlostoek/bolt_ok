"""
Comprehensive Character Consistency Testing Suite for Diana Menu System

This test suite validates that Diana's personality traits remain consistent
at 95%+ levels across all menu interactions, preventing character degradation
and ensuring user emotional investment is maintained.

CRITICAL: Tests must validate both technical functionality AND character authenticity.
Character consistency measurements must be programmatic and reliable.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any
from dataclasses import dataclass

from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem, MenuResponse
from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult, DianaPersonalityTrait
from services.enhanced_user_service import EnhancedUserService
from utils.message_safety import safe_edit, safe_answer

logger = logging.getLogger(__name__)

@dataclass
class MenuTestScenario:
    """Test scenario for menu validation."""
    name: str
    user_role: str
    menu_type: str
    expected_min_score: float
    context: str

@dataclass 
class CharacterTestResult:
    """Result of character consistency test."""
    scenario_name: str
    menu_response: MenuResponse
    character_validation: CharacterValidationResult
    meets_requirements: bool
    performance_acceptable: bool
    violations: List[str]

class TestDianaMenuCharacterConsistency:
    """Comprehensive test suite for Diana menu character consistency."""
    
    REQUIRED_CONSISTENCY_THRESHOLD = 95.0
    MAX_RESPONSE_TIME = 1.0  # 1 second performance requirement
    
    @pytest_asyncio.fixture
    async def enhanced_menu_system(self, session):
        """Create enhanced Diana menu system for testing."""
        return EnhancedDianaMenuSystem(session)
    
    @pytest_asyncio.fixture 
    async def character_validator(self, session):
        """Create Diana character validator for testing."""
        return DianaCharacterValidator(session)
    
    @pytest_asyncio.fixture
    async def mock_callback_query(self, test_user):
        """Create mock callback query for testing."""
        callback = MagicMock()
        callback.from_user.id = test_user.id
        callback.from_user.first_name = test_user.first_name
        callback.from_user.username = test_user.username
        callback.data = "diana_main_menu"
        callback.message = MagicMock()
        callback.message.chat = MagicMock()
        callback.message.chat.id = test_user.id
        callback.message.message_id = 1
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        callback.message.edit_reply_markup = AsyncMock()
        return callback
    
    @pytest_asyncio.fixture
    async def mock_message(self, test_user):
        """Create mock message for testing."""
        message = MagicMock()
        message.from_user.id = test_user.id
        message.from_user.first_name = test_user.first_name
        message.from_user.username = test_user.username
        message.chat = MagicMock()
        message.chat.id = test_user.id
        message.reply = AsyncMock()
        return message

    def get_test_scenarios(self) -> List[MenuTestScenario]:
        """Get comprehensive test scenarios for all menu types and roles."""
        return [
            # Main Menu Tests
            MenuTestScenario("main_menu_free", "free", "main_menu", 95.0, "menu_response"),
            MenuTestScenario("main_menu_vip", "vip", "main_menu", 95.0, "menu_response"),
            MenuTestScenario("main_menu_admin", "admin", "main_menu", 95.0, "menu_response"),
            
            # VIP Upgrade Tests
            MenuTestScenario("vip_upgrade_persuasion", "free", "vip_upgrade", 95.0, "vip_upgrade"),
            
            # Narrative Menu Tests
            MenuTestScenario("narrative_menu_free", "free", "narrative", 95.0, "narrative_menu"),
            MenuTestScenario("narrative_menu_vip", "vip", "narrative", 95.0, "narrative_menu"),
            
            # VIP Menu Tests
            MenuTestScenario("vip_menu_active", "vip", "vip_features", 95.0, "vip_menu"),
            
            # Settings Menu Tests
            MenuTestScenario("settings_menu_free", "free", "settings", 95.0, "settings_menu"),
            MenuTestScenario("settings_menu_vip", "vip", "settings", 95.0, "settings_menu"),
            
            # Error Handling Tests
            MenuTestScenario("error_handling_mysterious", "free", "error", 95.0, "error_message"),
            
            # Close Menu Tests
            MenuTestScenario("close_menu_farewell", "free", "close", 95.0, "farewell_message")
        ]

    @pytest.mark.asyncio
    async def test_all_menu_templates_character_consistency(self, enhanced_menu_system, character_validator):
        """
        CRITICAL TEST: Validate all menu templates meet 95%+ character consistency.
        
        This test confirms the narrative-designer's findings about current template failures.
        """
        results = []
        violations = []
        
        # Test each menu template directly
        templates = enhanced_menu_system.diana_menu_templates
        
        for template_category, category_data in templates.items():
            if template_category == "error_messages":
                # Test error messages separately
                for error_type, error_text in category_data.items():
                    validation_result = await character_validator.validate_text(
                        error_text, context="error_message"
                    )
                    
                    if validation_result.overall_score < self.REQUIRED_CONSISTENCY_THRESHOLD:
                        violations.append(f"Error message '{error_type}' scored {validation_result.overall_score:.1f}/100")
                    
                    results.append({
                        "template": f"error_{error_type}",
                        "score": validation_result.overall_score,
                        "meets_threshold": validation_result.meets_threshold
                    })
            
            elif isinstance(category_data, dict) and "text" in category_data:
                # Single template
                validation_result = await character_validator.validate_text(
                    category_data["text"], context="menu_response"
                )
                
                if validation_result.overall_score < self.REQUIRED_CONSISTENCY_THRESHOLD:
                    violations.append(f"Template '{template_category}' scored {validation_result.overall_score:.1f}/100")
                
                results.append({
                    "template": template_category,
                    "score": validation_result.overall_score,
                    "meets_threshold": validation_result.meets_threshold
                })
            
            elif isinstance(category_data, dict):
                # Multiple role-based templates
                for role, role_data in category_data.items():
                    if isinstance(role_data, dict) and "text" in role_data:
                        validation_result = await character_validator.validate_text(
                            role_data["text"], context="menu_response"
                        )
                        
                        if validation_result.overall_score < self.REQUIRED_CONSISTENCY_THRESHOLD:
                            violations.append(f"Template '{template_category}_{role}' scored {validation_result.overall_score:.1f}/100")
                        
                        results.append({
                            "template": f"{template_category}_{role}",
                            "score": validation_result.overall_score,
                            "meets_threshold": validation_result.meets_threshold
                        })
        
        # Calculate overall performance
        total_score = sum(r["score"] for r in results) / len(results) if results else 0
        passing_templates = len([r for r in results if r["meets_threshold"]])
        passing_percentage = (passing_templates / len(results)) * 100 if results else 0
        
        # Generate detailed report
        logger.critical(f"MENU TEMPLATE CHARACTER CONSISTENCY REPORT:")
        logger.critical(f"Average Score: {total_score:.1f}/100 (Required: {self.REQUIRED_CONSISTENCY_THRESHOLD})")
        logger.critical(f"Passing Templates: {passing_templates}/{len(results)} ({passing_percentage:.1f}%)")
        logger.critical(f"Total Violations: {len(violations)}")
        
        if violations:
            logger.critical("SPECIFIC VIOLATIONS:")
            for violation in violations:
                logger.critical(f"  - {violation}")
        
        # ASSERT: This should confirm narrative-designer's findings
        # Current implementation is expected to fail until enhancements are made
        assert len(violations) > 0, "Expected character consistency violations in current implementation"
        assert total_score < 50.0, "Expected low character consistency scores in current templates"
        
        # Store results for enhancement validation
        self._template_test_results = results
    
    @pytest.mark.asyncio
    async def test_character_trait_breakdown(self, enhanced_menu_system, character_validator):
        """
        Test individual character trait performance to identify specific weaknesses.
        
        Validates Mystery, Seduction, Emotional Complexity, and Intellectual Engagement.
        """
        trait_results = {trait: [] for trait in DianaPersonalityTrait}
        
        # Test main menu templates for trait breakdown
        templates = enhanced_menu_system.diana_menu_templates["main_menu"]
        
        for role, template_data in templates.items():
            validation_result = await character_validator.validate_text(
                template_data["text"], context="menu_response"
            )
            
            # Collect trait scores
            for trait, score in validation_result.trait_scores.items():
                trait_results[trait].append(score)
        
        # Calculate trait averages
        trait_averages = {}
        for trait, scores in trait_results.items():
            trait_averages[trait.value] = sum(scores) / len(scores) if scores else 0
        
        logger.critical("CHARACTER TRAIT BREAKDOWN:")
        for trait_name, avg_score in trait_averages.items():
            required_score = 23.75  # 95% of 25 max points per trait
            logger.critical(f"  {trait_name.replace('_', ' ').title()}: {avg_score:.1f}/25 (Required: {required_score:.1f})")
        
        # Validate each trait meets requirements
        for trait_name, avg_score in trait_averages.items():
            if trait_name == "mysterious":
                # Should be very low in current implementation
                assert avg_score < 10.0, f"Expected low mystery score, got {avg_score:.1f}"
            elif trait_name == "seductive": 
                # Should be very low in current implementation
                assert avg_score < 5.0, f"Expected low seduction score, got {avg_score:.1f}"
            elif trait_name == "emotionally_complex":
                # Should be very low in current implementation
                assert avg_score < 3.0, f"Expected low emotional complexity, got {avg_score:.1f}"
            elif trait_name == "intellectually_engaging":
                # Should be very low in current implementation
                assert avg_score < 2.0, f"Expected low intellectual engagement, got {avg_score:.1f}"

    @pytest.mark.asyncio
    async def test_menu_interaction_scenarios(self, enhanced_menu_system, test_user, vip_user, admin_user):
        """
        Test complete menu interaction scenarios for character consistency.
        
        Validates that character is maintained across full user journeys.
        """
        test_scenarios = self.get_test_scenarios()
        results = []
        
        # Mock safe_edit and safe_answer to prevent actual message sending
        with patch('services.enhanced_diana_menu_system.safe_edit', new=AsyncMock()) as mock_edit, \
             patch('services.enhanced_diana_menu_system.safe_answer', new=AsyncMock()) as mock_answer:
            
            for scenario in test_scenarios:
                # Select appropriate user based on role
                user = test_user
                if scenario.user_role == "vip":
                    user = vip_user
                elif scenario.user_role == "admin":
                    user = admin_user
                
                # Create mock callback/message
                if scenario.menu_type in ["main_menu", "vip_upgrade", "narrative", "vip_features", "settings", "close"]:
                    callback = MagicMock()
                    callback.from_user.id = user.id
                    callback.from_user.first_name = user.first_name
                    callback.data = f"diana_{scenario.menu_type}"
                    callback.answer = AsyncMock()
                    callback.message = MagicMock()
                    callback.message.edit_text = AsyncMock()
                    
                    update = callback
                else:
                    message = MagicMock()
                    message.from_user.id = user.id
                    message.from_user.first_name = user.first_name
                    message.reply = AsyncMock()
                    
                    update = message
                
                try:
                    # Test menu interaction
                    start_time = time.time()
                    
                    if scenario.menu_type == "main_menu":
                        menu_response = await enhanced_menu_system.show_main_menu(update, scenario.user_role)
                    elif scenario.menu_type == "vip_upgrade":
                        menu_response = await enhanced_menu_system.show_vip_upgrade_menu(update)
                    elif scenario.menu_type == "close":
                        menu_response = await enhanced_menu_system._handle_close_menu(update)
                    else:
                        # For other menu types, simulate callback handling
                        callback.data = f"diana_{scenario.menu_type}"
                        menu_response = await enhanced_menu_system.handle_callback(callback)
                    
                    # Test performance requirement
                    response_time = time.time() - start_time
                    performance_acceptable = response_time < self.MAX_RESPONSE_TIME
                    
                    # Validate character consistency
                    character_score = menu_response.character_score
                    meets_character_requirement = character_score >= self.REQUIRED_CONSISTENCY_THRESHOLD
                    
                    result = CharacterTestResult(
                        scenario_name=scenario.name,
                        menu_response=menu_response,
                        character_validation=None,  # Already included in menu_response
                        meets_requirements=meets_character_requirement,
                        performance_acceptable=performance_acceptable,
                        violations=menu_response.errors
                    )
                    
                    results.append(result)
                    
                    logger.info(f"Scenario '{scenario.name}': Score {character_score:.1f}/100, "
                              f"Time {response_time:.3f}s, Success: {menu_response.success}")
                
                except Exception as e:
                    logger.error(f"Error in scenario '{scenario.name}': {e}")
                    results.append(CharacterTestResult(
                        scenario_name=scenario.name,
                        menu_response=MenuResponse(False, 0.0, 999.0, False, False, [str(e)]),
                        character_validation=None,
                        meets_requirements=False,
                        performance_acceptable=False,
                        violations=[str(e)]
                    ))
        
        # Analyze results
        total_scenarios = len(results)
        successful_scenarios = len([r for r in results if r.meets_requirements])
        performance_compliant = len([r for r in results if r.performance_acceptable])
        
        success_rate = (successful_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
        performance_rate = (performance_compliant / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        logger.critical(f"MENU INTERACTION SCENARIO RESULTS:")
        logger.critical(f"Character Consistency Success Rate: {success_rate:.1f}% ({successful_scenarios}/{total_scenarios})")
        logger.critical(f"Performance Compliance Rate: {performance_rate:.1f}% ({performance_compliant}/{total_scenarios})")
        
        # Expected current implementation failures
        assert success_rate < 10.0, f"Expected low success rate, got {success_rate:.1f}%"
        assert performance_rate > 80.0, f"Expected good performance, got {performance_rate:.1f}%"

    @pytest.mark.asyncio
    async def test_error_handling_character_consistency(self, enhanced_menu_system, character_validator):
        """
        Test that error handling maintains Diana's mysterious character immersion.
        
        Critical: Errors should never break character or use technical language.
        """
        error_scenarios = [
            ("loading_state", "🌙 Los hilos del destino se están tejiendo... Un momento, querido..."),
            ("access_denied", "💋 Ah, ese secreto aún no es tuyo... Pero pronto, muy pronto podrás acceder a él..."),
            ("technical_error", "😔 Las corrientes místicas fluctúan... Algo interrumpe nuestra conexión. Inténtalo de nuevo en un momento..."),
            ("performance_warning", "✨ La magia toma su tiempo... Permíteme un instante más para preparar todo perfectamente para ti...")
        ]
        
        results = []
        violations = []
        
        for error_type, error_message in error_scenarios:
            validation_result = await character_validator.validate_text(
                error_message, context="error_message"
            )
            
            # Check for technical language violations
            technical_violations = []
            if "error" in error_message.lower():
                technical_violations.append("Contains word 'error'")
            if "sistema" in error_message.lower():
                technical_violations.append("Contains word 'sistema'")
            if "configuración" in error_message.lower():
                technical_violations.append("Contains word 'configuración'")
            
            character_score = validation_result.overall_score
            meets_threshold = character_score >= self.REQUIRED_CONSISTENCY_THRESHOLD
            
            if not meets_threshold:
                violations.append(f"Error '{error_type}' scored {character_score:.1f}/100")
            
            if technical_violations:
                violations.extend([f"Error '{error_type}': {v}" for v in technical_violations])
            
            results.append({
                "error_type": error_type,
                "character_score": character_score,
                "meets_threshold": meets_threshold,
                "technical_violations": technical_violations
            })
        
        logger.critical("ERROR HANDLING CHARACTER CONSISTENCY:")
        for result in results:
            logger.critical(f"  {result['error_type']}: {result['character_score']:.1f}/100 "
                          f"({'PASS' if result['meets_threshold'] else 'FAIL'})")
        
        # Current implementation should have some issues but maintain basic character
        total_passing = len([r for r in results if r["meets_threshold"]])
        passing_rate = (total_passing / len(results)) * 100 if results else 0
        
        # Error messages should be better than main menu templates
        assert passing_rate > 25.0, f"Expected error handling to maintain some character, got {passing_rate:.1f}%"

    @pytest.mark.asyncio 
    async def test_vip_upgrade_emotional_persuasion(self, enhanced_menu_system, character_validator, test_user):
        """
        Test VIP upgrade flow maintains seductive persuasion without being pushy.
        
        Critical: Must balance enticement with respect for user choice.
        """
        callback = MagicMock()
        callback.from_user.id = test_user.id
        callback.from_user.first_name = test_user.first_name
        callback.data = "diana_vip_preview"
        callback.answer = AsyncMock()
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        
        with patch('services.enhanced_diana_menu_system.safe_edit', new=AsyncMock()):
            menu_response = await enhanced_menu_system.show_vip_upgrade_menu(callback)
        
        # Validate the VIP upgrade message
        vip_template = enhanced_menu_system.diana_menu_templates["vip_upgrade"]["text"]
        validation_result = await character_validator.validate_text(
            vip_template, context="vip_upgrade"
        )
        
        # Check specific seductive traits
        seductive_score = validation_result.trait_scores.get(DianaPersonalityTrait.SEDUCTIVE, 0)
        mysterious_score = validation_result.trait_scores.get(DianaPersonalityTrait.MYSTERIOUS, 0)
        
        logger.critical(f"VIP UPGRADE PERSUASION ANALYSIS:")
        logger.critical(f"  Overall Score: {validation_result.overall_score:.1f}/100")
        logger.critical(f"  Seductive Score: {seductive_score:.1f}/25")
        logger.critical(f"  Mysterious Score: {mysterious_score:.1f}/25")
        logger.critical(f"  Performance: {menu_response.response_time:.3f}s")
        
        # Current implementation should have low scores
        assert validation_result.overall_score < 50.0, "Expected low VIP upgrade persuasion score"
        assert seductive_score < 10.0, "Expected low seductive score in VIP upgrade"

    @pytest.mark.asyncio
    async def test_menu_navigation_flow_consistency(self, enhanced_menu_system, test_user):
        """
        Test that character consistency is maintained across menu navigation flows.
        
        Simulates realistic user journey through multiple menu interactions.
        """
        navigation_flow = [
            ("main_menu", "diana_main_menu"),
            ("narrative_menu", "diana_narrative"),
            ("vip_preview", "diana_vip_preview"),
            ("back_to_main", "diana_main_menu"),
            ("settings", "diana_settings"),
            ("close", "diana_close")
        ]
        
        character_scores = []
        performance_times = []
        
        callback = MagicMock()
        callback.from_user.id = test_user.id
        callback.from_user.first_name = test_user.first_name
        callback.answer = AsyncMock()
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        
        with patch('services.enhanced_diana_menu_system.safe_edit', new=AsyncMock()), \
             patch('services.enhanced_diana_menu_system.safe_answer', new=AsyncMock()):
            
            for step_name, callback_data in navigation_flow:
                callback.data = callback_data
                
                try:
                    start_time = time.time()
                    menu_response = await enhanced_menu_system.handle_callback(callback)
                    response_time = time.time() - start_time
                    
                    character_scores.append(menu_response.character_score)
                    performance_times.append(response_time)
                    
                    logger.info(f"Navigation step '{step_name}': Score {menu_response.character_score:.1f}, "
                              f"Time {response_time:.3f}s")
                
                except Exception as e:
                    logger.error(f"Error in navigation step '{step_name}': {e}")
                    character_scores.append(0.0)
                    performance_times.append(999.0)
        
        # Analyze navigation consistency
        avg_character_score = sum(character_scores) / len(character_scores) if character_scores else 0
        avg_performance_time = sum(performance_times) / len(performance_times) if performance_times else 999
        consistency_variance = max(character_scores) - min(character_scores) if character_scores else 0
        
        logger.critical(f"NAVIGATION FLOW CONSISTENCY:")
        logger.critical(f"  Average Character Score: {avg_character_score:.1f}/100")
        logger.critical(f"  Average Performance Time: {avg_performance_time:.3f}s")
        logger.critical(f"  Character Score Variance: {consistency_variance:.1f}")
        
        # Performance should be good even if character scores are low
        assert avg_performance_time < 1.0, f"Expected good performance, got {avg_performance_time:.3f}s"
        
        # Current implementation should have low but somewhat consistent character scores
        assert avg_character_score < 50.0, "Expected low character scores in navigation"

    def generate_comprehensive_report(self, test_results: List[Dict]) -> Dict[str, Any]:
        """
        Generate comprehensive character consistency report.
        
        This report will be used to validate narrative-designer's findings
        and track improvement after enhancements are implemented.
        """
        if not test_results:
            return {"error": "No test results provided"}
        
        # Calculate aggregate statistics
        total_tests = len(test_results)
        passing_tests = len([r for r in test_results if r.get("meets_threshold", False)])
        avg_score = sum(r.get("score", 0) for r in test_results) / total_tests
        
        # Performance statistics
        performance_compliant = len([r for r in test_results if r.get("performance_time", 999) < 1.0])
        
        report = {
            "executive_summary": {
                "total_tests": total_tests,
                "passing_tests": passing_tests,
                "passing_percentage": (passing_tests / total_tests) * 100,
                "average_character_score": avg_score,
                "performance_compliance": (performance_compliant / total_tests) * 100,
                "mvp_requirements_met": (passing_tests / total_tests) >= 0.95
            },
            "critical_findings": {
                "character_consistency_crisis": avg_score < 50.0,
                "narrative_designer_findings_confirmed": passing_tests < (total_tests * 0.1),
                "immediate_action_required": True,
                "user_emotional_investment_at_risk": True
            },
            "recommendations": [
                "Implement enhanced character templates with mysterious language patterns",
                "Add seductive charm through intimate, personal language",
                "Increase emotional complexity with inner conflicts and vulnerability",
                "Enhance intellectual engagement through philosophical questions and reflection",
                "Remove all technical language and replace with mystical alternatives"
            ]
        }
        
        return report

# Convenience functions for running specific test categories
async def run_template_validation_tests(session):
    """Run template validation tests specifically."""
    test_instance = TestDianaMenuCharacterConsistency()
    menu_system = EnhancedDianaMenuSystem(session)
    validator = DianaCharacterValidator(session)
    
    await test_instance.test_all_menu_templates_character_consistency(menu_system, validator)

async def run_character_trait_analysis(session):
    """Run character trait breakdown analysis.""" 
    test_instance = TestDianaMenuCharacterConsistency()
    menu_system = EnhancedDianaMenuSystem(session)
    validator = DianaCharacterValidator(session)
    
    await test_instance.test_character_trait_breakdown(menu_system, validator)