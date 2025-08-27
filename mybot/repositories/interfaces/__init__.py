"""Repository interfaces for domain aggregates."""

from .user_repository import IUserRepository
from .narrative_repository import INarrativeRepository
from .game_repository import IGameRepository
from .point_repository import IPointRepository
from .mission_repository import IMissionRepository
from .achievement_repository import IAchievementRepository
from .channel_repository import IChannelRepository
from .auction_repository import IAuctionRepository
from .config_repository import IConfigRepository

__all__ = [
    'IUserRepository',
    'INarrativeRepository',
    'IGameRepository', 
    'IPointRepository',
    'IMissionRepository',
    'IAchievementRepository',
    'IChannelRepository',
    'IAuctionRepository',
    'IConfigRepository',
]