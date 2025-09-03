# tests/interfaces/test_unified_narrative_contract.py

import pytest
from abc import ABC
from typing import Dict, Any, List, Optional
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Importaremos la interfaz cuando exista
# from services.interfaces.unified_narrative_interface import IUnifiedNarrativeInterface

class TestUnifiedNarrativeContract:
    """
    Tests de contrato que TODA implementación de IUnifiedNarrativeInterface
    DEBE pasar. Define el comportamiento mínimo requerido.
    """
    
    @pytest.fixture
    def narrative_interface(self):
        """Mock de la interfaz con comportamiento esperado mínimo"""
        interface = AsyncMock()  # spec=IUnifiedNarrativeInterface cuando exista
        
        # === Comportamientos base que DEBE tener cualquier implementación ===
        
        # get_fragment DEBE retornar estructura específica
        interface.get_fragment.return_value = {
            'id': 'fragment_001',
            'content': 'Contenido del fragmento',
            'is_active': True,
            'requires_vip': False,
            'next_fragments': ['fragment_002', 'fragment_003']
        }
        
        # get_or_create_user_state DEBE manejar usuarios nuevos
        interface.get_or_create_user_state.return_value = {
            'user_id': 123,
            'current_fragment': 'fragment_001',
            'completed_fragments': [],
            'unlocked_clues': [],
            'choices_made': {},
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # check_user_access DEBE retornar booleano
        interface.check_user_access.return_value = True
        
        # check_vip_requirement DEBE incluir campos específicos
        interface.check_vip_requirement.return_value = {
            'required': False,
            'has_access': True,
            'expires_at': None
        }
        
        # get_available_decisions DEBE retornar lista estructurada
        interface.get_available_decisions.return_value = [
            {
                'id': 'decision_001',
                'text': 'Opción A',
                'requirements': {'points': 0},
                'available': True
            },
            {
                'id': 'decision_002', 
                'text': 'Opción B',
                'requirements': {'points': 50},
                'available': False
            }
        ]
        
        # process_decision DEBE retornar resultado estructurado
        interface.process_decision.return_value = {
            'success': True,
            'next_fragment': {'id': 'fragment_002'},
            'error': None,
            'requirements_met': True
        }
        
        # get_user_progress_percentage DEBE ser 0-100
        interface.get_user_progress_percentage.return_value = 25.0
        
        return interface
    
    # === TESTS DE ESTRUCTURA DE DATOS ===
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_fragment_structure(self, narrative_interface):
        """get_fragment DEBE retornar estructura con campos obligatorios"""
        fragment = await narrative_interface.get_fragment('any_id')
        
        # Campos obligatorios
        assert 'id' in fragment, "Fragment DEBE tener 'id'"
        assert 'content' in fragment, "Fragment DEBE tener 'content'"
        assert 'is_active' in fragment, "Fragment DEBE tener 'is_active'"
        assert 'requires_vip' in fragment, "Fragment DEBE tener 'requires_vip'"
        
        # Tipos correctos
        assert isinstance(fragment['id'], str)
        assert isinstance(fragment['content'], str)
        assert isinstance(fragment['is_active'], bool)
        assert isinstance(fragment['requires_vip'], bool)
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_user_state_structure(self, narrative_interface):
        """get_or_create_user_state DEBE retornar estado completo"""
        state = await narrative_interface.get_or_create_user_state(123)
        
        # Campos obligatorios
        required_fields = [
            'user_id', 'current_fragment', 'completed_fragments',
            'unlocked_clues', 'choices_made'
        ]
        
        for field in required_fields:
            assert field in state, f"UserState DEBE tener campo '{field}'"
        
        # Tipos correctos
        assert isinstance(state['user_id'], int)
        assert isinstance(state['current_fragment'], (str, type(None)))
        assert isinstance(state['completed_fragments'], list)
        assert isinstance(state['unlocked_clues'], list)
        assert isinstance(state['choices_made'], dict)
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_vip_requirement_structure(self, narrative_interface):
        """check_vip_requirement DEBE retornar estructura específica"""
        vip_info = await narrative_interface.check_vip_requirement(123, 'fragment_id')
        
        assert 'required' in vip_info
        assert 'has_access' in vip_info
        assert 'expires_at' in vip_info
        
        assert isinstance(vip_info['required'], bool)
        assert isinstance(vip_info['has_access'], bool)
        # expires_at puede ser None o datetime
    
    # === TESTS DE COMPORTAMIENTO OBLIGATORIO ===
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_progress_percentage_bounds(self, narrative_interface):
        """get_user_progress_percentage DEBE estar entre 0 y 100"""
        progress = await narrative_interface.get_user_progress_percentage(123)
        
        assert isinstance(progress, (int, float))
        assert 0 <= progress <= 100, "Progress DEBE estar entre 0 y 100"
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_access_check_returns_boolean(self, narrative_interface):
        """check_user_access DEBE retornar booleano estricto"""
        access = await narrative_interface.check_user_access(123, 'fragment_id')
        
        assert isinstance(access, bool), "check_user_access DEBE retornar bool"
        assert access in [True, False], "Debe ser True o False, no truthy/falsy"
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_decision_processing_result(self, narrative_interface):
        """process_decision DEBE incluir success y manejar errores"""
        result = await narrative_interface.process_decision(
            user_id=123,
            fragment_id='frag_1',
            decision_id='dec_1'
        )
        
        assert 'success' in result
        assert isinstance(result['success'], bool)
        
        if result['success']:
            assert result.get('error') is None
            assert result.get('requirements_met') == True
        else:
            assert result.get('error') is not None
            assert isinstance(result['error'], str)
    
    # === TESTS DE MANEJO DE ERRORES ===
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_invalid_fragment_handling(self, narrative_interface):
        """get_fragment con ID inválido DEBE lanzar ValueError"""
        narrative_interface.get_fragment.side_effect = ValueError("Fragment not found")
        
        with pytest.raises(ValueError) as exc:
            await narrative_interface.get_fragment('invalid_id')
        
        assert "Fragment not found" in str(exc.value)
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_new_user_state_creation(self, narrative_interface):
        """get_or_create_user_state DEBE crear estado para usuarios nuevos"""
        # Simular usuario nuevo
        new_user_id = 99999
        
        state = await narrative_interface.get_or_create_user_state(new_user_id)
        
        assert state is not None
        assert state['user_id'] == new_user_id
        assert state['completed_fragments'] == []
        assert state['unlocked_clues'] == []
    
    # === TESTS DE CONSISTENCIA ===
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_decision_availability_consistency(self, narrative_interface):
        """Decisiones disponibles DEBE ser consistente con requisitos"""
        decisions = await narrative_interface.get_available_decisions(123, 'fragment_1')
        
        for decision in decisions:
            assert 'available' in decision
            assert 'requirements' in decision
            
            # Si hay requisitos no cumplidos, no debe estar disponible
            if decision.get('requirements', {}).get('points', 0) > 0:
                # Verificar lógica de disponibilidad
                if not decision['available']:
                    assert decision['requirements']['points'] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.contract
    async def test_reset_clears_all_progress(self, narrative_interface):
        """reset_user_progress DEBE limpiar TODO el progreso"""
        narrative_interface.reset_user_progress.return_value = {
            'user_id': 123,
            'current_fragment': None,
            'completed_fragments': [],
            'unlocked_clues': [],
            'choices_made': {}
        }
        
        reset_state = await narrative_interface.reset_user_progress(123)
        
        assert reset_state['completed_fragments'] == []
        assert reset_state['unlocked_clues'] == []
        assert reset_state['choices_made'] == {}
        assert reset_state['current_fragment'] is None