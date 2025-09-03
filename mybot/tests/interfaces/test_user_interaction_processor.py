"""
Tests para la implementación del procesador de interacciones de usuario.
Tests de integración para UserInteractionProcessor y UserInteractionService.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from services.interfaces.user_interaction_interface import (
    InteractionContext,
    InteractionResult,
    InteractionType
)
from services.interfaces.emotional_state_interface import EmotionalState
from services.user_interaction_service import UserInteractionService
from services.user_interaction_processor import UserInteractionProcessor
from database.models import User, InteractionLog
from aiogram.types import Message, CallbackQuery


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
async def interaction_processor(mock_session):
    """Procesador de interacciones de prueba."""
    return UserInteractionProcessor(mock_session)


@pytest_asyncio.fixture
async def mock_message():
    """Mock de mensaje de Telegram."""
    message = MagicMock()
    message.from_user.id = 12345
    message.text = "Hola mundo"
    message.message_id = 123
    message.chat.id = -100123456789
    message.content_type = "text"
    message.date = datetime.now()
    message.photo = None
    message.document = None
    message.video = None
    return message


@pytest_asyncio.fixture
async def mock_callback():
    """Mock de callback query de Telegram."""
    callback = MagicMock()
    callback.from_user.id = 12345
    callback.data = "test_callback"
    callback.id = "callback123"
    callback.message.message_id = 123
    callback.message.chat.id = -100123456789
    callback.inline_message_id = None
    return callback


class TestUserInteractionProcessor:
    """Tests para el procesador principal de interacciones."""
    
    @pytest.mark.asyncio
    async def test_process_message_interaction_creates_correct_context(
        self, interaction_processor, mock_message, mock_session, mock_user
    ):
        """Test: procesar mensaje crea contexto correcto."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        result = await interaction_processor.process_message_interaction(mock_message)
        
        # Assert
        assert result is not None
        assert isinstance(result, InteractionResult)
        # Verificar que se llamaron los métodos de la sesión (logging)
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_callback_interaction_creates_correct_context(
        self, interaction_processor, mock_callback, mock_session, mock_user
    ):
        """Test: procesar callback crea contexto correcto."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        result = await interaction_processor.process_callback_interaction(mock_callback)
        
        # Assert
        assert result is not None
        assert isinstance(result, InteractionResult)
        # Verificar que se registró la interacción
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_command_interaction_handles_command_parsing(
        self, interaction_processor, mock_message, mock_session, mock_user
    ):
        """Test: procesar comando maneja parsing correctamente."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        command = "start"
        args = "referral_123"
        
        # Act
        result = await interaction_processor.process_command_interaction(
            mock_message, command, args
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, InteractionResult)
        mock_session.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_reaction_interaction_handles_emoji_reactions(
        self, interaction_processor, mock_session, mock_user
    ):
        """Test: procesar reacción maneja emojis correctamente."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        user_id = 12345
        emoji = "❤️"
        target_message_id = 456
        
        # Act
        result = await interaction_processor.process_reaction_interaction(
            user_id, emoji, target_message_id
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, InteractionResult)
        mock_session.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_set_dependencies_configures_services_correctly(
        self, interaction_processor, mock_session
    ):
        """Test: configurar dependencias las asigna correctamente."""
        # Arrange
        mock_emotional_manager = AsyncMock()
        mock_point_service = AsyncMock()
        mock_notification_service = AsyncMock()
        
        # Act
        interaction_processor.set_dependencies(
            emotional_manager=mock_emotional_manager,
            point_service=mock_point_service,
            notification_service=mock_notification_service
        )
        
        # Assert
        service = interaction_processor._get_service()
        assert service.emotional_manager == mock_emotional_manager
        assert service.point_service == mock_point_service
        assert service.notification_service == mock_notification_service
    
    @pytest.mark.asyncio
    async def test_get_user_interaction_history_returns_correct_format(
        self, interaction_processor, mock_session
    ):
        """Test: obtener historial retorna formato correcto."""
        # Arrange
        user_id = 12345
        mock_logs = [
            MagicMock(
                user_id=user_id,
                interaction_type="message",
                raw_data={"text": "test"},
                created_at=datetime.now(),
                session_data={}
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_logs
        
        # Act
        history = await interaction_processor.get_user_interaction_history(user_id)
        
        # Assert
        assert isinstance(history, list)
        mock_session.execute.assert_called()


class TestUserInteractionService:
    """Tests para el servicio base de interacciones."""
    
    @pytest_asyncio.fixture
    async def interaction_service(self, mock_session):
        """Servicio de interacciones de prueba."""
        return UserInteractionService(
            session=mock_session,
            emotional_manager=None,
            point_service=None,
            notification_service=None
        )
    
    @pytest_asyncio.fixture
    async def interaction_context(self):
        """Contexto de interacción de prueba."""
        return InteractionContext(
            user_id=12345,
            interaction_type=InteractionType.MESSAGE,
            raw_data={"text": "Hola mundo", "message_id": 123},
            timestamp=datetime.now(),
            session_data={"session_id": "test_session"}
        )
    
    @pytest.mark.asyncio
    async def test_validate_interaction_valid_context_returns_true(
        self, interaction_service, interaction_context, mock_session, mock_user
    ):
        """Test: validar contexto válido retorna True."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        is_valid, errors = await interaction_service.validate_interaction(interaction_context)
        
        # Assert
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_interaction_missing_user_returns_false(
        self, interaction_service, interaction_context, mock_session
    ):
        """Test: validar con usuario faltante retorna False."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Act
        is_valid, errors = await interaction_service.validate_interaction(interaction_context)
        
        # Assert
        assert is_valid is False
        assert any("not found" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_interaction_callback_missing_data_returns_false(
        self, interaction_service, mock_session, mock_user
    ):
        """Test: validar callback sin datos requeridos retorna False."""
        # Arrange
        callback_context = InteractionContext(
            user_id=12345,
            interaction_type=InteractionType.CALLBACK,
            raw_data={"invalid": "data"},  # Sin callback_data
            timestamp=datetime.now(),
            session_data={}
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        is_valid, errors = await interaction_service.validate_interaction(callback_context)
        
        # Assert
        assert is_valid is False
        assert any("callback_data required" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_process_interaction_with_emotional_manager_analyzes_emotion(
        self, interaction_service, interaction_context, mock_session, mock_user
    ):
        """Test: procesar con gestor emocional analiza emoción."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        mock_emotional_manager = AsyncMock()
        mock_emotional_manager.analyze_interaction_emotion.return_value = EmotionalState.ENGAGED
        interaction_service.emotional_manager = mock_emotional_manager
        
        # Act
        result = await interaction_service.process_interaction(interaction_context)
        
        # Assert
        assert result.emotional_impact == EmotionalState.ENGAGED
        assert "emotional_analysis_completed" in result.side_effects
        mock_emotional_manager.analyze_interaction_emotion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_interaction_with_point_service_awards_points(
        self, interaction_service, interaction_context, mock_session, mock_user
    ):
        """Test: procesar con servicio de puntos otorga puntos."""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        mock_point_service = AsyncMock()
        interaction_service.point_service = mock_point_service
        
        # Act
        result = await interaction_service.process_interaction(interaction_context)
        
        # Assert
        assert result.points_awarded == 1  # MESSAGE interaction base points
        assert "points_awarded" in result.side_effects
        mock_point_service.add_points.assert_called_once_with(12345, 1, "interaction_reward")
    
    @pytest.mark.asyncio
    async def test_log_interaction_creates_database_entry(
        self, interaction_service, interaction_context, mock_session
    ):
        """Test: registrar interacción crea entrada en base de datos."""
        # Arrange
        result = InteractionResult(
            success=True,
            response_data={"processed_as": "message"},
            side_effects=["message_processed"],
            emotional_impact=EmotionalState.SATISFIED,
            points_awarded=10
        )
        
        # Act
        await interaction_service.log_interaction(interaction_context, result)
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verificar el objeto creado
        added_log = mock_session.add.call_args[0][0]
        assert isinstance(added_log, InteractionLog)
        assert added_log.user_id == 12345
        assert added_log.interaction_type == "message"
        assert added_log.success is True
        assert added_log.emotional_impact == "satisfied"
        assert added_log.points_awarded == 10
    
    @pytest.mark.asyncio
    async def test_get_interaction_history_returns_chronological_order(
        self, interaction_service, mock_session
    ):
        """Test: obtener historial retorna orden cronológico."""
        # Arrange
        user_id = 12345
        mock_logs = [
            MagicMock(
                user_id=user_id,
                interaction_type="message",
                raw_data={"text": "mensaje 1"},
                created_at=datetime(2024, 1, 1, 10, 0, 0),
                session_data={}
            ),
            MagicMock(
                user_id=user_id,
                interaction_type="callback",
                raw_data={"callback_data": "test"},
                created_at=datetime(2024, 1, 1, 11, 0, 0),
                session_data={}
            )
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_logs
        
        # Act
        history = await interaction_service.get_interaction_history(user_id)
        
        # Assert
        assert len(history) == 2
        assert all(isinstance(ctx, InteractionContext) for ctx in history)
        assert history[0].user_id == user_id
    
    @pytest.mark.asyncio
    async def test_get_interaction_history_empty_for_new_user(
        self, interaction_service, mock_session
    ):
        """Test: historial vacío para usuario nuevo."""
        # Arrange
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Act
        history = await interaction_service.get_interaction_history(99999)
        
        # Assert
        assert isinstance(history, list)
        assert len(history) == 0
    
    @pytest.mark.asyncio
    async def test_get_interaction_history_negative_limit_raises_error(
        self, interaction_service
    ):
        """Test: límite negativo en historial genera error."""
        # Act & Assert
        with pytest.raises(ValueError, match="limit cannot be negative"):
            await interaction_service.get_interaction_history(12345, -1)
    
    @pytest.mark.asyncio
    async def test_calculate_interaction_points_returns_correct_values(
        self, interaction_service, interaction_context
    ):
        """Test: calcular puntos retorna valores correctos por tipo."""
        # Test MESSAGE (1 punto)
        points = await interaction_service._calculate_interaction_points(interaction_context)
        assert points == 1
        
        # Test CALLBACK (2 puntos)
        interaction_context.interaction_type = InteractionType.CALLBACK
        points = await interaction_service._calculate_interaction_points(interaction_context)
        assert points == 2
        
        # Test REACTION (3 puntos)
        interaction_context.interaction_type = InteractionType.REACTION
        points = await interaction_service._calculate_interaction_points(interaction_context)
        assert points == 3