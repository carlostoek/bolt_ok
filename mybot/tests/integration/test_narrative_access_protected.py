"""
Tests de protección para Narrative Access Service - Critical VIP Business Logic.
Estos tests protegen el control de acceso VIP durante refactoring.
"""
import pytest
from unittest.mock import AsyncMock, patch
from services.integration.narrative_access_service import NarrativeAccessService
from services.subscription_service import SubscriptionService
from services.narrative_service import NarrativeService


@pytest.mark.asyncio
class TestNarrativeAccessProtection:
    """Tests críticos para el servicio de acceso narrativo que protege contenido VIP."""

    async def test_can_access_fragment_contenido_gratis(self, session, test_user):
        """
        CRITICAL: Test que protege el acceso a contenido gratuito.
        Los fragmentos gratuitos (nivel 1-3) DEBEN ser accesibles a todos los usuarios.
        """
        service = NarrativeAccessService(session)
        
        # Mock subscription service (should not be called for free content)
        service.subscription_service.is_subscription_active = AsyncMock(return_value=False)
        
        # Test free content fragments
        free_fragments = [
            "level1_intro",
            "level2_romance", 
            "level3_tension",
            "start",
            "intro_chapter"
        ]
        
        for fragment_key in free_fragments:
            result = await service.can_access_fragment(test_user.id, fragment_key)
            
            # Critical assertions - free content must always be accessible
            assert result is True, f"Free fragment '{fragment_key}' must be accessible to all users"
            
        # Verify subscription service was never called for free content
        service.subscription_service.is_subscription_active.assert_not_called()

    async def test_can_access_fragment_vip_con_suscripcion_activa(self, session, vip_user):
        """
        CRITICAL: Test que protege el acceso VIP para usuarios suscritos.
        Los usuarios con suscripción activa DEBEN acceder a contenido VIP.
        """
        service = NarrativeAccessService(session)
        
        # Mock active subscription
        service.subscription_service.is_subscription_active = AsyncMock(return_value=True)
        
        # Test VIP content fragments
        vip_fragments = [
            "level4_intimate",
            "level5_exclusive", 
            "level6_ultimate",
            "vip_special_scene",
            "vip_ending"
        ]
        
        for fragment_key in vip_fragments:
            service.subscription_service.is_subscription_active.reset_mock()
            result = await service.can_access_fragment(vip_user.id, fragment_key)
            
            # Critical assertions - VIP users must access VIP content
            assert result is True, f"VIP fragment '{fragment_key}' must be accessible to subscribed users"
            service.subscription_service.is_subscription_active.assert_called_once_with(vip_user.id)

    async def test_can_access_fragment_vip_sin_suscripcion(self, session, test_user):
        """
        CRITICAL: Test que protege el contenido VIP contra acceso no autorizado.
        Los usuarios sin suscripción NO deben acceder a contenido VIP.
        """
        service = NarrativeAccessService(session)
        
        # Mock inactive subscription
        service.subscription_service.is_subscription_active = AsyncMock(return_value=False)
        
        # Test VIP content protection
        vip_fragments = [
            "level4_intimate",
            "level5_exclusive", 
            "level6_ultimate",
            "vip_special_scene",
            "vip_bonus_content"
        ]
        
        for fragment_key in vip_fragments:
            service.subscription_service.is_subscription_active.reset_mock()
            result = await service.can_access_fragment(test_user.id, fragment_key)
            
            # Critical assertions - non-VIP users must be blocked from VIP content
            assert result is False, f"VIP fragment '{fragment_key}' must be blocked for non-subscribers"
            service.subscription_service.is_subscription_active.assert_called_once_with(test_user.id)

    async def test_get_accessible_fragment_suscripcion_requerida(self, session, test_user):
        """
        CRITICAL: Test que protege el mensaje de suscripción requerida.
        Los usuarios sin acceso deben recibir el mensaje correcto de suscripción.
        """
        service = NarrativeAccessService(session)
        
        # Mock methods to simulate blocked access
        service.can_access_fragment = AsyncMock(return_value=False)
        
        # Test subscription required response
        result = await service.get_accessible_fragment(test_user.id, "level5_exclusive")
        
        # Critical assertions - subscription required message must be correct
        assert result["type"] == "subscription_required", "Response type must indicate subscription requirement"
        assert "message" in result, "Response must include user-friendly message"
        assert "requested_fragment" in result, "Response must track requested fragment"
        assert result["requested_fragment"] == "level5_exclusive", "Requested fragment must be preserved"
        assert "VIP" in result["message"], "Message must mention VIP requirement"
        
    async def test_get_accessible_fragment_acceso_exitoso(self, session, vip_user):
        """
        CRITICAL: Test que protege el acceso exitoso a fragmentos.
        Los usuarios con acceso deben recibir el fragmento solicitado.
        """
        service = NarrativeAccessService(session)
        
        # Mock successful access
        service.can_access_fragment = AsyncMock(return_value=True)
        
        # Mock fragment data
        fragment_data = {
            "key": "level4_intimate",
            "content": "Diana te mira con ojos ardientes...",
            "choices": [{"text": "Continuar", "cost": 0}]
        }
        service.narrative_service.get_user_current_fragment = AsyncMock(return_value=fragment_data)
        
        # Test successful access
        result = await service.get_accessible_fragment(vip_user.id, "level4_intimate")
        
        # Critical assertions - successful access must return fragment
        assert result == fragment_data, "Successful access must return actual fragment data"
        service.can_access_fragment.assert_called_once_with(vip_user.id, "level4_intimate")
        
    async def test_boundaries_nivel_vip_exactos(self, session, test_user):
        """
        CRITICAL: Test que protege los límites exactos entre contenido gratuito y VIP.
        Los límites entre nivel 3 (gratis) y nivel 4 (VIP) deben ser exactos.
        """
        service = NarrativeAccessService(session)
        
        # Mock inactive subscription
        service.subscription_service.is_subscription_active = AsyncMock(return_value=False)
        
        # Test boundary cases
        boundary_tests = [
            ("level3_final", True),     # Last free level
            ("level4_start", False),   # First VIP level
            ("vip_anything", False),   # Any VIP prefix
            ("level6_ultimate", False) # High VIP level
        ]
        
        for fragment_key, should_access in boundary_tests:
            service.subscription_service.is_subscription_active.reset_mock()
            result = await service.can_access_fragment(test_user.id, fragment_key)
            
            # Critical assertions - boundaries must be exact
            assert result == should_access, f"Fragment '{fragment_key}' access should be {should_access}"
            
            if fragment_key.startswith(("level4_", "level5_", "level6_", "vip_")):
                service.subscription_service.is_subscription_active.assert_called_once_with(test_user.id)
            else:
                service.subscription_service.is_subscription_active.assert_not_called()
                
    async def test_error_handling_servicio_suscripcion_falla(self, session, test_user):
        """
        CRITICAL: Test que protege el manejo de errores en servicio de suscripción.
        Los errores en verificación de suscripción NO deben otorgar acceso por defecto.
        """
        service = NarrativeAccessService(session)
        
        # Mock subscription service to raise exception
        service.subscription_service.is_subscription_active = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        
        # Test VIP fragment access during service error
        # Note: The current implementation doesn't have explicit error handling
        # This test documents expected behavior for future error handling
        with pytest.raises(Exception):
            await service.can_access_fragment(test_user.id, "level4_intimate")
            
        # This test protects against accidentally granting access during errors
        
    async def test_integration_flujo_completo_acceso_narrativo(self, session, test_user, vip_user):
        """
        CRITICAL: Test de integración que simula flujo completo de acceso narrativo.
        Simula: usuario libre intenta VIP -> se bloquea -> se suscribe -> accede.
        """
        service = NarrativeAccessService(session)
        
        fragment_key = "level5_exclusive"
        
        # 1. Free user tries to access VIP content (should be blocked)
        service.subscription_service.is_subscription_active = AsyncMock(return_value=False)
        
        blocked_result = await service.get_accessible_fragment(test_user.id, fragment_key)
        
        # Critical assertions - free user must be blocked
        assert blocked_result["type"] == "subscription_required", "Free user must be blocked from VIP content"
        assert blocked_result["requested_fragment"] == fragment_key, "Blocked request must be tracked"
        
        # 2. VIP user accesses same content (should succeed)
        service.subscription_service.is_subscription_active = AsyncMock(return_value=True)
        
        fragment_data = {
            "key": fragment_key,
            "content": "Contenido VIP exclusivo...",
            "choices": []
        }
        service.narrative_service.get_user_current_fragment = AsyncMock(return_value=fragment_data)
        
        success_result = await service.get_accessible_fragment(vip_user.id, fragment_key)
        
        # Critical assertions - VIP user must get content
        assert success_result == fragment_data, "VIP user must receive fragment content"
        
        # Verify both subscription checks happened
        assert service.subscription_service.is_subscription_active.call_count == 2, "Both users must be checked for subscription"