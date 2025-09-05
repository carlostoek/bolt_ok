#!/usr/bin/env python3
"""
Script to fix all MenuResponse instantiations in enhanced_diana_menu_system.py
to use the safe creation method for BaseModel debugging.
"""

import re
import os
import sys

def fix_menu_response_instantiations(file_path: str):
    """Fix all MenuResponse instantiations to use safe creation method."""
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count original MenuResponse instances
    original_count = len(re.findall(r'return MenuResponse\(', content))
    
    # Replace return MenuResponse( with return self._create_safe_menu_response(
    # But be careful to not replace ones already fixed
    pattern = r'return MenuResponse\('
    replacement = r'return self._create_safe_menu_response('
    
    # Only replace if not already using safe method
    def replace_func(match):
        # Get some context before the match to check if it's already safe
        start_pos = max(0, match.start() - 100)
        context_before = content[start_pos:match.start()]
        
        if 'self._create_safe_menu_response(' in context_before:
            return match.group(0)  # Already safe, don't change
        else:
            return replacement
    
    new_content = re.sub(pattern, replace_func, content)
    
    # Also handle MenuResponse instantiations not in return statements
    pattern2 = r'MenuResponse\s*\('
    def replace_func2(match):
        # Get context to check if this is inside a return statement we just processed
        start_pos = max(0, match.start() - 50)
        context_before = new_content[start_pos:match.start()]
        
        if 'return self._create_safe_menu_response(' in context_before:
            return match.group(0)  # Already handled
        elif 'return' in context_before and 'MenuResponse' in context_before:
            return 'self._create_safe_menu_response('
        else:
            return match.group(0)  # Leave other cases as-is for now
    
    new_content = re.sub(pattern2, replace_func2, new_content)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Count new instances
    new_safe_count = len(re.findall(r'self\._create_safe_menu_response\(', new_content))
    remaining_unsafe = len(re.findall(r'return MenuResponse\(', new_content))
    
    print(f"✅ Fixed MenuResponse instantiations in {file_path}")
    print(f"   Original unsafe: {original_count}")
    print(f"   Converted to safe: {new_safe_count}")
    print(f"   Remaining unsafe: {remaining_unsafe}")
    
    return new_safe_count, remaining_unsafe

if __name__ == "__main__":
    file_path = "/home/azureuser/repos/bolt_ok/mybot/services/enhanced_diana_menu_system.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    try:
        safe_count, unsafe_count = fix_menu_response_instantiations(file_path)
        
        if unsafe_count == 0:
            print("🎉 All MenuResponse instantiations have been converted to safe versions!")
        else:
            print(f"⚠️  {unsafe_count} MenuResponse instantiations still need manual review")
            
    except Exception as e:
        print(f"❌ Error fixing MenuResponse instantiations: {e}")
        sys.exit(1)