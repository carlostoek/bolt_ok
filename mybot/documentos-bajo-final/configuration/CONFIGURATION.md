# DianaBot - Configuration and Setup Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Git
- PostgreSQL (recommended) or SQLite (for development)
- Telegram Bot Token from @BotFather

### Python Dependencies
```bash
pip install aiogram SQLAlchemy python-dotenv alembic asyncpg aiosqlite
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
VIP_CHANNEL_ID=your_vip_channel_id_here

# Database Configuration
DATABASE_URL=sqlite:///bot.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# Admin Configuration
ADMIN_IDS=123456789,987654321
```

### Optional Environment Variables

```env
# Flask Admin Panel (if using)
SECRET_KEY=change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=True
ADMIN_IPS=127.0.0.1,::1

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5000

# Pagination
ITEMS_PER_PAGE=20
```

## Database Setup

### Initial Database Creation

1. **Using SQLite (Development)**:
   ```bash
   # Database file will be created automatically as bot.db
   # No additional setup required
   ```

2. **Using PostgreSQL (Production)**:
   ```sql
   CREATE DATABASE telegram_bot;
   CREATE USER bot_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE telegram_bot TO bot_user;
   ```

### Database Initialization

The bot automatically initializes the database on first run:
- Creates all necessary tables
- Sets up initial schema
- Applies any pending migrations

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd mybot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual values
```

### 5. Initialize Database
```bash
# The bot will initialize the database on first run
python bot.py
```

## Bot Token Setup

### 1. Get Bot Token
- Contact @BotFather on Telegram
- Use `/newbot` command
- Follow instructions to create your bot
- Copy the provided token

### 2. Configure Bot Token
- Add the token to your `.env` file as `BOT_TOKEN`
- Make sure to set privacy mode to disabled if needed for channel access

### 3. Channel Setup
- Create your VIP channel
- Add your bot as administrator with necessary permissions
- Get the channel ID (use @userinfobot to find it)
- Add channel ID to `VIP_CHANNEL_ID` in your `.env`

## Admin User Setup

### Setting Admin Privileges

Admin users are defined in the `ADMIN_IDS` environment variable:
- Comma-separated list of Telegram user IDs
- Users with these IDs will have access to admin features
- Use @userinfobot to get user IDs

Example:
```
ADMIN_IDS=123456789,987654321,111222333
```

## Database Migration

### Using Alembic (if configured)

The bot includes Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Check current revision
alembic current
```

## Running the Bot

### Development Mode
```bash
python bot.py
```

### Production Mode
```bash
# With gunicorn (if needed for production)
gunicorn -w 1 -k uvicorn.workers.UvicornWorker bot:app
```

## Admin Panel Setup (Optional)

### Flask Admin Panel

If using the Flask admin panel:

1. **Install Flask dependencies**:
   ```bash
   pip install -r requirements_panel.txt
   ```

2. **Configure admin panel** in `.env`:
   ```env
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=production  # or development
   FLASK_DEBUG=False
   ADMIN_IPS=your_ip_address,127.0.0.1
   DATABASE_URL=sqlite:///../bot.db  # Point to main bot database
   ```

3. **Run admin panel**:
   ```bash
   cd admin_panel
   python app.py
   ```

## Configuration Files

### Main Configuration (`bot.py`)
- Handles bot initialization
- Sets up middleware
- Registers handlers
- Configures background tasks

### Database Configuration (`database/setup.py`)
- Database connection setup
- Session management
- Connection pooling

### Localization Configuration
- Text localization in `utils/localization.py`
- Message templates in `utils/messages.py`

## Service Configuration

### Background Services
The bot runs several background services:
- Channel request processing
- VIP subscription management
- Auction monitoring
- User journey scheduling
- Free channel cleanup

These are configured in `services/scheduler.py`

### Middleware Configuration
- DB Session Middleware: Injects database sessions
- Points Middleware: Handles point awarding
- User Registration Middleware: Manages user registration
- Visual Feedback Middleware: Provides immediate responses
- Gamification Middleware: Enhances user engagement

## Customization Options

### Narrative Customization
- Add new story fragments in `narrative_fragments/`
- Modify narrative flow in `handlers/narrative_handler.py`
- Update character dialogues in database

### Shop Customization
- Add products via admin panel or directly in database
- Configure pricing and availability
- Set up product unlocks and requirements

### Gamification Customization
- Add new missions in `services/mission_service.py`
- Configure achievement criteria
- Adjust point rewards and penalties

## Security Configuration

### IP Whitelist (Admin Panel)
- Configure `ADMIN_IPS` in environment
- Restricts admin panel access to specified IPs
- Recommended for production environments

### Rate Limiting
- Built-in Telegram API rate limiting
- Custom rate limiting can be added in middlewares

### Data Protection
- User data is stored with privacy considerations
- Anonymous messaging preserves user identity
- VIP feature access is role-based

## Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check if bot token is correct
   - Verify internet connection
   - Check if bot is not in privacy mode (for group/channel access)

2. **Database connection errors**:
   - Verify DATABASE_URL in environment
   - Check database server is running
   - Ensure proper permissions

3. **Admin features not working**:
   - Verify ADMIN_IDS in environment
   - Check if user ID matches exactly
   - Ensure admin commands are properly configured

4. **Channel access not working**:
   - Verify VIP_CHANNEL_ID is correct
   - Check bot has admin privileges in channel
   - Ensure channel ID format is correct

### Logging Configuration
- Logs are written to `bot.log` file
- Console output for development
- Configure log levels in `bot.py`

## Production Deployment

### Environment Variables for Production
```env
BOT_TOKEN=your_production_bot_token
VIP_CHANNEL_ID=your_production_channel_id
ADMIN_IDS=production_admin_ids
DATABASE_URL=postgresql://user:password@prod-server/dbname
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=production_secret_key
ADMIN_IPS=production_admin_ips
```

### Performance Considerations
- Use PostgreSQL for production
- Configure proper connection pooling
- Set up monitoring and alerting
- Implement proper backup strategies

This setup guide provides all necessary information to configure and run the DianaBot in both development and production environments.