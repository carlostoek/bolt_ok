"""
Test file for NarrativeAdminService validation functionality.
"""
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestNarrativeAdminService(unittest.IsolatedAsyncioTestCase):
    """Test the NarrativeAdminService validation functionality."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Mock the database session
        self.mock_session = AsyncMock()
        self.mock_session.execute = AsyncMock()
        self.mock_session.add = AsyncMock()
        self.mock_session.commit = AsyncMock()
        self.mock_session.rollback = AsyncMock()
        self.mock_session.refresh = AsyncMock()
        
        # Import the service after mocking dependencies
        with patch('database.narrative_models') as mock_models:
            # Mock the StoryFragment and NarrativeChoice models
            mock_story_fragment = MagicMock()
            mock_story_fragment.key = "test_fragment"
            mock_models.StoryFragment.return_value = mock_story_fragment
            
            mock_narrative_choice = MagicMock()
            mock_models.NarrativeChoice.return_value = mock_narrative_choice
            
            # Mock the select function
            with patch('sqlalchemy.select') as mock_select:
                mock_select.return_value = MagicMock()
                
                # Now we can import the service
                from services.narrative_admin_service import NarrativeAdminService
                self.service = NarrativeAdminService(self.mock_session)
    
    async def test_create_story_fragment_valid(self):
        """Test creating a valid story fragment."""
        # Mock that the fragment doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result
        
        fragment_data = {
            "key": "test_fragment_1",
            "text": "This is a test fragment.",
            "character": "Diana",
            "level": 1
        }
        
        result = await self.service.create_story_fragment(fragment_data)
        print(f"Create valid fragment result: {result}")
        
        # Should succeed
        self.assertEqual(result["status"], "success")
    
    async def test_create_story_fragment_invalid(self):
        """Test creating an invalid story fragment."""
        fragment_data = {
            "key": "invalid key",  # Invalid key with space
            "text": ""  # Empty text
        }
        
        result = await self.service.create_story_fragment(fragment_data)
        print(f"Create invalid fragment result: {result}")
        
        # Should fail validation
        self.assertEqual(result["status"], "validation_error")
        self.assertIn("errors", result)
    
    async def test_create_story_fragment_duplicate(self):
        """Test creating a fragment with duplicate key."""
        # Mock that the fragment already exists
        mock_fragment = MagicMock()
        mock_fragment.key = "existing_fragment"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_fragment
        self.mock_session.execute.return_value = mock_result
        
        fragment_data = {
            "key": "existing_fragment",
            "text": "This is a duplicate fragment."
        }
        
        result = await self.service.create_story_fragment(fragment_data)
        print(f"Create duplicate fragment result: {result}")
        
        # Should fail with duplicate error
        self.assertEqual(result["status"], "error")
        self.assertIn("already exists", result["message"])
    
    async def test_update_story_fragment_not_found(self):
        """Test updating a non-existent fragment."""
        # Mock that the fragment doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result
        
        updates = {
            "text": "Updated text"
        }
        
        result = await self.service.update_story_fragment("nonexistent_fragment", updates)
        print(f"Update nonexistent fragment result: {result}")
        
        # Should fail with not found error
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])
    
    async def test_delete_story_fragment_not_found(self):
        """Test deleting a non-existent fragment."""
        # Mock that the fragment doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result
        
        result = await self.service.delete_story_fragment("nonexistent_fragment")
        print(f"Delete nonexistent fragment result: {result}")
        
        # Should fail with not found error
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])
    
    async def test_delete_start_fragment(self):
        """Test deleting the start fragment (should be prevented)."""
        # Mock that the start fragment exists
        mock_fragment = MagicMock()
        mock_fragment.key = "start"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_fragment
        self.mock_session.execute.return_value = mock_result
        
        result = await self.service.delete_story_fragment("start")
        print(f"Delete start fragment result: {result}")
        
        # Should fail with cannot delete error
        self.assertEqual(result["status"], "error")
        self.assertIn("Cannot delete", result["message"])

if __name__ == "__main__":
    unittest.main()