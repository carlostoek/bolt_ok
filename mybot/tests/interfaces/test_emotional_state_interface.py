import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Importar la interfaz real
from services.interfaces.emotional_state_interface import (
    IEmotionalStateManager, EmotionalState, EmotionalContext
)

class TestEmotionalStateInterface:
    """Tests TDD para IEmotionalStateManager"""
    
    @pytest_asyncio.fixture
    async def emotional_state_service(self, mock_session):
        """Mock del servicio de estados emocionales"""
        service = AsyncMock(spec=IEmotionalStateManager)
        service.session = mock_session
        return service

    @pytest_asyncio.fixture
    async def sample_emotional_context(self, sample_timestamp):
        """Contexto emocional de ejemplo"""
        return EmotionalContext(
            primary_state=EmotionalState.NEUTRAL,
            intensity=0.5,
            secondary_states={},
            last_updated=sample_timestamp,
            triggers=[]
        )

    @pytest.mark.asyncio
    async def test_get_user_emotional_state_new_user_returns_neutral(
        self, emotional_state_service, sample_user_id
    ):
        """Test: Usuario nuevo debe retornar estado emocional neutral"""
        # Arrange
        expected_context = EmotionalContext(
            primary_state=EmotionalState.NEUTRAL,
            intensity=0.0,
            secondary_states={},
            last_updated=datetime.now(),
            triggers=[]
        )
        emotional_state_service.get_user_emotional_state.return_value = expected_context
        
        # Act
        result = await emotional_state_service.get_user_emotional_state(sample_user_id)
        
        # Assert
        assert result.primary_state == EmotionalState.NEUTRAL
        assert result.intensity == 0.0
        assert len(result.triggers) == 0
        emotional_state_service.get_user_emotional_state.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_user_emotional_state_existing_user_returns_current_state(
        self, emotional_state_service, sample_user_id, sample_emotional_context
    ):
        """Test: Usuario existente debe retornar su estado actual"""
        # Arrange
        sample_emotional_context.primary_state = EmotionalState.ENGAGED
        sample_emotional_context.intensity = 0.8
        emotional_state_service.get_user_emotional_state.return_value = sample_emotional_context
        
        # Act
        result = await emotional_state_service.get_user_emotional_state(sample_user_id)
        
        # Assert
        assert result.primary_state == EmotionalState.ENGAGED
        assert result.intensity == 0.8
        emotional_state_service.get_user_emotional_state.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_emotional_state_valid_parameters_updates_successfully(
        self, emotional_state_service, sample_user_id, sample_emotional_context
    ):
        """Test: Actualización de estado emocional con parámetros válidos"""
        # Arrange
        new_state = EmotionalState.EXCITED
        intensity = 0.9
        trigger = "completed_fragment"
        
        updated_context = EmotionalContext(
            primary_state=new_state,
            intensity=intensity,
            secondary_states={EmotionalState.SATISFIED: 0.3},
            last_updated=datetime.now(),
            triggers=[trigger]
        )
        emotional_state_service.update_emotional_state.return_value = updated_context
        
        # Act
        result = await emotional_state_service.update_emotional_state(
            sample_user_id, new_state, intensity, trigger
        )
        
        # Assert
        assert result.primary_state == new_state
        assert result.intensity == intensity
        assert trigger in result.triggers
        emotional_state_service.update_emotional_state.assert_called_once_with(
            sample_user_id, new_state, intensity, trigger
        )

    @pytest.mark.asyncio
    async def test_update_emotional_state_invalid_intensity_raises_validation_error(
        self, emotional_state_service, sample_user_id
    ):
        """Test: Intensidad inválida debe lanzar error de validación"""
        # Arrange
        invalid_intensity = 1.5  # > 1.0
        emotional_state_service.update_emotional_state.side_effect = ValueError(
            "Intensity must be between 0.0 and 1.0"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Intensity must be between 0.0 and 1.0"):
            await emotional_state_service.update_emotional_state(
                sample_user_id, EmotionalState.EXCITED, invalid_intensity, "test"
            )

    @pytest.mark.asyncio
    async def test_analyze_interaction_emotion_positive_interaction_returns_engaged(
        self, emotional_state_service, sample_user_id
    ):
        """Test: Interacción positiva debe retornar estado engaged"""
        # Arrange
        interaction_data = {
            "type": "fragment_completion",
            "completion_time": 30,  # rápido
            "user_choice": "positive_option"
        }
        emotional_state_service.analyze_interaction_emotion.return_value = EmotionalState.ENGAGED
        
        # Act
        result = await emotional_state_service.analyze_interaction_emotion(
            sample_user_id, interaction_data
        )
        
        # Assert
        assert result == EmotionalState.ENGAGED
        emotional_state_service.analyze_interaction_emotion.assert_called_once_with(
            sample_user_id, interaction_data
        )

    @pytest.mark.asyncio
    async def test_analyze_interaction_emotion_negative_interaction_returns_frustrated(
        self, emotional_state_service, sample_user_id
    ):
        """Test: Interacción negativa debe retornar estado frustrated"""
        # Arrange
        interaction_data = {
            "type": "failed_attempt",
            "attempts": 5,
            "completion_time": 300  # muy lento
        }
        emotional_state_service.analyze_interaction_emotion.return_value = EmotionalState.FRUSTRATED
        
        # Act
        result = await emotional_state_service.analyze_interaction_emotion(
            sample_user_id, interaction_data
        )
        
        # Assert
        assert result == EmotionalState.FRUSTRATED

    @pytest.mark.asyncio
    async def test_get_recommended_content_tone_excited_state_returns_energetic(
        self, emotional_state_service, sample_user_id
    ):
        """Test: Estado excited debe recomendar tono energético"""
        # Arrange
        emotional_state_service.get_recommended_content_tone.return_value = "energetic"
        
        # Act
        result = await emotional_state_service.get_recommended_content_tone(sample_user_id)
        
        # Assert
        assert result == "energetic"

    @pytest.mark.asyncio
    async def test_get_recommended_content_tone_confused_state_returns_supportive(
        self, emotional_state_service, sample_user_id
    ):
        """Test: Estado confused debe recomendar tono supportive"""
        # Arrange
        emotional_state_service.get_recommended_content_tone.return_value = "supportive"
        
        # Act
        result = await emotional_state_service.get_recommended_content_tone(sample_user_id)
        
        # Assert
        assert result == "supportive"