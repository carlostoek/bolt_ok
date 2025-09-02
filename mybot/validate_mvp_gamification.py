#!/usr/bin/env python3
# validate_mvp_gamification.py
"""
MVP Gamification System Validation Script
Validates all gamification components meet MVP requirements and Diana character consistency.
"""

import asyncio
import sys
from typing import Dict, Any, List
from datetime import datetime
import json

# Import validation components
from services.point_service import POINTS_CONFIG, DIANA_REWARD_MESSAGES
from services.level_service import MVP_LEVEL_THRESHOLDS, MVP_LEVELS
from services.mvp_mission_service import MVP_MISSIONS
from services.mvp_achievement_service import MVP_ACHIEVEMENTS


class MVPGamificationValidator:
    """Comprehensive validator for MVP gamification system."""
    
    def __init__(self):
        self.validation_results = {
            "points_system": {},
            "level_system": {},
            "mission_system": {},
            "achievement_system": {},
            "character_consistency": {},
            "performance_validation": {},
            "integration_validation": {},
            "overall_score": 0,
            "errors": [],
            "warnings": []
        }
    
    def validate_points_system(self) -> Dict[str, Any]:
        """Validate MVP points calculation engine."""
        results = {"passed": True, "details": {}}
        
        # Validate MVP economic rules
        required_configs = {
            'story_fragment_completion': 10,
            'decision_made': 5,
            'daily_login': 15,
            'mission_completed': 25,
            'achievement_unlocked': 50,
            'channel_reaction': 2,
            'vip_bonus_multiplier': 1.5
        }
        
        for config_key, expected_value in required_configs.items():
            if config_key not in POINTS_CONFIG:
                results["passed"] = False
                self.validation_results["errors"].append(f"Missing points config: {config_key}")
            elif POINTS_CONFIG[config_key] != expected_value:
                results["passed"] = False
                self.validation_results["errors"].append(
                    f"Incorrect points value for {config_key}: "
                    f"expected {expected_value}, got {POINTS_CONFIG[config_key]}"
                )
            else:
                results["details"][config_key] = "✓ Correct"
        
        # Validate Diana reward messages exist
        required_message_types = ['besitos_earned', 'level_up', 'mission_completed', 'achievement_unlocked']
        for msg_type in required_message_types:
            if msg_type not in DIANA_REWARD_MESSAGES:
                results["passed"] = False
                self.validation_results["errors"].append(f"Missing Diana message type: {msg_type}")
            elif not DIANA_REWARD_MESSAGES[msg_type]:
                results["passed"] = False
                self.validation_results["errors"].append(f"Empty Diana messages for: {msg_type}")
            else:
                results["details"][f"diana_messages_{msg_type}"] = f"✓ {len(DIANA_REWARD_MESSAGES[msg_type])} messages"
        
        return results
    
    def validate_level_system(self) -> Dict[str, Any]:
        """Validate MVP level progression system."""
        results = {"passed": True, "details": {}}
        
        # Validate level count (20 levels)
        if len(MVP_LEVELS) != 20:
            results["passed"] = False
            self.validation_results["errors"].append(f"Expected 20 levels, got {len(MVP_LEVELS)}")
        else:
            results["details"]["level_count"] = "✓ 20 levels"
        
        # Validate threshold progression
        expected_thresholds = {
            1: 0, 2: 100, 3: 200, 4: 300, 5: 400,  # 100 per level
            6: 600, 7: 800, 8: 1000, 9: 1200, 10: 1400,  # 200 per level
            11: 1900, 12: 2400, 13: 2900, 14: 3400, 15: 3900,  # 500 per level
            16: 4400, 17: 4900, 18: 5400, 19: 5900, 20: 6400
        }
        
        threshold_errors = 0
        for level, expected_threshold in expected_thresholds.items():
            if level <= len(MVP_LEVEL_THRESHOLDS):
                actual_threshold = MVP_LEVEL_THRESHOLDS[level-1][1]  # level, threshold tuple
                if actual_threshold != expected_threshold:
                    results["passed"] = False
                    threshold_errors += 1
                    self.validation_results["errors"].append(
                        f"Level {level} threshold: expected {expected_threshold}, got {actual_threshold}"
                    )
        
        if threshold_errors == 0:
            results["details"]["thresholds"] = "✓ All thresholds correct"
        
        # Validate Spanish level names with seductive personality
        spanish_indicators = ["novata", "curiosa", "encantada", "seducida", "cautivada", "devotida", "misteriosa"]
        spanish_count = 0
        
        for level_id, name, min_points, reward in MVP_LEVELS[:10]:  # Check first 10
            name_lower = name.lower()
            if any(indicator in name_lower for indicator in spanish_indicators):
                spanish_count += 1
        
        if spanish_count >= 5:  # At least half should have Spanish seductive names
            results["details"]["spanish_names"] = f"✓ {spanish_count} Spanish seductive names"
        else:
            results["passed"] = False
            self.validation_results["warnings"].append(
                f"Only {spanish_count} levels have Spanish seductive names, expected more"
            )
        
        return results
    
    def validate_mission_system(self) -> Dict[str, Any]:
        """Validate MVP mission system."""
        results = {"passed": True, "details": {}}
        
        # Validate mission count (10 missions)
        if len(MVP_MISSIONS) != 10:
            results["passed"] = False
            self.validation_results["errors"].append(f"Expected 10 missions, got {len(MVP_MISSIONS)}")
        else:
            results["details"]["mission_count"] = "✓ 10 missions"
        
        # Validate required mission types
        required_mission_types = [
            'story_progress', 'decision_making', 'login_streak', 'channel_engagement',
            'vip_subscription', 'achievement_collection', 'community_engagement',
            'points_accumulation', 'level_achievement'
        ]
        
        mission_types = [m['type'] for m in MVP_MISSIONS]
        missing_types = []
        
        for required_type in required_mission_types:
            if required_type not in mission_types:
                missing_types.append(required_type)
        
        if missing_types:
            results["passed"] = False
            self.validation_results["errors"].append(f"Missing mission types: {missing_types}")
        else:
            results["details"]["mission_types"] = "✓ All required types present"
        
        # Validate Diana character consistency in mission messages
        spanish_missions = 0
        seductive_missions = 0
        
        for mission in MVP_MISSIONS:
            description = mission['description'].lower()
            completion_msg = mission['diana_completion_message'].lower()
            
            # Check for Spanish terms
            spanish_terms = ['conmigo', 'cariño', 'amor', 'mi', 'juntas', 'nuestra']
            if any(term in description + completion_msg for term in spanish_terms):
                spanish_missions += 1
            
            # Check for seductive/intimate language
            seductive_terms = ['seductora', 'íntima', 'especial', 'fasci', 'intrig', 'conmueve']
            if any(term in description + completion_msg for term in seductive_terms):
                seductive_missions += 1
        
        if spanish_missions >= 8:  # 80% should have Spanish terms
            results["details"]["spanish_character"] = f"✓ {spanish_missions}/10 missions with Spanish terms"
        else:
            self.validation_results["warnings"].append(
                f"Only {spanish_missions}/10 missions have Spanish character terms"
            )
        
        if seductive_missions >= 6:  # 60% should have seductive language
            results["details"]["seductive_character"] = f"✓ {seductive_missions}/10 missions with seductive language"
        else:
            self.validation_results["warnings"].append(
                f"Only {seductive_missions}/10 missions have seductive language"
            )
        
        return results
    
    def validate_achievement_system(self) -> Dict[str, Any]:
        """Validate MVP achievement system."""
        results = {"passed": True, "details": {}}
        
        # Validate achievement count (15 achievements)
        if len(MVP_ACHIEVEMENTS) != 15:
            results["passed"] = False
            self.validation_results["errors"].append(f"Expected 15 achievements, got {len(MVP_ACHIEVEMENTS)}")
        else:
            results["details"]["achievement_count"] = "✓ 15 achievements"
        
        # Validate rarity distribution
        rarity_counts = {}
        for achievement in MVP_ACHIEVEMENTS:
            rarity = achievement.get('rarity', 'unknown')
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        expected_rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
        for rarity in expected_rarities:
            if rarity not in rarity_counts:
                results["passed"] = False
                self.validation_results["errors"].append(f"Missing rarity tier: {rarity}")
        
        if all(rarity in rarity_counts for rarity in expected_rarities):
            results["details"]["rarity_distribution"] = f"✓ All rarities: {rarity_counts}"
        
        # Validate Diana character consistency
        intimate_achievements = 0
        spanish_achievements = 0
        
        for achievement in MVP_ACHIEVEMENTS:
            unlock_msg = achievement['diana_unlock_message'].lower()
            
            # Check for intimate language
            intimate_terms = ['mi amor', 'cariño', 'especial', 'íntima', 'corazón', 'alma', 'mía']
            if any(term in unlock_msg for term in intimate_terms):
                intimate_achievements += 1
            
            # Check for Spanish terms
            spanish_terms = ['mi', 'tu', 'nuestra', 'juntas', 'conmigo', 'amor', 'cariño']
            if any(term in unlock_msg for term in spanish_terms):
                spanish_achievements += 1
        
        if intimate_achievements >= 12:  # 80% should have intimate language
            results["details"]["intimate_language"] = f"✓ {intimate_achievements}/15 achievements with intimate language"
        else:
            self.validation_results["warnings"].append(
                f"Only {intimate_achievements}/15 achievements have intimate language"
            )
        
        return results
    
    def validate_character_consistency(self) -> Dict[str, Any]:
        """Validate Diana's character consistency across all systems."""
        results = {"passed": True, "details": {}}
        
        # Collect all Diana messages from all systems
        all_messages = []
        
        # From points system
        for msg_list in DIANA_REWARD_MESSAGES.values():
            all_messages.extend(msg_list)
        
        # From missions
        all_messages.extend([m['description'] for m in MVP_MISSIONS])
        all_messages.extend([m['diana_completion_message'] for m in MVP_MISSIONS])
        
        # From achievements
        all_messages.extend([a['diana_unlock_message'] for a in MVP_ACHIEVEMENTS])
        
        # From levels
        all_messages.extend([reward for _, _, _, reward in MVP_LEVELS if reward])
        
        # Character consistency analysis
        spanish_messages = 0
        seductive_messages = 0
        consistent_voice = 0
        
        spanish_indicators = ['mi', 'tu', 'amor', 'cariño', 'conmigo', 'juntas', 'nuestra']
        seductive_indicators = ['seductora', 'íntima', 'especial', 'fasci', 'intrig', 'mister', 'secret']
        voice_indicators = ['...', '😘', '💋', '💕', '💖', '🌹', '✨', '💎', '👑']
        
        for message in all_messages:
            message_lower = message.lower()
            
            if any(indicator in message_lower for indicator in spanish_indicators):
                spanish_messages += 1
            
            if any(indicator in message_lower for indicator in seductive_indicators):
                seductive_messages += 1
            
            if any(indicator in message for indicator in voice_indicators):
                consistent_voice += 1
        
        total_messages = len(all_messages)
        spanish_percentage = (spanish_messages / total_messages) * 100
        seductive_percentage = (seductive_messages / total_messages) * 100
        voice_percentage = (consistent_voice / total_messages) * 100
        
        # Character consistency scoring
        character_score = 0
        if spanish_percentage >= 70:  # 70% should have Spanish elements
            character_score += 30
            results["details"]["spanish_consistency"] = f"✓ {spanish_percentage:.1f}% Spanish elements"
        else:
            self.validation_results["warnings"].append(f"Spanish consistency: {spanish_percentage:.1f}% (target: 70%)")
        
        if seductive_percentage >= 40:  # 40% should have seductive elements
            character_score += 30
            results["details"]["seductive_consistency"] = f"✓ {seductive_percentage:.1f}% seductive elements"
        else:
            self.validation_results["warnings"].append(f"Seductive consistency: {seductive_percentage:.1f}% (target: 40%)")
        
        if voice_percentage >= 60:  # 60% should have emojis/voice indicators
            character_score += 40
            results["details"]["voice_consistency"] = f"✓ {voice_percentage:.1f}% consistent voice"
        else:
            self.validation_results["warnings"].append(f"Voice consistency: {voice_percentage:.1f}% (target: 60%)")
        
        results["details"]["character_score"] = f"{character_score}/100"
        if character_score < 70:
            results["passed"] = False
            self.validation_results["errors"].append(f"Character consistency score too low: {character_score}/100")
        
        return results
    
    def validate_performance_requirements(self) -> Dict[str, Any]:
        """Validate performance requirements (<500ms operations)."""
        results = {"passed": True, "details": {}}
        
        # Test calculation performance
        start_time = datetime.now()
        
        # Simulate heavy gamification calculations
        for i in range(1000):
            # Level calculations
            level = next((l for l, t in MVP_LEVEL_THRESHOLDS if i >= t), 1)
            
            # Points calculations
            points = i * POINTS_CONFIG['story_fragment_completion']
            if i % 2 == 0:  # VIP user simulation
                points *= POINTS_CONFIG['vip_bonus_multiplier']
        
        end_time = datetime.now()
        calculation_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        
        if calculation_time < 100:  # Should be much faster than 500ms requirement
            results["details"]["calculation_performance"] = f"✓ {calculation_time:.2f}ms for 1000 operations"
        else:
            results["passed"] = False
            self.validation_results["errors"].append(f"Performance too slow: {calculation_time:.2f}ms for calculations")
        
        # Validate data structure efficiency
        mission_lookup_time = datetime.now()
        for mission in MVP_MISSIONS:
            mission_id = mission['id']
        lookup_time = (datetime.now() - mission_lookup_time).total_seconds() * 1000
        
        results["details"]["data_structure_efficiency"] = f"✓ {lookup_time:.2f}ms for data access"
        
        return results
    
    def validate_integration_requirements(self) -> Dict[str, Any]:
        """Validate integration with existing systems."""
        results = {"passed": True, "details": {}}
        
        # Validate service imports work
        try:
            from services.mvp_gamification_service import MVPGamificationService
            from services.narrative_gamification_integration import NarrativeGamificationIntegration
            results["details"]["service_imports"] = "✓ All services importable"
        except ImportError as e:
            results["passed"] = False
            self.validation_results["errors"].append(f"Import error: {str(e)}")
        
        # Validate database model compatibility
        try:
            from database.models import User, Mission, Achievement, UserStats
            results["details"]["model_compatibility"] = "✓ Database models compatible"
        except ImportError as e:
            results["passed"] = False
            self.validation_results["errors"].append(f"Database model error: {str(e)}")
        
        return results
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete MVP gamification validation."""
        print("🎯 Starting MVP Gamification System Validation...")
        print("=" * 60)
        
        # Run all validation modules
        validation_modules = [
            ("Points System", self.validate_points_system),
            ("Level System", self.validate_level_system),
            ("Mission System", self.validate_mission_system),
            ("Achievement System", self.validate_achievement_system),
            ("Character Consistency", self.validate_character_consistency),
            ("Performance Requirements", self.validate_performance_requirements),
            ("Integration Requirements", self.validate_integration_requirements)
        ]
        
        passed_modules = 0
        total_modules = len(validation_modules)
        
        for module_name, validation_func in validation_modules:
            print(f"\n🔍 Validating {module_name}...")
            
            try:
                module_results = validation_func()
                self.validation_results[module_name.lower().replace(" ", "_")] = module_results
                
                if module_results["passed"]:
                    print(f"✅ {module_name}: PASSED")
                    passed_modules += 1
                    
                    # Show details
                    for detail_key, detail_value in module_results["details"].items():
                        print(f"   {detail_value}")
                else:
                    print(f"❌ {module_name}: FAILED")
                    
            except Exception as e:
                print(f"💥 {module_name}: ERROR - {str(e)}")
                self.validation_results["errors"].append(f"{module_name} validation error: {str(e)}")
        
        # Calculate overall score
        self.validation_results["overall_score"] = (passed_modules / total_modules) * 100
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"Modules Passed: {passed_modules}/{total_modules}")
        print(f"Overall Score: {self.validation_results['overall_score']:.1f}%")
        
        if self.validation_results["errors"]:
            print(f"\n❌ Errors ({len(self.validation_results['errors'])}):")
            for error in self.validation_results["errors"]:
                print(f"   • {error}")
        
        if self.validation_results["warnings"]:
            print(f"\n⚠️  Warnings ({len(self.validation_results['warnings'])}):")
            for warning in self.validation_results["warnings"]:
                print(f"   • {warning}")
        
        # Final assessment
        if self.validation_results["overall_score"] >= 95:
            print("\n🏆 EXCELLENT: MVP Gamification System meets all requirements!")
            print("   Diana's character consistency: MAINTAINED")
            print("   Performance requirements: MET")
            print("   Integration requirements: SATISFIED")
        elif self.validation_results["overall_score"] >= 80:
            print("\n✅ GOOD: MVP Gamification System is ready with minor improvements needed")
        else:
            print("\n❌ NEEDS WORK: MVP Gamification System requires significant improvements")
        
        return self.validation_results


def main():
    """Main validation entry point."""
    validator = MVPGamificationValidator()
    
    try:
        results = validator.run_validation()
        
        # Save results to file
        with open("mvp_gamification_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Detailed report saved to: mvp_gamification_validation_report.json")
        
        # Exit with appropriate code
        if results["overall_score"] >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Needs improvement
            
    except Exception as e:
        print(f"\n💥 VALIDATION FAILED: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()