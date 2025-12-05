# DianaBot - Module-by-Module Breakdown

## Core Application Structure

### Main Entry Point (`bot.py`)
- **Purpose**: Main application initialization and dispatcher setup
- **Key Features**:
  - Database middleware injection
  - Global error handling
  - Background task management
  - Handler registration
  - Middleware pipeline configuration
- **Dependencies**: Aiogram 3, SQLAlchemy, custom handlers and services

## Handler Modules

### 1. Basic Handlers
- **`handlers/start.py`**: Initial bot interaction and user registration
  - Creates new users in database
  - Handles admin vs regular user routing
  - Onboarding integration

- **`handlers/main_menu.py`**: Main navigation interface
  - Home, Backpack, Wallet, Missions, Settings, Help
  - Narrative continuation
  - Role-based menu presentation

- **`handlers/free_user.py`**: Free user specific functionality
  - Channel access requests
  - Free content access
  - Conversion triggers

### 2. Narrative System Handlers
- **`handlers/narrative_handler.py`**: Core story progression
  - Fragment display and navigation
  - Decision processing
  - Auto-continuation
  - Enhanced L1F1 with archetype detection
  - Requirements checking and blocking

- **`handlers/admin_narrative_handlers.py`**: Admin narrative tools
  - Narrative management interface
  - Fragment creation/modification

### 3. Gamification Handlers
- **`handlers/vip/gamification.py`**: VIP gamification features
  - Mission management
  - Achievement tracking
  - Point systems

- **`handlers/missions_handler.py`**: Mission system
  - Available missions display
  - Mission progress tracking
  - Reward distribution

- **`handlers/daily_gift.py`**: Daily reward system
  - Daily gift collection
  - Streak tracking

### 4. VIP Exclusive Features (Mi Diván)
- **`handlers/midivan_handler.py`**: VIP exclusive hub
  - Compatibility quizzes with Diana
  - Anonymous messaging system
  - Activity tracking and statistics
  - FSM for quiz flow management

- **`handlers/vip/menu.py`**: VIP main menu
  - Subscription information
  - Mission access
  - Badge viewing
  - Game profile display

- **`handlers/vip/auction_user.py`**: VIP auction participation
  - Auction browsing
  - Bidding system
  - Bid history
  - Notification management

### 5. Shop System
- **`handlers/shop_handlers.py`**: Product purchasing system
  - Product browsing and details
  - Purchase flow with confirmation
  - Inventory management
  - Besitos pack upselling
  - Post-purchase upselling

### 6. Channel Administration
- **`handlers/channel_access.py`**: Channel access management
  - Request processing
  - Subscription verification
  - VIP channel access
  - Free channel management

- **`handlers/admin.py`**: Admin panel access
  - Admin menu
  - Manual scheduler execution
  - Admin-only functions

### 7. Minigames and Interactive Features
- **`handlers/minigames.py`**: Game functionality
  - Roulette and other mini-games
  - Free spins and paid games

- **`handlers/lore_handlers.py`**: Lore piece management
  - Unlocked content display
  - Backpack functionality

### 8. Testing and Evaluation
- **`handlers/test_evaluation_handler.py`**: Evaluation system
  - Quiz taking
  - Result processing
  - Emotional analysis

- **`handlers/quiz_handler.py`**: Quiz functionality
  - Quiz management
  - Question handling
  - Answer processing

## Service Modules

### 1. Core Services
- **`services/narrative_service.py`**: Story management
  - Fragment retrieval and display
  - User progress tracking
  - Decision processing
  - Requirements checking

- **`services/point_service.py`**: Points management
  - Awarding points for actions
  - Reaction handling
  - Poll answer processing

- **`services/user_service.py`**: User management
  - User creation and updates
  - Role management
  - Profile handling

### 2. Gamification Services
- **`services/mission_service.py`**: Mission system
  - Mission creation and management
  - Progress tracking
  - Reward distribution
  - Challenge processing

- **`services/achievement_service.py`**: Achievement system
  - Achievement tracking
  - Badge management
  - Unlock conditions

- **`services/level_service.py`**: Level progression
  - Level calculation
  - XP management
  - Reward distribution

### 3. VIP Services
- **`services/subscription_service.py`**: VIP subscriptions
  - Subscription management
  - Expiration tracking
  - VIP status validation

- **`services/vip_grant_service.py`**: VIP access grants
  - Free VIP distribution
  - Grant tracking
  - Audit logging

- **`services/midivan_service.py`**: Mi Diván functionality
  - Quiz management
  - Anonymous messaging
  - Activity tracking
  - Compatibility analysis

### 4. Commerce Services
- **`services/shop_service.py`**: Shop operations
  - Product management
  - Purchase processing
  - Inventory tracking
  - Unlock validation

- **`services/auction_service.py`**: Auction system
  - Real-time bidding
  - Participant management
  - Winner determination
  - Notification system

### 5. Specialized Services
- **`services/coordinador_central.py`**: Central business logic
  - Unified action execution
  - Complex workflow management
  - Cross-service coordination

- **`services/narrative_state_machine.py`**: Narrative flow control
  - State management for story progression
  - Shop return handling
  - Decision processing

- **`services/user_service.py`**: User management (Fase 4.5)
  - Complete user management functionality
  - User data retrieval and updates
  - User role management (free/VIP)
  - Besitos adjustment tools
  - User blocking and status management

- **`services/archetype_analyzer.py`**: Personality analysis
  - User archetype detection
  - Response pattern analysis
  - Behavioral classification

- **`services/scheduler.py`**: Background task management
  - Channel request processing
  - VIP subscription updates
  - Auction monitoring
  - Cleanup operations

## Database Modules

### 1. Core Models
- **`database/models.py`**: Main data models
  - User, Mission, Achievement, ShopItem, Auction, Bid
  - Subscription and VIP management
  - Challenge and minigame tracking

- **`database/narrative_models.py`**: Narrative-specific models
  - StoryFragment, NarrativeChoice, UserNarrativeState
  - Fragment relationships and progression

- **`database/midivan_models.py`**: VIP exclusive models
  - CompatibilityQuiz, QuizQuestion, QuizOption
  - QuizAttempt, AnonymousMessage, DivanActivity

### 2. Database Setup
- **`database/setup.py`**: Database initialization
  - Connection pool setup
  - Session management
  - Migration handling

## Middleware Modules

### 1. Core Middlewares
- **`middlewares/points_middleware.py`**: Points awarding
  - Message, reaction, poll processing
  - Admin bypass logic
  - Mission progress tracking

- **`middlewares/gamification_middleware.py`**: Gamification integration
  - Enhanced user engagement
  - Progress tracking

- **`middlewares/visual_feedback_middleware.py`**: User experience enhancement
  - Immediate response feedback
  - Emotional interaction patterns

## Keyboard Modules

### 1. UI Components
- **`keyboards/`**: All interface keyboards
  - Main menu keyboards
  - Narrative navigation
  - Shop browsing
  - Auction bidding
  - Admin panel interfaces

## Utility Modules

### 1. Core Utilities
- **`utils/`**: Helper functions and utilities
  - Message safety patches
  - Menu management
  - Localization
  - Text processing
  - User role management

### 2. Configuration
- **`config/`**: Configuration management
  - Environment variables
  - Bot settings
  - Feature flags

## Admin Panel

### 1. Web Interface
- **`admin_panel/`**: Flask-based admin panel
  - Narrative management
  - Shop item management
  - Automation triggers
  - User management (Fase 4.5)
    - Advanced user listing with filtering and bulk operations
    - User detail views with purchase history and narrative progress
    - User editing functionality with role and besitos management
    - User blocking/deletion with confirmations
    - Purchase history tracking
    - Statistics and analytics
  - API endpoints for admin functions

Each module is designed to be cohesive and focused on specific functionality while maintaining clear interfaces with other modules. This modular design allows for independent development, testing, and maintenance of different features.