"""
Tests para validar el sistema de pistas en el sistema administrativo de narrativa.
Verifica que las pistas se desbloquean correctamente y que los requisitos de pistas
para fragmentos se aplican adecuadamente.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


# Implementación básica del servicio narrativo para probar el sistema de pistas
class TestNarrativeService:
    """Implementación básica del servicio narrativo para pruebas."""
    
    def __init__(self, session):
        self.session = session
    
    async def get_user_state(self, user_id):
        """Obtiene el estado narrativo del usuario."""
        query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(query)
        state = result.scalar_one_or_none()
        
        if not state:
            state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                visited_fragments=[],
                completed_fragments=[],
                unlocked_clues=[]
            )
            self.session.add(state)
            await self.session.commit()
        
        return state
    
    async def unlock_clue(self, user_id, clue_code):
        """Desbloquea una pista para un usuario."""
        state = await self.get_user_state(user_id)
        
        if clue_code in state.unlocked_clues:
            return False  # Ya desbloqueada
        
        state.unlocked_clues.append(clue_code)
        await self.session.commit()
        return True
    
    async def has_required_clues(self, user_id, required_clues):
        """Verifica si el usuario tiene todas las pistas requeridas."""
        if not required_clues:
            return True
            
        state = await self.get_user_state(user_id)
        return all(clue in state.unlocked_clues for clue in required_clues)
    
    async def can_access_fragment(self, user_id, fragment_id):
        """Verifica si el usuario puede acceder a un fragmento específico."""
        query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
        result = await self.session.execute(query)
        fragment = result.scalar_one_or_none()
        
        if not fragment:
            return False
            
        if not fragment.is_active:
            return False
            
        # Verificar pistas requeridas
        return await self.has_required_clues(user_id, fragment.required_clues)


@pytest.mark.asyncio
async def test_clue_requirement_enforcement(session: AsyncSession):
    """Verificar que se aplican correctamente los requisitos de pistas."""
    # Crear servicio de prueba
    narrative_service = TestNarrativeService(session)
    
    # Crear fragmento con requisito de pista
    fragment = NarrativeFragment(
        title="Fragmento con requisito de pista",
        content="Contenido del fragmento",
        fragment_type="STORY",
        required_clues=["PISTA_SECRETA", "CLAVE_MAESTRA"],
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear usuario de prueba
    user_id = 12345
    
    # Verificar que el usuario no puede acceder sin las pistas
    can_access = await narrative_service.can_access_fragment(user_id, fragment.id)
    assert can_access is False
    
    # Desbloquear solo una pista
    await narrative_service.unlock_clue(user_id, "PISTA_SECRETA")
    
    # Verificar que todavía no puede acceder
    can_access = await narrative_service.can_access_fragment(user_id, fragment.id)
    assert can_access is False
    
    # Desbloquear la segunda pista
    await narrative_service.unlock_clue(user_id, "CLAVE_MAESTRA")
    
    # Verificar que ahora sí puede acceder
    can_access = await narrative_service.can_access_fragment(user_id, fragment.id)
    assert can_access is True


@pytest.mark.asyncio
async def test_clue_unlock_propagation(session: AsyncSession):
    """Verificar que el desbloqueo de pistas se propaga correctamente."""
    # Crear servicio de prueba
    narrative_service = TestNarrativeService(session)
    
    # Crear fragmentos con requisitos de pistas encadenados
    fragment1 = NarrativeFragment(
        title="Fragmento inicial",
        content="Contenido del fragmento inicial",
        fragment_type="STORY",
        required_clues=[],  # Sin requisitos
        triggers={"clues": ["PISTA_NIVEL_1"]},  # Otorga pista al completar
        is_active=True
    )
    
    fragment2 = NarrativeFragment(
        title="Fragmento nivel 1",
        content="Contenido del fragmento nivel 1",
        fragment_type="STORY",
        required_clues=["PISTA_NIVEL_1"],  # Requiere pista del fragmento 1
        triggers={"clues": ["PISTA_NIVEL_2"]},  # Otorga pista al completar
        is_active=True
    )
    
    fragment3 = NarrativeFragment(
        title="Fragmento nivel 2",
        content="Contenido del fragmento nivel 2",
        fragment_type="STORY",
        required_clues=["PISTA_NIVEL_1", "PISTA_NIVEL_2"],  # Requiere ambas pistas
        is_active=True
    )
    
    # Guardar fragmentos
    session.add_all([fragment1, fragment2, fragment3])
    await session.commit()
    await session.refresh(fragment1)
    await session.refresh(fragment2)
    await session.refresh(fragment3)
    
    # Crear usuario de prueba
    user_id = 67890
    
    # Verificar acceso inicial
    assert await narrative_service.can_access_fragment(user_id, fragment1.id) is True  # Sin requisitos
    assert await narrative_service.can_access_fragment(user_id, fragment2.id) is False  # Requiere PISTA_NIVEL_1
    assert await narrative_service.can_access_fragment(user_id, fragment3.id) is False  # Requiere ambas pistas
    
    # Simular completar fragmento1 y recibir pista
    await narrative_service.unlock_clue(user_id, "PISTA_NIVEL_1")
    
    # Verificar acceso después de primera pista
    assert await narrative_service.can_access_fragment(user_id, fragment2.id) is True  # Ahora tiene PISTA_NIVEL_1
    assert await narrative_service.can_access_fragment(user_id, fragment3.id) is False  # Todavía falta PISTA_NIVEL_2
    
    # Simular completar fragmento2 y recibir segunda pista
    await narrative_service.unlock_clue(user_id, "PISTA_NIVEL_2")
    
    # Verificar acceso después de segunda pista
    assert await narrative_service.can_access_fragment(user_id, fragment3.id) is True  # Ahora tiene ambas pistas


@pytest.mark.asyncio
async def test_clue_in_choice_requirements(session: AsyncSession):
    """Verificar que las pistas también pueden funcionar como requisitos para opciones específicas."""
    # Crear servicio de prueba
    narrative_service = TestNarrativeService(session)
    
    # Crear fragmentos para prueba de opciones
    decision_fragment = NarrativeFragment(
        title="Decisión con requisitos de pista",
        content="Contenido del fragmento de decisión",
        fragment_type="DECISION",
        required_clues=[],  # El fragmento en sí no requiere pistas
        is_active=True
    )
    
    target1 = NarrativeFragment(
        title="Destino sin requisito",
        content="Este fragmento es accesible sin pistas",
        fragment_type="STORY",
        is_active=True
    )
    
    target2 = NarrativeFragment(
        title="Destino con requisito de pista",
        content="Este fragmento requiere una pista especial",
        fragment_type="STORY",
        required_clues=["PISTA_ESPECIAL"],
        is_active=True
    )
    
    # Guardar fragmentos
    session.add_all([decision_fragment, target1, target2])
    await session.commit()
    await session.refresh(decision_fragment)
    await session.refresh(target1)
    await session.refresh(target2)
    
    # Configurar opciones en el fragmento de decisión
    # Una opción sin requisitos, otra que requiere pista
    decision_fragment.choices = [
        {
            "text": "Opción normal",
            "next_fragment": target1.id,
            "requirements": {}
        },
        {
            "text": "Opción especial (requiere pista)",
            "next_fragment": target2.id,
            "requirements": {
                "clues": ["PISTA_ESPECIAL"]
            }
        }
    ]
    await session.commit()
    
    # Crear usuario de prueba
    user_id = 55555
    
    # Verificar acceso directo a los fragmentos
    assert await narrative_service.can_access_fragment(user_id, decision_fragment.id) is True
    assert await narrative_service.can_access_fragment(user_id, target1.id) is True
    assert await narrative_service.can_access_fragment(user_id, target2.id) is False  # Requiere pista
    
    # Simular que el usuario obtiene la pista especial
    await narrative_service.unlock_clue(user_id, "PISTA_ESPECIAL")
    
    # Verificar que ahora puede acceder al fragmento con requisito
    assert await narrative_service.can_access_fragment(user_id, target2.id) is True


@pytest.mark.asyncio
async def test_clue_system_admin_interface(session: AsyncSession):
    """Verificar que el servicio administrativo maneja correctamente las pistas de usuario."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear usuario de prueba con algunas pistas
    user_id = 99999
    user_state = UserNarrativeState(
        user_id=user_id,
        current_fragment_id=None,
        visited_fragments=[],
        completed_fragments=[],
        unlocked_clues=["PISTA1", "PISTA2", "PISTA3"]
    )
    session.add(user_state)
    await session.commit()
    
    # Obtener progreso del usuario a través del servicio administrativo
    user_progress = await admin_service.get_user_narrative_progress(user_id)
    
    # Verificar que las pistas se reportan correctamente
    assert len(user_progress["unlocked_clues"]) == 3
    assert "PISTA1" in user_progress["unlocked_clues"]
    assert "PISTA2" in user_progress["unlocked_clues"]
    assert "PISTA3" in user_progress["unlocked_clues"]
    
    # Reiniciar el progreso del usuario
    await admin_service.reset_user_narrative(user_id)
    
    # Verificar que las pistas se han reiniciado
    user_progress = await admin_service.get_user_narrative_progress(user_id)
    assert len(user_progress["unlocked_clues"]) == 0


@pytest.mark.asyncio
async def test_fragment_with_multiple_clue_combinations(session: AsyncSession):
    """Verificar que los fragmentos pueden requerir combinaciones de pistas."""
    # Crear servicio de prueba
    narrative_service = TestNarrativeService(session)
    
    # Crear fragmento con requisitos complejos
    fragment = NarrativeFragment(
        title="Fragmento con requisitos complejos",
        content="Este fragmento requiere varias pistas",
        fragment_type="STORY",
        required_clues=["PISTA_A", "PISTA_B", "PISTA_C"],
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear usuario de prueba
    user_id = 77777
    
    # Verificar que no puede acceder inicialmente
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is False
    
    # Desbloquear pistas una por una y verificar acceso
    await narrative_service.unlock_clue(user_id, "PISTA_A")
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is False
    
    await narrative_service.unlock_clue(user_id, "PISTA_B")
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is False
    
    await narrative_service.unlock_clue(user_id, "PISTA_C")
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is True
    
    # Verificar que el orden de desbloqueo no importa con otro usuario
    user_id2 = 88888
    
    # Desbloquear en orden diferente
    await narrative_service.unlock_clue(user_id2, "PISTA_C")
    await narrative_service.unlock_clue(user_id2, "PISTA_A")
    assert await narrative_service.can_access_fragment(user_id2, fragment.id) is False
    
    await narrative_service.unlock_clue(user_id2, "PISTA_B")
    assert await narrative_service.can_access_fragment(user_id2, fragment.id) is True


@pytest.mark.asyncio
async def test_clue_requirement_changes(session: AsyncSession):
    """Verificar que los cambios en los requisitos de pistas se aplican correctamente."""
    # Crear servicio de prueba y servicio administrativo
    narrative_service = TestNarrativeService(session)
    admin_service = NarrativeAdminService(session)
    
    # Crear fragmento con requisitos iniciales
    fragment = NarrativeFragment(
        title="Fragmento con requisitos cambiantes",
        content="Este fragmento cambiará sus requisitos",
        fragment_type="STORY",
        required_clues=["PISTA_X"],
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear usuario de prueba
    user_id = 44444
    
    # Usuario no tiene pistas, no puede acceder
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is False
    
    # Desbloquear la pista requerida
    await narrative_service.unlock_clue(user_id, "PISTA_X")
    
    # Ahora puede acceder
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is True
    
    # Cambiar los requisitos del fragmento a través del servicio administrativo
    await admin_service.update_fragment(fragment.id, {
        "required_clues": ["PISTA_X", "PISTA_Y"]  # Añadir un nuevo requisito
    })
    
    # Verificar que ahora no puede acceder de nuevo
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is False
    
    # Desbloquear la nueva pista requerida
    await narrative_service.unlock_clue(user_id, "PISTA_Y")
    
    # Verificar que puede acceder nuevamente
    assert await narrative_service.can_access_fragment(user_id, fragment.id) is True
    
    # Eliminar todos los requisitos
    await admin_service.update_fragment(fragment.id, {
        "required_clues": []  # Sin requisitos
    })
    
    # Crear un nuevo usuario sin pistas
    user_id2 = 33333
    
    # Verificar que el nuevo usuario puede acceder sin pistas
    assert await narrative_service.can_access_fragment(user_id2, fragment.id) is True