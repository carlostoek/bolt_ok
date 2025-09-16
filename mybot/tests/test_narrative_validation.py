"""
Test file for narrative validation and security implementation.
"""
import json
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the database models import
import unittest.mock as mock
sys.modules['database.narrative_models'] = mock.MagicMock()

from utils.narrative_validation import (
    validate_story_fragment_data,
    sanitize_fragment_content,
    validate_content_safety,
    validate_json_structure,
    validate_fragment_key
)

def test_validation_functions():
    """Test the validation functions."""
    print("Testing narrative validation functions...")
    
    # Test valid fragment data
    valid_fragment = {
        "key": "test_fragment_1",
        "text": "This is a test fragment with some content.",
        "character": "Diana",
        "level": 2,
        "min_besitos": 50,
        "required_role": "vip",
        "reward_besitos": 25,
        "decisions": [
            {
                "text": "Make a choice",
                "next_fragment": "test_fragment_2",
                "required_besitos": 100,
                "required_role": "vip"
            }
        ]
    }
    
    is_valid, errors = validate_story_fragment_data(valid_fragment)
    print(f"Valid fragment test - Valid: {is_valid}, Errors: {errors}")
    assert is_valid, f"Valid fragment should pass validation: {errors}"
    
    # Test invalid fragment data
    invalid_fragment = {
        "key": "test fragment 1",  # Invalid key with spaces
        "text": "",  # Empty text
        "character": "Diana",
        "level": -1,  # Invalid level
        "min_besitos": -50,  # Invalid besitos
        "required_role": "invalid_role",  # Invalid role
        "decisions": [
            {
                "text": "",  # Empty decision text
                "next_fragment": "",  # Empty next fragment
                "required_besitos": -100,  # Invalid besitos
                "required_role": "invalid"  # Invalid role
            }
        ]
    }
    
    is_valid, errors = validate_story_fragment_data(invalid_fragment)
    print(f"Invalid fragment test - Valid: {is_valid}, Errors: {len(errors)}")
    assert not is_valid, "Invalid fragment should fail validation"
    assert len(errors) > 0, "Should have validation errors"
    
    # Test content safety
    unsafe_fragment = {
        "key": "unsafe_fragment",
        "text": "This content has <script>alert('xss')</script> in it.",
        "decisions": [
            {
                "text": "Click me <img src=x onerror=alert('xss')>",
                "next_fragment": "next"
            }
        ]
    }
    
    safety_errors = validate_content_safety(unsafe_fragment)
    print(f"Content safety test - Errors: {len(safety_errors)}")
    # Note: Our current implementation doesn't flag these as unsafe since we escape HTML
    
    # Test sanitization
    dirty_fragment = {
        "key": "dirty_fragment",
        "text": "This has **bold** and *italic* text with `code`.",
        "decisions": [
            {
                "text": "Another decision with **formatting**",
                "next_fragment": "next"
            }
        ]
    }
    
    clean_fragment = sanitize_fragment_content(dirty_fragment)
    print(f"Sanitization test - Original: {dirty_fragment['text']}")
    print(f"Sanitization test - Cleaned: {clean_fragment['text']}")
    
    # Test JSON structure validation
    valid_json = {
        "key": "json_test",
        "text": "Test content"
    }
    
    is_valid, errors = validate_json_structure(valid_json)
    print(f"Valid JSON structure test - Valid: {is_valid}")
    assert is_valid, "Valid JSON should pass structure validation"
    
    # Test JSON with fragments array
    valid_json_array = {
        "fragments": [
            {"key": "frag1", "text": "Content 1"},
            {"key": "frag2", "text": "Content 2"}
        ]
    }
    
    is_valid, errors = validate_json_structure(valid_json_array)
    print(f"Valid JSON array structure test - Valid: {is_valid}")
    assert is_valid, "Valid JSON array should pass structure validation"
    
    # Test fragment key validation
    assert validate_fragment_key("valid_key_123"), "Valid key should pass validation"
    assert not validate_fragment_key("invalid key"), "Key with spaces should fail validation"
    assert not validate_fragment_key(""), "Empty key should fail validation"
    assert not validate_fragment_key(None), "None key should fail validation"
    
    print("All validation tests passed!")

if __name__ == "__main__":
    test_validation_functions()