"""Game aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import (
    Trivia, TriviaQuestion, TriviaAttempt, TriviaUserAnswer,
    MiniGamePlay, Challenge, UserChallengeProgress,
    Event, Raffle, RaffleEntry
)
from datetime import datetime


class IGameRepository(ABC):
    """Repository interface for Game aggregate operations."""
    
    # Trivia operations
    @abstractmethod
    async def get_trivia_by_id(self, trivia_id: int) -> Optional[Trivia]:
        """Get trivia by ID."""
        pass
    
    @abstractmethod
    async def get_active_trivias(self) -> List[Trivia]:
        """Get all active trivias."""
        pass
    
    @abstractmethod
    async def create_trivia(self, trivia_data: Dict[str, Any]) -> Trivia:
        """Create a new trivia."""
        pass
    
    @abstractmethod
    async def update_trivia(self, trivia: Trivia) -> Trivia:
        """Update existing trivia."""
        pass
    
    @abstractmethod
    async def delete_trivia(self, trivia_id: int) -> bool:
        """Delete trivia."""
        pass
    
    # Trivia question operations
    @abstractmethod
    async def get_trivia_questions(self, trivia_id: int) -> List[TriviaQuestion]:
        """Get all questions for a trivia."""
        pass
    
    @abstractmethod
    async def get_trivia_question_by_id(self, question_id: int) -> Optional[TriviaQuestion]:
        """Get trivia question by ID."""
        pass
    
    @abstractmethod
    async def create_trivia_question(self, question_data: Dict[str, Any]) -> TriviaQuestion:
        """Create a new trivia question."""
        pass
    
    @abstractmethod
    async def update_trivia_question(self, question: TriviaQuestion) -> TriviaQuestion:
        """Update existing trivia question."""
        pass
    
    @abstractmethod
    async def delete_trivia_question(self, question_id: int) -> bool:
        """Delete trivia question."""
        pass
    
    # Trivia attempt operations
    @abstractmethod
    async def create_trivia_attempt(self, user_id: int, trivia_id: int) -> TriviaAttempt:
        """Create a new trivia attempt."""
        pass
    
    @abstractmethod
    async def get_user_trivia_attempts(self, user_id: int) -> List[TriviaAttempt]:
        """Get all trivia attempts by user."""
        pass
    
    @abstractmethod
    async def get_trivia_attempt_by_id(self, attempt_id: int) -> Optional[TriviaAttempt]:
        """Get trivia attempt by ID."""
        pass
    
    @abstractmethod
    async def update_trivia_attempt_score(self, attempt_id: int, score: int) -> TriviaAttempt:
        """Update trivia attempt score."""
        pass
    
    @abstractmethod
    async def complete_trivia_attempt(self, attempt_id: int, score: int) -> TriviaAttempt:
        """Complete trivia attempt with final score."""
        pass
    
    # Trivia answer operations
    @abstractmethod
    async def record_trivia_answer(self, attempt_id: int, question_id: int, answer: str, is_correct: bool) -> TriviaUserAnswer:
        """Record user's answer to trivia question."""
        pass
    
    @abstractmethod
    async def get_attempt_answers(self, attempt_id: int) -> List[TriviaUserAnswer]:
        """Get all answers for a trivia attempt."""
        pass
    
    # Minigame operations
    @abstractmethod
    async def record_minigame_play(self, user_id: int, game_type: str, is_free: bool = True, cost_points: float = 0) -> MiniGamePlay:
        """Record a minigame play session."""
        pass
    
    @abstractmethod
    async def get_user_minigame_history(self, user_id: int, game_type: Optional[str] = None) -> List[MiniGamePlay]:
        """Get user's minigame play history."""
        pass
    
    @abstractmethod
    async def get_last_minigame_play(self, user_id: int, game_type: str) -> Optional[MiniGamePlay]:
        """Get user's last play for specific game type."""
        pass
    
    @abstractmethod
    async def can_user_play_free_game(self, user_id: int, game_type: str, cooldown_hours: int = 24) -> bool:
        """Check if user can play free version of game."""
        pass
    
    # Challenge operations
    @abstractmethod
    async def get_challenge_by_id(self, challenge_id: int) -> Optional[Challenge]:
        """Get challenge by ID."""
        pass
    
    @abstractmethod
    async def get_active_challenges(self) -> List[Challenge]:
        """Get all active challenges."""
        pass
    
    @abstractmethod
    async def get_challenges_by_type(self, challenge_type: str) -> List[Challenge]:
        """Get challenges by type (daily, weekly, monthly)."""
        pass
    
    @abstractmethod
    async def create_challenge(self, challenge_data: Dict[str, Any]) -> Challenge:
        """Create a new challenge."""
        pass
    
    @abstractmethod
    async def update_challenge(self, challenge: Challenge) -> Challenge:
        """Update existing challenge."""
        pass
    
    @abstractmethod
    async def delete_challenge(self, challenge_id: int) -> bool:
        """Delete challenge."""
        pass
    
    # User challenge progress operations
    @abstractmethod
    async def get_user_challenge_progress(self, user_id: int, challenge_id: int) -> Optional[UserChallengeProgress]:
        """Get user's progress on specific challenge."""
        pass
    
    @abstractmethod
    async def get_user_all_challenge_progress(self, user_id: int) -> List[UserChallengeProgress]:
        """Get all user challenge progress entries."""
        pass
    
    @abstractmethod
    async def update_challenge_progress(self, user_id: int, challenge_id: int, progress: int) -> UserChallengeProgress:
        """Update user's challenge progress."""
        pass
    
    @abstractmethod
    async def complete_user_challenge(self, user_id: int, challenge_id: int) -> UserChallengeProgress:
        """Mark challenge as completed for user."""
        pass
    
    # Event operations
    @abstractmethod
    async def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        pass
    
    @abstractmethod
    async def get_active_events(self) -> List[Event]:
        """Get all active events."""
        pass
    
    @abstractmethod
    async def create_event(self, event_data: Dict[str, Any]) -> Event:
        """Create a new event."""
        pass
    
    @abstractmethod
    async def update_event(self, event: Event) -> Event:
        """Update existing event."""
        pass
    
    @abstractmethod
    async def end_event(self, event_id: int) -> Event:
        """End an active event."""
        pass
    
    @abstractmethod
    async def get_current_point_multiplier(self) -> int:
        """Get current global point multiplier from active events."""
        pass
    
    # Raffle operations
    @abstractmethod
    async def get_raffle_by_id(self, raffle_id: int) -> Optional[Raffle]:
        """Get raffle by ID."""
        pass
    
    @abstractmethod
    async def get_active_raffles(self) -> List[Raffle]:
        """Get all active raffles."""
        pass
    
    @abstractmethod
    async def create_raffle(self, raffle_data: Dict[str, Any]) -> Raffle:
        """Create a new raffle."""
        pass
    
    @abstractmethod
    async def update_raffle(self, raffle: Raffle) -> Raffle:
        """Update existing raffle."""
        pass
    
    @abstractmethod
    async def end_raffle(self, raffle_id: int, winner_id: Optional[int] = None) -> Raffle:
        """End raffle and optionally set winner."""
        pass
    
    # Raffle entry operations
    @abstractmethod
    async def enter_raffle(self, raffle_id: int, user_id: int) -> RaffleEntry:
        """Enter user into raffle."""
        pass
    
    @abstractmethod
    async def get_raffle_entries(self, raffle_id: int) -> List[RaffleEntry]:
        """Get all entries for a raffle."""
        pass
    
    @abstractmethod
    async def get_user_raffle_entries(self, user_id: int) -> List[RaffleEntry]:
        """Get all raffle entries by user."""
        pass
    
    @abstractmethod
    async def is_user_in_raffle(self, raffle_id: int, user_id: int) -> bool:
        """Check if user has entered specific raffle."""
        pass
    
    @abstractmethod
    async def get_random_raffle_winner(self, raffle_id: int) -> Optional[int]:
        """Get random winner from raffle entries."""
        pass
    
    # Statistics and analytics
    @abstractmethod
    async def get_trivia_statistics(self, trivia_id: int) -> Dict[str, Any]:
        """Get statistics for specific trivia."""
        pass
    
    @abstractmethod
    async def get_user_trivia_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's trivia statistics."""
        pass
    
    @abstractmethod
    async def get_minigame_statistics(self, game_type: str) -> Dict[str, Any]:
        """Get statistics for specific minigame type."""
        pass
    
    @abstractmethod
    async def get_user_minigame_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's minigame statistics."""
        pass
    
    @abstractmethod
    async def get_challenge_statistics(self, challenge_id: int) -> Dict[str, Any]:
        """Get statistics for specific challenge."""
        pass
    
    @abstractmethod
    async def get_global_game_statistics(self) -> Dict[str, Any]:
        """Get global game system statistics."""
        pass