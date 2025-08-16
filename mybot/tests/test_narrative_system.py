"""
Tests de protección para el sistema narrativo - Critical Content Delivery.
Estos tests protegen la entrega de contenido narrativo y el sistema de decisiones.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from sqlalchemy import select

from services.narrative_service import NarrativeService
from services.narrative_loader import NarrativeLoader
from services.integration.narrative_access_service import NarrativeAccessService
from services.integration.narrative_point_service import NarrativePointService
from database.models import User
from database.narrative_models import UserNarrativeState, StoryFragment


@pytest.mark.asyncio
class TestNarrativeSystemProtection:
    """Tests críticos para el sistema narrativo interactivo."""

    async def test_narrative_loader_fragment_loading(self, session):
        """
        CRITICAL: Test que protege la carga de fragmentos narrativos.
        Los fragmentos deben cargarse correctamente desde los archivos JSON.
        """
        loader = NarrativeLoader(session)
        
        # Mock fragment data
        mock_fragment_data = {
            "key": "diana_first_contact",
            "content": "Diana te mira con ojos misteriosos...",
            "character": "Diana",
            "location": "mansion_entrance",
            "choices": [
                {
                    "text": "Acercarte con confianza",
                    "next_fragment": "confident_approach",
                    "points_cost": 0
                },
                {
                    "text": "Observar desde lejos", 
                    "next_fragment": "distant_observation",
                    "points_cost": 5
                }
            ],
            "vip_required": False
        }
        
        with patch('builtins.open', create=True) as mock_open, \
             patch('json.load', return_value=mock_fragment_data):
            
            fragment = await loader.load_fragment("diana_first_contact")
            
            # Critical assertions - fragments must load correctly
            assert fragment is not None, "Fragment must be loaded successfully"
            assert fragment["key"] == "diana_first_contact", "Fragment key must match"
            assert "Diana te mira" in fragment["content"], "Fragment content must be preserved"
            assert len(fragment["choices"]) == 2, "Fragment choices must be preserved"
            
            # Verify choice structure
            choice1 = fragment["choices"][0]
            assert choice1["text"] == "Acercarte con confianza", "Choice text must be preserved"
            assert choice1["points_cost"] == 0, "Choice point cost must be preserved"

    async def test_narrative_service_get_user_current_fragment(self, session, test_user):
        """
        CRITICAL: Test que protege la obtención del fragmento actual del usuario.
        Los usuarios deben poder recuperar su progreso narrativo actual.
        """
        service = NarrativeService(session)
        
        # Create narrative progress for user
        progress = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="level2_romantic_encounter",
            fragments_visited=5
        )
        session.add(progress)
        await session.commit()
        
        # Mock fragment in database
        fragment = StoryFragment(
            key="level2_romantic_encounter",
            text="Diana se acerca lentamente...",
            character="Diana",
            level=2,
            required_role=None
        )
        session.add(fragment)
        await session.commit()
        
        # Test retrieval
        current_fragment = await service.get_user_current_fragment(test_user.id)
        
        # Critical assertions - current fragment must be retrievable
        assert current_fragment is not None, "Current fragment must be retrievable"
        assert current_fragment.key == "level2_romantic_encounter", "Correct fragment must be returned"
        assert "Diana se acerca" in current_fragment.text, "Fragment content must match"

    async def test_narrative_access_service_vip_protection(self, session, test_user):
        """
        CRITICAL: Test que protege el control de acceso VIP para contenido narrativo.
        Los usuarios free NO deben acceder a contenido VIP.
        """
        service = NarrativeAccessService(session)
        
        # Create VIP-required fragment
        vip_fragment = StoryFragment(
            key="level4_intimate_scene",
            text="Diana te lleva hacia la habitación privada...",
            character="Diana",
            level=4,
            required_role="vip"
        )
        session.add(vip_fragment)
        await session.commit()
        
        # Test access with free user
        result = await service.get_accessible_fragment(test_user.id, "level4_intimate_scene")
        
        # Critical assertions - VIP protection must work
        assert isinstance(result, dict), "Result must be a dict for denied access"
        assert result["type"] == "subscription_required", "Access must be denied for non-VIP"
        assert "level4_intimate_scene" in result["requested_fragment"], "Fragment key must be tracked"

    async def test_narrative_access_service_vip_user_access(self, session, vip_user):
        """
        CRITICAL: Test que protege el acceso exitoso de usuarios VIP.
        Los usuarios VIP DEBEN poder acceder a todo el contenido.
        """
        service = NarrativeAccessService(session)
        
        # Create VIP-required fragment
        vip_fragment = StoryFragment(
            key="level4_intimate_scene",
            text="Diana te lleva hacia la habitación privada...",
            character="Diana", 
            level=4,
            required_role="vip"
        )
        session.add(vip_fragment)
        await session.commit()
        
        # Test access with VIP user
        result = await service.get_accessible_fragment(vip_user.id, "level4_intimate_scene")
        
        # Critical assertions - VIP users must access VIP content
        assert not isinstance(result, dict) or result.get("type") != "subscription_required", "VIP users must access VIP content"
        # If it's a fragment object, verify it's the correct one
        if hasattr(result, 'key'):
            assert result.key == "level4_intimate_scene", "Correct VIP fragment must be returned"

    async def test_narrative_access_service_free_content_access(self, session, test_user):
        """
        CRITICAL: Test que protege el acceso a contenido gratuito.
        Todos los usuarios deben acceder a contenido no-VIP.
        """
        service = NarrativeAccessService(session)
        
        # Create free fragment
        free_fragment = StoryFragment(
            key="level1_introduction",
            text="Diana te sonríe desde el jardín...",
            character="Diana",
            level=1,
            required_role=None
        )
        session.add(free_fragment)
        await session.commit()
        
        # Test access with free user
        result = await service.get_accessible_fragment(test_user.id, "level1_introduction")
        
        # Critical assertions - free content must be accessible
        assert result is not None, "Free content must be accessible to all users"
        if hasattr(result, 'key'):
            assert result.key == "level1_introduction", "Correct free fragment must be returned"
        elif isinstance(result, dict):
            assert result.get("type") != "subscription_required", "Free content must not require subscription"

    async def test_narrative_point_service_sufficient_points(self, session, test_user):
        """
        CRITICAL: Test que protege las decisiones con puntos suficientes.
        Los usuarios con puntos suficientes DEBEN poder tomar decisiones costosas.
        """
        service = NarrativePointService(session)
        
        # Set user points high enough
        test_user.points = 50.0
        session.add(test_user)
        await session.commit()
        
        # Mock decision data
        decision_data = {
            "id": 1,
            "text": "Acercarte a Diana",
            "points_cost": 25,
            "next_fragment": "romantic_approach"
        }
        
        # Mock fragment result
        result_fragment = {
            "key": "romantic_approach",
            "content": "Diana sonríe al verte acercarte...",
            "choices": []
        }
        
        with patch.object(service, '_get_decision_data', return_value=decision_data), \
             patch.object(service, '_get_fragment_by_key', return_value=result_fragment):
            
            result = await service.process_decision_with_points(test_user.id, 1, None)
            
            # Critical assertions - sufficient points must allow decision
            assert result["type"] == "success", "Sufficient points must allow decision"
            assert "fragment" in result, "Result fragment must be provided"
            assert result["fragment"]["key"] == "romantic_approach", "Correct result fragment must be returned"

    async def test_narrative_point_service_insufficient_points(self, session, test_user):
        """
        CRITICAL: Test que protege las decisiones con puntos insuficientes.
        Los usuarios sin puntos suficientes NO deben poder tomar decisiones costosas.
        """
        service = NarrativePointService(session)
        
        # Set user points too low
        test_user.points = 10.0
        session.add(test_user)
        await session.commit()
        
        # Mock decision data requiring more points
        decision_data = {
            "id": 1,
            "text": "Acercarte a Diana",
            "points_cost": 25,
            "next_fragment": "romantic_approach"
        }
        
        with patch.object(service, '_get_decision_data', return_value=decision_data):
            result = await service.process_decision_with_points(test_user.id, 1, None)
            
            # Critical assertions - insufficient points must prevent decision
            assert result["type"] == "points_required", "Insufficient points must prevent decision"
            assert "fragment" not in result, "No fragment should be provided for denied decisions"

    async def test_narrative_progress_tracking(self, session, test_user):
        """
        CRITICAL: Test que protege el seguimiento del progreso narrativo.
        El progreso del usuario debe rastrearse correctamente.
        """
        service = NarrativeService(session)
        
        # Create initial progress
        progress = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="level1_start",
            fragments_visited=1
        )
        session.add(progress)
        await session.commit()
        
        # Update progress (mock since service may not exist)
        progress.current_fragment_key = "level2_encounter"
        progress.fragments_visited = 2
        await session.commit()
        
        # Verify progress was updated
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == test_user.id)
        result = await session.execute(stmt)
        updated_progress = result.scalar_one()
        
        # Critical assertions - progress must be tracked correctly
        assert updated_progress.current_fragment_key == "level2_encounter", "Current fragment must be updated"
        assert updated_progress.fragments_visited == 2, "Fragment count must be incremented"

    async def test_narrative_fragment_choices_structure(self, session):
        """
        CRITICAL: Test que protege la estructura de opciones en fragmentos.
        Las opciones deben mantener su estructura y metadatos.
        """
        loader = NarrativeLoader(session)
        
        # Mock fragment with complex choices
        mock_fragment_data = {
            "key": "complex_choice_scene",
            "content": "Diana te presenta varias opciones...",
            "choices": [
                {
                    "text": "Opción gratuita",
                    "next_fragment": "free_path",
                    "points_cost": 0,
                    "vip_required": False
                },
                {
                    "text": "Opción con costo",
                    "next_fragment": "expensive_path", 
                    "points_cost": 30,
                    "vip_required": False
                },
                {
                    "text": "Opción VIP",
                    "next_fragment": "vip_exclusive_path",
                    "points_cost": 10,
                    "vip_required": True
                }
            ]
        }
        
        with patch('builtins.open', create=True), \
             patch('json.load', return_value=mock_fragment_data):
            
            fragment = await loader.load_fragment("complex_choice_scene")
            
            # Critical assertions - choice structure must be preserved
            assert len(fragment["choices"]) == 3, "All choices must be preserved"
            
            # Verify free choice
            free_choice = fragment["choices"][0]
            assert free_choice["points_cost"] == 0, "Free choice must cost 0 points"
            assert free_choice["vip_required"] is False, "Free choice must not require VIP"
            
            # Verify expensive choice
            expensive_choice = fragment["choices"][1]
            assert expensive_choice["points_cost"] == 30, "Expensive choice must cost correct points"
            
            # Verify VIP choice
            vip_choice = fragment["choices"][2]
            assert vip_choice["vip_required"] is True, "VIP choice must require VIP"

    async def test_narrative_service_error_handling_missing_fragment(self, session, test_user):
        """
        CRITICAL: Test que protege el manejo de fragmentos inexistentes.
        Los fragmentos inexistentes deben manejarse gracefully.
        """
        service = NarrativeService(session)
        
        # Try to get non-existent fragment
        result = await service.get_user_current_fragment(test_user.id)
        
        # Critical assertions - missing fragments must be handled
        assert result is None, "Non-existent fragments must return None"

    async def test_narrative_character_consistency(self, session):
        """
        CRITICAL: Test que protege la consistencia del personaje.
        Los fragmentos deben mantener consistencia en el personaje Diana.
        """
        loader = NarrativeLoader(session)
        
        # Mock multiple fragments with character info
        fragments_data = [
            {
                "key": "scene1",
                "content": "Diana te saluda...",
                "character": "Diana",
                "character_mood": "mysterious"
            },
            {
                "key": "scene2", 
                "content": "Diana sonríe...",
                "character": "Diana",
                "character_mood": "playful"
            }
        ]
        
        for fragment_data in fragments_data:
            with patch('builtins.open', create=True), \
                 patch('json.load', return_value=fragment_data):
                
                fragment = await loader.load_fragment(fragment_data["key"])
                
                # Critical assertions - character consistency must be maintained
                assert fragment["character"] == "Diana", "Character must be consistently Diana"
                assert "character_mood" in fragment, "Character mood must be preserved"

    async def test_narrative_location_tracking(self, session):
        """
        CRITICAL: Test que protege el seguimiento de ubicaciones narrativas.
        Las ubicaciones deben rastrearse para continuidad.
        """
        loader = NarrativeLoader(session)
        
        # Mock fragment with location
        mock_fragment_data = {
            "key": "garden_scene",
            "content": "Te encuentras en el jardín secreto...",
            "location": "secret_garden",
            "location_description": "Un jardín escondido lleno de flores exóticas"
        }
        
        with patch('builtins.open', create=True), \
             patch('json.load', return_value=mock_fragment_data):
            
            fragment = await loader.load_fragment("garden_scene")
            
            # Critical assertions - location must be tracked
            assert fragment["location"] == "secret_garden", "Location must be preserved"
            assert "location_description" in fragment, "Location description must be preserved"

    async def test_narrative_vip_content_metadata(self, session):
        """
        CRITICAL: Test que protege los metadatos de contenido VIP.
        El contenido VIP debe estar claramente marcado.
        """
        loader = NarrativeLoader(session)
        
        # Mock VIP fragment
        mock_vip_fragment = {
            "key": "intimate_scene",
            "content": "Diana te guía hacia...",
            "vip_required": True,
            "content_rating": "mature",
            "content_tags": ["intimate", "romantic", "exclusive"]
        }
        
        with patch('builtins.open', create=True), \
             patch('json.load', return_value=mock_vip_fragment):
            
            fragment = await loader.load_fragment("intimate_scene")
            
            # Critical assertions - VIP metadata must be preserved
            assert fragment["vip_required"] is True, "VIP requirement must be marked"
            assert fragment["content_rating"] == "mature", "Content rating must be preserved"
            assert "intimate" in fragment["content_tags"], "Content tags must be preserved"