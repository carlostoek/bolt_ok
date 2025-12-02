# DianaBot - Admin Panel Guide

## Overview

The DianaBot Admin Panel is a Flask-based web interface that provides administrators with comprehensive tools to manage all aspects of the bot, including narrative content, shop items, automation triggers, and user management.

## Architecture

### Tech Stack
- **Backend**: Flask 2.x
- **Database**: SQLAlchemy (shared with main bot)
- **Frontend**: HTML templates with JavaScript
- **API**: RESTful API endpoints
- **Security**: IP-based whitelisting

### Project Structure
```
admin_panel/
├── api/                # API endpoints
│   ├── narrative.py    # Narrative management
│   ├── shop.py         # Shop management
│   ├── automation.py   # Automation triggers
│   └── references.py   # Reference data
├── services/           # Backend services
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── app.py             # Main Flask application
├── config.py          # Configuration
└── extensions.py      # Flask extensions
```

## Setup and Configuration

### Environment Variables
The admin panel shares configuration with the main bot:
```env
# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development     # or production
FLASK_DEBUG=True         # False in production

# Database Configuration
DATABASE_URL=sqlite:///../bot.db  # Point to main bot database

# Security Configuration
ADMIN_IPS=127.0.0.1,::1          # IP whitelist
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5000
```

### IP Whitelisting
The admin panel implements IP-based security:
- Only IPs listed in `ADMIN_IPS` can access the panel
- Access is restricted by default in production
- Development mode allows all IPs

## API Endpoints

### Narrative Management API (`/api/v1/narrative`)

#### Create Fragment with Nested Data
- **Endpoint**: `POST /api/v1/narrative/fragments`
- **Purpose**: Create story fragments with optional nested product and choices
- **Request Body**:
```json
{
  "key": "CAP10_INTRO",
  "text": "Entraste a la habitación oscura...",
  "image_url": "https://...",
  "min_besitos": 0,
  "required_role": null,
  "reward_besitos": 10,
  "unlock_product": {
    "name": "Acceso Capítulo 10",
    "description": "Desbloquea el capítulo completo",
    "price": 50,
    "is_vip_only": false
  },
  "choices": [
    {
      "text": "Entrar sigilosamente",
      "destination_fragment_key": "CAP10_SIGILO",
      "required_besitos": 0
    }
  ]
}
```
- **Response**: Complete creation with nested objects and validation

#### List Fragments with Advanced Filtering
- **Endpoint**: `GET /api/v1/narrative/fragments`
- **Query Parameters**:
  - `page`, `per_page`: Pagination
  - `search`: Text search in key and content
  - `is_locked`: Filter by access requirements
  - `required_role`: Role-based filtering
  - `has_choices`: Presence of choices
  - `min_besitos_min/max`: Besitos range
  - `sort_by`, `sort_order`: Sorting
  - `include`: Eager loading (choices, unlock_product)

#### Get Single Fragment
- **Endpoint**: `GET /api/v1/narrative/fragments/<fragment_key>`
- **Features**: Complete fragment with all relations

### Shop Management API (`/api/v1/shop`)
- **Current Status**: API blueprint exists but implementation is pending
- **Planned Features**: Product management, inventory, pricing, availability

### Automation Management API (`/api/v1/automation`)
- **Current Status**: API blueprint exists but implementation is pending
- **Planned Features**: Trigger management, automation rules, scheduling

### Validation Service
- **Purpose**: Comprehensive data validation for nested creation
- **Features**: 
  - Cross-reference validation
  - Business rule validation
  - Data integrity checks
  - Warning generation

## Web Interface

### Dashboard (`/`)
- **Purpose**: Main admin overview
- **Features**: Quick stats, recent activity, navigation shortcuts

### Narrative Management
- **List View** (`/narrative/fragments`): Browse all story fragments
- **Create View** (`/narrative/fragments/new`): Create new fragments
- **Edit View** (`/narrative/fragments/{key}/edit`): Edit existing fragments

### Shop Management
- **List View** (`/shop/items`): Browse shop products
- **Create View** (`/shop/items/new`): Create new products

### Automation Management
- **List View** (`/automation/triggers`): Browse automation triggers
- **Create View** (`/automation/triggers/new`): Create new triggers

## Security Features

### IP Whitelisting
- **Production**: Only whitelisted IPs can access
- **Development**: All IPs allowed (when `DEBUG=True`)
- **Configuration**: Set in `ADMIN_IPS` environment variable

### Database Access
- **Shared Database**: Uses same database as main bot
- **Read/Write Access**: Full CRUD operations permitted
- **Transaction Safety**: Atomic operations with rollback support

### Input Validation
- **Server-side Validation**: All data validated on server
- **SQL Injection Protection**: SQLAlchemy parameterized queries
- **XSS Prevention**: Input sanitization and output encoding

## Error Handling

### HTTP Status Codes
- **200**: Success
- **201**: Resource created
- **400**: Validation error
- **403**: Access denied
- **404**: Resource not found
- **409**: Duplicate entry
- **500**: Server error

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "field": "field_name"  // for validation errors
}
```

## Database Integration

### Shared Models
The admin panel uses the same models as the main bot:
- **User Management**: `User` model
- **Narrative**: `StoryFragment`, `NarrativeChoice`, `UserNarrativeState`
- **Shop**: `ShopItem`, `UserPurchase`, `ProductFile`
- **VIP Features**: `CompatibilityQuiz`, `AnonymousMessage`, etc.

### Transaction Management
- **Atomic Operations**: Complex nested operations in single transactions
- **Rollback Support**: Automatic rollback on errors
- **Consistency**: Maintains data consistency across related objects

## Development and Customization

### Adding New API Endpoints
1. Create new blueprint in `api/` directory
2. Define routes with proper validation
3. Implement business logic
4. Add to main app in `app.py`

### Adding New Views
1. Create HTML templates in `templates/`
2. Add routes in `app.py` registration functions
3. Implement backend logic in API endpoints
4. Add navigation links

### Security Considerations
- Always validate user permissions
- Implement proper authentication if needed
- Use parameterized queries
- Validate and sanitize all inputs
- Log security-relevant events

## Running the Admin Panel

### Development Mode
```bash
cd admin_panel
python app.py
# Runs on http://127.0.0.1:5000
```

### Production Mode
```bash
# Using gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 admin_panel.app:app
```

## Monitoring and Maintenance

### Logging
- **Access Logging**: All requests logged with IP and endpoint
- **Error Logging**: Detailed error information with stack traces
- **Security Logging**: Access denied events logged

### Performance Considerations
- **Database Queries**: Use eager loading to prevent N+1 queries
- **Pagination**: Implement pagination for large datasets
- **Caching**: Consider caching for frequently accessed data
- **Connection Pooling**: Proper database connection management

## Troubleshooting

### Common Issues
1. **Access Denied**: Check `ADMIN_IPS` configuration
2. **Database Connection**: Verify `DATABASE_URL` points to correct database
3. **Missing Models**: Ensure all bot models are importable
4. **Validation Errors**: Check request format against API documentation

### Debugging Tips
- Enable Flask debug mode for detailed error messages
- Check bot database is accessible from admin panel
- Verify all required environment variables are set
- Monitor logs for error patterns

The admin panel provides a comprehensive web-based interface for managing all aspects of the DianaBot, with secure access controls and robust API endpoints for efficient content and user management.