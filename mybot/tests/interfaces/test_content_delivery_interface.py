import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Union

from services.interfaces.content_delivery_interface import (
    IContentDeliveryService, ContentType, DeliveryChannel, 
    ContentPackage
)
from services.emotional_state_service import EmotionalState

class DeliveryContext:
    def __init__(self, user_id, channel, emotional_state, personalization_data, delivery_constraints):
        self.user_id = user_id
        self.channel = channel
        self.emotional_state = emotional_state
        self.personalization_data = personalization_data
        self.delivery_constraints = delivery_constraints

class TestContentDeliveryInterface:
    """Tests TDD para IContentDeliveryService"""
    
    @pytest_asyncio.fixture
    async def content_delivery_service(self, mock_session):
        """Mock del servicio de entrega de contenido"""
        service = AsyncMock(spec=IContentDeliveryService)
        service.session = mock_session
        service.prepare_content = AsyncMock()
        service.deliver_content = AsyncMock()
        service.personalize_content = AsyncMock()
        service.validate_delivery_constraints = AsyncMock()
        return service

    @pytest.fixture
    def sample_delivery_context(self, sample_user_id):
        """Contexto de entrega de ejemplo"""
        return DeliveryContext(
            user_id=sample_user_id,
            channel=DeliveryChannel.DIRECT_MESSAGE,
            emotional_state=EmotionalState.NEUTRAL,
            personalization_data={"language": "es", "tone": "friendly"},
            delivery_constraints={"max_length": 4000}
        )

    @pytest.fixture
    def sample_content_package(self):
        """Paquete de contenido de ejemplo"""
        return ContentPackage(
            content_id="fragment_001",
            content_type=ContentType.TEXT,
            payload="Texto de ejemplo",
            metadata={"title": "Fragmento 1", "category": "story"},
            delivery_options={"parse_mode": "Markdown"}
        )

    @pytest.mark.asyncio
    async def test_prepare_content_valid_context_returns_personalized_package(
        self, content_delivery_service, sample_delivery_context, sample_content_package
    ):
        """Test: Contexto válido debe retornar paquete personalizado"""
        # Arrange
        content_id = "fragment_001"
        content_delivery_service.prepare_content.return_value = sample_content_package
        
        # Act
        result = await content_delivery_service.prepare_content(content_id, sample_delivery_context)
        
        # Assert
        assert result.content_id == content_id
        assert result.content_type == ContentType.TEXT
        assert isinstance(result.payload, str)
        content_delivery_service.prepare_content.assert_called_once_with(
            content_id, sample_delivery_context
        )

    @pytest.mark.asyncio
    async def test_prepare_content_invalid_content_id_raises_not_found_error(
        self, content_delivery_service, sample_delivery_context
    ):
        """Test: ID de contenido inválido debe lanzar error NotFound"""
        # Arrange
        invalid_content_id = "nonexistent_fragment"
        content_delivery_service.prepare_content.side_effect = ValueError(
            f"Content not found: {invalid_content_id}"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Content not found"):
            await content_delivery_service.prepare_content(
                invalid_content_id, sample_delivery_context
            )

    @pytest.mark.asyncio
    async def test_deliver_content_direct_message_channel_sends_successfully(
        self, content_delivery_service, sample_content_package, sample_delivery_context
    ):
        """Test: Canal de mensaje directo debe enviar exitosamente"""
        # Arrange
        content_delivery_service.deliver_content.return_value = True
        
        # Act
        result = await content_delivery_service.deliver_content(
            sample_content_package, sample_delivery_context
        )
        
        # Assert
        assert result is True
        content_delivery_service.deliver_content.assert_called_once_with(
            sample_content_package, sample_delivery_context
        )

    @pytest.mark.asyncio
    async def test_deliver_content_invalid_channel_returns_false(
        self, content_delivery_service, sample_content_package, sample_delivery_context
    ):
        """Test: Canal inválido debe retornar False"""
        # Arrange
        sample_delivery_context.channel = None  # Canal inválido
        content_delivery_service.deliver_content.return_value = False
        
        # Act
        result = await content_delivery_service.deliver_content(
            sample_content_package, sample_delivery_context
        )
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_personalize_content_emotional_context_adapts_tone(
        self, content_delivery_service, sample_delivery_context
    ):
        """Test: Contexto emocional debe adaptar el tono del contenido"""
        # Arrange
        original_content = "Este es un mensaje neutral."
        sample_delivery_context.emotional_state = EmotionalState.EXCITED
        expected_content = "¡Este es un mensaje emocionante!"
        content_delivery_service.personalize_content.return_value = expected_content
        
        # Act
        result = await content_delivery_service.personalize_content(
            original_content, sample_delivery_context
        )
        
        # Assert
        assert result == expected_content
        assert result != original_content
        content_delivery_service.personalize_content.assert_called_once_with(
            original_content, sample_delivery_context
        )

    @pytest.mark.asyncio
    async def test_personalize_content_no_context_returns_original(
        self, content_delivery_service, sample_delivery_context
    ):
        """Test: Sin contexto emocional debe retornar contenido original"""
        # Arrange
        original_content = "Contenido sin personalizar."
        sample_delivery_context.emotional_state = EmotionalState.NEUTRAL
        content_delivery_service.personalize_content.return_value = original_content
        
        # Act
        result = await content_delivery_service.personalize_content(
            original_content, sample_delivery_context
        )
        
        # Assert
        assert result == original_content

    @pytest.mark.asyncio
    async def test_validate_delivery_constraints_valid_package_returns_true(
        self, content_delivery_service, sample_content_package, sample_delivery_context
    ):
        """Test: Paquete válido debe pasar validación de restricciones"""
        # Arrange
        content_delivery_service.validate_delivery_constraints.return_value = (True, [])
        
        # Act
        is_valid, errors = await content_delivery_service.validate_delivery_constraints(
            sample_content_package, sample_delivery_context
        )
        
        # Assert
        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_delivery_constraints_violates_constraints_returns_false_with_errors(
        self, content_delivery_service, sample_content_package, sample_delivery_context
    ):
        """Test: Violación de restricciones debe retornar False con errores"""
        # Arrange
        sample_content_package.payload = "A" * 5000  # Excede max_length
        expected_errors = ["Content exceeds maximum length of 4000 characters"]
        content_delivery_service.validate_delivery_constraints.return_value = (False, expected_errors)
        
        # Act
        is_valid, errors = await content_delivery_service.validate_delivery_constraints(
            sample_content_package, sample_delivery_context
        )
        
        # Assert
        assert is_valid is False
        assert len(errors) > 0
        assert "exceeds maximum length" in errors[0]