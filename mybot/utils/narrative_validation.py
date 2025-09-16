"""
Validation and security utilities for narrative content.
Provides input sanitization, content validation, and security measures.
"""
import re
import html
import logging
from typing import Dict, Any, List, Optional, Tuple
from database.narrative_models import StoryFragment

logger = logging.getLogger(__name__)

# Allowed HTML tags for rich text content (if needed)
ALLOWED_TAGS = {
    'b', 'i', 'u', 's', 'em', 'strong', 'code', 'pre', 
    'br', 'p', 'div', 'span', 'ul', 'ol', 'li'
}

# Restricted keywords that should not appear in content
RESTRICTED_KEYWORDS = [
    'script', 'javascript', 'eval', 'alert', 'onload', 'onclick',
    'onerror', 'onmouseover', 'onfocus', 'onblur', 'onsubmit'
]

# Character limits for various fields
MAX_KEY_LENGTH = 50
MAX_TEXT_LENGTH = 65535
MAX_CHARACTER_LENGTH = 50
MAX_DECISION_TEXT_LENGTH = 500

def validate_story_fragment_data(fragment_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate story fragment data for required fields and constraints.
    
    Args:
        fragment_data: Dictionary containing fragment data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate required fields
    if not fragment_data.get('key'):
        errors.append("Fragment key is required")
    elif not isinstance(fragment_data.get('key'), str):
        errors.append("Fragment key must be a string")
    elif len(fragment_data['key']) > MAX_KEY_LENGTH:
        errors.append(f"Fragment key exceeds maximum length of {MAX_KEY_LENGTH}")
    elif not re.match(r'^[a-zA-Z0-9_-]+$', fragment_data['key']):
        errors.append("Fragment key contains invalid characters (only alphanumeric, underscore, hyphen allowed)")
    
    if not fragment_data.get('text'):
        errors.append("Fragment text is required")
    elif not isinstance(fragment_data.get('text'), str):
        errors.append("Fragment text must be a string")
    elif len(fragment_data['text']) > MAX_TEXT_LENGTH:
        errors.append(f"Fragment text exceeds maximum length of {MAX_TEXT_LENGTH}")
    
    # Validate optional fields
    character = fragment_data.get('character')
    if character is not None:
        if not isinstance(character, str):
            errors.append("Character must be a string")
        elif len(character) > MAX_CHARACTER_LENGTH:
            errors.append(f"Character name exceeds maximum length of {MAX_CHARACTER_LENGTH}")
    
    level = fragment_data.get('level')
    if level is not None:
        if not isinstance(level, int) or level < 1:
            errors.append("Level must be a positive integer")
    
    min_besitos = fragment_data.get('min_besitos')
    if min_besitos is not None:
        if not isinstance(min_besitos, int) or min_besitos < 0:
            errors.append("Min besitos must be a non-negative integer")
    
    reward_besitos = fragment_data.get('reward_besitos')
    if reward_besitos is not None:
        if not isinstance(reward_besitos, int) or reward_besitos < 0:
            errors.append("Reward besitos must be a non-negative integer")
    
    required_role = fragment_data.get('required_role')
    if required_role is not None:
        if not isinstance(required_role, str):
            errors.append("Required role must be a string")
        elif required_role not in ['free', 'vip', 'admin']:
            errors.append("Required role must be one of: free, vip, admin")
    
    auto_next = fragment_data.get('auto_next_fragment_key')
    if auto_next is not None:
        if not isinstance(auto_next, str):
            errors.append("Auto next fragment key must be a string")
        elif len(auto_next) > MAX_KEY_LENGTH:
            errors.append(f"Auto next fragment key exceeds maximum length of {MAX_KEY_LENGTH}")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', auto_next):
            errors.append("Auto next fragment key contains invalid characters")
    
    decisions = fragment_data.get('decisions', [])
    if not isinstance(decisions, list):
        errors.append("Decisions must be a list")
    else:
        for i, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                errors.append(f"Decision {i} must be a dictionary")
                continue
                
            decision_text = decision.get('text')
            if not decision_text:
                errors.append(f"Decision {i} text is required")
            elif not isinstance(decision_text, str):
                errors.append(f"Decision {i} text must be a string")
            elif len(decision_text) > MAX_DECISION_TEXT_LENGTH:
                errors.append(f"Decision {i} text exceeds maximum length of {MAX_DECISION_TEXT_LENGTH}")
            
            next_fragment = decision.get('next_fragment')
            if not next_fragment:
                errors.append(f"Decision {i} next fragment is required")
            elif not isinstance(next_fragment, str):
                errors.append(f"Decision {i} next fragment must be a string")
            elif len(next_fragment) > MAX_KEY_LENGTH:
                errors.append(f"Decision {i} next fragment key exceeds maximum length of {MAX_KEY_LENGTH}")
            elif not re.match(r'^[a-zA-Z0-9_-]+$', next_fragment):
                errors.append(f"Decision {i} next fragment key contains invalid characters")
            
            required_besitos = decision.get('required_besitos')
            if required_besitos is not None:
                if not isinstance(required_besitos, int) or required_besitos < 0:
                    errors.append(f"Decision {i} required besitos must be a non-negative integer")
            
            required_role = decision.get('required_role')
            if required_role is not None:
                if not isinstance(required_role, str):
                    errors.append(f"Decision {i} required role must be a string")
                elif required_role not in ['free', 'vip', 'admin']:
                    errors.append(f"Decision {i} required role must be one of: free, vip, admin")
    
    # Validate content safety
    content_errors = validate_content_safety(fragment_data)
    errors.extend(content_errors)
    
    return len(errors) == 0, errors

def validate_content_safety(fragment_data: Dict[str, Any]) -> List[str]:
    """
    Validate content for security and appropriateness.
    
    Args:
        fragment_data: Dictionary containing fragment data
        
    Returns:
        List of content safety errors
    """
    errors = []
    
    # Check text content for restricted keywords
    text_content = fragment_data.get('text', '')
    if text_content:
        safety_errors = _check_content_for_safety_issues(text_content)
        errors.extend(safety_errors)
    
    # Check decisions for safety issues
    decisions = fragment_data.get('decisions', [])
    for i, decision in enumerate(decisions):
        decision_text = decision.get('text', '')
        if decision_text:
            safety_errors = _check_content_for_safety_issues(decision_text)
            for error in safety_errors:
                errors.append(f"Decision {i}: {error}")
    
    return errors

def _check_content_for_safety_issues(content: str) -> List[str]:
    """
    Check content for potential security or appropriateness issues.
    
    Args:
        content: Text content to check
        
    Returns:
        List of safety issue descriptions
    """
    errors = []
    
    # Convert to lowercase for case-insensitive checks
    content_lower = content.lower()
    
    # Check for restricted keywords
    for keyword in RESTRICTED_KEYWORDS:
        if keyword in content_lower:
            errors.append(f"Content contains restricted keyword: {keyword}")
    
    # Check for excessive repeated characters (potential spam)
    if re.search(r'(.)\1{10,}', content):
        errors.append("Content contains excessive repeated characters")
    
    # Check for excessive consecutive whitespace
    if re.search(r'\s{20,}', content):
        errors.append("Content contains excessive whitespace")
    
    return errors

def sanitize_fragment_content(fragment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize fragment content to prevent XSS and other security issues.
    
    Args:
        fragment_data: Dictionary containing fragment data
        
    Returns:
        Sanitized fragment data
    """
    sanitized_data = fragment_data.copy()
    
    # Sanitize text content
    if 'text' in sanitized_data and sanitized_data['text']:
        sanitized_data['text'] = _sanitize_text_content(sanitized_data['text'])
    
    # Sanitize decisions
    if 'decisions' in sanitized_data and sanitized_data['decisions']:
        sanitized_decisions = []
        for decision in sanitized_data['decisions']:
            sanitized_decision = decision.copy()
            if 'text' in sanitized_decision and sanitized_decision['text']:
                sanitized_decision['text'] = _sanitize_text_content(sanitized_decision['text'])
            sanitized_decisions.append(sanitized_decision)
        sanitized_data['decisions'] = sanitized_decisions
    
    # Sanitize character name
    if 'character' in sanitized_data and sanitized_data['character']:
        sanitized_data['character'] = _sanitize_basic_text(sanitized_data['character'])
    
    # Sanitize fragment key
    if 'key' in sanitized_data and sanitized_data['key']:
        sanitized_data['key'] = _sanitize_basic_text(sanitized_data['key'])
    
    return sanitized_data

def _sanitize_text_content(text: str) -> str:
    """
    Sanitize rich text content while preserving allowed formatting.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Escape HTML to prevent XSS
    sanitized = html.escape(text)
    
    # Allow some basic formatting by converting markdown-like syntax
    # Convert **bold** to <b>bold</b>
    sanitized = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', sanitized)
    
    # Convert *italic* to <i>italic</i>
    sanitized = re.sub(r'\*(.*?)\*', r'<i>\1</i>', sanitized)
    
    # Convert _underline_ to <u>underline</u>
    sanitized = re.sub(r'_(.*?)_', r'<u>\1</u>', sanitized)
    
    # Convert `code` to <code>code</code>
    sanitized = re.sub(r'`(.*?)`', r'<code>\1</code>', sanitized)
    
    return sanitized

def _sanitize_basic_text(text: str) -> str:
    """
    Sanitize basic text (names, keys, etc.) by removing or escaping dangerous characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Remove control characters except common whitespace
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit length
    return sanitized[:MAX_KEY_LENGTH] if len(sanitized) > MAX_KEY_LENGTH else sanitized

def validate_fragment_key(fragment_key: str) -> bool:
    """
    Validate a fragment key format.
    
    Args:
        fragment_key: Fragment key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not fragment_key or not isinstance(fragment_key, str):
        return False
    
    if len(fragment_key) > MAX_KEY_LENGTH:
        return False
    
    # Only allow alphanumeric characters, underscores, and hyphens
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', fragment_key))

def validate_json_structure(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the overall JSON structure of narrative data.
    
    Args:
        data: JSON data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if it's a valid dict
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return False, errors
    
    # Check for top-level fragments structure
    if 'fragments' in data:
        if not isinstance(data['fragments'], list):
            errors.append("'fragments' must be a list")
        else:
            for i, fragment in enumerate(data['fragments']):
                if not isinstance(fragment, dict):
                    errors.append(f"Fragment {i} must be a dictionary")
                else:
                    # Validate each fragment
                    _, fragment_errors = validate_story_fragment_data(fragment)
                    for error in fragment_errors:
                        errors.append(f"Fragment {i}: {error}")
    else:
        # Single fragment structure
        _, fragment_errors = validate_story_fragment_data(data)
        errors.extend(fragment_errors)
    
    return len(errors) == 0, errors