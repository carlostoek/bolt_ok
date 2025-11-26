# This file serves as a central point for Alembic to discover all database models.
# It imports the Base from base.py and then imports all models.
from .base import Base
from database.models import (
    User,
    AuctionStatus,
    Reward,
    UserReward,
    Achievement,
    UserAchievement,
    Mission,
    UserMissionEntry,
    ContentSet,
    GiftRecord,
    UserMilestone,
    Event,
    Raffle,
    RaffleEntry,
    Badge,
    UserBadge,
    Level,
    VipSubscription,
    VipGrant,
    UserStats,
    InviteToken,
    SubscriptionPlan,
    SubscriptionToken,
    Token,
    Tariff,
    ConfigEntry,
    BotConfig,
    Channel,
    PendingChannelRequest,
    Challenge,
    UserChallengeProgress,
    ButtonReaction,
    Auction,
    Bid,
    AuctionParticipant,
    MiniGamePlay,
    LorePiece,
    ShopItem,
    UserPurchase,
    ProductFile,
    UserLorePiece,
    Trivia,
    TriviaQuestion,
    TriviaAttempt,
    TriviaUserAnswer
)
from database.narrative_models import (
    StoryFragment,
    NarrativeChoice,
    UserNarrativeState
)
from database.midivan_models import (
    CompatibilityQuiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    AnonymousMessage,
    DivanActivity
)
from database.emotional_models import (
    ResponseType,
    VulnerabilityLevel,
    EmotionalIntensity,
    UserEmotionalProfile,
    EmotionalInteraction,
    InteractionType,
    ConversationMemory,
    EmotionalTrigger,
    EmotionalAnalysisSession,
    ArchetypeClassification,
    EmotionalState,
)

# You can add any other models here
