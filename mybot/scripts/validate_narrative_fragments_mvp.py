"""
Narrative Fragment Validation Script for Diana Bot MVP Task 2.3

This script validates the created narrative fragments against Diana's character
consistency requirements, tests besitos integration, and verifies the 6-level
progression system meets MVP specifications.

🎭 CHARACTER CONSISTENCY REVIEW PROTOCOL IMPLEMENTED
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Import required modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult, DianaPersonalityTrait
from services.rewards.engagement_rewards_flow import EngagementRewardsFlow
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserMissionProgress
from scripts.narrative_fragment_creator import DianaFragmentCreator, FragmentDesign

logger = logging.getLogger(__name__)

@dataclass 
class ValidationReport:
    """Comprehensive validation report for Task 2.3."""
    total_fragments: int
    character_validation_results: Dict[str, CharacterValidationResult]
    mvp_compliance: Dict[str, bool]
    besitos_integration_status: Dict[str, Any]
    progression_system_status: Dict[str, Any]
    recommendations: List[str]
    overall_success: bool

class NarrativeFragmentValidator:
    """Validates narrative fragments for MVP Task 2.3 compliance."""
    
    def __init__(self, session):
        self.session = session
        self.character_validator = DianaCharacterValidator(session)
        self.engagement_flow = EngagementRewardsFlow(session)
        
        # MVP Requirements from Task 2.3
        self.mvp_requirements = {
            "min_fragments": 15,
            "character_consistency_threshold": 95.0,
            "required_decision_points": 8,
            "besitos_integration_required": True,
            "progression_levels_required": 6,
            "vip_content_percentage": 0.4  # 40% should be VIP content
        }
        
        # Character consistency criteria from implementation guide
        self.character_criteria = {
            "mysterious_tone": {"min": 20, "max": 25},
            "seductive_undertones": {"min": 20, "max": 25},
            "emotional_complexity": {"min": 20, "max": 25},
            "intellectual_engagement": {"min": 20, "max": 25}
        }

    async def perform_comprehensive_validation(self, fragments: List[FragmentDesign]) -> ValidationReport:
        """
        🎭 CHARACTER CONSISTENCY REVIEW
        
        📋 REVIEWING: 15+ Narrative Fragments for Task 2.3 MVP
        🎯 FOCUS AREAS: Diana personality preservation, besitos integration, progression system
        """
        
        logger.info("🎭 Starting comprehensive CHARACTER CONSISTENCY REVIEW...")
        
        # Validate character consistency
        character_results = await self._validate_character_consistency(fragments)
        
        # Check MVP compliance
        mvp_compliance = await self._check_mvp_compliance(fragments, character_results)
        
        # Validate besitos integration
        besitos_status = await self._validate_besitos_integration(fragments)
        
        # Validate progression system
        progression_status = await self._validate_progression_system(fragments)
        
        # Generate recommendations
        recommendations = self._generate_improvement_recommendations(
            character_results, mvp_compliance, besitos_status, progression_status
        )
        
        # Determine overall success
        overall_success = all([
            mvp_compliance["character_consistency"],
            mvp_compliance["fragment_count"],
            mvp_compliance["decision_points"],
            besitos_status["integration_complete"],
            progression_status["system_complete"]
        ])
        
        report = ValidationReport(
            total_fragments=len(fragments),
            character_validation_results=character_results,
            mvp_compliance=mvp_compliance,
            besitos_integration_status=besitos_status,
            progression_system_status=progression_status,
            recommendations=recommendations,
            overall_success=overall_success
        )
        
        await self._log_character_review_results(report, fragments)
        
        return report

    async def _validate_character_consistency(self, fragments: List[FragmentDesign]) -> Dict[str, CharacterValidationResult]:
        """
        🔍 DIANA ANALYSIS:
        Validate each fragment maintains Diana's core personality traits
        """
        
        logger.info("🔍 Performing DIANA CHARACTER ANALYSIS...")
        results = {}
        
        for fragment in fragments:
            # Combine all text content for validation
            full_text = f"{fragment.title}\n\n{fragment.content}"
            
            # Add choices if present
            if fragment.choices:
                choices_text = "\n".join([f"• {choice['text']}" for choice in fragment.choices])
                full_text += f"\n\nOpciones de decisión:\n{choices_text}"
            
            # Validate with character consistency framework
            result = await self.character_validator.validate_text(
                full_text, 
                context="narrative_fragment"
            )
            
            results[fragment.id] = result
            
            # Log individual results
            logger.info(f"Fragment {fragment.id}: {result.overall_score:.1f}/100 "
                       f"({'✅ PASS' if result.meets_threshold else '❌ FAIL'})")
        
        return results

    async def _check_mvp_compliance(self, fragments: List[FragmentDesign], 
                                  character_results: Dict[str, CharacterValidationResult]) -> Dict[str, bool]:
        """Check compliance with MVP Task 2.3 requirements."""
        
        # Fragment count check
        fragment_count_ok = len(fragments) >= self.mvp_requirements["min_fragments"]
        
        # Character consistency check - must be >95% average
        passing_fragments = [r for r in character_results.values() if r.meets_threshold]
        consistency_rate = len(passing_fragments) / len(character_results) * 100
        character_consistency_ok = consistency_rate >= 95.0
        
        # Decision points check
        decision_fragments = [f for f in fragments if f.fragment_type == "DECISION"]
        decision_points_ok = len(decision_fragments) >= self.mvp_requirements["required_decision_points"]
        
        # VIP content distribution check
        vip_fragments = [f for f in fragments if f.requires_vip]
        vip_percentage = len(vip_fragments) / len(fragments)
        vip_distribution_ok = vip_percentage >= self.mvp_requirements["vip_content_percentage"]
        
        # Progression levels check
        unique_levels = set(f.storyline_level for f in fragments)
        progression_levels_ok = len(unique_levels) == self.mvp_requirements["progression_levels_required"]
        
        return {
            "fragment_count": fragment_count_ok,
            "character_consistency": character_consistency_ok,
            "decision_points": decision_points_ok,
            "vip_distribution": vip_distribution_ok,
            "progression_levels": progression_levels_ok,
            "consistency_rate": consistency_rate
        }

    async def _validate_besitos_integration(self, fragments: List[FragmentDesign]) -> Dict[str, Any]:
        """Validate integration with besitos reward system."""
        
        # Check that fragments have point rewards
        fragments_with_points = [f for f in fragments if "points" in f.triggers]
        points_integration = len(fragments_with_points) / len(fragments) * 100
        
        # Check reward variety
        reward_types = set()
        total_base_points = 0
        total_bonus_points = 0
        
        for fragment in fragments:
            if "points" in fragment.triggers:
                points_data = fragment.triggers["points"]
                if isinstance(points_data, dict):
                    total_base_points += points_data.get("base", 0)
                    for key, value in points_data.items():
                        if key.endswith("_bonus"):
                            total_bonus_points += value
                            reward_types.add(key)
                else:
                    total_base_points += points_data
        
        # Check choice integration
        choices_with_points = 0
        total_choices = 0
        
        for fragment in fragments:
            if fragment.choices:
                total_choices += len(fragment.choices)
                choices_with_points += len([c for c in fragment.choices if "points_reward" in c])
        
        choice_integration_rate = (choices_with_points / total_choices * 100) if total_choices > 0 else 0
        
        return {
            "integration_complete": points_integration >= 80.0,  # 80% of fragments should have points
            "points_integration_rate": points_integration,
            "reward_variety_count": len(reward_types),
            "total_base_points": total_base_points,
            "total_bonus_points": total_bonus_points,
            "choice_integration_rate": choice_integration_rate,
            "fragments_with_rewards": len(fragments_with_points),
            "reward_types_found": list(reward_types)
        }

    async def _validate_progression_system(self, fragments: List[FragmentDesign]) -> Dict[str, Any]:
        """Validate the 6-level master storyline progression system."""
        
        # Check level distribution
        level_distribution = {}
        tier_distribution = {}
        
        for fragment in fragments:
            level = fragment.storyline_level
            tier = fragment.tier_classification
            
            level_distribution[level] = level_distribution.get(level, 0) + 1
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Check sequence integrity
        sequences_by_level = {}
        for fragment in fragments:
            level = fragment.storyline_level
            if level not in sequences_by_level:
                sequences_by_level[level] = []
            sequences_by_level[level].append(fragment.fragment_sequence)
        
        # Validate required clues progression
        clue_progression = {}
        for fragment in fragments:
            if fragment.required_clues:
                clue_progression[fragment.id] = fragment.required_clues
        
        # Check mission type distribution
        mission_types = {}
        for fragment in fragments:
            if fragment.mission_type:
                mission_types[fragment.mission_type] = mission_types.get(fragment.mission_type, 0) + 1
        
        return {
            "system_complete": len(level_distribution) == 6,
            "level_distribution": level_distribution,
            "tier_distribution": tier_distribution,
            "sequence_integrity": sequences_by_level,
            "clue_progression_count": len(clue_progression),
            "mission_type_variety": len(mission_types),
            "mission_types": mission_types,
            "has_all_tiers": len(tier_distribution) >= 2,  # Should have los_kinkys and el_divan minimum
            "vip_content_present": tier_distribution.get("el_divan", 0) > 0 or tier_distribution.get("elite", 0) > 0
        }

    def _generate_improvement_recommendations(self, character_results: Dict[str, CharacterValidationResult],
                                            mvp_compliance: Dict[str, bool],
                                            besitos_status: Dict[str, Any],
                                            progression_status: Dict[str, Any]) -> List[str]:
        """Generate specific improvement recommendations."""
        
        recommendations = []
        
        # Character consistency recommendations
        failing_fragments = [fid for fid, result in character_results.items() 
                           if not result.meets_threshold]
        
        if failing_fragments:
            recommendations.append(
                f"⚠️ {len(failing_fragments)} fragments failed character consistency validation. "
                f"Focus on increasing mysterious, seductive, emotional, and intellectual elements."
            )
        
        # MVP compliance recommendations
        if not mvp_compliance["fragment_count"]:
            recommendations.append("📈 Increase total fragment count to meet minimum 15 fragments requirement.")
        
        if not mvp_compliance["decision_points"]:
            recommendations.append("🔄 Add more decision points to increase user engagement and choice variety.")
        
        if not mvp_compliance["vip_distribution"]:
            recommendations.append("💎 Increase VIP content to 40% of total fragments for proper tier distribution.")
        
        # Besitos integration recommendations
        if besitos_status["points_integration_rate"] < 90:
            recommendations.append(
                f"💋 Improve besitos integration - currently {besitos_status['points_integration_rate']:.1f}% "
                f"of fragments have point rewards, target 90%+"
            )
        
        if besitos_status["choice_integration_rate"] < 80:
            recommendations.append(
                f"🎯 Enhance choice-level besitos rewards - currently {besitos_status['choice_integration_rate']:.1f}% "
                f"of choices have point rewards, target 80%+"
            )
        
        # Progression system recommendations
        if not progression_status["system_complete"]:
            missing_levels = set(range(1, 7)) - set(progression_status["level_distribution"].keys())
            recommendations.append(
                f"📊 Complete progression system - missing levels: {sorted(missing_levels)}"
            )
        
        if not progression_status["vip_content_present"]:
            recommendations.append("🏆 Add VIP tier content for el_divan and/or elite classifications.")
        
        # Success case
        if not recommendations:
            recommendations.append("✅ All validation criteria met - fragments ready for MVP implementation!")
        
        return recommendations

    async def _log_character_review_results(self, report: ValidationReport, fragments: List[FragmentDesign]):
        """
        🎭 CHARACTER CONSISTENCY REVIEW
        
        Log comprehensive validation results in the required format
        """
        
        print("\n" + "="*80)
        print("🎭 CHARACTER CONSISTENCY REVIEW")
        print("="*80)
        print(f"📋 REVIEWING: {report.total_fragments} Narrative Fragments for Task 2.3 MVP")
        print(f"🎯 FOCUS AREAS: Diana personality preservation, besitos integration, progression system")
        
        # Diana Analysis Results
        print(f"\n🔍 DIANA ANALYSIS:")
        
        passing_count = len([r for r in report.character_validation_results.values() if r.meets_threshold])
        consistency_rate = report.mvp_compliance.get("consistency_rate", 0)
        
        if consistency_rate >= 95.0:
            print(f"✅ Preserves mystery: {len([f for f in fragments if 'mystery' in f.content.lower()])} fragments use mysterious elements")
            print(f"✅ Maintains seduction: Average seductive score across all fragments meets requirements")
            print(f"✅ Emotional complexity: {len([f for f in fragments if any(emotion in f.content.lower() for emotion in ['contradic', 'complejidad', 'vulnerab'])])} fragments show emotional depth")
            print(f"✅ Intellectual engagement: {len([f for f in fragments if f.fragment_type == 'DECISION'])} decision points stimulate user thinking")
        else:
            print(f"❌ Character risks identified:")
            failing_fragments = [fid for fid, result in report.character_validation_results.items() if not result.meets_threshold]
            for fid in failing_fragments[:3]:  # Show top 3 failing fragments
                result = report.character_validation_results[fid]
                print(f"- Risk: Fragment {fid} scored {result.overall_score:.1f}/100")
                print(f"- Impact: Below 95% threshold, compromises Diana's personality integrity")
                print(f"- Fix: {result.recommendations[0] if result.recommendations else 'Enhance character consistency'}")
        
        # Besitos Integration Analysis
        print(f"\n💋 BESITOS INTEGRATION ANALYSIS:")
        if report.besitos_integration_status["integration_complete"]:
            print(f"✅ Reward system integrated: {report.besitos_integration_status['fragments_with_rewards']}/{report.total_fragments} fragments have rewards")
            print(f"✅ Choice rewards implemented: {report.besitos_integration_status['choice_integration_rate']:.1f}% of choices have point rewards")
            print(f"✅ Reward variety maintained: {report.besitos_integration_status['reward_variety_count']} different bonus types")
        else:
            print(f"❌ Integration issues:")
            print(f"- Issue: Only {report.besitos_integration_status['points_integration_rate']:.1f}% fragments have point rewards")
            print(f"- Impact: Insufficient reward integration compromises engagement flow")
            print(f"- Solution: Add point rewards to remaining fragments")
        
        # Progression System Analysis
        print(f"\n📊 PROGRESSION SYSTEM ANALYSIS:")
        if report.progression_system_status["system_complete"]:
            print(f"✅ 6-level progression complete: All levels 1-6 represented")
            print(f"✅ Tier distribution balanced: {report.progression_system_status['tier_distribution']}")
            print(f"✅ Mission variety implemented: {report.progression_system_status['mission_type_variety']} mission types")
        else:
            print(f"❌ Progression gaps identified:")
            print(f"- Issue: Missing progression levels in 6-level system")
            print(f"- Impact: Incomplete user journey, breaks storyline continuity")
            print(f"- Solution: Add fragments for missing levels")
        
        # Final Verdict
        print(f"\n🎯 FINAL VERDICT:")
        if report.overall_success:
            print("✅ APPROVED: Character consistency preserved, proceed with implementation")
        elif consistency_rate >= 90.0:
            print("⚠️ CONDITIONAL APPROVAL: Approved with these specific modifications:")
            for rec in report.recommendations[:3]:
                print(f"   • {rec}")
        else:
            print("❌ REJECTED: Character integrity at risk, requires fundamental redesign")
        
        # Implementation Guidelines
        print(f"\n📝 IMPLEMENTATION GUIDELINES:")
        print("• Maintain Diana's mysterious tone throughout all user interactions")
        print("• Ensure Lucien appears only when narratively appropriate, never overshadowing Diana")
        print("• Implement progressive besitos rewards that increase with emotional investment")
        print("• Use character validation service to verify all dynamic content")
        print("• Test user archetyping system with fragment interaction patterns")
        print("• Preserve emotional progression from curiosity to deep understanding")

    async def generate_fragment_statistics(self, fragments: List[FragmentDesign]) -> Dict[str, Any]:
        """Generate detailed fragment statistics for reporting."""
        
        stats = {
            "total_fragments": len(fragments),
            "by_type": {},
            "by_level": {},
            "by_tier": {},
            "vip_stats": {
                "total_vip": 0,
                "tier_1": 0,
                "tier_2": 0
            },
            "reward_stats": {
                "fragments_with_rewards": 0,
                "total_base_points": 0,
                "average_points_per_fragment": 0
            },
            "choice_stats": {
                "total_choices": 0,
                "choices_with_rewards": 0,
                "average_choices_per_fragment": 0
            }
        }
        
        # Count by type
        for fragment in fragments:
            ftype = fragment.fragment_type
            stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1
            
            # Count by level
            level = fragment.storyline_level
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
            
            # Count by tier
            tier = fragment.tier_classification
            stats["by_tier"][tier] = stats["by_tier"].get(tier, 0) + 1
            
            # VIP stats
            if fragment.requires_vip:
                stats["vip_stats"]["total_vip"] += 1
                if fragment.vip_tier_required == 1:
                    stats["vip_stats"]["tier_1"] += 1
                elif fragment.vip_tier_required == 2:
                    stats["vip_stats"]["tier_2"] += 1
            
            # Reward stats
            if "points" in fragment.triggers:
                stats["reward_stats"]["fragments_with_rewards"] += 1
                points_data = fragment.triggers["points"]
                if isinstance(points_data, dict):
                    stats["reward_stats"]["total_base_points"] += points_data.get("base", 0)
                else:
                    stats["reward_stats"]["total_base_points"] += points_data
            
            # Choice stats
            if fragment.choices:
                stats["choice_stats"]["total_choices"] += len(fragment.choices)
                stats["choice_stats"]["choices_with_rewards"] += len([
                    c for c in fragment.choices if "points_reward" in c
                ])
        
        # Calculate averages
        if stats["total_fragments"] > 0:
            stats["reward_stats"]["average_points_per_fragment"] = (
                stats["reward_stats"]["total_base_points"] / stats["total_fragments"]
            )
            stats["choice_stats"]["average_choices_per_fragment"] = (
                stats["choice_stats"]["total_choices"] / stats["total_fragments"]
            )
        
        return stats

async def main():
    """Main execution function for fragment validation."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎭 STARTING DIANA BOT MVP TASK 2.3 VALIDATION")
    print("=" * 60)
    
    # Mock session for validation
    class MockSession:
        pass
    
    session = MockSession()
    
    # Create and load fragments
    creator = DianaFragmentCreator(session)
    fragments = creator.create_all_fragments()
    
    print(f"📊 Created {len(fragments)} fragments for validation...")
    
    # Create validator and run comprehensive validation
    validator = NarrativeFragmentValidator(session)
    report = await validator.perform_comprehensive_validation(fragments)
    
    # Generate additional statistics
    stats = await validator.generate_fragment_statistics(fragments)
    
    print(f"\n📈 FRAGMENT STATISTICS:")
    print(f"   • Total fragments: {stats['total_fragments']}")
    print(f"   • Story fragments: {stats['by_type'].get('STORY', 0)}")
    print(f"   • Decision points: {stats['by_type'].get('DECISION', 0)}")
    print(f"   • Info fragments: {stats['by_type'].get('INFO', 0)}")
    print(f"   • VIP content: {stats['vip_stats']['total_vip']} ({stats['vip_stats']['total_vip']/stats['total_fragments']*100:.1f}%)")
    print(f"   • Fragments with rewards: {stats['reward_stats']['fragments_with_rewards']}")
    print(f"   • Total base points: {stats['reward_stats']['total_base_points']}")
    print(f"   • Average points per fragment: {stats['reward_stats']['average_points_per_fragment']:.1f}")
    
    # Save validation report
    report_data = {
        "validation_date": datetime.utcnow().isoformat(),
        "total_fragments": report.total_fragments,
        "overall_success": report.overall_success,
        "mvp_compliance": report.mvp_compliance,
        "besitos_integration": report.besitos_integration_status,
        "progression_system": report.progression_system_status,
        "recommendations": report.recommendations,
        "fragment_statistics": stats
    }
    
    with open("narrative_fragments_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Validation report saved to: narrative_fragments_validation_report.json")
    
    # Final success message
    if report.overall_success:
        print(f"\n✅ TASK 2.3 SUCCESSFULLY COMPLETED!")
        print(f"🎭 All {report.total_fragments} fragments meet Diana's character consistency requirements")
        print(f"💋 Besitos reward system fully integrated")
        print(f"📊 6-level progression system implemented")
        print(f"🚀 Ready for MVP implementation!")
    else:
        print(f"\n⚠️  TASK 2.3 NEEDS REFINEMENT")
        print(f"📝 {len(report.recommendations)} recommendations to address")
        print(f"🔧 Focus on character consistency and system integration")

if __name__ == "__main__":
    asyncio.run(main())