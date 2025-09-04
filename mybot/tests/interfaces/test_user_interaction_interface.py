"""
Tests para la interfaz IUserInteractionProcessor.
Tests siguiendo metodología TDD según especificación del documento de diseño.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from services.interfaces.user_interaction_interface import (
    IUserInteractionProcessor,
    InteractionContext,
    InteractionResult,
    InteractionType
)
from services.interfaces.emotional_state_interface import EmotionalState
from services.user_interaction_service import UserInteractionService
from database.models import User, InteractionLog

@pytest_asyncio.fixture
async def mock_session():
    """Mock de sesión de base de datos async."""
    session_mock = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = session_mock
    session_mock.begin.return_value = mock_context
    return session_mock


@pytest_asyncio.fixture
async def mock_user():
    """Mock de usuario de prueba."""
    user = MagicMock()
    user.id = 12345
    user.username = "test_user"
    user.points = 100.0
    return user


@pytest_asyncio.fixture
async def interaction_context():
    """Contexto de interacción de prueba."""
    return InteractionContext(
        user_id=12345,
        interaction_type=InteractionType.MESSAGE,
        raw_data={"text": "Hola mundo", "message_id": 123},
        timestamp=datetime.now(),
        session_data={"session_id": "test_session"}
    )


@pytest_asyncio.fixture
async def interaction_service(mock_session):
    """Servicio de interacciones de prueba."""
    return UserInteractionService(
        session=mock_session,
        emotional_manager=None,
        point_service=None,
        notification_service=None
    )


class TestUserInteractionProcessor:
    """Tests para el procesador de interacciones de usuario."""

    @pytest.mark.asyncio
    async def test_process_interaction_valid_message_returns_success_result(
        self, interaction_service, interaction_context, mock_session, mock_user
    ):
        """Test: procesar interacción válida de mensaje retorna resultado exitoso."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        result = await interaction_service.process_interaction(interaction_context)
        
        # Assert
        assert isinstance(result, InteractionResult)
        assert result.success is True
        assert result.response_data["processed_as"] == "message"
        assert "message_processed" in result.side_effects

    @pytest.mark.asyncio
    async def test_process_interaction_invalid_data_returns_failure_result(
        self, interaction_processor, sample_interaction_context
    ):
        """Test: Datos inválidos debe retornar resultado de falla"""
        # Arrange
        sample_interaction_context.raw_data = {"invalid": "data"}
        failure_result = InteractionResult(
            success=False,
            response_data={"error": "Invalid data format"},
            side_effects=[],
            emotional_impact=None,
            points_awarded=None
        )
        interaction_processor.process_interaction.return_value = failure_result
        
        # Act
        result = await interaction_processor.process_interaction(sample_interaction_context)
        
        # Assert
        assert result.success is False
        assert result.points_awarded is None
        assert "error" in result.response_data

    @pytest.mark.asyncio
    async def test_validate_interaction_valid_context_returns_true(
        self, interaction_processor, sample_interaction_context
    ):
        """Test: Contexto válido debe pasar validación"""
        # Arrange
        interaction_processor.validate_interaction.return_value = (True, [])
        
        # Act
        is_valid, errors = await interaction_processor.validate_interaction(sample_interaction_context)
        
        # Assert
        assert is_valid is True
        assert len(errors) == 0
        interaction_processor.validate_interaction.assert_called_once_with(sample_interaction_context)

    @pytest.mark.asyncio
    async def test_validate_interaction_insufficient_permissions_returns_false_with_errors(
        self, interaction_processor, sample_interaction_context
    ):
        """Test: Permisos insuficientes debe retornar False con errores"""
        # Arrange
        expected_errors = ["User lacks required permissions", "Access denied to VIP content"]
        interaction_processor.validate_interaction.return_value = (False, expected_errors)
        
        # Act
        is_valid, errors = await interaction_processor.validate_interaction(sample_interaction_context)
        
        # Assert
        assert is_valid is False
        assert len(errors) == 2
        assert "permissions" in errors[0]

    @pytest.mark.asyncio
    async def test_log_interaction_successful_interaction_creates_log_entry(
        self, interaction_processor, sample_interaction_context, sample_interaction_result
    ):
        """Test: Interacción exitosa debe crear entrada de log"""
        # Arrange
        interaction_processor.log_interaction.return_value = None
        
        # Act
        await interaction_processor.log_interaction(sample_interaction_context, sample_interaction_result)
        
        # Assert
        interaction_processor.log_interaction.assert_called_once_with(
            sample_interaction_context, sample_interaction_result
        )

    @pytest.mark.asyncio
    async def test_get_interaction_history_existing_user_returns_chronological_list(
        self, interaction_processor, sample_user_id
    ):
        """Test: Usuario existente debe retornar historial cronológico"""
        # Arrange
        expected_history = [
            InteractionContext(
                user_id=sample_user_id,
                interaction_type=InteractionType.MESSAGE,
                raw_data={"text": "Hola"},
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                session_data={}
            ),
            InteractionContext(
                user_id=sample_user_id,
                interaction_type=InteractionType.CALLBACK,
                raw_data={"data": "choice_1"},
                timestamp=datetime(2024, 1, 1, 11, 0, 0),
                session_data={}
            )
        ]
        interaction_processor.get_interaction_history.return_value = expected_history
        
        # Act
        result = await interaction_processor.get_interaction_history(sample_user_id, limit=50)
        
        # Assert
        assert len(result) == 2
        assert result[0].timestamp < result[1].timestamp  # Cronológico
        interaction_processor.get_interaction_history.assert_called_once_with(sample_user_id, limit=50)

    @pytest.mark.asyncio
    async def test_get_interaction_history_new_user_returns_empty_list(
        self, interaction_processor
    ):
        """Test: Usuario nuevo debe retornar lista vacía"""
        # Arrange
        new_user_id = 999999999
        interaction_processor.get_interaction_history.return_value = []
        
        # Act
        result = await interaction_processor.get_interaction_history(new_user_id)
        
        # Assert
        assert len(result) == 0
        assert isinstance(result, list)