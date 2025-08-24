"""
Test to verify the integrity of the narrative test infrastructure.

This test ensures that all the required test files and components are in place.
"""
import pytest
import os
import importlib.util
import sys


class TestInfrastructureIntegrity:
    """Tests to verify that the narrative test infrastructure is intact."""
    
    def test_conftest_exists(self):
        """Test that conftest.py exists and can be imported."""
        conftest_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conftest.py")
        assert os.path.exists(conftest_path), "conftest.py not found"
        
        # Attempt to import conftest
        spec = importlib.util.spec_from_file_location("conftest", conftest_path)
        conftest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conftest)
        
        # Check some essential fixtures are defined
        assert hasattr(conftest, "mock_db_setup"), "mock_db_setup fixture not found in conftest.py"
        assert hasattr(conftest, "bot_mock"), "bot_mock fixture not found in conftest.py"
        assert hasattr(conftest, "mock_story_fragments"), "mock_story_fragments fixture not found in conftest.py"
    
    def test_narrative_test_files_exist(self):
        """Test that all narrative test files exist."""
        test_files = [
            "test_narrative_engine.py",
            "test_narrative_flow.py",
            "test_emotional_states.py",
            "test_narrative_rewards.py",
            "test_user_journey.py"
        ]
        
        for test_file in test_files:
            file_path = os.path.join(os.path.dirname(__file__), test_file)
            assert os.path.exists(file_path), f"{test_file} not found"
    
    def test_run_script_exists(self):
        """Test that the run_narrative_tests.py script exists."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "run_narrative_tests.py")
        assert os.path.exists(script_path), "run_narrative_tests.py not found"
    
    def test_documentation_exists(self):
        """Test that documentation files exist."""
        readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README_NARRATIVE_TESTS.md")
        assert os.path.exists(readme_path), "README_NARRATIVE_TESTS.md not found"
        
        summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "NARRATIVE_TEST_INFRASTRUCTURE_SUMMARY.md")
        assert os.path.exists(summary_path), "NARRATIVE_TEST_INFRASTRUCTURE_SUMMARY.md not found"
    
    def test_test_categories_defined(self):
        """Test that all test categories are defined in run_narrative_tests.py."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "run_narrative_tests.py")
        
        # Import the script as a module
        spec = importlib.util.spec_from_file_location("run_narrative_tests", script_path)
        run_script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_script)
        
        # Check test categories
        categories = getattr(run_script, "TEST_CATEGORIES", {})
        expected_categories = ["all", "basic", "flow", "emotional", "rewards", "journey", "demo"]
        
        for category in expected_categories:
            assert category in categories, f"Category '{category}' not defined in TEST_CATEGORIES"