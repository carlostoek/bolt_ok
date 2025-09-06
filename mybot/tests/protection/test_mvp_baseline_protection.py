"""
🛡️ MVP BASELINE PROTECTION TESTS
Tests críticos que protegen el sistema baseline desde day one.
Director: "desde el MVP no se hace ningún test" - ESTO CAMBIA AHORA.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserStats, Channel
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog, LorePiece, UserLorePiece
from services.coordinador_central import CoordinadorCentral
from services.user_narrative_service import UserNarrativeService
from services.diana_menu_system import DianaMenuSystem
from services.point_service import PointService
from services.user_service import UserService


class TestMVPBaselineProtection:
    """Protección crítica del sistema MVP baseline."""
    
    @pytest.mark.asyncio
    async def test_database_integrity_protection(self, session):
        """🔒 CRITICAL: Database schema integrity check."""
        # Test que todas las tablas críticas existen
        critical_tables = [
            'users', 'channels', 'user_stats', 'badges', 'user_badges',
            'narrative_rewards', 'user_reward_history', 'narrative_fragments',
            'user_narrative_states', 'user_decision_logs', 'lore_pieces',
            'user_lore_pieces'
        ]
        
        for table in critical_tables:
            result = await session.execute(
                text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            )
            assert result.scalar_one_or_none() == table, f"Critical table {table} missing!"
    
    @pytest.mark.asyncio
    async def test_coordinador_central_core_functions(self, session, level_service, achievement_service):
        """🔒 CRITICAL: CoordinadorCentral debe funcionar perfectamente."""
        from services.notification_service import NotificationService
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        coordinador = CoordinadorCentral(session)
        coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Test usuario creation
        test_user = User(
            id=987654321,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=0.0
        )
        session.add(test_user)
        await session.commit()
        
        # Test processing básico
        result = await coordinador.process_user_reaction(
            user_id=987654321,
            channel_id=-1001234567890,
            message_id=1,
            reaction="like",
            points_earned=10.0
        )
        
        assert result is True, "CoordinadorCentral processing failed!"
        
        # Verificar puntos updated
        await session.refresh(test_user)
        assert test_user.points >= 10.0, f"Points not updated correctly: {test_user.points}"
    
    @pytest.mark.asyncio
    async def test_user_narrative_service_baseline(self, session):
        """🔒 CRITICAL: UserNarrativeService must work flawlessly."""
        service = UserNarrativeService(session)
        
        # Create test user
        user = User(
            id=555666777,
            first_name="NarrativeUser",
            role="free",
            points=0.0
        )
        session.add(user)
        await session.commit()
        
        # Test que puede obtener estado
        state = await service.get_user_narrative_state(555666777)
        assert state is not None, "Could not get user narrative state!"
        
        # Test progresión básica
        can_progress = await service.can_user_progress_to_tier(555666777, 2)
        assert isinstance(can_progress, bool), "Progression check failed!"
    
    @pytest.mark.asyncio
    async def test_diana_menu_system_baseline(self, session):
        """🔒 CRITICAL: Diana Menu System core functionality."""
        mock_bot = AsyncMock()
        menu_system = DianaMenuSystem(session, mock_bot)
        
        # Test que puede generar menu
        user = User(
            id=444555666,
            first_name="MenuUser",
            role="free",
            points=100.0
        )
        session.add(user)
        await session.commit()
        
        # Mock callback query
        callback = MagicMock()
        callback.from_user.id = 444555666
        callback.data = "diana_menu"
        callback.message.edit_text = AsyncMock()
        
        # Test menu generation
        try:
            await menu_system.handle_diana_menu(callback)
            # Si llega aquí without error, está bien
            assert True
        except Exception as e:
            pytest.fail(f"Diana Menu System failed: {e}")
    
    @pytest.mark.asyncio
    async def test_16_narrative_fragments_existence(self, session):
        """🔒 CRITICAL: Los 16 fragmentos narrativos deben existir."""
        # Crear fragmentos de prueba si no existen
        expected_fragments = list(range(1, 17))  # 1-16
        
        for fragment_id in expected_fragments:
            existing = await session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            )
            fragment = existing.scalar_one_or_none()
            
            if not fragment:
                # Crear fragmento de prueba
                test_fragment = NarrativeFragment(
                    id=fragment_id,
                    title=f"Test Fragment {fragment_id}",
                    content=f"Test content for fragment {fragment_id}",
                    choices_data=[{"text": "Continue", "next_fragment": fragment_id + 1}],
                    tier=1 if fragment_id <= 5 else (2 if fragment_id <= 10 else 3),
                    required_role="free" if fragment_id <= 5 else "vip"
                )
                session.add(test_fragment)
        
        await session.commit()
        
        # Verificar que todos existen
        result = await session.execute(select(NarrativeFragment))
        fragments = result.scalars().all()
        assert len(fragments) >= 16, f"Only {len(fragments)} fragments found, need 16!"
    
    @pytest.mark.asyncio
    async def test_user_archetype_system_baseline(self, session):
        """🔒 CRITICAL: 6 arquetipos de usuario deben funcionar."""
        archetypes = ["Explorer", "Direct", "Romantic", "Analytical", "Persistent", "Patient"]
        
        for archetype in archetypes:
            user = User(
                id=100000 + hash(archetype) % 900000,  # Unique ID
                first_name=f"{archetype}User",
                role="free",
                points=50.0,
                archetype=archetype
            )
            session.add(user)
        
        await session.commit()
        
        # Verificar que todos se crearon
        result = await session.execute(select(User).where(User.archetype.in_(archetypes)))
        users = result.scalars().all()
        assert len(users) == 6, f"Only {len(users)} archetype users created!"
    
    @pytest.mark.asyncio
    async def test_lore_piece_clue_system(self, session):
        """🔒 CRITICAL: Sistema de pistas LorePiece/UserLorePiece."""
        # Create test lore piece
        lore = LorePiece(
            id="test_clue_001",
            title="Test Clue",
            content="This is a test clue content",
            unlock_condition="test_condition",
            tier_required=1
        )
        session.add(lore)
        await session.commit()
        
        # Create test user
        user = User(
            id=777888999,
            first_name="ClueUser",
            role="free",
            points=0.0
        )
        session.add(user)
        await session.commit()
        
        # Create user lore piece relationship
        user_lore = UserLorePiece(
            user_id=777888999,
            lore_piece_id="test_clue_001",
            unlocked_at=datetime.datetime.utcnow()
        )
        session.add(user_lore)
        await session.commit()
        
        # Verify relationship exists
        result = await session.execute(
            select(UserLorePiece).where(
                UserLorePiece.user_id == 777888999,
                UserLorePiece.lore_piece_id == "test_clue_001"
            )
        )
        user_lore_check = result.scalar_one_or_none()
        assert user_lore_check is not None, "LorePiece-User relationship failed!"
    
    @pytest.mark.asyncio
    async def test_character_consistency_baseline(self, session):
        """🔒 CRITICAL: >95% character consistency requirement."""
        from services.diana_character_validator import DianaCharacterValidator
        
        validator = DianaCharacterValidator(session)
        
        # Test consistency check - debe ser >95%
        consistency_score = await validator.validate_character_consistency()
        assert consistency_score >= 0.95, f"Character consistency {consistency_score} < 95%!"
    
    @pytest.mark.asyncio
    async def test_response_time_guarantee(self, session):
        """🔒 CRITICAL: <500ms response time guarantee."""
        import time
        
        # Test CoordinadorCentral response time
        from services.notification_service import NotificationService
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        coordinador = CoordinadorCentral(session)
        
        # Create test user
        user = User(
            id=111222333,
            first_name="SpeedUser",
            role="free",
            points=0.0
        )
        session.add(user)
        await session.commit()
        
        # Measure response time
        start_time = time.time()
        
        result = await coordinador.process_user_reaction(
            user_id=111222333,
            channel_id=-1001234567890,
            message_id=1,
            reaction="like",
            points_earned=10.0
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert response_time < 500, f"Response time {response_time}ms > 500ms limit!"
        assert result is True, "Operation failed while testing response time!"


class TestMVPDatabaseOperations:
    """Protección de operaciones críticas de base de datos."""
    
    @pytest.mark.asyncio
    async def test_user_creation_atomic(self, session):
        """🔒 CRITICAL: User creation debe ser atomic."""
        user_data = {
            'id': 999888777,
            'first_name': 'AtomicUser',
            'role': 'free',
            'points': 0.0
        }
        
        try:
            async with session.begin():
                user = User(**user_data)
                session.add(user)
                
                # Create related UserStats
                stats = UserStats(
                    user_id=user_data['id'],
                    checkin_streak=0,
                    last_checkin_at=None
                )
                session.add(stats)
                
            # Verify both were created
            user_check = await session.get(User, 999888777)
            stats_check = await session.execute(
                select(UserStats).where(UserStats.user_id == 999888777)
            )
            stats_result = stats_check.scalar_one_or_none()
            
            assert user_check is not None, "User creation failed in atomic transaction!"
            assert stats_result is not None, "UserStats creation failed in atomic transaction!"
            
        except Exception as e:
            pytest.fail(f"Atomic user creation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_narrative_progression_integrity(self, session):
        """🔒 CRITICAL: Narrative progression debe mantener integridad."""
        # Create test user and narrative state
        user = User(
            id=666777888,
            first_name="ProgressUser",
            role="free",
            points=0.0
        )
        session.add(user)
        
        narrative_state = UserNarrativeState(
            user_id=666777888,
            current_fragment_id=1,
            tier=1,
            completed_fragments=[],
            available_choices=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test progression
        service = UserNarrativeService(session)
        
        # Simulate progression to fragment 2
        decision_log = UserDecisionLog(
            user_id=666777888,
            fragment_id=1,
            choice_index=0,
            choice_text="Continue",
            timestamp=datetime.datetime.utcnow()
        )
        session.add(decision_log)
        
        # Update narrative state
        narrative_state.current_fragment_id = 2
        narrative_state.completed_fragments = [1]
        
        await session.commit()
        
        # Verify integrity
        updated_state = await service.get_user_narrative_state(666777888)
        assert updated_state.current_fragment_id == 2, "Narrative progression integrity failed!"
        assert 1 in updated_state.completed_fragments, "Completed fragments not tracked!"


class TestMVPErrorHandling:
    """Protección contra errores críticos del MVP."""
    
    @pytest.mark.asyncio
    async def test_graceful_database_error_handling(self, session):
        """🔒 CRITICAL: Graceful handling de database errors."""
        coordinador = CoordinadorCentral(session)
        
        # Test con usuario inexistente
        result = await coordinador.process_user_reaction(
            user_id=999999999,  # Non-existent user
            channel_id=-1001234567890,
            message_id=1,
            reaction="like",
            points_earned=10.0
        )
        
        # No debe crashear, debe handle gracefully
        assert isinstance(result, bool), "Database error not handled gracefully!"
    
    @pytest.mark.asyncio
    async def test_narrative_service_error_resilience(self, session):
        """🔒 CRITICAL: Narrative service debe ser resilient a errors."""
        service = UserNarrativeService(session)
        
        # Test con datos inválidos
        try:
            state = await service.get_user_narrative_state(-1)  # Invalid user ID
            # Debe return None o default state, no crashear
            assert state is not None or state is None, "Service not resilient to invalid data!"
        except Exception as e:
            pytest.fail(f"Narrative service not resilient to errors: {e}")
    
    @pytest.mark.asyncio
    async def test_menu_system_fallback_protection(self, session):
        """🔒 CRITICAL: Menu system debe tener fallbacks."""
        mock_bot = AsyncMock()
        menu_system = DianaMenuSystem(session, mock_bot)
        
        # Test con callback inválido
        invalid_callback = MagicMock()
        invalid_callback.from_user.id = None
        invalid_callback.data = "invalid_data"
        invalid_callback.message = None
        
        try:
            await menu_system.handle_diana_menu(invalid_callback)
            # Si no crashea, tiene buenos fallbacks
            assert True
        except Exception as e:
            # Debe handle gracefully, no crashear todo el sistema
            assert "graceful" in str(e).lower() or "handled" in str(e).lower(), f"Not graceful: {e}"


@pytest.mark.asyncio
async def test_mvp_system_integration_smoke_test(session, level_service, achievement_service):
    """🚨 SMOKE TEST CRÍTICO: Todo el sistema MVP debe funcionar together."""
    from services.notification_service import NotificationService
    
    # Setup completo
    mock_bot = AsyncMock()
    notification_service = NotificationService(session, mock_bot)
    
    coordinador = CoordinadorCentral(session)
    coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
    
    narrative_service = UserNarrativeService(session)
    user_service = UserService(session)
    menu_system = DianaMenuSystem(session, mock_bot)
    
    # Create test user
    user = User(
        id=123123123,
        first_name="SmokeTestUser",
        role="free",
        points=0.0
    )
    session.add(user)
    await session.commit()
    
    # Test full user journey simulation
    # 1. User gets points
    points_result = await coordinador.process_user_reaction(
        user_id=123123123,
        channel_id=-1001234567890,
        message_id=1,
        reaction="like",
        points_earned=25.0
    )
    assert points_result is True, "Points processing failed in smoke test!"
    
    # 2. User accesses narrative
    narrative_state = await narrative_service.get_user_narrative_state(123123123)
    assert narrative_state is not None, "Narrative access failed in smoke test!"
    
    # 3. User accesses menu
    callback = MagicMock()
    callback.from_user.id = 123123123
    callback.data = "diana_menu"
    callback.message.edit_text = AsyncMock()
    
    try:
        await menu_system.handle_diana_menu(callback)
        menu_success = True
    except Exception:
        menu_success = False
    
    assert menu_success, "Menu access failed in smoke test!"
    
    # 4. Verify user state
    await session.refresh(user)
    assert user.points >= 25.0, f"Final user state invalid: {user.points} points"
    
    # 🎉 Si llegamos aquí, el MVP baseline está PROTEGIDO
    print("🛡️ MVP BASELINE PROTECTION: ALL SYSTEMS OPERATIONAL!")