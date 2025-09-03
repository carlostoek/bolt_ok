"""
Tests for the EnhancedDianaMenuSystem to ensure character consistency,
performance, and robustness, especially in narrative keyboard creation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
from database.narrative_unified import NarrativeFragment

@pytest.fixture
def mock_session() -> AsyncMock:
    """Provides a mock SQLAlchemy AsyncSession."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def menu_system(mock_session: AsyncMock) -> EnhancedDianaMenuSystem:
    """Provides an instance of EnhancedDianaMenuSystem with a mock session."""
    return EnhancedDianaMenuSystem(mock_session)

@pytest.mark.asyncio
class TestEnhancedDianaMenuSystem:
    """
    Test suite for the EnhancedDianaMenuSystem, focusing on the robustness
    of narrative-related UI components.
    """

    async def test_create_narrative_keyboard_handles_malformed_choices_gracefully(self, menu_system: EnhancedDianaMenuSystem):
        """
        CRITICAL: Verifies that _create_narrative_keyboard does not crash when
        a narrative fragment contains malformed or invalid choice data.
        This test simulates various problematic data scenarios to ensure the
        defensive coding added to the system works as expected.
        """
        # 1. Define a mock narrative fragment with malformed choices
        mock_fragment_with_bad_data = NarrativeFragment(
            id="test-fragment-bad-choices",
            title="Fragmento con Opciones Malformadas",
            fragment_type="DECISION",
            is_active=True,
            choices=[
                {"text": "Opción Válida 1"},
                {"text": None},  # text is None
                "no es un diccionario",  # choice is not a dict
                {"wrong_key": "No hay clave 'text'"},  # Missing 'text' key
                {"text": 12345},  # text is not a string
                {"text": "Opción Válida 2"},
            ]
        )

        # 2. Define a mock progress summary (can be simple for this test)
        mock_progress_summary = {"current_level": 1}

        # 3. Call the method under test
        # This should execute without raising an exception
        keyboard = await menu_system._create_narrative_keyboard(
            fragment=mock_fragment_with_bad_data,
            progress_summary=mock_progress_summary
        )

        # 4. Assertions to verify graceful handling
        # The keyboard should still be created
        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')

        # It should contain buttons for the valid choices only
        # Expected valid buttons: "Opción Válida 1", "Opción Válida 2", plus standard buttons
        
        # Flatten the list of buttons for easier inspection
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        
        # Check that the two valid choice buttons were created
        valid_choice_buttons = [
            btn for btn in all_buttons 
            if btn.callback_data.startswith("narrative_choice_")
        ]
        assert len(valid_choice_buttons) == 2, "Deberían haberse creado solo 2 botones de opción válidos"
        
        # Verify the text of the valid buttons
        assert "Opción Válida 1" in valid_choice_buttons[0].text
        assert "Opción Válida 2" in valid_choice_buttons[1].text
        
        # Verify that standard navigation buttons are still present
        progress_button = next((btn for btn in all_buttons if btn.callback_data == "narrative_progress"), None)
        profile_button = next((btn for btn in all_buttons if btn.callback_data == "narrative_profile"), None)
        main_menu_button = next((btn for btn in all_buttons if btn.callback_data == "diana_main_menu"), None)
        
        assert progress_button is not None, "El botón de progreso debería estar presente"
        assert profile_button is not None, "El botón de perfil debería estar presente"
        assert main_menu_button is not None, "El botón de menú principal debería estar presente"

    async def test_create_narrative_keyboard_with_valid_fragment(self, menu_system: EnhancedDianaMenuSystem):
        """
        Tests the normal, successful creation of a narrative keyboard with a valid
        decision fragment to ensure no regressions were introduced.
        """
        # 1. Define a valid mock narrative fragment
        mock_fragment_valid = NarrativeFragment(
            id="test-fragment-valid",
            title="Fragmento Válido",
            fragment_type="DECISION",
            is_active=True,
            choices=[
                {"text": "Primera Opción"},
                {"text": "Segunda Opción"},
            ]
        )
        
        # 2. Call the method
        keyboard = await menu_system._create_narrative_keyboard(
            fragment=mock_fragment_valid,
            progress_summary={"current_level": 1}
        )
        
        # 3. Assertions
        assert keyboard is not None
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        
        choice_buttons = [btn for btn in all_buttons if btn.callback_data.startswith("narrative_choice_")]
        assert len(choice_buttons) == 2, "Deberían haberse creado 2 botones de opción"
        assert "Primera Opción" in choice_buttons[0].text
        assert "Segunda Opción" in choice_buttons[1].text
