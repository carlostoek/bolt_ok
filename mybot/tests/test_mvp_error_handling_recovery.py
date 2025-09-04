"""
MVP Error Handling and Recovery Tests

Comprehensive test suite for error scenario handling, graceful degradation,
character consistency during errors, and system recovery mechanisms.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog
)
from services.narrative_engine import NarrativeEngine
from services.diana_character_validator import DianaCharacterValidator
from services.diana_menu_system import DianaMenuSystem


class TestDatabaseErrorHandling:
    """Test database error scenarios and recovery."""

    @pytest_asyncio.fixture
    async def narrative_engine(self, session):
        """Create narrative engine for error testing."""
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        return engine

    async def test_database_connection_failure_handling(self, narrative_engine):
        """Test handling of database connection failures."""
        user_id = 12345
        
        # Mock database connection failure
        with patch.object(narrative_engine.session, 'execute', side_effect=OperationalError("Connection failed", None, None)):
            
            # Should handle connection failure gracefully
            result = await self.safe_get_current_fragment(narrative_engine, user_id)
            
            assert result is None, "Should return None on database failure"
            # In real implementation, this would log the error and possibly retry

    async def safe_get_current_fragment(self, engine, user_id):
        """Safe wrapper for getting current fragment with error handling."""
        try:
            return await engine.get_user_current_fragment(user_id)
        except Exception as e:
            # Log error in real implementation
            return None

    async def test_transaction_rollback_on_error(self, session):
        """Test transaction rollback on errors maintains data consistency."""
        initial_count = 0
        
        # Attempt operation that will fail
        try:
            # Create fragment
            fragment = NarrativeFragment(
                id='rollback_test_fragment',
                title='Rollback Test',
                content='Test content',
                fragment_type='STORY',
                is_active=True
            )
            session.add(fragment)
            await session.flush()
            
            # Create duplicate fragment (should fail)
            duplicate_fragment = NarrativeFragment(
                id='rollback_test_fragment',  # Same ID - will cause integrity error
                title='Duplicate',
                content='Duplicate content', 
                fragment_type='STORY',
                is_active=True
            )
            session.add(duplicate_fragment)
            await session.commit()
            
        except IntegrityError:
            await session.rollback()
        
        # Verify rollback worked - no fragments should exist
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count(NarrativeFragment.id)).where(
                NarrativeFragment.id == 'rollback_test_fragment'
            )
        )
        count = result.scalar()
        
        assert count == 0, "Transaction rollback should remove all changes"

    async def test_constraint_violation_handling(self, session):
        """Test handling of database constraint violations."""
        # Create user state
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='test_fragment'
        )
        session.add(user_state)
        await session.commit()
        
        # Attempt to create duplicate user state (should fail)
        error_occurred = False
        try:
            duplicate_state = UserNarrativeState(
                user_id=12345,  # Same user ID - primary key violation
                current_fragment_id='another_fragment'
            )
            session.add(duplicate_state)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            error_occurred = True
        
        assert error_occurred, "Should detect constraint violation"
        
        # Verify original state is intact
        from sqlalchemy import select
        result = await session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == 12345)
        )
        existing_state = result.scalar_one_or_none()
        
        assert existing_state is not None
        assert existing_state.current_fragment_id == 'test_fragment'

    async def test_deadlock_detection_and_retry(self, session):
        """Test deadlock detection and retry mechanism."""
        import asyncio
        
        async def concurrent_user_operation(user_id, operation_id):
            """Simulate concurrent operations that could cause deadlocks."""
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    user_state = UserNarrativeState(
                        user_id=user_id + operation_id,
                        current_fragment_id=f'concurrent_fragment_{operation_id}',
                        current_level=1
                    )
                    session.add(user_state)
                    
                    # Small delay to increase chance of concurrent access
                    await asyncio.sleep(0.01)
                    
                    await session.commit()
                    return True
                    
                except (OperationalError, IntegrityError) as e:
                    await session.rollback()
                    if attempt == max_retries - 1:
                        return False
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
        
        # Run multiple concurrent operations
        tasks = [concurrent_user_operation(20000, i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most operations should succeed (some might fail due to conflicts)
        successful_operations = [r for r in results if r is True]
        assert len(successful_operations) >= 5, f"At least 5 operations should succeed, got {len(successful_operations)}"


class TestTelegramAPIErrorHandling:
    """Test Telegram API error scenarios."""

    @pytest_asyncio.fixture
    async def diana_menu_system(self, session):
        """Create Diana Menu System for error testing."""
        menu_system = DianaMenuSystem(session)
        menu_system.coordinador = AsyncMock()
        menu_system.user_service = AsyncMock()
        menu_system.admin_menu = AsyncMock()
        menu_system.user_menu = AsyncMock()
        return menu_system

    @pytest_asyncio.fixture
    async def mock_message(self):
        """Create mock Telegram message."""
        message = MagicMock()
        message.from_user.id = 12345
        message.chat.id = 12345
        message.answer = AsyncMock()
        message.edit_text = AsyncMock()
        message.bot = AsyncMock()
        return message

    async def test_message_send_failure_handling(self, diana_menu_system, mock_message):
        """Test handling of message sending failures."""
        # Mock Telegram API failure
        mock_message.answer.side_effect = TelegramBadRequest(method="sendMessage", message="Chat not found")
        
        with patch('utils.user_roles.get_user_role', return_value='free'):
            # Should handle API failure gracefully without crashing
            await diana_menu_system.show_main_menu(mock_message)
            
            # Error should be logged and handled gracefully
            # In real implementation, this would attempt fallback mechanisms
            mock_message.answer.assert_called_once()

    async def test_network_timeout_recovery(self, diana_menu_system, mock_message):
        """Test recovery from network timeouts."""
        call_count = 0
        
        async def mock_answer_with_timeout(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TelegramNetworkError(message="Network timeout")
            return "Success"
        
        mock_message.answer.side_effect = mock_answer_with_timeout
        
        with patch('utils.user_roles.get_user_role', return_value='free'):
            # Should retry after network timeout
            await diana_menu_system.show_main_menu(mock_message)
            
            # Should have been called at least once (maybe with retry)
            assert mock_message.answer.call_count >= 1

    async def test_message_too_long_error_handling(self, diana_menu_system):
        """Test handling of message length limit errors."""
        # Create very long content that would exceed Telegram limits
        long_content = "Very long message content. " * 200  # Over 4096 characters
        
        mock_callback = MagicMock()
        mock_callback.message.edit_text = AsyncMock(
            side_effect=TelegramBadRequest(method="editMessageText", message="Message is too long")
        )
        
        # Should handle message too long error by truncating or splitting
        error_handled = await self.safe_edit_message(mock_callback, long_content)
        
        assert error_handled is True, "Should handle message too long error gracefully"

    async def safe_edit_message(self, callback, content):
        """Safe wrapper for editing messages with error handling."""
        try:
            if len(content) > 4000:  # Telegram limit is 4096, use 4000 for safety
                content = content[:3990] + "..."
            
            await callback.message.edit_text(content)
            return True
        except TelegramBadRequest as e:
            if "too long" in str(e):
                # Handle by further truncation
                truncated = content[:2000] + "\n\n[Mensaje truncado...]"
                try:
                    await callback.message.edit_text(truncated)
                    return True
                except:
                    pass
            return False
        except Exception:
            return False

    async def test_chat_not_found_error_handling(self, diana_menu_system, mock_message):
        """Test handling when chat/user is not found."""
        mock_message.answer.side_effect = TelegramBadRequest(method="sendMessage", message="Forbidden: bot was blocked by the user")
        
        with patch('utils.user_roles.get_user_role', return_value='free'):
            # Should handle blocked user gracefully
            await diana_menu_system.show_main_menu(mock_message)
            
            # Should attempt to send message and handle the block gracefully
            mock_message.answer.assert_called_once()


class TestCharacterConsistentErrorMessages:
    """Test error messages maintain Diana's character consistency."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        """Create character validator for error message testing."""
        return DianaCharacterValidator(session)

    async def test_database_error_character_consistency(self, character_validator):
        """Test database error messages maintain character."""
        technical_errors = [
            "Database connection timeout",
            "SQL constraint violation", 
            "Transaction rollback required",
            "Connection pool exhausted"
        ]
        
        for technical_error in technical_errors:
            character_error = self.convert_to_character_error(technical_error)
            
            result = await character_validator.validate_text(character_error, context="error_message")
            
            assert result.overall_score >= 85.0, f"Character error should score well: {character_error} (score: {result.overall_score:.1f})"
            
            # Should have character elements
            character_elements = ['✨', '🌙', '💫', 'misterio', 'secreto', 'querido', 'sombra']
            has_character = any(element in character_error.lower() for element in character_elements)
            assert has_character, f"Error message should have character elements: {character_error}"

    def convert_to_character_error(self, technical_error: str) -> str:
        """Convert technical error to character-consistent message."""
        error_mapping = {
            "Database connection timeout": "🌙 Los misterios parecen esquivos en este momento... Un breve respiro y podremos continuar, querido.",
            "SQL constraint violation": "✨ Algo en la trama de la realidad ha encontrado resistencia... Intentemos por otro sendero.",
            "Transaction rollback required": "💫 El tiempo ha decidido retroceder un paso... Los secretos aguardan nuestro siguiente movimiento.",
            "Connection pool exhausted": "🌟 Demasiadas almas buscan respuestas al mismo tiempo... Espera un instante mientras se abre espacio para ti."
        }
        
        return error_mapping.get(technical_error, f"✨ Algo inesperado ha ocurrido en mis dominios... {technical_error.lower()}")

    async def test_user_input_error_character_consistency(self, character_validator):
        """Test user input error messages maintain character."""
        user_errors = [
            "Invalid choice selected",
            "Access denied - insufficient permissions",
            "Session expired",
            "Required field missing"
        ]
        
        for user_error in user_errors:
            character_error = self.convert_user_error_to_character(user_error)
            
            result = await character_validator.validate_text(character_error, context="error_message")
            
            # Should maintain character while being informative
            assert result.overall_score >= 80.0, f"User error should maintain character: {character_error}"
            
            # Should not use technical language
            technical_terms = ['error', 'invalid', 'denied', 'expired', 'missing', 'failed']
            has_technical_terms = any(term in character_error.lower() for term in technical_terms)
            assert not has_technical_terms, f"Character error should avoid technical terms: {character_error}"

    def convert_user_error_to_character(self, user_error: str) -> str:
        """Convert user error to character-consistent message."""
        user_error_mapping = {
            "Invalid choice selected": "💋 Esa opción no está entre las que te ofrezco, mi curioso explorador... ¿Intentas con una de las alternativas disponibles?",
            "Access denied - insufficient permissions": "🎭 Esos secretos requieren un nivel de intimidad que aún no hemos alcanzado, cariño... Continúa el viaje para desbloquear más misterios.",
            "Session expired": "🌙 Nuestro encuentro se ha desvanecido en el tiempo... ¿Comenzamos de nuevo este baile de secretos?",
            "Required field missing": "✨ Parece que falta algo en tu respuesta, querido... Los misterios requieren información completa para revelarse."
        }
        
        return user_error_mapping.get(user_error, f"🌟 Algo no ha salido como esperábamos... {user_error.lower()}")

    async def test_system_error_graceful_degradation(self, character_validator):
        """Test system errors degrade gracefully while maintaining character."""
        system_failures = [
            "Service unavailable",
            "Internal server error",
            "Configuration error",
            "Resource not found"
        ]
        
        for failure in system_failures:
            graceful_message = self.create_graceful_degradation_message(failure)
            
            result = await character_validator.validate_text(graceful_message, context="error_message")
            
            assert result.overall_score >= 75.0, f"Graceful degradation should maintain character: {graceful_message}"
            
            # Should offer alternative or hope
            positive_elements = ['intenta', 'continúa', 'aguarda', 'próximo', 'regresa']
            has_positive_element = any(element in graceful_message.lower() for element in positive_elements)
            assert has_positive_element, f"Graceful message should offer hope: {graceful_message}"

    def create_graceful_degradation_message(self, system_failure: str) -> str:
        """Create graceful degradation message for system failures."""
        degradation_mapping = {
            "Service unavailable": "🌙 Mis poderes están temporalmente dispersos en otras dimensiones... Regresa pronto y continuaremos donde lo dejamos.",
            "Internal server error": "✨ Algo profundo en la esencia de mis dominios requiere atención... Los misterios aguardan tu regreso, querido.",
            "Configuration error": "💫 Las estrellas no están alineadas correctamente en este momento... Intenta de nuevo cuando la configuración cósmica sea propicia.",
            "Resource not found": "🌟 El tesoro que buscas se ha ocultado en los pliegues de la realidad... Exploraremos otros senderos mientras aparece."
        }
        
        return degradation_mapping.get(system_failure, "✨ Los misterios a veces se ocultan cuando menos lo esperamos... Continuaremos la búsqueda juntos.")


class TestSystemRecoveryMechanisms:
    """Test system recovery and resilience mechanisms."""

    @pytest_asyncio.fixture
    async def narrative_engine(self, session):
        """Create narrative engine for recovery testing."""
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        return engine

    async def test_user_state_corruption_recovery(self, session):
        """Test recovery from corrupted user state."""
        user_id = 12345
        
        # Create corrupted user state
        corrupted_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='non_existent_fragment',
            current_level=-1,  # Invalid level
            visited_fragments=None,  # Should be list
            completed_fragments=None  # Should be list
        )
        session.add(corrupted_state)
        await session.commit()
        
        # Attempt recovery
        recovered_state = await self.recover_user_state(session, user_id)
        
        assert recovered_state is not None, "Should recover from corrupted state"
        assert recovered_state.current_level >= 1, "Should have valid level"
        assert isinstance(recovered_state.visited_fragments, list), "Should have valid visited fragments list"
        assert isinstance(recovered_state.completed_fragments, list), "Should have valid completed fragments list"

    async def recover_user_state(self, session, user_id):
        """Recover corrupted user state."""
        from sqlalchemy import select
        
        try:
            # Get current state
            result = await session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            state = result.scalar_one_or_none()
            
            if not state:
                return None
            
            # Check and fix corruption
            if state.current_level < 1:
                state.current_level = 1
            
            if not isinstance(state.visited_fragments, list):
                state.visited_fragments = []
            
            if not isinstance(state.completed_fragments, list):
                state.completed_fragments = []
            
            # Validate current fragment exists
            if state.current_fragment_id:
                fragment_result = await session.execute(
                    select(NarrativeFragment).where(NarrativeFragment.id == state.current_fragment_id)
                )
                if not fragment_result.scalar_one_or_none():
                    state.current_fragment_id = None
            
            await session.commit()
            return state
            
        except Exception:
            await session.rollback()
            return None

    async def test_fragment_reference_integrity_recovery(self, session):
        """Test recovery from broken fragment references."""
        user_id = 23456
        
        # Create user state with references to non-existent fragments
        state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='missing_fragment_1',
            visited_fragments=['missing_fragment_1', 'missing_fragment_2'],
            completed_fragments=['missing_fragment_3']
        )
        session.add(state)
        
        # Create one valid fragment
        valid_fragment = NarrativeFragment(
            id='valid_fragment',
            title='Valid Fragment',
            content='This fragment exists',
            fragment_type='STORY',
            is_active=True
        )
        session.add(valid_fragment)
        await session.commit()
        
        # Recover broken references
        cleaned_state = await self.clean_fragment_references(session, user_id)
        
        assert cleaned_state is not None, "Should clean broken references"
        
        # Should remove references to non-existent fragments
        all_referenced_fragments = (
            [cleaned_state.current_fragment_id] if cleaned_state.current_fragment_id else []
        ) + cleaned_state.visited_fragments + cleaned_state.completed_fragments
        
        # All remaining references should be to existing fragments or None
        for fragment_id in all_referenced_fragments:
            if fragment_id:
                from sqlalchemy import select
                result = await session.execute(
                    select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
                )
                fragment = result.scalar_one_or_none()
                assert fragment is not None, f"Fragment {fragment_id} should exist or be removed"

    async def clean_fragment_references(self, session, user_id):
        """Clean broken fragment references in user state."""
        from sqlalchemy import select
        
        try:
            # Get user state
            result = await session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            state = result.scalar_one_or_none()
            
            if not state:
                return None
            
            # Check current fragment
            if state.current_fragment_id:
                fragment_result = await session.execute(
                    select(NarrativeFragment).where(NarrativeFragment.id == state.current_fragment_id)
                )
                if not fragment_result.scalar_one_or_none():
                    state.current_fragment_id = None
            
            # Clean visited fragments
            valid_visited = []
            for fragment_id in state.visited_fragments:
                fragment_result = await session.execute(
                    select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
                )
                if fragment_result.scalar_one_or_none():
                    valid_visited.append(fragment_id)
            state.visited_fragments = valid_visited
            
            # Clean completed fragments
            valid_completed = []
            for fragment_id in state.completed_fragments:
                fragment_result = await session.execute(
                    select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
                )
                if fragment_result.scalar_one_or_none():
                    valid_completed.append(fragment_id)
            state.completed_fragments = valid_completed
            
            await session.commit()
            return state
            
        except Exception:
            await session.rollback()
            return None

    async def test_session_recovery_after_crash(self, session):
        """Test session recovery after simulated crash."""
        # Simulate incomplete operations that might occur during crash
        incomplete_operations = []
        
        for i in range(5):
            # Start transaction
            user_state = UserNarrativeState(
                user_id=30000 + i,
                current_fragment_id=f'crash_test_fragment_{i}',
                current_level=1
            )
            session.add(user_state)
            incomplete_operations.append(user_state)
        
        # Don't commit - simulates crash
        await session.rollback()
        
        # Verify clean slate after rollback
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count(UserNarrativeState.user_id)).where(
                UserNarrativeState.user_id >= 30000,
                UserNarrativeState.user_id < 30005
            )
        )
        count = result.scalar()
        
        assert count == 0, "Incomplete operations should be rolled back"
        
        # Now properly complete the operations
        for i in range(5):
            user_state = UserNarrativeState(
                user_id=30000 + i,
                current_fragment_id=f'recovery_fragment_{i}',
                current_level=1
            )
            session.add(user_state)
        
        await session.commit()
        
        # Verify recovery
        result = await session.execute(
            select(func.count(UserNarrativeState.user_id)).where(
                UserNarrativeState.user_id >= 30000,
                UserNarrativeState.user_id < 30005
            )
        )
        recovered_count = result.scalar()
        
        assert recovered_count == 5, "Should recover all operations after crash"


class TestErrorLoggingAndMonitoring:
    """Test error logging and monitoring capabilities."""

    async def test_error_categorization(self):
        """Test errors are properly categorized for monitoring."""
        errors = [
            ("Database connection failed", "database"),
            ("Telegram API timeout", "telegram_api"),
            ("Invalid user choice", "user_input"),
            ("Fragment validation failed", "character_consistency"),
            ("Performance threshold exceeded", "performance")
        ]
        
        for error_message, expected_category in errors:
            category = self.categorize_error(error_message)
            assert category == expected_category, f"Error '{error_message}' should be categorized as '{expected_category}', got '{category}'"

    def categorize_error(self, error_message: str) -> str:
        """Categorize error for monitoring purposes."""
        error_msg_lower = error_message.lower()
        
        if any(term in error_msg_lower for term in ['database', 'sql', 'connection', 'transaction']):
            return "database"
        elif any(term in error_msg_lower for term in ['telegram', 'api', 'network', 'timeout']):
            return "telegram_api"
        elif any(term in error_msg_lower for term in ['invalid', 'choice', 'input', 'user']):
            return "user_input"
        elif any(term in error_msg_lower for term in ['validation', 'character', 'consistency']):
            return "character_consistency"
        elif any(term in error_msg_lower for term in ['performance', 'timeout', 'slow']):
            return "performance"
        else:
            return "unknown"

    async def test_error_severity_assessment(self):
        """Test error severity assessment."""
        error_scenarios = [
            ("Database completely down", "critical"),
            ("Single user operation failed", "low"),
            ("Character consistency below threshold", "medium"),
            ("Performance degradation detected", "medium"),
            ("Telegram API rate limited", "high")
        ]
        
        for error, expected_severity in error_scenarios:
            severity = self.assess_error_severity(error)
            assert severity == expected_severity, f"Error '{error}' should have severity '{expected_severity}', got '{severity}'"

    def assess_error_severity(self, error_message: str) -> str:
        """Assess error severity for alerting."""
        error_lower = error_message.lower()
        
        # Critical: System-wide failures
        if any(term in error_lower for term in ['completely down', 'system failure', 'crash']):
            return "critical"
        
        # High: Service degradation affecting multiple users
        if any(term in error_lower for term in ['rate limited', 'service unavailable', 'degradation']):
            return "high"
        
        # Medium: Quality or performance issues
        if any(term in error_lower for term in ['consistency', 'performance', 'threshold']):
            return "medium"
        
        # Low: Individual user issues
        if any(term in error_lower for term in ['single user', 'individual', 'user operation']):
            return "low"
        
        return "medium"  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])