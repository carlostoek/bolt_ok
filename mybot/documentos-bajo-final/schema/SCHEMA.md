# DianaBot - Database Schema Documentation

## Overview

The DianaBot database schema is designed to support all aspects of the bot's functionality, including user management, narrative progression, gamification, VIP features, auctions, and commerce. The schema is implemented using SQLAlchemy ORM with support for both SQLite (development) and PostgreSQL (production).

## Database Models

### Core User Model

#### `User` (database/models.py)
```sql
Table: users
- id: BigInteger (Primary Key, Unique) - Telegram user ID
- username: String (nullable)
- first_name: String (nullable)
- last_name: String (nullable)
- points: Float (default: 0) - Besitos currency
- level: Integer (default: 1)
- achievements: JSON (default: {}) - Unlocked achievements
- missions_completed: JSON (default: {}) - Completed missions
- last_daily_mission_reset: DateTime (default: now)
- last_weekly_mission_reset: DateTime (default: now)
- created_at: DateTime (default: now)
- updated_at: DateTime (default: now, onupdate: now)
- role: String (default: "free") - User role (free, vip, admin)
- vip_expires_at: DateTime (nullable) - VIP expiration date
- last_reminder_sent_at: DateTime (nullable)
- menu_state: String (default: "root") - Current menu state
- is_admin: Boolean (default: False) - Admin status
```

**Relationships:**
- One-to-one: `UserNarrativeState` (narrative state)
- One-to-many: `UserPurchase` (purchases)
- One-to-many: `UserAchievement` (unlocked achievements)
- One-to-many: `UserMissionEntry` (mission progress)

### Narrative System Models

#### `StoryFragment` (database/narrative_models.py)
```sql
Table: story_fragments
- id: Integer (Primary Key)
- key: String(50) (Unique, Not Null) - Fragment identifier
- text: Text (Not Null) - Fragment content
- image_url: String(500) (nullable) - Optional image URL
- character: String(50) (default: "Lucien") - Speaking character
- level: Integer (default: 1) - Narrative level
- min_besitos: Integer (default: 0) - Minimum besitos required
- required_role: String (nullable, indexed) - Required user role
- reward_besitos: Integer (default: 0) - Reward for viewing
- unlocks_achievement_id: String (Foreign Key to achievements.id, nullable, indexed)
- auto_next_fragment_key: String(50) (nullable) - Auto-advance target
- archetype_variant: String(20) (nullable, indexed) - Archetype-specific variant
- fragment_metadata: JSON (nullable) - Additional metadata
- created_at: DateTime (default: now)
- updated_at: DateTime (default: now, onupdate: now)
```

**Relationships:**
- One-to-many: `NarrativeChoice` (source fragment)
- Many-to-one: `Achievement` (unlocks achievement)
- One-to-many: `ShopItem` (unlocked by product purchase)

#### `NarrativeChoice` (database/narrative_models.py)
```sql
Table: narrative_choices
- id: Integer (Primary Key)
- source_fragment_id: Integer (Foreign Key to story_fragments.id, Not Null)
- destination_fragment_key: String(50) (Not Null) - Target fragment key
- text: String (Not Null) - Choice text
- required_besitos: Integer (default: 0) - Required besitos for choice
- required_role: String (nullable) - Required role for choice
- created_at: DateTime (default: now)
```

**Relationships:**
- Many-to-one: `StoryFragment` (source fragment)

#### `UserNarrativeState` (database/narrative_models.py)
```sql
Table: user_narrative_states
- user_id: BigInteger (Primary Key, Foreign Key to users.id)
- current_fragment_key: String(50) (nullable) - Current position in narrative
- choices_made: JSON (default: list) - History of choices
- fragments_visited: Integer (default: 0) - Count of visited fragments
- total_besitos_earned: Integer (default: 0) - Total besitos earned from narrative
- narrative_started_at: DateTime (default: now) - When narrative started
- last_activity_at: DateTime (default: now, onupdate: now) - Last interaction
- shop_redirect_fragment_key: String(50) (nullable) - Fragment before shop visit
- pending_decision_id: Integer (nullable) - Decision to process after purchase
- unlocked_fragments: JSON (default: list) - Unlocked fragment keys
```

**Relationships:**
- One-to-one: `User` (user)

### Gamification Models

#### `Mission` (database/models.py)
```sql
Table: missions
- id: String (Primary Key, Unique) - Mission identifier
- name: String (Not Null) - Mission name
- description: Text (nullable) - Mission description
- reward_points: Integer (default: 0) - Besitos reward
- type: String (default: "one_time") - Mission type
- target_value: Integer (default: 1) - Target to achieve
- duration_days: Integer (default: 0) - Duration in days
- is_active: Boolean (default: True) - Active status
- requires_action: Boolean (default: False) - Requires specific action
- action_data: JSON (nullable) - Additional action data
- unlocks_lore_piece_code: String (Foreign Key to lore_pieces.code_name, nullable, indexed)
- created_at: DateTime (default: now)
- mission_category: String (nullable) - Category (narrative, social, etc.)
- is_hidden: Boolean (default: False) - Hidden from users
- icon_emoji: String (nullable) - Visual icon
- difficulty_level: Integer (default: 1) - Difficulty (1-5)
- tags: JSON (default: []) - Tags array
- prerequisite_mission_id: String (Foreign Key to missions.id, nullable)
- unlocks_mission_id: String (Foreign Key to missions.id, nullable)
- time_limit_minutes: Integer (nullable) - Time limit
- bonus_points_if_fast: Integer (nullable) - Bonus for quick completion
- min_ranking_position: Integer (nullable) - Ranking requirement
- max_completions_global: Integer (nullable) - Global completion limit
- current_completions_global: Integer (default: 0) - Current global completions
- repeatable: Boolean (default: False) - Can be repeated
- reset_period: String (nullable) - Reset period (daily, weekly, monthly)
- xp_reward: Integer (default: 0) - Additional XP reward
```

#### `UserMissionEntry` (database/models.py)
```sql
Table: user_mission_entries
- id: Integer (Primary Key, Auto-increment)
- user_id: BigInteger (Foreign Key to users.id)
- mission_id: String (Foreign Key to missions.id)
- progress_value: Integer (default: 0) - Current progress
- completed: Boolean (default: False) - Completion status
- completed_at: DateTime (nullable) - Completion timestamp
```

**Constraints:**
- Unique: (user_id, mission_id)

#### `Achievement` (database/models.py)
```sql
Table: achievements
- id: String (Primary Key) - Achievement identifier
- name: String (Not Null) - Achievement name
- condition_type: String (Not Null) - Condition type
- condition_value: Integer (Not Null) - Condition value
- reward_text: String (Not Null) - Reward description
- created_at: DateTime (default: now)
```

**Relationships:**
- One-to-many: `StoryFragment` (unlocks achievement)

#### `UserAchievement` (database/models.py)
```sql
Table: user_achievements
- user_id: BigInteger (Primary Key, Foreign Key to users.id)
- achievement_id: String (Primary Key, Foreign Key to achievements.id)
- unlocked_at: DateTime (default: now)
```

**Constraints:**
- Unique: (user_id, achievement_id)

### VIP and Subscription Models

#### `VipSubscription` (database/models.py)
```sql
Table: vip_subscriptions
- user_id: BigInteger (Primary Key) - Telegram user ID
- expires_at: DateTime (nullable) - VIP expiration date
- created_at: DateTime (default: now)
```

#### `VipGrant` (database/models.py)
```sql
Table: vip_grants
- id: Integer (Primary Key, Auto-increment)
- user_id: BigInteger (Foreign Key to users.id, Not Null)
- days_granted: Integer (Not Null) - Days of VIP granted
- source: String(50) (Not Null) - Source (narrative, reward, achievement, admin)
- source_id: Integer (nullable) - Source identifier
- granted_at: DateTime (default: now)
- expires_at: DateTime (Not Null) - Expiration date
- invite_link: String(255) (nullable) - Invite link if applicable
```

### Shop and Commerce Models

#### `ShopItem` (database/models.py)
```sql
Table: shop_items
- id: Integer (Primary Key, Auto-increment)
- name: String(255) (Not Null) - Item name
- description: Text (nullable) - Item description
- price: Integer (Not Null) - Price in besitos
- is_vip_only: Boolean (default: False) - VIP-only item
- unlocks_lore_piece_id: Integer (Foreign Key to lore_pieces.id, nullable)
- unlocks_fragment_key: String(50) (nullable) - Fragment unlocked by purchase
- image_file_id: String(255) (nullable) - Telegram file ID
- stock_limit: Integer (nullable) - Stock limit (NULL = unlimited)
- max_purchases_per_user: Integer (default: 1) - Max purchases per user
- available_from: DateTime (nullable) - Availability start
- available_until: DateTime (nullable) - Availability end
- unlock_requirements: JSON (nullable) - Complex unlock requirements
- is_active: Boolean (default: True) - Active status
- created_at: DateTime (default: now)
```

**Relationships:**
- Many-to-one: `LorePiece` (unlocks lore piece)
- One-to-many: `ProductFile` (associated files)
- One-to-many: `UserPurchase` (purchases)

#### `UserPurchase` (database/models.py)
```sql
Table: user_purchases
- id: Integer (Primary Key, Auto-increment)
- user_id: BigInteger (Foreign Key to users.id, Not Null)
- shop_item_id: Integer (Foreign Key to shop_items.id, Not Null)
- purchased_at: DateTime (default: now)
- price_paid: Integer (Not Null) - Price paid at time of purchase
```

**Relationships:**
- Many-to-one: `User` (buyer)
- Many-to-one: `ShopItem` (purchased item)

#### `ProductFile` (database/models.py)
```sql
Table: product_files
- id: Integer (Primary Key, Auto-increment)
- shop_item_id: Integer (Foreign Key to shop_items.id, Not Null)
- file_type: String(20) (Not Null) - File type (photo, video, document)
- file_id: String(255) (Not Null) - Telegram file ID
- order_index: Integer (default: 0) - Display order
- created_at: DateTime (default: now)
```

**Relationships:**
- Many-to-one: `ShopItem` (parent item)

### Mi Diván (VIP Exclusive) Models

#### `CompatibilityQuiz` (database/midivan_models.py)
```sql
Table: compatibility_quizzes
- id: Integer (Primary Key, Auto-increment)
- title: String(200) (Not Null) - Quiz title
- description: Text (nullable) - Quiz description
- is_active: Boolean (default: True) - Active status
- created_at: DateTime (default: now)
- updated_at: DateTime (default: now, onupdate: now)
- besitos_reward: Integer (default: 50) - Reward for completion
- total_questions: Integer (default: 0) - Number of questions
- average_completion_time: Integer (nullable) - Average time in seconds
```

**Relationships:**
- One-to-many: `QuizQuestion` (questions)
- One-to-many: `QuizAttempt` (attempts)

#### `QuizQuestion` (database/midivan_models.py)
```sql
Table: quiz_questions
- id: Integer (Primary Key, Auto-increment)
- quiz_id: Integer (Foreign Key to compatibility_quizzes.id, Not Null)
- question_number: Integer (Not Null) - Order in quiz
- question_text: Text (Not Null) - Question content
- category: String(50) (nullable) - Category (personality, interests, etc.)
- created_at: DateTime (default: now)
```

**Relationships:**
- Many-to-one: `CompatibilityQuiz` (parent quiz)
- One-to-many: `QuizOption` (answer options)

#### `QuizOption` (database/midivan_models.py)
```sql
Table: quiz_options
- id: Integer (Primary Key, Auto-increment)
- question_id: Integer (Foreign Key to quiz_questions.id, Not Null)
- option_number: Integer (Not Null) - Order in question (A, B, C, D)
- option_text: Text (Not Null) - Answer option text
- compatibility_score: Integer (default: 50) - Compatibility score (0-100)
- diana_response: Text (nullable) - Diana's response to this choice
- created_at: DateTime (default: now)
```

**Relationships:**
- Many-to-one: `QuizQuestion` (parent question)

#### `QuizAttempt` (database/midivan_models.py)
```sql
Table: quiz_attempts
- id: Integer (Primary Key, Auto-increment)
- user_id: BigInteger (Foreign Key to users.id, Not Null)
- quiz_id: Integer (Foreign Key to compatibility_quizzes.id, Not Null)
- started_at: DateTime (default: now) - Attempt start time
- completed_at: DateTime (nullable) - Completion time
- is_completed: Boolean (default: False) - Completion status
- current_question_number: Integer (default: 1) - Current question
- total_score: Float (default: 0.0) - Total compatibility score (0-100)
- compatibility_level: String(50) (nullable) - Compatibility level text
- answers: JSON (default: dict) - {question_id: option_id}
- besitos_earned: Integer (default: 0) - Besitos earned
- reward_claimed: Boolean (default: False) - Reward claimed status
- completion_time_seconds: Integer (nullable) - Time to complete
```

**Relationships:**
- Many-to-one: `User` (test taker)
- Many-to-one: `CompatibilityQuiz` (quiz taken)

#### `AnonymousMessage` (database/midivan_models.py)
```sql
Table: anonymous_messages
- id: Integer (Primary Key, Auto-increment)
- user_id: BigInteger (Foreign Key to users.id, Not Null)
- message_text: Text (Not Null) - Message content
- sent_at: DateTime (default: now) - Send timestamp
- is_read: Boolean (default: False) - Read status
- read_at: DateTime (nullable) - Read timestamp
- is_responded: Boolean (default: False) - Response status
- responded_at: DateTime (nullable) - Response timestamp
- response_text: Text (nullable) - Diana's response
- response_sent_to_user: Boolean (default: False) - Sent to user status
- response_sent_at: DateTime (nullable) - Response sent timestamp
- message_length: Integer (Not Null) - Message character count
- sentiment: String(20) (nullable) - Sentiment (positive, neutral, etc.)
- admin_notes: Text (nullable) - Admin notes (admin-only)
- flagged_for_review: Boolean (default: False) - Review flag
```

**Relationships:**
- Many-to-one: `User` (sender)

### Auction System Models

#### `Auction` (database/models.py)
```sql
Table: auctions
- id: Integer (Primary Key, Auto-increment)
- name: String (Not Null) - Auction name
- description: Text (nullable) - Auction description
- prize_description: Text (Not Null) - Prize description
- initial_price: Integer (Not Null) - Starting bid amount
- current_highest_bid: Integer (default: 0) - Current highest bid
- highest_bidder_id: BigInteger (Foreign Key to users.id, nullable) - Current leader
- winner_id: BigInteger (Foreign Key to users.id, nullable) - Auction winner
- status: Enum (default: pending) - Auction status (pending, active, ended, cancelled)
- start_time: DateTime (Not Null) - Auction start time
- end_time: DateTime (Not Null) - Auction end time
- created_by: BigInteger (Foreign Key to users.id, Not Null) - Creator
- created_at: DateTime (default: now)
- ended_at: DateTime (nullable) - End timestamp
- min_bid_increment: Integer (default: 10) - Minimum bid increment
- max_participants: Integer (nullable) - Maximum participants limit
- auto_extend_minutes: Integer (default: 5) - Auto-extend if bid in last X minutes
```

#### `Bid` (database/models.py)
```sql
Table: bids
- id: Integer (Primary Key, Auto-increment)
- auction_id: Integer (Foreign Key to auctions.id, Not Null)
- user_id: BigInteger (Foreign Key to users.id, Not Null)
- amount: Integer (Not Null) - Bid amount
- timestamp: DateTime (default: now) - Bid time
- is_winning: Boolean (default: False) - Current winning bid status
```

**Constraints:**
- Unique: (auction_id, user_id, amount)

#### `AuctionParticipant` (database/models.py)
```sql
Table: auction_participants
- auction_id: Integer (Primary Key, Foreign Key to auctions.id)
- user_id: BigInteger (Primary Key, Foreign Key to users.id)
- joined_at: DateTime (default: now) - Join time
- notifications_enabled: Boolean (default: True) - Notification status
- last_notified_at: DateTime (nullable) - Last notification time
```

### Lore and Content Models

#### `LorePiece` (database/models.py)
```sql
Table: lore_pieces
- id: Integer (Primary Key, Auto-increment)
- code_name: String (Unique, Not Null) - Lore piece identifier
- title: String (Not Null) - Lore piece title
- description: Text (nullable) - Lore piece description
- content_type: String (Not Null) - Content type
- content: Text (Not Null) - Lore piece content
- category: String (nullable) - Content category
- is_main_story: Boolean (default: False) - Main story content
- unlock_condition_type: String (nullable) - Unlock condition type
- unlock_condition_value: String (nullable) - Unlock condition value
- created_at: DateTime (default: now)
- updated_at: DateTime (default: now, onupdate: now)
- is_active: Boolean (default: True) - Active status
```

#### `UserLorePiece` (database/models.py)
```sql
Table: user_lore_pieces
- user_id: BigInteger (Primary Key, Foreign Key to users.id)
- lore_piece_id: Integer (Primary Key, Foreign Key to lore_pieces.id)
- unlocked_at: DateTime (default: now) - Unlock time
- context: JSON (nullable) - Unlock context
```

**Constraints:**
- Unique: (user_id, lore_piece_id)

### Additional System Models

#### `UserStats` (database/models.py)
```sql
Table: user_stats
- user_id: BigInteger (Primary Key, Foreign Key to users.id)
- last_activity_at: DateTime (default: now) - Last activity
- last_checkin_at: DateTime (nullable) - Last check-in
- last_daily_gift_at: DateTime (nullable) - Last daily gift
- last_notified_points: Float (default: 0) - Last notified points
- messages_sent: Integer (default: 0) - Total messages sent
- checkin_streak: Integer (default: 0) - Check-in streak
- last_roulette_at: DateTime (nullable) - Last roulette spin
```

#### `Channel` (database/models.py)
```sql
Table: channels
- id: BigInteger (Primary Key) - Telegram channel ID
- title: String (nullable) - Channel title
- reactions: JSON (default: list) - List of allowed reactions (e.g., ["👍", "❤️", "😂"])
- reaction_points: JSON (default: dict) - Points per reaction (e.g., {"👍": 0.5, "❤️": 1.0})
```

#### `PendingChannelRequest` (database/models.py)
```sql
Table: pending_channel_requests
- id: Integer (Primary Key, Auto-increment)
- user_id: BigInteger (Not Null) - Requesting user
- chat_id: BigInteger (Not Null) - Channel ID
- request_timestamp: DateTime (default: now) - Request time
- approved: Boolean (default: False) - Approval status
```

## Database Relationships

### Narrative System Relationships
- `User` ↔ `UserNarrativeState` (one-to-one)
- `StoryFragment` → `NarrativeChoice` (one-to-many, source fragment)
- `NarrativeChoice` → `StoryFragment` (many-to-one, destination)
- `StoryFragment` → `Achievement` (many-to-one, unlocks achievement)

### Shop System Relationships
- `User` → `UserPurchase` (one-to-many)
- `ShopItem` → `UserPurchase` (one-to-many)
- `ShopItem` → `ProductFile` (one-to-many)
- `ShopItem` → `LorePiece` (many-to-one, unlocks lore)

### VIP System Relationships
- `User` → `VipSubscription` (one-to-one)
- `User` → `QuizAttempt` (one-to-many)
- `CompatibilityQuiz` → `QuizQuestion` (one-to-many)
- `QuizQuestion` → `QuizOption` (one-to-many)

### Auction System Relationships
- `User` → `Auction` (one-to-many, as creator)
- `User` → `Bid` (one-to-many)
- `Auction` → `Bid` (one-to-many)
- `Auction` → `AuctionParticipant` (one-to-many)

## Indexes and Performance

### Primary Indexes
- All primary keys are indexed by default
- Foreign key columns are indexed where frequently queried

### Special Indexes
- `users.role` - For role-based queries
- `story_fragments.required_role` - For access control
- `story_fragments.archetype_variant` - For variant selection
- `shop_items.is_vip_only` - For VIP filtering
- `auctions.status` - For status-based queries

### Unique Constraints
- `User.id` - Telegram user ID
- `StoryFragment.key` - Fragment identifier
- `Achievement.id` - Achievement identifier
- `LorePiece.code_name` - Lore piece identifier
- `Bid` (auction_id, user_id, amount) - Prevent duplicate bids
- `UserAchievement` (user_id, achievement_id) - Prevent duplicate achievements
- `UserLorePiece` (user_id, lore_piece_id) - Prevent duplicate lore unlocks

## Migration Strategy

The database uses Alembic for schema migrations, allowing for:
- Version-controlled schema changes
- Automatic migration generation
- Rollback capabilities
- Production-safe deployments

## Security Considerations

### Data Protection
- User personal information is stored with privacy in mind
- Anonymous messaging preserves user identity
- Sensitive data access is role-restricted
- Audit trails for VIP access grants

### Access Control
- Role-based access to different data types
- VIP-only features restricted by role checks
- Admin-only operations clearly marked
- Data isolation between user types

This comprehensive schema supports all functionality of the DianaBot while maintaining data integrity, performance, and security across all modules.