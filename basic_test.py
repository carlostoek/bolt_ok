#!/usr/bin/env python3
"""
Basic functionality tests for Botmaestro components.
"""
import asyncio
import sys
import os

# Set up environment
os.environ.setdefault('BOT_TOKEN', 'test_token_12345')
os.environ.setdefault('ADMIN_IDS', '123456789')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test.db')

# Add mybot to path
sys.path.insert(0, '/data/data/com.termux/files/home/repos/bolt_ok/mybot')

def test_basic_imports():
    """Test basic module imports"""
    print("🧪 Testing basic imports...")
    
    results = []
    
    # Test config loading
    try:
        from utils.config import Config
        results.append(("Config module", True, f"Database: {Config.DATABASE_URL}"))
    except Exception as e:
        results.append(("Config module", False, str(e)))
    
    # Test database base
    try:
        from database.base import Base
        results.append(("Database base", True, "Base class loaded"))
    except Exception as e:
        results.append(("Database base", False, str(e)))
    
    # Test database models
    try:
        from database.models import User, Achievement, Mission
        results.append(("Database models", True, "Core models loaded"))
    except Exception as e:
        results.append(("Database models", False, str(e)))
    
    # Test utilities
    try:
        from utils.text_utils import sanitize_text
        test_input = "Test <script>alert(1)</script> message"
        sanitized = sanitize_text(test_input)
        results.append(("Text utilities", True, f"Sanitization works: '{sanitized}'"))
    except Exception as e:
        results.append(("Text utilities", False, str(e)))
    
    # Test menu utilities
    try:
        from utils.menu_utils import create_navigation_keyboard
        results.append(("Menu utilities", True, "Navigation utilities loaded"))
    except Exception as e:
        results.append(("Menu utilities", False, str(e)))
    
    return results

def test_service_structure():
    """Test service layer structure"""
    print("🔧 Testing service structure...")
    
    results = []
    
    # Test point service
    try:
        from services.point_service import PointService
        results.append(("Point Service", True, "Service class loaded"))
    except Exception as e:
        results.append(("Point Service", False, str(e)))
    
    # Test user service
    try:
        from services.user_service import UserService
        results.append(("User Service", True, "Service class loaded"))
    except Exception as e:
        results.append(("User Service", False, str(e)))
    
    # Test narrative service
    try:
        from services.narrative_service import NarrativeService
        results.append(("Narrative Service", True, "Service class loaded"))
    except Exception as e:
        results.append(("Narrative Service", False, str(e)))
    
    return results

def test_handler_structure():
    """Test handler structure"""
    print("📱 Testing handler structure...")
    
    results = []
    
    # Test main menu handler
    try:
        from handlers.main_menu import router as main_menu_router
        results.append(("Main Menu Handler", True, "Router loaded"))
    except Exception as e:
        results.append(("Main Menu Handler", False, str(e)))
    
    # Test start handler
    try:
        from handlers.start import router as start_router
        results.append(("Start Handler", True, "Router loaded"))
    except Exception as e:
        results.append(("Start Handler", False, str(e)))
    
    return results

def print_results(test_name, results):
    """Print test results in a formatted way"""
    print(f"\n📊 {test_name} Results:")
    print("=" * 50)
    
    passed = 0
    for test, success, details in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test}")
        if details:
            print(f"    {details}")
        if success:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed ({passed/len(results)*100:.1f}%)")
    return passed == len(results)

def main():
    """Run all basic tests"""
    print("🚀 Ejecutando tests básicos del sistema Botmaestro")
    print("=" * 60)
    
    all_passed = True
    
    # Run test suites
    import_results = test_basic_imports()
    all_passed &= print_results("Basic Imports", import_results)
    
    service_results = test_service_structure()
    all_passed &= print_results("Service Structure", service_results)
    
    handler_results = test_handler_structure()
    all_passed &= print_results("Handler Structure", handler_results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ¡TODOS LOS TESTS BÁSICOS PASARON! Los componentes principales están funcionando.")
    else:
        print("⚠️  Algunos tests básicos fallaron. El sistema puede tener problemas de configuración.")
    
    total_tests = len(import_results) + len(service_results) + len(handler_results)
    print(f"\n📈 Total: {total_tests} tests básicos ejecutados")

if __name__ == "__main__":
    main()