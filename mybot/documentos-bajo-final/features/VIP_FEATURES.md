# DianaBot - VIP Features Documentation (Mi Diván)

## Overview

The VIP features of DianaBot, collectively known as "Mi Diván", represent the premium experience offering exclusive content and interactions for VIP members. These features include compatibility testing with Diana, anonymous messaging, and special content access.

## VIP Access Requirements

### Subscription System
- Users must have active VIP subscription status
- Subscription can be obtained through:
  - Paid subscriptions
  - Free trial periods (admin-granted)
  - Achievement-based rewards
  - Special promotions

### Role Verification
- VIP status is verified through the `get_user_role()` function
- Access to VIP features is restricted to users with "vip" role
- Subscription expiration is checked in real-time

## Mi Diván (VIP Exclusive Hub)

### Main Menu Access
- **Command**: `midivan:main`
- **Access**: VIP users only
- **Features**:
  - Enhanced subscription information display
  - Compatibility quiz access
  - Anonymous messaging to Diana
  - Activity statistics
  - Quick access to VIP features

### Subscription Information Display
The main menu shows detailed subscription information including:
- Status (active, expiring soon, permanent, etc.)
- Days remaining until expiration
- Activity summary (quizzes completed, messages sent, etc.)
- Pending response notifications

## Compatibility Quiz System

### Quiz Structure
- **Quiz Model**: `CompatibilityQuiz` (database/midivan_models.py)
- **Questions**: `QuizQuestion` with multiple options
- **Options**: `QuizOption` with compatibility scores (0-100)
- **Attempts**: `QuizAttempt` tracks user progress and results

### Quiz Flow
1. **Quiz Introduction**: Shows quiz title, description, and details
2. **Question Display**: Presents questions with timed responses
3. **Answer Processing**: Calculates compatibility score
4. **Results Display**: Shows compatibility level and rewards
5. **Post-Quiz Actions**: Option to send message to Diana

### Compatibility Levels
- **90%+**: "Perfect Match" - Highest compatibility
- **80-89%**: "Great Match" - Very compatible
- **70-79%**: "Good Match" - Compatible
- **60-69%**: "Moderate Match" - Somewhat compatible
- **50-59%**: "Low Match" - Less compatible
- **Below 50%**: "Not Compatible" - Low compatibility

### Quiz Rewards
- Besitos reward for completing quizzes
- Compatibility level affects user classification
- Special recognition for high scores

## Anonymous Messaging System

### Message Flow
1. **Message Composition**: Users write anonymous messages to Diana
2. **Privacy Assurance**: System guarantees anonymity
3. **Message Storage**: Messages stored with privacy controls
4. **Diana's Response**: Diana responds through the bot interface
5. **Notification**: User receives response notification

### Privacy Features
- **Anonymity**: User identity is never revealed to Diana
- **Secure Storage**: Messages stored with privacy controls
- **Status Tracking**: Message status (sent, read, responded)
- **Admin Review**: Optional admin review process

### Message Management
- **Message History**: Users can view their sent messages
- **Response Tracking**: Track which messages received responses
- **Pending Notifications**: Alert users to pending responses
- **Status Updates**: Real-time status updates

### Message Features
- **Length Validation**: Minimum 10 characters, maximum 1000 characters
- **Content Guidelines**: Clear guidelines on appropriate content
- **Important Notes**: Specific instructions for meaningful messages
- **Privacy Statement**: Clear privacy policy

## Activity Tracking and Statistics

### User Activity Summary
The system tracks various Mi Diván activities:
- **Quizzes Completed**: Total number of quizzes taken
- **Compatibility Level**: Best compatibility achieved
- **Messages Sent**: Total anonymous messages sent
- **Responses Received**: Messages that received responses
- **Pending Responses**: Number of messages awaiting response

### Statistics Display
- **Quiz Statistics**: Completion count, average score, best score, compatibility level
- **Message Statistics**: Sent count, responded count, pending count
- **Progress Tracking**: Long-term engagement metrics

## Auction System (VIP Exclusive)

### VIP-Only Auctions
- **Access Control**: Only VIP users can participate in bidding
- **Free users**: Can view auctions but cannot bid
- **Admin-created**: Auctions created by administrators
- **Real-time Bidding**: Live bidding experience

### Auction Features
- **Bid Management**: Place bids, view current highest bid
- **Notification System**: Alerts for outbid situations
- **History Tracking**: View participation history
- **Results Display**: Clear indication of wins/losses

### Auction Process
1. **Auction Discovery**: Browse active auctions
2. **Bid Placement**: Place bids with minimum increment
3. **Status Monitoring**: Track auction progress
4. **Result Notification**: Receive win/loss notifications

## VIP Gamification System

### VIP Missions
- **Exclusive Missions**: Available only to VIP users
- **Higher Rewards**: Better point rewards than free missions
- **Special Challenges**: Unique VIP-only challenges
- **Progress Tracking**: Separate VIP mission progress

### VIP Badges and Achievements
- **Exclusive Badges**: Special badges only for VIP users
- **Achievement Tracking**: VIP-specific achievements
- **Recognition**: Special recognition for VIP accomplishments

## User Experience Enhancements

### Emotional Feedback
- **Diana's Voice**: Personalized responses from Diana
- **Emotional Responses**: Emotionally engaging interactions
- **Immediate Feedback**: Quick responses to user actions
- **Personalization**: Tailored experience based on user data

### Conversion Optimization
- **Upselling**: Strategic upselling at key moments
- **Session Interest**: Prompts for individual sessions
- **VIP Promotions**: Special offers for VIP upgrades
- **Monetization**: Strategic monetization points

## Technical Implementation

### FSM States
- **QuizStates.taking_quiz**: User is in quiz flow
- **MessageStates.writing_message**: User is composing message
- **UserAuctionStates**: Various auction-related states

### Database Models
- **CompatibilityQuiz**: Main quiz model
- **QuizQuestion**: Individual quiz questions
- **QuizOption**: Answer options with scores
- **QuizAttempt**: User's quiz attempts
- **AnonymousMessage**: Anonymous messages to Diana
- **DivanActivity**: Activity tracking

### Service Integration
- **MiDivanService**: Main service for Mi Diván features
- **SubscriptionService**: VIP status verification
- **NarrativeService**: Integration with narrative system
- **NotificationService**: Message and auction notifications

## Security and Privacy

### Data Protection
- **Anonymity**: Guaranteed anonymity for messaging
- **Secure Storage**: Encrypted storage of sensitive data
- **Access Controls**: Strict access controls for admin features
- **Audit Logging**: Comprehensive audit trails

### Privacy Controls
- **Message Privacy**: No identity linkage in messages
- **Data Isolation**: VIP data separated from free user data
- **Admin Access**: Limited admin access to sensitive data
- **Compliance**: GDPR and privacy regulation compliance

## User Journey Integration

### Narrative Connection
- **Story Integration**: Mi Diván features connected to main narrative
- **Progression**: VIP features enhance overall story experience
- **Rewards**: VIP actions unlock narrative content
- **Engagement**: Higher engagement through exclusive features

### Conversion Path
- **Free to VIP**: Clear path from free to VIP features
- **Engagement Loop**: Features designed to increase engagement
- **Value Proposition**: Clear value in VIP features
- **Retention**: Features designed for long-term retention

## Admin Management

### VIP Feature Administration
- **Quiz Management**: Create and manage compatibility quizzes
- **Message Monitoring**: Monitor anonymous messages (with privacy controls)
- **Activity Analytics**: Track VIP user engagement
- **Content Management**: Manage VIP-only content

### VIP User Management
- **Subscription Management**: Manage VIP subscriptions
- **Access Control**: Grant/revoke VIP access
- **Audit Trail**: Track VIP access changes
- **Reporting**: VIP user analytics and reports

The Mi Diván system represents the premium experience of DianaBot, offering VIP users exclusive access to Diana through compatibility quizzes and anonymous messaging, while maintaining strict privacy controls and providing engaging, personalized experiences.