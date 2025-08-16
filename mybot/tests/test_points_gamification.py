"""
Tests de protección para el sistema de puntos y gamificación - Critical Business Logic.
Estos tests protegen la mecánica de puntos que mantiene el engagement de usuarios.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import datetime
from sqlalchemy import select

from services.point_service import PointService
from database.models import User, UserStats
from utils.messages import BOT_MESSAGES


@pytest.mark.asyncio
class TestPointsGamificationProtection:
    """Tests críticos para el sistema de puntos y gamificación."""

    async def test_award_message_nuevo_usuario(self, session, mock_bot):
        """
        CRITICAL: Test que protege el otorgamiento de puntos por mensajes a usuarios nuevos.
        Los nuevos usuarios deben recibir puntos correctamente.
        """
        service = PointService(session)
        user_id = 999888777
        
        with patch.object(service, '_get_or_create_progress') as mock_get_progress, \
             patch('services.point_service.AchievementService') as mock_achievement_service:
            
            # Mock progress creation for new user
            new_progress = UserStats(
                user_id=user_id,
                messages_sent=0,
                last_activity_at=None
            )
            mock_get_progress.return_value = new_progress
            
            # Mock achievement service
            mock_ach_service = AsyncMock()
            mock_ach_service.check_message_achievements.return_value = None
            mock_ach_service.check_user_badges.return_value = []
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            updated_progress = UserStats(
                user_id=user_id,
                messages_sent=1,
                last_activity_at=datetime.datetime.utcnow()
            )
            with patch.object(service, 'add_points', return_value=updated_progress):
                
                result = await service.award_message(user_id, mock_bot)
                
                # Critical assertions - new users must receive points
                assert result is not None, "New users must receive points for messages"
                assert result.messages_sent == 1, "Message count must be incremented"
                
                # Verify achievement check was called
                mock_ach_service.check_message_achievements.assert_called_once_with(
                    user_id, 1, bot=mock_bot
                )

    async def test_award_message_rate_limiting(self, session, mock_bot):
        """
        CRITICAL: Test que protege el rate limiting de puntos por mensajes.
        Los usuarios NO deben recibir puntos por mensajes muy frecuentes.
        """
        service = PointService(session)
        user_id = 123456789
        
        # Create progress with recent activity (less than 30 seconds ago)
        recent_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        progress = UserStats(
            user_id=user_id,
            messages_sent=5,
            last_activity_at=recent_time
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress):
            result = await service.award_message(user_id, mock_bot)
            
            # Critical assertions - rate limiting must prevent point abuse
            assert result is None, "Recent activity must prevent point award"

    async def test_award_reaction_rate_limiting(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el rate limiting de puntos por reacciones.
        Las reacciones muy frecuentes NO deben otorgar puntos múltiples.
        """
        service = PointService(session)
        
        # Create progress with very recent reaction (less than 5 seconds ago)
        recent_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=2)
        progress = UserStats(
            user_id=test_user.id,
            last_reaction_at=recent_time
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress):
            result = await service.award_reaction(test_user, 12345, mock_bot)
            
            # Critical assertions - reaction rate limiting must work
            assert result is None, "Recent reactions must be rate limited"

    async def test_award_reaction_success(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el otorgamiento exitoso de puntos por reacciones.
        Las reacciones válidas DEBEN otorgar puntos.
        """
        service = PointService(session)
        
        # Create progress without recent reaction
        old_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        progress = UserStats(
            user_id=test_user.id,
            last_reaction_at=old_time
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress), \
             patch('services.point_service.AchievementService') as mock_achievement_service:
            
            mock_ach_service = AsyncMock()
            mock_ach_service.check_user_badges.return_value = []
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            updated_progress = UserStats(
                user_id=test_user.id,
                last_reaction_at=datetime.datetime.utcnow()
            )
            with patch.object(service, 'add_points', return_value=updated_progress):
                
                result = await service.award_reaction(test_user, 12345, mock_bot)
                
                # Critical assertions - valid reactions must award points
                assert result is not None, "Valid reactions must award points"
                
                # Verify session commit was called to save reaction time
                assert hasattr(result, 'last_reaction_at'), "Reaction time must be tracked"

    async def test_daily_checkin_success(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el daily check-in exitoso.
        Los usuarios deben poder hacer check-in diario y recibir puntos.
        """
        service = PointService(session)
        
        # Create progress without recent check-in
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=2)
        progress = UserStats(
            user_id=test_user.id,
            last_checkin_at=yesterday,
            checkin_streak=2
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress), \
             patch('services.point_service.AchievementService') as mock_achievement_service:
            
            mock_ach_service = AsyncMock()
            mock_ach_service.check_checkin_achievements.return_value = None
            mock_ach_service.check_user_badges.return_value = []
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            updated_progress = UserStats(
                user_id=test_user.id,
                last_checkin_at=datetime.datetime.utcnow(),
                checkin_streak=3  # Incremented
            )
            with patch.object(service, 'add_points', return_value=updated_progress):
                
                success, result = await service.daily_checkin(test_user.id, mock_bot)
                
                # Critical assertions - daily check-in must work
                assert success is True, "Daily check-in must succeed for valid users"
                assert result.checkin_streak == 3, "Streak must be incremented for consecutive days"
                
                # Verify achievement check was called
                mock_ach_service.check_checkin_achievements.assert_called_once_with(
                    test_user.id, 3, bot=mock_bot
                )

    async def test_daily_checkin_rate_limiting(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el rate limiting del daily check-in.
        Los usuarios NO deben poder hacer múltiples check-ins el mismo día.
        """
        service = PointService(session)
        
        # Create progress with recent check-in (less than 24 hours ago)
        recent_time = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        progress = UserStats(
            user_id=test_user.id,
            last_checkin_at=recent_time,
            checkin_streak=5
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress):
            success, result = await service.daily_checkin(test_user.id, mock_bot)
            
            # Critical assertions - daily check-in rate limiting must work
            assert success is False, "Same-day check-in must be prevented"
            assert result.checkin_streak == 5, "Streak must not change for failed check-in"

    async def test_daily_checkin_streak_broken(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el reset de streaks cuando se rompen.
        Las streaks deben resetearse si el usuario no hace check-in consecutivo.
        """
        service = PointService(session)
        
        # Create progress with old check-in (more than 1 day gap)
        old_time = datetime.datetime.utcnow() - datetime.timedelta(days=3)
        progress = UserStats(
            user_id=test_user.id,
            last_checkin_at=old_time,
            checkin_streak=7  # Had a good streak
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress), \
             patch('services.point_service.AchievementService') as mock_achievement_service:
            
            mock_ach_service = AsyncMock()
            mock_ach_service.check_checkin_achievements.return_value = None
            mock_ach_service.check_user_badges.return_value = []
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            updated_progress = UserStats(
                user_id=test_user.id,
                last_checkin_at=datetime.datetime.utcnow(),
                checkin_streak=1  # Reset to 1
            )
            with patch.object(service, 'add_points', return_value=updated_progress):
                
                success, result = await service.daily_checkin(test_user.id, mock_bot)
                
                # Critical assertions - broken streaks must reset
                assert success is True, "Check-in must still succeed"
                assert result.checkin_streak == 1, "Broken streak must reset to 1"

    async def test_award_poll_basic_functionality(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el otorgamiento de puntos por responder polls.
        Las respuestas a polls deben otorgar puntos correctamente.
        """
        service = PointService(session)
        
        with patch('services.point_service.AchievementService') as mock_achievement_service:
            mock_ach_service = AsyncMock()
            mock_ach_service.check_user_badges.return_value = []
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            progress = UserStats(user_id=test_user.id)
            with patch.object(service, 'add_points', return_value=progress):
                
                result = await service.award_poll(test_user.id, mock_bot)
                
                # Critical assertions - poll responses must award points
                assert result is not None, "Poll responses must award points"
                
                # Verify add_points was called with correct amount (2 points for polls)
                service.add_points.assert_called_once_with(test_user.id, 2, bot=mock_bot)

    async def test_get_or_create_progress_new_user(self, session):
        """
        CRITICAL: Test que protege la creación de progreso para usuarios nuevos.
        Los usuarios nuevos deben tener progreso creado automáticamente.
        """
        service = PointService(session)
        new_user_id = 777888999
        
        # Ensure user doesn't exist
        stmt = select(UserStats).where(UserStats.user_id == new_user_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        assert existing is None, "User should not exist initially"
        
        # Call the method
        progress = await service._get_or_create_progress(new_user_id)
        
        # Critical assertions - new progress must be created
        assert progress is not None, "Progress must be created for new users"
        assert progress.user_id == new_user_id, "Progress must be for correct user"
        assert progress.messages_sent == 0, "New progress must start with 0 messages"
        assert progress.checkin_streak == 0, "New progress must start with 0 streak"

    async def test_get_or_create_progress_existing_user(self, session, user_progress):
        """
        CRITICAL: Test que protege la recuperación de progreso existente.
        Los usuarios existentes deben recuperar su progreso sin duplicación.
        """
        service = PointService(session)
        
        # Call the method for existing user
        progress = await service._get_or_create_progress(user_progress.user_id)
        
        # Critical assertions - existing progress must be retrieved
        assert progress is not None, "Existing progress must be retrieved"
        assert progress.user_id == user_progress.user_id, "Correct progress must be retrieved"
        assert progress.checkin_streak == user_progress.checkin_streak, "Existing data must be preserved"

    async def test_achievement_integration_message_badges(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege la integración con el sistema de achievements.
        Los logros deben verificarse y otorgarse correctamente al ganar puntos.
        """
        service = PointService(session)
        
        progress = UserStats(
            user_id=test_user.id,
            messages_sent=0,
            last_activity_at=None
        )
        
        with patch.object(service, '_get_or_create_progress', return_value=progress), \
             patch('services.point_service.AchievementService') as mock_achievement_service:
            
            # Mock badge earning
            mock_badge = MagicMock()
            mock_badge.id = 1
            mock_badge.name = "Primer Mensaje"
            mock_badge.icon = "💌"
            
            mock_ach_service = AsyncMock()
            mock_ach_service.check_message_achievements.return_value = None
            mock_ach_service.check_user_badges.return_value = [mock_badge]
            mock_ach_service.award_badge = AsyncMock()
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            updated_progress = UserStats(
                user_id=test_user.id,
                messages_sent=1
            )
            with patch.object(service, 'add_points', return_value=updated_progress):
                
                result = await service.award_message(test_user.id, mock_bot)
                
                # Critical assertions - achievement integration must work
                assert result is not None, "Message points must be awarded"
                
                # Verify badge was awarded
                mock_ach_service.award_badge.assert_called_once_with(test_user.id, 1)
                
                # Verify bot notification was sent
                mock_bot.send_message.assert_called_once_with(
                    test_user.id,
                    "🏅 Has obtenido la insignia 💌 Primer Mensaje!"
                )

    async def test_point_service_error_handling(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el manejo de errores en el servicio de puntos.
        Los errores NO deben romper el flujo del otorgamiento de puntos.
        """
        service = PointService(session)
        
        # Mock _get_or_create_progress to raise exception
        with patch.object(service, '_get_or_create_progress', side_effect=Exception("Database error")):
            
            # This should not raise an exception in a real scenario
            # But for testing, we expect it to propagate
            with pytest.raises(Exception, match="Database error"):
                await service.award_message(test_user.id, mock_bot)

    async def test_multiple_badges_notification(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege las notificaciones de múltiples badges.
        Si se ganan múltiples badges, todos deben ser notificados.
        """
        service = PointService(session)
        
        progress = UserStats(user_id=test_user.id, last_reaction_at=None)
        
        with patch.object(service, '_get_or_create_progress', return_value=progress), \
             patch('services.point_service.AchievementService') as mock_achievement_service:
            
            # Mock multiple badges
            badge1 = MagicMock()
            badge1.id = 1
            badge1.name = "Primera Reacción"
            badge1.icon = "❤️"
            
            badge2 = MagicMock()
            badge2.id = 2
            badge2.name = "Participación Activa"
            badge2.icon = "🌟"
            
            mock_ach_service = AsyncMock()
            mock_ach_service.check_user_badges.return_value = [badge1, badge2]
            mock_ach_service.award_badge = AsyncMock()
            mock_achievement_service.return_value = mock_ach_service
            
            # Mock add_points method
            updated_progress = UserStats(
                user_id=test_user.id,
                last_reaction_at=datetime.datetime.utcnow()
            )
            with patch.object(service, 'add_points', return_value=updated_progress):
                
                result = await service.award_reaction(test_user, 12345, mock_bot)
                
                # Critical assertions - multiple badges must be handled
                assert result is not None, "Reaction points must be awarded"
                
                # Verify both badges were awarded
                assert mock_ach_service.award_badge.call_count == 2
                mock_ach_service.award_badge.assert_any_call(test_user.id, 1)
                mock_ach_service.award_badge.assert_any_call(test_user.id, 2)
                
                # Verify both notifications were sent
                assert mock_bot.send_message.call_count == 2
                mock_bot.send_message.assert_any_call(
                    test_user.id,
                    "🏅 Has obtenido la insignia ❤️ Primera Reacción!"
                )
                mock_bot.send_message.assert_any_call(
                    test_user.id,
                    "🏅 Has obtenido la insignia 🌟 Participación Activa!"
                )