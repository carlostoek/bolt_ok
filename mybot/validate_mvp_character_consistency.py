#!/usr/bin/env python3
"""
MVP Character Consistency Validation Script

This script validates that all implementations preserve Diana and Lucien's character consistency
across the narrative system integrations.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

# Character consistency patterns
DIANA_PATTERNS = {
    'mysterious_tone': [
        r'💋.*[mM]isterio',
        r'✨.*secreto',
        r'🌙.*profund',
        r'🔮.*verdad',
        r'💫.*alma',
        r'[Qq]uerido'
    ],
    'seductive_essence': [
        r'💋',
        r'[Aa]mor',
        r'[Qq]uerido',
        r'[Cc]ariño',
        r'[Mm]i.*amor',
        r'[Ss]usurr'
    ],
    'emotional_intelligence': [
        r'[Ss]iento.*que',
        r'[Pp]uedo.*ver',
        r'[Tt]u.*corazón',
        r'[Tt]u.*alma',
        r'[Ee]mocional'
    ]
}

LUCIEN_PATTERNS = {
    'supportive_guidance': [
        r'[Gg]uía',
        r'[Aa]poyo',
        r'[Oo]rient',
        r'[Rr]ecomiend',
        r'[Ss]ugier'
    ],
    'professional_tone': [
        r'[Uu]suario',
        r'[Ss]istema',
        r'[Pp]roceso',
        r'[Aa]ctualiz',
        r'[Mm]onitor'
    ],
    'coordination_role': [
        r'[Cc]oordin',
        r'[Gg]estión',
        r'[Aa]dministr',
        r'[Cc]ontrol',
        r'[Ss]eguimient'
    ]
}

class CharacterConsistencyValidator:
    """Validates character consistency across narrative implementations."""
    
    def __init__(self):
        self.diana_score = 0.0
        self.lucien_score = 0.0
        self.total_diana_responses = 0
        self.total_lucien_responses = 0
        self.issues_found = []
        
    def validate_text(self, text: str, character: str) -> Dict[str, Any]:
        """Validate a single text for character consistency."""
        if character.lower() == 'diana':
            return self._validate_diana_text(text)
        elif character.lower() == 'lucien':
            return self._validate_lucien_text(text)
        else:
            return {'score': 0.0, 'issues': ['Unknown character']}
    
    def _validate_diana_text(self, text: str) -> Dict[str, Any]:
        """Validate Diana character consistency."""
        score = 0.0
        issues = []
        pattern_matches = {'mysterious_tone': 0, 'seductive_essence': 0, 'emotional_intelligence': 0}
        
        # Check for Diana's characteristic patterns
        for category, patterns in DIANA_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pattern_matches[category] += 1
        
        # Calculate score based on pattern presence
        total_categories = len(DIANA_PATTERNS)
        categories_matched = sum(1 for count in pattern_matches.values() if count > 0)
        
        score = (categories_matched / total_categories) * 100
        
        # Check for consistency issues
        if pattern_matches['seductive_essence'] == 0:
            issues.append("Missing Diana's seductive essence (💋, querido, amor)")
        
        if pattern_matches['mysterious_tone'] == 0 and len(text) > 50:
            issues.append("Missing Diana's mysterious tone for longer responses")
        
        # Check for inappropriate language
        inappropriate_patterns = [
            r'[Ee]rror',
            r'[Ff]allo',
            r'[Ss]istema.*caído',
            r'[Bb]ase.*datos',
            r'[Cc]ódigo.*error'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Technical language inappropriate for Diana: {pattern}")
                score -= 20
        
        return {
            'score': max(score, 0.0),
            'pattern_matches': pattern_matches,
            'issues': issues
        }
    
    def _validate_lucien_text(self, text: str) -> Dict[str, Any]:
        """Validate Lucien character consistency."""
        score = 0.0
        issues = []
        pattern_matches = {'supportive_guidance': 0, 'professional_tone': 0, 'coordination_role': 0}
        
        # Check for Lucien's characteristic patterns
        for category, patterns in LUCIEN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pattern_matches[category] += 1
        
        # Calculate score
        total_categories = len(LUCIEN_PATTERNS)
        categories_matched = sum(1 for count in pattern_matches.values() if count > 0)
        
        score = (categories_matched / total_categories) * 100
        
        # Check for consistency issues
        if pattern_matches['professional_tone'] == 0:
            issues.append("Missing Lucien's professional tone")
        
        # Check for inappropriate Diana-like language in Lucien responses
        diana_patterns = [r'💋', r'[Qq]uerido', r'[Aa]mor.*mío', r'[Ss]educt']
        for pattern in diana_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Inappropriate Diana-like language in Lucien response: {pattern}")
                score -= 30
        
        return {
            'score': max(score, 0.0),
            'pattern_matches': pattern_matches,
            'issues': issues
        }

def extract_character_responses_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Extract character responses from source files."""
    responses = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Look for Diana responses
        diana_patterns = [
            r'diana_announcement["\']:\s*["\']([^"\']+)["\']',
            r'diana_response["\']:\s*["\']([^"\']+)["\']',
            r'narrative_justification["\']:\s*["\']([^"\']+)["\']',
            r'diana_insight["\']:\s*["\']([^"\']+)["\']',
            r'diana_presentation["\']:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in diana_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.strip()) > 10:  # Filter out very short responses
                    responses.append({
                        'character': 'diana',
                        'text': match.strip(),
                        'source_file': file_path,
                        'type': 'response'
                    })
        
        # Look for Lucien responses
        lucien_patterns = [
            r'lucien_guidance["\']:\s*["\']([^"\']+)["\']',
            r'lucien_coordination["\']:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in lucien_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.strip()) > 10:
                    responses.append({
                        'character': 'lucien',
                        'text': match.strip(),
                        'source_file': file_path,
                        'type': 'guidance'
                    })
    
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    
    return responses

def validate_mvp_implementations():
    """Validate character consistency across MVP implementations."""
    validator = CharacterConsistencyValidator()
    
    # Files to validate
    implementation_files = [
        'services/mvp_decision_tree_service.py',
        'services/decision_achievement_integration.py',
        'services/decision_performance_optimizer.py',
        'services/vip_tier_management_service.py'
    ]
    
    print("🎭 MVP CHARACTER CONSISTENCY VALIDATION")
    print("=" * 50)
    
    all_responses = []
    
    # Extract responses from all files
    for file_path in implementation_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            responses = extract_character_responses_from_file(str(full_path))
            all_responses.extend(responses)
            print(f"📄 {file_path}: {len(responses)} character responses found")
    
    if not all_responses:
        print("❌ No character responses found in implementation files")
        return False
    
    print(f"\n📊 ANALYZING {len(all_responses)} TOTAL RESPONSES")
    print("-" * 50)
    
    diana_responses = [r for r in all_responses if r['character'] == 'diana']
    lucien_responses = [r for r in all_responses if r['character'] == 'lucien']
    
    print(f"💋 Diana responses: {len(diana_responses)}")
    print(f"🎩 Lucien responses: {len(lucien_responses)}")
    
    # Validate Diana responses
    diana_scores = []
    diana_issues = []
    
    for response in diana_responses:
        validation = validator.validate_text(response['text'], 'diana')
        diana_scores.append(validation['score'])
        
        if validation['issues']:
            diana_issues.extend([
                {
                    'text': response['text'][:100] + "...",
                    'file': response['source_file'],
                    'issues': validation['issues']
                }
            ])
    
    # Validate Lucien responses
    lucien_scores = []
    lucien_issues = []
    
    for response in lucien_responses:
        validation = validator.validate_text(response['text'], 'lucien')
        lucien_scores.append(validation['score'])
        
        if validation['issues']:
            lucien_issues.extend([
                {
                    'text': response['text'][:100] + "...",
                    'file': response['source_file'],
                    'issues': validation['issues']
                }
            ])
    
    # Calculate overall scores
    diana_avg_score = sum(diana_scores) / len(diana_scores) if diana_scores else 0
    lucien_avg_score = sum(lucien_scores) / len(lucien_scores) if lucien_scores else 0
    overall_score = (diana_avg_score + lucien_avg_score) / 2 if (diana_scores or lucien_scores) else 0
    
    print(f"\n🎯 CONSISTENCY SCORES")
    print("-" * 20)
    print(f"💋 Diana Average: {diana_avg_score:.1f}%")
    print(f"🎩 Lucien Average: {lucien_avg_score:.1f}%")
    print(f"🎭 Overall Score: {overall_score:.1f}%")
    
    # Report issues
    if diana_issues:
        print(f"\n⚠️  DIANA CONSISTENCY ISSUES ({len(diana_issues)})")
        print("-" * 30)
        for issue in diana_issues[:5]:  # Show first 5 issues
            print(f"📄 {issue['file']}")
            print(f"📝 Text: {issue['text']}")
            print(f"❌ Issues: {', '.join(issue['issues'])}")
            print()
    
    if lucien_issues:
        print(f"\n⚠️  LUCIEN CONSISTENCY ISSUES ({len(lucien_issues)})")
        print("-" * 30)
        for issue in lucien_issues[:5]:  # Show first 5 issues
            print(f"📄 {issue['file']}")
            print(f"📝 Text: {issue['text']}")
            print(f"❌ Issues: {', '.join(issue['issues'])}")
            print()
    
    # Final assessment
    print("\n🏆 FINAL ASSESSMENT")
    print("-" * 20)
    
    if overall_score >= 90:
        print("✅ EXCELLENT: Character consistency is exceptional")
        status = "EXCELLENT"
    elif overall_score >= 80:
        print("✅ GOOD: Character consistency is strong")
        status = "GOOD"
    elif overall_score >= 70:
        print("⚠️  ACCEPTABLE: Character consistency needs minor improvements")
        status = "ACCEPTABLE"
    else:
        print("❌ NEEDS IMPROVEMENT: Character consistency requires attention")
        status = "NEEDS_IMPROVEMENT"
    
    # MVP Requirements Check
    mvp_requirements_met = (
        overall_score >= 75 and  # Minimum 75% consistency
        len(diana_responses) > 0 and  # Diana responses exist
        diana_avg_score >= 70  # Diana's core consistency maintained
    )
    
    print(f"\n📋 MVP REQUIREMENTS")
    print("-" * 20)
    print(f"✅ Overall Score >= 75%: {'✅' if overall_score >= 75 else '❌'}")
    print(f"✅ Diana Responses Exist: {'✅' if len(diana_responses) > 0 else '❌'}")
    print(f"✅ Diana Score >= 70%: {'✅' if diana_avg_score >= 70 else '❌'}")
    print(f"\n🎯 MVP STATUS: {'✅ READY' if mvp_requirements_met else '❌ NOT READY'}")
    
    # Save detailed report
    report = {
        'timestamp': str(asyncio.get_event_loop().time()),
        'overall_score': overall_score,
        'diana_score': diana_avg_score,
        'lucien_score': lucien_avg_score,
        'diana_responses_count': len(diana_responses),
        'lucien_responses_count': len(lucien_responses),
        'diana_issues': diana_issues,
        'lucien_issues': lucien_issues,
        'mvp_requirements_met': mvp_requirements_met,
        'status': status
    }
    
    with open('character_consistency_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Detailed report saved to: character_consistency_report.json")
    
    return mvp_requirements_met

if __name__ == "__main__":
    success = validate_mvp_implementations()
    exit(0 if success else 1)