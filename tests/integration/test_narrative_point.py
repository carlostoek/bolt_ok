"""
Tests for the NarrativePointService integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mybot.services.integration.narrative_point_service import NarrativePointService

@pytest.mark.asyncio
async def test_can_make_decision_no_points_required():
    """Test that decisions with no point requirements are always allowed."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativePointService(session_mock)
    
    # Mock decision query
    decision_mock = MagicMock()
    decision_mock.points_required = None
    
    session_mock.execute = AsyncMock()
    session_mock.execute.return_value.scalar_one_or_none.return_value = decision_mock
    
    # Test
    result = await service.can_make_decision(123, 456)
    
    # Assert
    assert result is True
    session_mock.execute.assert_called_once()

@pytest.mark.asyncio
async def test_can_make_decision_sufficient_points():
    """Test that decisions with point requirements are allowed when user has enough points."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativePointService(session_mock)
    
    # Mock decision query
    decision_mock = MagicMock()
    decision_mock.points_required = 10
    
    session_mock.execute = AsyncMock()
    session_mock.execute.return_value.scalar_one_or_none.return_value = decision_mock
    
    # Mock point service
    service.point_service.get_user_points = AsyncMock(return_value=15)
    
    # Test
    result = await service.can_make_decision(123, 456)
    
    # Assert
    assert result is True
    service.point_service.get_user_points.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_can_make_decision_insufficient_points():
    """Test that decisions with point requirements are denied when user has insufficient points."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativePointService(session_mock)
    
    # Mock decision query
    decision_mock = MagicMock()
    decision_mock.points_required = 20
    
    session_mock.execute = AsyncMock()
    session_mock.execute.return_value.scalar_one_or_none.return_value = decision_mock
    
    # Mock point service
    service.point_service.get_user_points = AsyncMock(return_value=15)
    
    # Test
    result = await service.can_make_decision(123, 456)
    
    # Assert
    assert result is False
    service.point_service.get_user_points.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_process_decision_with_points_success():
    """Test successful processing of a decision with point rewards."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativePointService(session_mock)
    
    # Mock methods
    service.can_make_decision = AsyncMock(return_value=True)
    
    # Mock decision query
    decision_mock = MagicMock()
    decision_mock.points_required = 5
    decision_mock.points_awarded = 10
    
    session_mock.execute = AsyncMock()
    session_mock.execute.return_value.scalar_one_or_none.return_value = decision_mock
    
    # Mock services
    service.point_service.deduct_points = AsyncMock()
    service.point_service.add_points = AsyncMock()
    
    # Mock narrative service
    fragment_mock = MagicMock()
    service.narrative_service.process_user_decision = AsyncMock(return_value=fragment_mock)
    
    # Test
    result = await service.process_decision_with_points(123, 456)
    
    # Assert
    assert result["type"] == "success"
    assert result["fragment"] == fragment_mock
    service.point_service.deduct_points.assert_called_once_with(123, 5)
    service.point_service.add_points.assert_called_once()
    service.narrative_service.process_user_decision.assert_called_once_with(123, 456)
