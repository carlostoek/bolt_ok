import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import List

# Importar las interfaces existentes y las nuevas
# from services.interfaces.user_narrative_interface import IUserNarrativeService
# from services.interfaces.emotional_state_interface import EmotionalState, EmotionalContext
# from services.interfaces.content_delivery_interface import ContentPackage, DeliveryContext

# Definiciones temporales para los tests (serán reemplazadas por las interfaces reales)
class EmotionalState:
    ENGAGED = "engaged"
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    SATISFIED = "satisfied"
    EXCITED = "excited"

class ContentType:
    TEXT = "text"

class EmotionalContext:
    def __init__(self, primary_state, intensity, secondary_states, last_updated, triggers):
        self.primary_state = primary_state
        self.intensity = intensity
        self.secondary_states = secondary_states
        self.last_updated = last_updated
        self.triggers = triggers

class ContentPackage:
    def __init__(self, content_id, content_type, payload, metadata, delivery_options):
        self.content_id = content_id
        self.content_type = content_type
        self.payload = payload
        self.metadata = metadata
        self.delivery_options = delivery_options

class InteractionResult:
    def __init__(self, success, response_data, side_effects, emotional_impact, points_awarded):
        self.success = success
        self.response_data = response_data
        self.side_effects = side_effects
        self.emotional_impact = emotional_impact
        self.points_awarded = points_awarded

class IUserNarrativeService:
    """Interface temporal para tests (será extendida)"""
    pass

class TestUnifiedNarrativeInterface:
    """Tests TDD para IUserNarrativeService Enhanced"""
    
    @pytest_asyncio.fixture
    async def narrative_service(self, mock_session):
        """Mock del servicio narrativo unificado"""
        service = AsyncMock(spec=IUserNarrativeService)
        service.session = mock_session
        return service

    @pytest.fixture
    def sample_emotional_context_engaged(self, sample_timestamp):
        """Contexto emocional engaged para tests"""
        return EmotionalContext(
            primary_state=EmotionalState.ENGAGED,
            intensity=0.7,
            secondary_states={EmotionalState.CURIOUS: 0.3},
            last_updated=sample_timestamp,
            triggers=["successful_choice"]
        )

    @pytest.fixture
    def sample_content_package_adapted(self):
        """Paquete de contenido adaptado emocionalmente"""
        return ContentPackage(
            content_id="fragment_002",
            content_type=ContentType.TEXT,
            payload="¡Excelente elección! Tu decisión ha abierto nuevos caminos...",
            metadata={"emotional_tone": "excited", "adaptation_applied": True},
            delivery_options={"parse_mode": "Markdown"}
        )

    @pytest.mark.asyncio
    async def test_get_contextualized_fragment_with_emotional_context_adapts_content(
        self, narrative_service, sample_user_id, sample_emotional_context_engaged, 
        sample_content_package_adapted
    ):
        """Test: Contexto emocional debe adaptar el contenido del fragmento"""
        # Arrange
        fragment_id = "fragment_002"
        narrative_service.get_contextualized_fragment.return_value = sample_content_package_adapted
        
        # Act
        result = await narrative_service.get_contextualized_fragment(
            sample_user_id, fragment_id, sample_emotional_context_engaged
        )
        
        # Assert
        assert result.content_id == fragment_id
        assert result.metadata["emotional_tone"] == "excited"
        assert result.metadata["adaptation_applied"] is True
        assert "¡Excelente" in result.payload  # Tono adaptado
        narrative_service.get_contextualized_fragment.assert_called_once_with(
            sample_user_id, fragment_id, sample_emotional_context_engaged
        )

    @pytest.mark.asyncio
    async def test_get_contextualized_fragment_neutral_emotion_returns_standard_content(
        self, narrative_service, sample_user_id
    ):
        """Test: Emoción neutral debe retornar contenido estándar"""
        # Arrange
        fragment_id = "fragment_001"
        neutral_context = EmotionalContext(
            primary_state=EmotionalState.NEUTRAL,
            intensity=0.0,
            secondary_states={},
            last_updated=datetime.now(),
            triggers=[]
        )
        standard_package = ContentPackage(
            content_id=fragment_id,
            content_type=ContentType.TEXT,
            payload="Contenido estándar del fragmento.",
            metadata={"emotional_tone": "neutral"},
            delivery_options={}
        )
        narrative_service.get_contextualized_fragment.return_value = standard_package
        
        # Act
        result = await narrative_service.get_contextualized_fragment(
            sample_user_id, fragment_id, neutral_context
        )
        
        # Assert
        assert result.metadata["emotional_tone"] == "neutral"
        assert "estándar" in result.payload

    @pytest.mark.asyncio
    async def test_process_narrative_interaction_choice_selection_updates_progress_and_emotion(
        self, narrative_service, sample_user_id
    ):
        """Test: Selección de opción debe actualizar progreso y emoción"""
        # Arrange
        interaction_data = {
            "type": "choice_selection",
            "fragment_id": "decision_001",
            "choice_id": "choice_positive",
            "choice_text": "Ayudar al personaje"
        }
        expected_result = InteractionResult(
            success=True,
            response_data={
                "next_fragment": "fragment_003",
                "progress_updated": True
            },
            side_effects=["progress_updated", "emotional_state_updated"],
            emotional_impact=EmotionalState.SATISFIED,
            points_awarded=15
        )
        narrative_service.process_narrative_interaction.return_value = expected_result
        
        # Act
        result = await narrative_service.process_narrative_interaction(
            sample_user_id, interaction_data
        )
        
        # Assert
        assert result.success is True
        assert result.emotional_impact == EmotionalState.SATISFIED
        assert result.points_awarded == 15
        assert "progress_updated" in result.side_effects
        narrative_service.process_narrative_interaction.assert_called_once_with(
            sample_user_id, interaction_data
        )

    @pytest.mark.asyncio
    async def test_get_personalized_narrative_flow_considers_emotional_state(
        self, narrative_service, sample_user_id
    ):
        """Test: Flujo narrativo personalizado debe considerar estado emocional"""
        # Arrange
        expected_flow = [
            "fragment_intro",
            "fragment_gentle_challenge",  # Adaptado para estado emocional
            "fragment_success_path",
            "fragment_conclusion"
        ]
        narrative_service.get_personalized_narrative_flow.return_value = expected_flow
        
        # Act
        result = await narrative_service.get_personalized_narrative_flow(sample_user_id)
        
        # Assert
        assert len(result) == 4
        assert "gentle_challenge" in result[1]  # Adaptación emocional
        assert isinstance(result, list)
        assert all(isinstance(fragment_id, str) for fragment_id in result)
        narrative_service.get_personalized_narrative_flow.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_narrative_emotional_impact_records_user_response(
        self, narrative_service, sample_user_id
    ):
        """Test: Actualización de impacto emocional debe registrar respuesta del usuario"""
        # Arrange
        fragment_id = "fragment_emotional_scene"
        emotional_response = EmotionalState.EXCITED
        narrative_service.update_narrative_emotional_impact.return_value = None
        
        # Act
        await narrative_service.update_narrative_emotional_impact(
            sample_user_id, fragment_id, emotional_response
        )
        
        # Assert
        narrative_service.update_narrative_emotional_impact.assert_called_once_with(
            sample_user_id, fragment_id, emotional_response
        )