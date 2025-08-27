"""
Repository Pattern Implementation for DianaBot.

This module provides abstraction layer for data access operations,
allowing flexibility and testability in data source interactions.
"""

from .interfaces import *
from .implementations import *

__all__ = [
    # Interfaces
    'IUserRepository',
    'INarrativeRepository', 
    'IGameRepository',
    'IPointRepository',
    'IMissionRepository',
    'IAchievementRepository',
    'IChannelRepository',
    'IAuctionRepository',
    'IConfigRepository',
    
    # Implementations
    'SqlUserRepository',
    'SqlNarrativeRepository',
    'SqlGameRepository', 
    'SqlPointRepository',
    'SqlMissionRepository',
    'SqlAchievementRepository',
    'SqlChannelRepository',
    'SqlAuctionRepository',
    'SqlConfigRepository',
]