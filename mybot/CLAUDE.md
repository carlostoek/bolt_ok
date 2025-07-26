# CLAUDE.md - Development Guide for Bolt OK Telegram Bot


```markdown
Eres un ingeniero senior full-stack especializado en modificaciones puntuales con gestión eficiente de contexto. Operarás bajo estos principios:

**Alcance Controlado**
1. Modo de análisis:
   - Por defecto: Solo procesarás archivos explícitamente mencionados
   - Dependencias: Verificarás máximo 2 niveles de profundidad
   - Exclusión automática: 
     * Archivos binarios/assets
     * Documentación no técnica
     * Librerías de terceros

2. Gestión de contexto:
   - Memoria activa: Máximo 3 archivos simultáneos
   - Referencias cruzadas optimizadas:
     ```python
     # REF: [archivo] [elemento] (vista resumida)
     # Ejemplo: # REF: utils/auth.py (get_current_user → retorna UserSchema)
     ```
   - Cache de contexto: 500 tokens máximo por archivo referenciado
**Proceso de Interacción**
1. Fase inicial:
   - Al recibir una solicitud, confirmarás:
     ```
     [CONFIRMACIÓN DE ALCANCE]
     Archivos principales a analizar: [lista]
     Dependencias críticas estimadas: [0-3 archivos]
     ¿Confirmar análisis? (y/n)
     ```

2. Durante el desarrollo:
   - Si se detecta necesidad de contexto adicional:
     ```
     [SOLICITUD DE CONTEXTO]
     Archivo requerido: ruta/archivo.ext
     Sección necesaria: [Líneas X-Y | Clase Z | Función W]
     Propósito: [Explicación técnica en 1 oración]
     ```

**Reglas de Implementación (Modificadas)**
1. Límites estrictos:
   - Máximo 1 archivo generado/modificado por respuesta
   - Dependencias: Solo incluir si cambian >30% de su contenido
   - Comentarios: Máximo 10% del total de líneas de código

2. Priorización:
   ```mermaid
   graph TD
       A[Cambio Solicitado] --> B{¿Requiere nueva funcionalidad?}
       B -->|Sí| C[Implementar solo core feature]
       B -->|No| D[Corregir solo líneas problemáticas]
       C & D --> E[Excluir documentación/ejemplos]
   ```

3. Estructura ajustada:
   - Requerimientos: Solo librerías directamente usadas
   - Tests: Solo cuando se modifique comportamiento público
   - Logging: Mantener existente (no agregar nuevos)

**Formato de Respuesta (Optimizado)**
```python
# ANÁLISIS (Tokens usados: X/8000)
Archivo principal: [ruta]
Dependencias procesadas: [lista compacta]

# CAMBIOS PROPUESTOS
"""[ruta/archivo.ext] (Líneas A-B)"""
[Código modificado (diff-style)]
```[Explicación técnica en 3 bullets max]

# CONTEXTO RELEVANTE
```[Fragmentos de código adyacentes (máx. 5 líneas)]```

# SIGUIENTES PASOS
1. [Acción inmediata requerida]
2. [Posibles optimizaciones futuras]
```

**Política de Tokens**
1. Si el análisis supera 7500 tokens:
   - Automáticamente:
     * Cambiar a modo "visión parcial"
     * Descartar metadatos no esenciales
     * Usar representaciones resumidas:
       ```python
       ClassName → CN; FunctionName → FN; etc.
       ```

2. Umbrales de notificación:
   - 6000 tokens: "Contexto aproximado al 75% de capacidad"
   - 7000 tokens: "Solicitar confirmación para continuar"
   - 8000 tokens: Detener procesamiento y requerir refinamiento

**Ejemplo de Flujo**
Usuario: "Corrige el error de autenticación en auth.py"
AI:
```
[CONFIRMACIÓN DE ALCANCE]
Archivos principales: auth.py
Dependencias críticas: models/user.py (solo schema)
Tokens estimados: 3200
¿Proceder? (y/n)
```
```

## System Overview

This is a sophisticated multi-tenant Telegram bot system designed for gamified adult content delivery with VIP subscriptions, interactive narratives, and comprehensive user engagement features.

### Architecture

- **Framework**: aiogram v3 (Telegram Bot API)
- **Database**: SQLAlchemy async ORM with PostgreSQL/SQLite support
- **Pattern**: Service layer architecture with Repository pattern
- **Multi-tenancy**: Each admin can configure independent bot instances
- **Gamification**: Points system, missions, achievements, levels, and auctions
- **Content**: Interactive narrative system with decision trees and VIP content

## Key Components

### Database Models (`database/models.py`)
- **User**: Core user data with roles (admin/vip/free), points, achievements
- **Narrative Models**: Interactive story fragments and user progress
- **Gamification**: Missions, achievements, levels, points system
- **Subscriptions**: VIP management with expiration tracking
- **Channel Management**: Multi-channel support with engagement tracking
- **Commerce**: Auctions, tokens, tariffs for monetization

### Services Layer
- **TenantService**: Multi-tenant configuration management
- **FreeChannelService**: Automated channel access with social media messaging
- **NarrativeService**: Interactive story management
- **PointService**: Gamification and rewards
- **CoordinadorCentral**: Facade pattern for complex workflows

### Key Features

#### Free Channel Access System
- Automatic social media messaging when users request channel access
- Configurable delay before approval (0-1440 minutes)
- Automatic role assignment as "free"
- Intelligent role priority (Admin > VIP > Free)
- VIP users can access both VIP and free channels without losing status

#### Role Management
- **Admin**: Full system access and configuration
- **VIP**: Access to premium content and free channels
- **Free**: Basic access to free channels only

#### Gamification
- Points system ("besitos" - kisses)
- Daily check-ins with streak bonuses
- Interactive missions and achievements
- Channel engagement rewards
- Real-time auction system

## Development Commands

### Database Operations
```bash
# Initialize database
python -c "from database.setup import init_db; import asyncio; asyncio.run(init_db())"

# Create migration (if using Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Running the Bot
```bash
# Development
python bot.py

# Production with logging
python bot.py 2>&1 | tee bot.log
```

### Testing
```bash
# Run all tests (if pytest is configured)
pytest

# Test specific functionality
python -m pytest tests/test_free_channel.py -v
```

## Configuration

### Environment Variables
- `BOT_TOKEN`: Telegram Bot API token
- `DATABASE_URL`: Database connection string
- `VIP_CHANNEL_ID`: Default VIP channel ID
- `FREE_CHANNEL_ID`: Default free channel ID

### Admin Configuration
Access admin panel via `/admin` command. Key configurations:
- Channel IDs for VIP and free channels
- Social media message templates
- Approval delay times (0-1440 minutes)
- Tariff and pricing setup

## Common Development Patterns

### Service Implementation
```python
class NewService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def method_name(self, user_id: int) -> Dict[str, Any]:
        try:
            # Implementation
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error in NewService.method_name: {e}")
            return {"success": False, "error": str(e)}
```

### Handler Implementation
```python
@router.message(Command("command"))
async def handler_name(message: Message, session: AsyncSession):
    try:
        # Use services for business logic
        service = SomeService(session)
        result = await service.do_something(message.from_user.id)
        
        # Safe message sending
        await safe_answer(message, result["message"])
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        await safe_answer(message, "Error message")
```

### Database Queries
```python
# Always use async patterns
from sqlalchemy import select

async def get_user_data(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

## Important Implementation Notes

### Message Safety
- All message sending uses `safe_answer()`, `safe_send_message()` utilities
- Empty messages are automatically replaced with default safe messages
- Prevents Telegram API errors from empty content

### Role Priority Logic
- VIP users can access both VIP and free channels
- Role verification uses both database and Telegram API checks
- Role upgrades never downgrade existing permissions

### Error Handling
- All services return structured responses with success/error states
- Global error handler catches and logs all exceptions
- Critical errors are logged with full stack traces

### Multi-tenancy
- Each admin can configure independent bot instances
- Tenant initialization creates default tariffs, missions, and levels
- Configuration state tracking for setup completion

## Recent Changes

### Fixed Import Errors (Production Issues)
- `utils/admin_check.py`: Added missing `from sqlalchemy import select`
- `handlers/admin/admin_menu.py`: Added missing `from keyboards.admin_kb import get_admin_kb`

### Enhanced Free Channel System
- Automatic social media messaging on join requests
- Configurable approval delays
- Intelligent role priority handling
- Comprehensive admin configuration interface

## Testing Procedures

### Free Channel Flow Testing
1. User sends join request to free channel
2. Verify automatic social media message is sent
3. Wait for configured delay period
4. Verify automatic approval and role assignment
5. Confirm VIP users retain VIP status

### Role Verification Testing
1. Test role hierarchy (Admin > VIP > Free)
2. Verify channel access permissions
3. Test role upgrades and downgrades
4. Confirm multi-channel access for VIP users

## Troubleshooting

### Common Issues
- **Import Errors**: Check all service imports are properly referenced
- **Database Connection**: Verify DATABASE_URL and connection pool settings
- **Telegram API**: Ensure bot token is valid and has proper permissions
- **Channel Access**: Verify bot is admin in all configured channels

### Debug Mode
Enable detailed logging by setting log level to DEBUG in `bot.py`:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

### Production Monitoring
- Check `bot.log` for error patterns
- Monitor database connection pool usage
- Track memory usage for long-running instances
- Verify scheduled tasks are running correctly

## Security Considerations

- Never commit tokens or credentials to repository
- Use environment variables for all sensitive configuration
- Validate all user inputs before processing
- Implement rate limiting for expensive operations
- Sanitize all text content before database storage

## Performance Notes

- Database sessions are managed via middleware
- Use `selectin` loading for related objects
- Background tasks run independently with error isolation
- Message safety prevents API rate limit issues
- Connection pooling handles concurrent users

This documentation should be updated as new features are added or architectural changes are made to the system.
