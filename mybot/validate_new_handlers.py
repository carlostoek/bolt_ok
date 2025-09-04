#!/usr/bin/env python3
"""
Validation script for newly created critical handlers.
Tests character consistency, error handling, and integration patterns.
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Any

def validate_diana_character_consistency(file_path: str) -> Dict[str, Any]:
    """
    Validate Diana's character consistency in handler messages.
    
    Checks for:
    - Seductive/mysterious personality patterns
    - Consistent use of Diana's voice
    - Proper emotional tone
    - Lucien's supportive coordination role
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {
        "diana_messages": [],
        "lucien_messages": [],
        "character_consistency_score": 0,
        "issues": [],
        "strengths": []
    }
    
    # Extract Diana messages
    diana_patterns = [
        r'"([^"]*Diana[^"]*)"',
        r"'([^']*Diana[^']*)'",
        r'f"([^"]*Diana[^"]*)"',
        r"f'([^']*Diana[^']*)'",
    ]
    
    for pattern in diana_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        results["diana_messages"].extend(matches)
    
    # Extract Lucien messages
    lucien_patterns = [
        r'"([^"]*Lucien[^"]*)"',
        r"'([^']*Lucien[^']*)'",
        r'f"([^"]*Lucien[^"]*)"',
        r"f'([^']*Lucien[^']*)'",
    ]
    
    for pattern in lucien_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        results["lucien_messages"].extend(matches)
    
    # Check for Diana's seductive/mysterious elements
    seductive_indicators = [
        "susurra", "seductoramente", "misterioso", "querido", "amor", 
        "cariño", "mi querido", "fascina", "emociona", "conmueve",
        "besitos", "perfecto", "impresionante", "dedicación", "aventura"
    ]
    
    diana_seductive_count = 0
    for message in results["diana_messages"]:
        for indicator in seductive_indicators:
            if indicator.lower() in message.lower():
                diana_seductive_count += 1
                break
    
    # Check for Lucien's supportive role
    lucien_supportive_indicators = [
        "coordina", "organiza", "sistema", "revisará", "operativo", 
        "listo", "configurar", "estado", "datos", "panel"
    ]
    
    lucien_supportive_count = 0
    for message in results["lucien_messages"]:
        for indicator in lucien_supportive_indicators:
            if indicator.lower() in message.lower():
                lucien_supportive_count += 1
                break
    
    # Calculate character consistency score
    total_diana = len(results["diana_messages"])
    total_lucien = len(results["lucien_messages"])
    
    if total_diana > 0:
        diana_consistency = (diana_seductive_count / total_diana) * 100
    else:
        diana_consistency = 0
        
    if total_lucien > 0:
        lucien_consistency = (lucien_supportive_count / total_lucien) * 100
    else:
        lucien_consistency = 100  # No Lucien messages is fine
    
    overall_consistency = (diana_consistency + lucien_consistency) / 2
    results["character_consistency_score"] = round(overall_consistency, 1)
    
    # Identify issues and strengths
    if diana_consistency < 80 and total_diana > 0:
        results["issues"].append(f"Diana personality consistency low: {diana_consistency:.1f}%")
    elif total_diana > 0:
        results["strengths"].append(f"Diana personality well maintained: {diana_consistency:.1f}%")
    
    if lucien_consistency < 80 and total_lucien > 0:
        results["issues"].append(f"Lucien role consistency low: {lucien_consistency:.1f}%")
    elif total_lucien > 0:
        results["strengths"].append(f"Lucien role properly implemented: {lucien_consistency:.1f}%")
    
    return results

def validate_error_handling(file_path: str) -> Dict[str, Any]:
    """
    Validate error handling patterns in handlers.
    
    Checks for:
    - Proper try/except blocks
    - Character-consistent error messages
    - Graceful degradation
    - Logging for debugging
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {
        "error_handlers": 0,
        "character_consistent_errors": 0,
        "logging_statements": 0,
        "graceful_degradation": 0,
        "issues": [],
        "strengths": []
    }
    
    # Count try/except blocks
    try_except_pattern = r'try:.*?except.*?:'
    results["error_handlers"] = len(re.findall(try_except_pattern, content, re.DOTALL))
    
    # Count character-consistent error messages
    error_patterns = [
        r'Diana.*error', r'Diana.*problema', r'Diana.*disculp', 
        r'Lucien.*error', r'Lucien.*problema', r'Lucien.*revisando'
    ]
    
    for pattern in error_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        results["character_consistent_errors"] += len(matches)
    
    # Count logging statements
    logging_pattern = r'logger\.(info|error|warning|debug)'
    results["logging_statements"] = len(re.findall(logging_pattern, content))
    
    # Check for graceful degradation patterns
    degradation_patterns = [
        r'fallback', r'default', r'placeholder', r'graceful',
        r'if not.*return.*', r'except.*continue', r'except.*pass'
    ]
    
    for pattern in degradation_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        results["graceful_degradation"] += len(matches)
    
    # Evaluate error handling quality
    if results["error_handlers"] < 5:
        results["issues"].append("Insufficient error handling blocks")
    else:
        results["strengths"].append(f"Good error handling coverage: {results['error_handlers']} blocks")
    
    if results["character_consistent_errors"] == 0 and results["error_handlers"] > 0:
        results["issues"].append("Error messages not character-consistent")
    elif results["character_consistent_errors"] > 0:
        results["strengths"].append("Error messages maintain character consistency")
    
    if results["logging_statements"] < results["error_handlers"]:
        results["issues"].append("Insufficient logging for debugging")
    else:
        results["strengths"].append("Adequate logging for debugging")
    
    return results

def validate_performance_patterns(file_path: str) -> Dict[str, Any]:
    """
    Validate performance optimization patterns.
    
    Checks for:
    - Async/await usage
    - Database query optimization hints
    - Response time considerations
    - Memory efficiency
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {
        "async_functions": 0,
        "await_calls": 0,
        "database_queries": 0,
        "optimization_hints": 0,
        "issues": [],
        "strengths": []
    }
    
    # Count async functions
    async_pattern = r'async def \w+'
    results["async_functions"] = len(re.findall(async_pattern, content))
    
    # Count await calls
    await_pattern = r'await '
    results["await_calls"] = len(re.findall(await_pattern, content))
    
    # Count database queries
    query_patterns = [
        r'session\.execute', r'session\.get', r'session\.query',
        r'select\(', r'func\.count', r'\.limit\(', r'\.offset\('
    ]
    
    for pattern in query_patterns:
        matches = re.findall(pattern, content)
        results["database_queries"] += len(matches)
    
    # Check for performance optimization hints
    optimization_patterns = [
        r'\.limit\(', r'\.scalar\(', r'pagination', r'batch',
        r'cache', r'optimize', r'performance', r'<1s', r'<2s'
    ]
    
    for pattern in optimization_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        results["optimization_hints"] += len(matches)
    
    # Evaluate performance patterns
    if results["async_functions"] < 5:
        results["issues"].append("Low async function usage")
    else:
        results["strengths"].append(f"Good async usage: {results['async_functions']} functions")
    
    if results["await_calls"] < results["async_functions"]:
        results["issues"].append("Missing await calls in async functions")
    else:
        results["strengths"].append("Proper async/await usage")
    
    if results["optimization_hints"] > 0:
        results["strengths"].append(f"Performance considerations present: {results['optimization_hints']} hints")
    else:
        results["issues"].append("No explicit performance optimizations found")
    
    return results

def validate_integration_patterns(file_path: str) -> Dict[str, Any]:
    """
    Validate integration with existing systems.
    
    Checks for:
    - Service layer integration
    - Event bus usage
    - Keyboard consistency
    - Menu system compatibility
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {
        "service_integrations": 0,
        "event_bus_usage": 0,
        "keyboard_functions": 0,
        "menu_callbacks": 0,
        "issues": [],
        "strengths": []
    }
    
    # Count service integrations
    service_patterns = [
        r'Service\(', r'from services\.', r'\.service', 
        r'MVP.*Service', r'NarrativeService', r'PointService'
    ]
    
    for pattern in service_patterns:
        matches = re.findall(pattern, content)
        results["service_integrations"] += len(matches)
    
    # Check event bus usage
    event_patterns = [
        r'event_bus', r'EventType', r'publish', r'emit'
    ]
    
    for pattern in event_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        results["event_bus_usage"] += len(matches)
    
    # Count keyboard functions
    keyboard_patterns = [
        r'def.*keyboard', r'InlineKeyboardBuilder', r'callback_data',
        r'builder\.button', r'as_markup'
    ]
    
    for pattern in keyboard_patterns:
        matches = re.findall(pattern, content)
        results["keyboard_functions"] += len(matches)
    
    # Count menu callback handling
    callback_patterns = [
        r'@router\.callback_query', r'callback\.data', r'F\.data',
        r'safe_handler', r'callback\.answer'
    ]
    
    for pattern in callback_patterns:
        matches = re.findall(pattern, content)
        results["menu_callbacks"] += len(matches)
    
    # Evaluate integration quality
    if results["service_integrations"] < 3:
        results["issues"].append("Low service layer integration")
    else:
        results["strengths"].append(f"Good service integration: {results['service_integrations']} references")
    
    if results["keyboard_functions"] < 3:
        results["issues"].append("Insufficient keyboard/UI functions")
    else:
        results["strengths"].append(f"Good UI integration: {results['keyboard_functions']} keyboard functions")
    
    if results["menu_callbacks"] < 5:
        results["issues"].append("Limited callback handling")
    else:
        results["strengths"].append(f"Comprehensive callback handling: {results['menu_callbacks']} handlers")
    
    if results["event_bus_usage"] > 0:
        results["strengths"].append("Integrated with event bus for analytics")
    else:
        results["issues"].append("No event bus integration found")
    
    return results

def generate_validation_report(file_path: str) -> Dict[str, Any]:
    """Generate comprehensive validation report for a handler file."""
    print(f"\n🔍 VALIDATING: {file_path}")
    print("=" * 60)
    
    character_validation = validate_diana_character_consistency(file_path)
    error_validation = validate_error_handling(file_path)
    performance_validation = validate_performance_patterns(file_path)
    integration_validation = validate_integration_patterns(file_path)
    
    # Calculate overall score
    scores = []
    
    if character_validation["character_consistency_score"] > 0:
        scores.append(character_validation["character_consistency_score"])
    
    # Error handling score (0-100)
    error_score = min(100, (error_validation["error_handlers"] * 10) + 
                           (error_validation["character_consistent_errors"] * 15) +
                           (error_validation["logging_statements"] * 5))
    scores.append(error_score)
    
    # Performance score (0-100)
    perf_score = min(100, (performance_validation["async_functions"] * 8) +
                          (performance_validation["optimization_hints"] * 10))
    scores.append(perf_score)
    
    # Integration score (0-100)
    integration_score = min(100, (integration_validation["service_integrations"] * 5) +
                                 (integration_validation["keyboard_functions"] * 10) +
                                 (integration_validation["menu_callbacks"] * 3) +
                                 (integration_validation["event_bus_usage"] * 15))
    scores.append(integration_score)
    
    overall_score = sum(scores) / len(scores) if scores else 0
    
    # Generate report
    report = {
        "file": file_path,
        "overall_score": round(overall_score, 1),
        "character_validation": character_validation,
        "error_validation": error_validation,  
        "performance_validation": performance_validation,
        "integration_validation": integration_validation,
        "recommendations": []
    }
    
    # Generate recommendations
    all_issues = (character_validation["issues"] + 
                 error_validation["issues"] + 
                 performance_validation["issues"] + 
                 integration_validation["issues"])
    
    all_strengths = (character_validation["strengths"] + 
                    error_validation["strengths"] + 
                    performance_validation["strengths"] + 
                    integration_validation["strengths"])
    
    report["total_issues"] = len(all_issues)
    report["total_strengths"] = len(all_strengths)
    
    # Print detailed report
    print(f"📊 OVERALL SCORE: {overall_score:.1f}/100")
    print(f"🎭 Character Consistency: {character_validation['character_consistency_score']:.1f}%")
    print(f"🛡️ Error Handling Score: {error_score:.1f}/100")
    print(f"⚡ Performance Score: {perf_score:.1f}/100") 
    print(f"🔗 Integration Score: {integration_score:.1f}/100")
    
    print(f"\n✅ STRENGTHS ({len(all_strengths)}):")
    for strength in all_strengths[:5]:  # Show top 5
        print(f"  • {strength}")
    
    print(f"\n⚠️ ISSUES TO IMPROVE ({len(all_issues)}):")
    for issue in all_issues[:5]:  # Show top 5
        print(f"  • {issue}")
    
    return report

def main():
    """Run validation on both new critical handlers."""
    print("🚀 DIANA BOT CRITICAL HANDLERS VALIDATION")
    print("=" * 60)
    print("Validating character consistency, error handling, and integration patterns")
    
    handlers_to_validate = [
        "handlers/admin/admin_narrative_handler.py",
        "handlers/user/gamification_handler.py"
    ]
    
    reports = []
    
    for handler_path in handlers_to_validate:
        if Path(handler_path).exists():
            report = generate_validation_report(handler_path)
            reports.append(report)
        else:
            print(f"❌ Handler not found: {handler_path}")
    
    # Summary
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    if reports:
        avg_score = sum(r["overall_score"] for r in reports) / len(reports)
        total_issues = sum(r["total_issues"] for r in reports)
        total_strengths = sum(r["total_strengths"] for r in reports)
        
        print(f"🎯 Average Score: {avg_score:.1f}/100")
        print(f"✅ Total Strengths: {total_strengths}")
        print(f"⚠️ Total Issues: {total_issues}")
        
        if avg_score >= 80:
            print("🏆 EXCELLENT: Handlers are production-ready!")
        elif avg_score >= 70:
            print("✅ GOOD: Handlers are solid with minor improvements needed")
        elif avg_score >= 60:
            print("⚠️ FAIR: Handlers need improvement before deployment")
        else:
            print("❌ POOR: Handlers require significant work")
        
        # Character consistency summary
        character_scores = [r["character_validation"]["character_consistency_score"] for r in reports]
        if character_scores:
            avg_character_score = sum(character_scores) / len(character_scores)
            print(f"🎭 Diana Character Consistency: {avg_character_score:.1f}%")
            
            if avg_character_score >= 90:
                print("   💋 Diana's personality perfectly preserved!")
            elif avg_character_score >= 75:
                print("   💕 Diana's character well maintained")  
            else:
                print("   ⚠️ Diana's character needs attention")
    else:
        print("❌ No handlers found to validate")
    
    print("\n🎭 Remember: Diana's mystery and Lucien's support must always be preserved!")
    return reports

if __name__ == "__main__":
    main()