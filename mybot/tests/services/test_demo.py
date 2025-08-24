"""
Demo test file to verify pytest setup.
"""
import pytest


class TestDemo:
    """Demo test cases."""
    
    def test_basic_assertion(self):
        """Basic assertion test."""
        assert True
        
    def test_simple_math(self):
        """Simple math test."""
        assert 1 + 1 == 2
        
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Async test function."""
        # Simulate async operation
        result = await self._async_demo()
        assert result == "success"
        
    async def _async_demo(self):
        """Demo async function."""
        return "success"