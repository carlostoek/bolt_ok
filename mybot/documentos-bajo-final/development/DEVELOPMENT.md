# DianaBot - Development Workflow

## Project Structure Overview

```
mybot/
├── admin_panel/          # Flask admin panel
├── alembic/             # Database migrations
├── app/                 # Application modules
├── config/              # Configuration files
├── constants/           # Constant definitions
├── core/                # Core functionality
├── data/                # Data files
├── database/            # Database models and setup
├── docs/                # Documentation
├── handlers/            # Telegram bot handlers
├── infrastructure/      # Infrastructure components
├── keyboards/           # Keyboard interfaces
├── locales/             # Localization files
├── middlewares/         # Middleware components
├── narrative_fragments/ # Narrative content
├── services/            # Business logic services
├── states/              # State management
├── utils/               # Utility functions
├── venv/                # Virtual environment (if exists)
├── bot.py              # Main application entry point
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── ...
```

## Development Environment Setup

### 1. Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd mybot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

### 3. Database Initialization
```bash
# Run the bot to initialize database
python bot.py
```

## Development Workflow

### 1. Feature Development Process

#### A. Planning Phase
1. Identify the feature/module to implement
2. Check existing architecture to understand integration points
3. Plan database changes (if any)
4. Consider impact on other modules
5. Document the feature requirements

#### B. Implementation Phase
1. Create a new branch for the feature:
   ```bash
   git checkout -b feature/feature-name
   ```

2. Implement the feature following the existing patterns:
   - Create handlers in appropriate subdirectories
   - Add services if new business logic is needed
   - Update models if new data structures are required
   - Add keyboard interfaces if UI changes are needed

3. Follow coding standards:
   - Use descriptive function and variable names
   - Add docstrings to functions and classes
   - Follow existing code style and formatting
   - Handle errors gracefully

4. Test the feature:
   - Test in development environment
   - Verify integration with other modules
   - Check error handling
   - Test edge cases

#### C. Testing Phase
1. Unit tests (if applicable):
   ```bash
   python -m pytest tests/
   ```

2. Integration testing with the bot
3. Verify database operations work correctly
4. Test with different user roles and permissions

#### D. Documentation Phase
1. Update documentation if needed
2. Add comments to complex code
3. Update API/command references if new functionality added

#### E. Merge Process
1. Push the feature branch:
   ```bash
   git add .
   git commit -m "Add feature: description of feature"
   git push origin feature/feature-name
   ```

2. Create a pull request
3. Request code review
4. Address review comments
5. Merge to main branch

### 2. Adding New Handlers

#### Handler Structure
```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import get_user_role
from utils.localization import get_text

router = Router()

@router.message(F.text == "Command Text")
async def handler_function(message: Message, session: AsyncSession):
    """Handler description"""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    # Handler logic here
    await message.answer("Response text")

# Register router in bot.py
```

### 3. Adding New Services

#### Service Structure
```python
class ServiceName:
    def __init__(self, session):
        self.session = session
    
    async def service_method(self, parameters):
        """Service method description"""
        # Business logic here
        return result
```

### 4. Database Changes

#### Adding New Models
1. Create model in `database/models.py` or appropriate module
2. Follow existing model patterns
3. Add proper relationships and constraints
4. Test with database operations

#### Migrations
```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

## Code Standards

### 1. Python Standards
- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Write clear, descriptive docstrings
- Keep functions focused and single-purpose
- Use async/await for asynchronous operations

### 2. Naming Conventions
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Use descriptive names that explain purpose

### 3. Error Handling
- Use try/catch blocks for database operations
- Log errors with appropriate context
- Provide user-friendly error messages
- Handle edge cases gracefully

### 4. Database Operations
- Always use sessions properly with async context
- Follow async/await patterns
- Handle database transactions appropriately
- Use eager loading when needed for performance

## Testing Strategy

### 1. Unit Testing
- Test individual functions and methods
- Mock external dependencies
- Test error conditions
- Verify business logic correctness

### 2. Integration Testing
- Test handler integration
- Verify database operations
- Test service interactions
- Validate user flows

### 3. End-to-End Testing
- Test complete user workflows
- Verify role-based access
- Test error recovery
- Validate data consistency

## Debugging

### 1. Logging
- Use structured logging with appropriate levels
- Include context in log messages
- Avoid logging sensitive information
- Use different log levels appropriately

### 2. Debugging Tools
- Use Python debugger (pdb) for complex issues
- Check database state directly when needed
- Monitor bot logs for issues
- Use development environment for testing

### 3. Common Debugging Scenarios
- User state issues: Check `UserNarrativeState` table
- Permission problems: Verify role assignment
- Database issues: Check connection and transactions
- Handler problems: Verify callback data and routing

## Version Control

### 1. Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/xxx`: Individual features
- `hotfix/xxx`: Urgent fixes
- `release/xxx`: Release preparation

### 2. Commit Messages
- Use clear, descriptive commit messages
- Follow conventional commits format when possible
- Reference issue numbers when applicable
- Keep commits focused and atomic

### 3. Pull Request Process
- Create PR from feature branch to develop/main
- Include description of changes
- Reference related issues
- Request reviews from team members
- Address feedback before merging

## Performance Considerations

### 1. Database Optimization
- Use eager loading to avoid N+1 queries
- Index frequently queried columns
- Optimize complex queries
- Use connection pooling

### 2. Memory Management
- Avoid storing large objects in memory unnecessarily
- Use generators for large datasets
- Close database sessions properly
- Monitor memory usage

### 3. Asynchronous Operations
- Use async/await consistently
- Avoid blocking operations
- Implement proper error handling
- Consider rate limiting

## Security Considerations

### 1. Input Validation
- Validate all user inputs
- Sanitize text inputs
- Validate callback data
- Check user permissions

### 2. Data Protection
- Protect sensitive user data
- Use secure session management
- Implement proper authentication
- Secure API endpoints

### 3. Bot Security
- Verify Telegram webhook signatures
- Implement rate limiting
- Protect against abuse
- Secure admin interfaces

## Deployment Workflow

### 1. Pre-deployment Checklist
- Run all tests successfully
- Verify database migrations
- Check configuration settings
- Review security settings
- Test in staging environment

### 2. Deployment Process
1. Update configuration for target environment
2. Apply database migrations if needed
3. Deploy code to production server
4. Restart bot application
5. Monitor logs for issues
6. Verify functionality

### 3. Post-deployment Verification
- Check bot is responding
- Verify all features work
- Monitor error logs
- Validate user access

This development workflow ensures consistent, maintainable code while supporting the complex multi-module architecture of the DianaBot system.