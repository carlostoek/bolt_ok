from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from database.models import User, Level, LorePiece, UserLorePiece
from utils.messages import BOT_MESSAGES
import logging

logger = logging.getLogger(__name__)

# MVP Level Progression System as per requirements
MVP_LEVELS = [
    # Level 1-5: 100 besitos per level
    (1, "Novata", 0, "Bienvenida a mi mundo..."),
    (2, "Curiosa", 100, "Te veo más interesada, cariño"),
    (3, "Encantada", 200, "Empiezo a confiar en ti"),
    (4, "Seducida", 300, "Hay algo especial en ti..."),
    (5, "Cautivada", 400, "Me tienes intrigada, amor"),
    # Level 6-10: 200 besitos per level  
    (6, "Devotida", 600, "Tu dedicación me conmueve"),
    (7, "Misteriosa", 800, "Compartimos secretos ahora"),
    (8, "Íntima", 1000, "Nuestra conexión se profundiza"),
    (9, "Apasionada", 1200, "Siento algo especial por ti"),
    (10, "Enamorada", 1400, "Mi corazón late más fuerte..."),
    # Level 11+: 500 besitos per level
    (11, "Alma Gemela", 1900, "Somos uno, mi amor"),
    (12, "Eternamente Unidas", 2400, "Para siempre juntas"),
    (13, "Diosa del Amor", 2900, "Eres mi todo"),
    (14, "Reina de mi Corazón", 3400, "Reinas en mi alma"),
    (15, "Emperatriz del Deseo", 3900, "El poder del amor nos une"),
    (16, "Divinidad Suprema", 4400, "Trasciendes lo mortal"),
    (17, "Esencia Pura", 4900, "Eres perfección absoluta"),
    (18, "Infinito Amor", 5400, "Nuestro amor es eterno"),
    (19, "Más allá del Tiempo", 5900, "Existimos fuera de la realidad"),
    (20, "Una Sola Alma", 6400, "Somos una en el cosmos"),
]

# Keep DEFAULT_LEVELS for backward compatibility if needed
DEFAULT_LEVELS = MVP_LEVELS

# MVP Level Thresholds for quick calculation
MVP_LEVEL_THRESHOLDS = [
    (1, 0),     # Level 1: 0 besitos
    (2, 100),   # Level 2: 100 besitos  
    (3, 200),   # Level 3: 200 besitos
    (4, 300),   # Level 4: 300 besitos
    (5, 400),   # Level 5: 400 besitos
    (6, 600),   # Level 6: 600 besitos (400 + 200)
    (7, 800),   # Level 7: 800 besitos (600 + 200)
    (8, 1000),  # Level 8: 1000 besitos (800 + 200)
    (9, 1200),  # Level 9: 1200 besitos (1000 + 200)
    (10, 1400), # Level 10: 1400 besitos (1200 + 200)
    (11, 1900), # Level 11: 1900 besitos (1400 + 500)
    (12, 2400), # Level 12: 2400 besitos (1900 + 500)
    (13, 2900), # Level 13: 2900 besitos (2400 + 500)
    (14, 3400), # Level 14: 3400 besitos (2900 + 500)
    (15, 3900), # Level 15: 3900 besitos (3400 + 500)
    (16, 4400), # Level 16: 4400 besitos (3900 + 500)
    (17, 4900), # Level 17: 4900 besitos (4400 + 500)
    (18, 5400), # Level 18: 5400 besitos (4900 + 500)
    (19, 5900), # Level 19: 5900 besitos (5400 + 500)
    (20, 6400), # Level 20: 6400 besitos (5900 + 500)
]

# Keep LEVELS for backward compatibility
LEVELS = MVP_LEVEL_THRESHOLDS

class LevelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _init_levels(self) -> None:
        result = await self.session.execute(select(Level))
        if result.scalars().first():
            return
        for level_id, name, min_points, reward in DEFAULT_LEVELS:
            self.session.add(Level(level_id=level_id, name=name, min_points=min_points, reward=reward))
        await self.session.commit()

    async def _get_levels(self) -> list[Level]:
        await self._init_levels()
        result = await self.session.execute(select(Level).order_by(Level.min_points))
        return result.scalars().all()

    async def list_levels(self) -> list[Level]:
        """Return all levels ordered by their number."""
        result = await self.session.execute(select(Level).order_by(Level.level_id))
        return result.scalars().all()

    async def create_level(
        self,
        level_number: int,
        name: str,
        required_points: int,
        reward: str | None = None,
    ) -> Level:
        new_level = Level(
            level_id=level_number,
            name=name,
            min_points=required_points,
            reward=reward,
        )
        self.session.add(new_level)
        await self.session.commit()
        await self.session.refresh(new_level)
        return new_level

    async def update_level(
        self,
        level_id: int,
        *,
        new_level_number: int | None = None,
        name: str | None = None,
        required_points: int | None = None,
        reward: str | None = None,
    ) -> bool:
        level = await self.session.get(Level, level_id)
        if not level:
            return False
        if new_level_number is not None:
            level.level_id = new_level_number
        if name is not None:
            level.name = name
        if required_points is not None:
            level.min_points = required_points
        if reward is not None:
            level.reward = reward
        await self.session.commit()
        return True

    async def delete_level(self, level_id: int) -> bool:
        level = await self.session.get(Level, level_id)
        if not level:
            return False
        await self.session.delete(level)
        await self.session.commit()
        return True

    async def get_level_threshold(self, level_id: int) -> int:
        levels = await self._get_levels()
        for lvl in levels:
            if lvl.level_id == level_id:
                return lvl.min_points
        return float("inf")

    async def get_level_for_points(self, points: float) -> Level:
        levels = await self._get_levels()
        current = levels[0]
        for lvl in levels:
            if points >= lvl.min_points:
                current = lvl
            else:
                break
        return current

    async def check_for_level_up(self, user: User, *, bot: Bot | None = None) -> bool:
        new_level = await self.get_level_for_points(user.points)
        if new_level.level_id != user.level:
            old_level = user.level
            user.level = new_level.level_id
            await self.session.commit()
            await self.session.refresh(user)
            
            # Send Diana's character-consistent level up notification
            if bot:
                from services.notification_service import NotificationService, NotificationPriority
                try:
                    notification_service = NotificationService(self.session, bot)
                    
                    # Diana's level up messages with seductive personality
                    diana_level_messages = [
                        f"¡Nivel {new_level.level_id}! {new_level.reward} Cada nivel que subes me permite conocerte mejor, cariño. 💎",
                        f"Has alcanzado el nivel {new_level.level_id}... {new_level.reward} Me fascina tu dedicación por mí. 🌹",
                        f"Nivel {new_level.level_id}, mi amor. {new_level.reward} Sigues sorprendiéndome día tras día. ✨"
                    ]
                    
                    import random
                    message = random.choice(diana_level_messages)
                    
                    await notification_service.add_notification(
                        user.id,
                        "level_up",
                        {
                            "message": message,
                            "old_level": old_level,
                            "new_level": new_level.level_id,
                            "level_name": new_level.name,
                            "reward": new_level.reward
                        },
                        priority=NotificationPriority.HIGH
                    )
                    
                    # Special milestone messages for important levels
                    if new_level.level_id in {5, 10, 15, 20}:
                        milestone_messages = {
                            5: "Nivel 5... Has demostrado que realmente te importo. Esto merece algo especial. 💋",
                            10: "¡Nivel 10! Nuestra conexión se vuelve más profunda. ¿Sientes cómo cambia todo entre nosotras? 💖",
                            15: "Nivel 15... Pocos llegan tan lejos conmigo. Eres verdaderamente especial, mi amor. 🔮",
                            20: "¡Nivel 20! Has alcanzado la perfección absoluta. Somos una sola alma ahora... 🌟"
                        }
                        
                        await notification_service.add_notification(
                            user.id,
                            "milestone_reached",
                            {
                                "message": milestone_messages[new_level.level_id],
                                "milestone_level": new_level.level_id
                            },
                            priority=NotificationPriority.CRITICAL
                        )
                        
                except Exception as e:
                    logger.error(f"Error sending Diana level up notification: {e}")
                    # Fallback to basic message if notification service fails
                    msg = f"¡Nivel {new_level.level_id}! {new_level.name} - {new_level.reward or ''}"
                    await bot.send_message(user.id, msg)

            # Desbloquear pistas de lore asociadas al nivel alcanzado
            unlock_code = getattr(new_level, "unlocks_lore_piece_code", None)
            if unlock_code:
                lore_stmt = select(LorePiece).where(LorePiece.code_name == unlock_code)
                lore_piece = (await self.session.execute(lore_stmt)).scalar_one_or_none()
                if lore_piece:
                    check_stmt = select(UserLorePiece).where(
                        UserLorePiece.user_id == user.id,
                        UserLorePiece.lore_piece_id == lore_piece.id,
                    )
                    exists = (await self.session.execute(check_stmt)).scalar_one_or_none()
                    if not exists:
                        self.session.add(UserLorePiece(user_id=user.id, lore_piece_id=lore_piece.id))
                        await self.session.commit()
                        if bot:
                            await bot.send_message(user.id, f"Has desbloqueado una nueva pista: {lore_piece.title}")
                        logger.info(
                            f"User {user.id} unlocked lore piece {unlock_code} via level {new_level.level_id}"
                        )
            return True
        return False


def get_user_level(points: int) -> int:
    """Calculate user level based on accumulated points using MVP thresholds."""
    current_level = MVP_LEVEL_THRESHOLDS[0][0]
    for level, threshold in MVP_LEVEL_THRESHOLDS:
        if points >= threshold:
            current_level = level
        else:
            break
    return current_level


def get_next_level_info(points: int) -> dict:
    """Return progress information towards the next level using MVP thresholds."""
    current_level = get_user_level(points)

    # Find thresholds for current and next levels
    current_threshold = 0
    next_threshold = None
    for level, threshold in MVP_LEVEL_THRESHOLDS:
        if level == current_level:
            current_threshold = threshold
        elif level > current_level and next_threshold is None:
            next_threshold = threshold
            break

    if next_threshold is None:
        # At max level (20)
        return {
            "current_level": current_level,
            "next_level": current_level,
            "points_needed": 0,
            "percentage_to_next": 1.0,
            "is_max_level": True,
        }

    points_needed = max(0, next_threshold - points)
    total_range = next_threshold - current_threshold
    percentage = (points - current_threshold) / total_range if total_range else 1
    
    # Get level names from MVP_LEVELS for display
    current_level_name = next((name for level_id, name, _, _ in MVP_LEVELS if level_id == current_level), f"Nivel {current_level}")
    next_level_name = next((name for level_id, name, _, _ in MVP_LEVELS if level_id == current_level + 1), f"Nivel {current_level + 1}")

    return {
        "current_level": current_level,
        "current_level_name": current_level_name,
        "next_level": current_level + 1,
        "next_level_name": next_level_name,
        "points_needed": points_needed,
        "percentage_to_next": min(max(percentage, 0), 1),
        "is_max_level": False,
    }
