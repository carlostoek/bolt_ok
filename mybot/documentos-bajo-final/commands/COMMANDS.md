# DianaBot - API/Command Reference

## Public Commands

### Basic Commands
- **`/start`**: Initialize bot interaction
  - Creates user in database if new
  - Shows appropriate menu based on user role (admin/regular/vip)
  - Handles onboarding for new users

- **`/historia`**: Continue narrative from last point
  - Shows current story fragment
  - Allows user to continue from where they left off
  - Starts narrative from beginning for new users

- **`/mi_historia`**: View narrative statistics
  - Shows current fragment
  - Displays progress percentage
  - Shows fragments visited and total accessible
  - Lists recent choices made

- **`/run_schedulers`**: (Admin only) Manually execute schedulers
  - Processes channel requests
  - Updates VIP subscriptions
  - Requires admin privileges

## Callback Commands

### Main Menu Navigation
- **`menu:minigames`**: Open minigames menu
- **`narrative_main_menu`**: Return to main narrative menu
- **`menu_principal`**: Alternative main menu return
- **`shop_access`**: Access shop interface
- **`view_inventory`**: View purchased items
- **`continue_narrative`**: Continue story from current point

### Narrative System
- **`start_narrative`**: Start or continue narrative
- **`continue_narrative_after_purchase`**: Return to story after shop purchase
- **`return_from_shop`**: Return to story after shopping
- **`narrative_auto_continue`**: Auto-advance story fragments
- **`narrative_go_back`**: Return to previous fragment
- **`narrative_help`**: Show narrative help
- **`narrative_stats`**: Show narrative statistics
- **`narrative_choice:{index}`**: Make narrative decision (0-based index)
- **`enhanced_l1f1_choice:{index}`**: Make choice in enhanced L1F1 with archetype tracking

### VIP Exclusive (Mi Diván)
- **`midivan:main`**: Access Mi Diván main menu
- **`midivan:quiz`**: Start compatibility quiz with Diana
- **`midivan:message`**: Start anonymous messaging to Diana
- **`midivan:my_messages`**: View sent messages and responses
- **`midivan:stats`**: View Mi Diván statistics
- **`midivan:view_msg:{id}`**: View specific message details
- **`quiz:start:{id}`**: Start specific quiz
- **`quiz:continue:{id}`**: Continue specific quiz

### Auction System
- **`auction_main`**: Access auction main menu
- **`view_active_auctions`**: View currently active auctions
- **`view_auction_{id}`**: View specific auction details
- **`place_bid_{id}`**: Start bidding process on auction
- **`quick_bid_{amount}`**: Quick bid with preset amount
- **`custom_bid_amount`**: Enter custom bid amount
- **`confirm_bid_{auction_id}_{amount}`**: Confirm bid
- **`cancel_bid`**: Cancel bidding process
- **`view_my_auctions`**: View user's participating auctions
- **`view_auction_history`**: View auction history
- **`toggle_notifications_{id}`**: Toggle auction notifications

### VIP Menu
- **`vip_menu`**: Access VIP main menu
- **`vip_subscription`**: View subscription information
- **`vip_missions`**: View VIP missions
- **`vip_badges`**: View VIP badges
- **`vip_game`**: Access VIP game features
- **`game_profile`**: View game profile
- **`gain_points`**: View points earning instructions

### Shop System
- **`view_product:{id}`**: View product details
- **`confirm_purchase:{id}`**: Confirm purchase of item
- **`buy_item:{id}`**: Execute purchase
- **`besitos_insufficient:{item_id}:{missing}`**: Handle insufficient besitos
- **`besitos_packs_list`**: Show besitos packages
- **`besitos_pack_{id}`**: View specific besitos package
- **`besitos_interest_{id}`**: Express interest in besitos package
- **`besitos_packs_bonus`**: Show bonus besitos packages
- **`session_interest_{type}`**: Express interest in session
- **`vip_interest_special`**: Express VIP interest from upsell

## Admin Commands

### Admin Panel Access
- **`/admin_menu`**: Access admin panel menu
- **`admin_button`**: Admin placeholder handler

### Admin Callbacks
- **`admin_button`**: Generic admin action placeholder

## User Interface Buttons

### Main Menu Buttons
- **`🏠 Inicio`**: Return to main menu
- **`🎒 Mochila`**: Access inventory/backpack
- **`💰 Billetera`**: Access wallet (in development)
- **`🎯 Misiones`**: Access missions
- **`⚙️ Configuración`**: Access settings (in development)
- **`❓ Ayuda`**: Access help (in development)
- **`📖 Historia`**: Continue narrative
- **`🔓 Nivel de Muestra`**: Access sample level
- **`📓 Diario Íntimo`**: Access intimate diary level

## Narrative System API

### Decision Processing
- **`narrative_choice:{index}`**: Process narrative decision
  - Handles user choices in story fragments
  - Validates requirements (besitos, role)
  - Processes special actions (shop redirects, item verification)
  - Updates user state and progresses story

### Requirements System
The system handles various requirements for narrative access:
- **Besitos Requirements**: Minimum points needed
- **Role Requirements**: VIP/free user access levels
- **Item Requirements**: Specific purchases needed
- **Achievement Requirements**: Specific achievements needed

## Shop System API

### Purchase Flow
1. **`shop_access`**: Browse available products
2. **`view_product:{id}`**: View product details
3. **`confirm_purchase:{id}`**: Confirm purchase intent
4. **`buy_item:{id}`**: Execute purchase
5. **`return_from_shop`**: Return to narrative after purchase

### Inventory Management
- **`view_inventory`**: Shows purchased items
- Tracks item unlocks and lore pieces
- Shows purchase history

## Mi Diván (VIP Exclusive) API

### Compatibility Quiz System
- **`midivan:quiz`**: Start quiz flow
- Shows quiz introduction and details
- Handles quiz progression
- Displays results and compatibility level

### Anonymous Messaging
- **`midivan:message`**: Start messaging flow
- Handles message composition and sending
- Tracks message status (sent, read, responded)
- Provides privacy controls

### Activity Tracking
- **`midivan:stats`**: Shows user statistics
- Tracks quiz completions
- Tracks message activity
- Shows compatibility history

## Auction System API

### Bidding Process
1. **`view_auction_{id}`**: View auction details
2. **`place_bid_{id}`**: Start bidding process
3. **`quick_bid_{amount}`** or **`custom_bid_amount`**: Select bid amount
4. **`confirm_bid_{auction_id}_{amount}`**: Confirm bid
5. **`toggle_notifications_{id}`**: Manage notifications

### Auction Management
- **`view_my_auctions`**: Shows user's participating auctions
- **`view_auction_history`**: Shows past auction participation
- Handles winner determination and notifications

## Gamification System API

### Mission System
- **`misiones_disponibles`**: View available missions
- Tracks mission progress
- Awards points for completion
- Handles daily/weekly mission resets

### Achievement System
- Automatic achievement unlocking
- Badge collection
- Progress tracking

## User Management System API (Fase 4.5)

### User Management Endpoints
- **`GET /api/v1/users`**: List users with advanced filtering
  - Parameters: page, per_page, search, role, min_besitos, max_besitos, is_blocked, days_inactive, sort_by, sort_order
  - Features: Pagination, search, advanced filtering, sorting
  - Response: Complete user list with purchase statistics

- **`GET /api/v1/users/{id}`**: Get user details
  - Returns: Complete user information, purchase history, narrative progress, statistics
  - Includes: Purchases, narrative state, activity stats

- **`PUT /api/v1/users/{id}`**: Update user
  - Fields: besitos, role, is_blocked
  - Updates user information based on provided data

- **`POST /api/v1/users/{id}/add-besitos`**: Modify besitos
  - Parameter: amount (positive to add, negative to subtract)
  - Updates user's besitos balance with validation

- **`POST /api/v1/users/{id}/change-role`**: Change user role
  - Parameter: role (free or vip)
  - Updates user's role status

- **`POST /api/v1/users/{id}/toggle-block`**: Block/unblock user
  - Toggles user's blocked status
  - Prevents/allows user access to bot features

- **`DELETE /api/v1/users/{id}`**: Delete user
  - Removes user and all related data
  - Includes: purchases, narrative state, achievements

- **`GET /api/v1/users/stats`**: Get user statistics
  - Returns: Total users, VIP users, free users, blocked users, active users (7d), average besitos

- **`POST /api/v1/users/bulk-action`**: Perform bulk actions
  - Parameters: user_ids, action, value
  - Actions: add_besitos, change_role, block, unblock
  - Applies action to multiple users at once

### Admin Panel User Management
- **`/users`**: Advanced user listing with filters and bulk actions
- **`/users/{id}`**: Complete user details view with narrative progress
- **`/users/{id}/edit`**: User editing functionality with role and besitos management

## Channel Access System

### Request Processing
- **`channel_access`**: Handle channel access requests
- Verify subscription status
- Process VIP and free channel access
- Manage approval workflows

## Error Handling

### Common Error Responses
- **Insufficient Besitos**: Redirects to shop with upsell
- **Role Requirements**: Explains VIP requirements
- **Item Requirements**: Shows needed purchases
- **Invalid States**: Handles edge cases gracefully

## State Management

### FSM States
- **QuizStates.taking_quiz**: User taking compatibility quiz
- **MessageStates.writing_message**: User composing message
- **UserAuctionStates.placing_custom_bid**: User placing custom bid
- **UserAuctionStates.confirming_bid**: User confirming bid

The API provides a comprehensive interface for all bot functionality with proper error handling, user role management, and state tracking across different systems.