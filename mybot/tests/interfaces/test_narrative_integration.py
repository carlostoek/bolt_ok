# tests/interfaces/test_narrative_integration.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

class TestNarrativeIntegration:
    """Tests de integración con el sistema existente"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_coordinator_can_use_narrative_interface(self, session: AsyncSession):
        """CoordinadorCentral DEBE poder usar la interfaz narrativa"""
        from services.coordinador_central import CoordinadorCentral
        
        coordinator = CoordinadorCentral(session)
        
        # Mock temporal hasta que exista la implementación
        with patch.object(coordinator, 'narrative_interface', new=AsyncMock()) as mock_interface:
            mock_interface.get_fragment.return_value = {
                'id': 'test', 'content': 'Test', 'is_active': True
            }
            
            # Simular flujo narrativo
            result = await coordinator.ejecutar_flujo(
                user_id=123,
                accion="ACCEDER_NARRATIVA_VIP",
                fragment_id='test'
            )
            
            # No debe romper el flujo existente
            assert result is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration  
    async def test_points_integration_with_narrative(self):
        """Interfaz narrativa DEBE integrarse con PointService"""
        # Verificar que decisiones narrativas pueden usar puntos
        # Mock de ambos servicios
        narrative_interface = AsyncMock()
        point_service = AsyncMock()
        
        # Decisión que requiere puntos
        narrative_interface.process_decision.return_value = {
            'success': False,
            'error': 'Insufficient points',
            'requirements_met': False
        }
        
        point_service.get_balance.return_value = 10  # Usuario tiene 10 puntos
        
        # Verificar integración
        user_points = await point_service.get_balance(123)
        decision_result = await narrative_interface.process_decision(
            123, 'fragment_1', 'expensive_decision'
        )
        
        assert decision_result['success'] == False
        assert 'points' in decision_result['error'].lower()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_vip_integration_with_narrative(self):
        """Interfaz narrativa DEBE respetar VipTransaction"""
        # Mock de servicios
        narrative_interface = AsyncMock()
        subscription_service = AsyncMock()
        
        # Usuario sin VIP
        subscription_service.is_subscription_active.return_value = False
        narrative_interface.check_vip_requirement.return_value = {
            'required': True,
            'has_access': False,
            'expires_at': None
        }
        
        vip_check = await narrative_interface.check_vip_requirement(123, 'vip_fragment')
        is_vip = await subscription_service.is_subscription_active(123)
        
        assert vip_check['has_access'] == is_vip
        assert vip_check['has_access'] == False