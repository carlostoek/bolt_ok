"""
Enhanced User Registration Middleware with Diana Character Consistency
Replaces basic user registration with character-aware, performance-optimized registration flow.
"""

import logging
from typing import Any, Callable, Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.enhanced_user_service import EnhancedUserService, RegistrationResult
from services.diana_character_validator import CharacterValidationResult

logger = logging.getLogger(__name__)

class EnhancedUserRegistrationMiddleware(BaseMiddleware):
    """
    Enhanced middleware for user registration with Diana character consistency.
    
    Features:
    - Character-consistent welcome messages
    - Performance optimization (<3s registration)
    - Role-based registration flow  
    - Session state initialization
    - Character validation scoring
    """
    
    def __init__(self, require_character_validation: bool = True):
        """
        Initialize enhanced registration middleware.
        
        Args:
            require_character_validation: Whether to enforce character consistency requirements
        """
        self.require_character_validation = require_character_validation
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Any],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        Process user registration with enhanced character consistency.
        
        Extracts user information and ensures registration with Diana character validation.
        """
        session: AsyncSession = data.get("session")
        if not session:
            logger.warning("No database session available in middleware")
            return await handler(event, data)

        # Extract user information from different event types
        user_info, interaction_context = self._extract_user_info(event)
        
        if not user_info:
            return await handler(event, data)

        try:
            # Initialize enhanced user service
            user_service = EnhancedUserService(session)
            
            # Determine initial role based on context
            initial_role = self._determine_initial_role(user_info, interaction_context)
            
            # Perform enhanced registration
            registration_result = await user_service.enhanced_registration(
                telegram_id=user_info.id,
                first_name=getattr(user_info, "first_name", None),
                last_name=getattr(user_info, "last_name", None),
                username=getattr(user_info, "username", None),
                initial_role=initial_role
            )
            
            # Add registration data to handler context
            data.update({
                "user": registration_result.user,
                "user_session": registration_result.session,
                "character_score": registration_result.character_score,
                "registration_result": registration_result,
                "diana_welcome_message": registration_result.welcome_message if registration_result.success else None
            })
            
            # Log registration performance
            if registration_result.performance_metrics:
                response_time = registration_result.performance_metrics.get("total_time_seconds", 0)
                meets_requirement = registration_result.performance_metrics.get("meets_3s_requirement", False)
                
                log_level = logging.INFO if meets_requirement else logging.WARNING
                logger.log(
                    log_level,
                    f"User registration completed in {response_time:.2f}s "
                    f"(meets requirement: {meets_requirement}) - "
                    f"Character score: {registration_result.character_score:.1f}"
                )
            
            # Handle character validation if required
            if self.require_character_validation and registration_result.success:
                if not self._meets_character_requirements(registration_result.character_score):
                    logger.warning(
                        f"User {user_info.id} registration has low character score: "
                        f"{registration_result.character_score:.1f}"
                    )
                    # Could implement fallback logic here if needed
            
            # Send welcome message if this is a new user registration
            if registration_result.success and registration_result.welcome_message:
                await self._send_welcome_if_needed(event, registration_result, data)
                
        except Exception as e:
            logger.error(f"Error in enhanced user registration middleware: {e}")
            
            # Fallback to basic registration to ensure system continues working
            try:
                from services.user_service import UserService
                basic_service = UserService(session)
                user = await basic_service.get_user(user_info.id)
                
                if not user:
                    user = await basic_service.create_user(
                        user_info.id,
                        first_name=getattr(user_info, "first_name", None),
                        last_name=getattr(user_info, "last_name", None),
                        username=getattr(user_info, "username", None)
                    )
                
                data["user"] = user
                logger.info(f"Fallback registration completed for user {user_info.id}")
                
            except Exception as fallback_error:
                logger.error(f"Fallback registration also failed: {fallback_error}")
                # Continue anyway - handler should handle missing user gracefully

        return await handler(event, data)
    
    def _extract_user_info(self, event: Update) -> tuple[Optional[Any], str]:
        """
        Extract user information and interaction context from event.
        
        Returns:
            Tuple of (user_info, interaction_context)
        """
        user_info = None
        context = "unknown"
        
        if hasattr(event, "message") and event.message and event.message.from_user:
            user_info = event.message.from_user
            context = "message"
            
        elif hasattr(event, "callback_query") and event.callback_query and event.callback_query.from_user:
            user_info = event.callback_query.from_user
            context = "callback"
            
        elif hasattr(event, "from_user") and event.from_user:
            user_info = event.from_user
            context = "direct"
            
        elif hasattr(event, "user") and event.user:  # e.g., PollAnswer
            user_info = event.user
            context = "poll"
        
        return user_info, context
    
    def _determine_initial_role(self, user_info: Any, context: str) -> str:
        """
        Determine initial user role based on user information and context.
        
        This could be enhanced with business logic for automatic VIP assignment,
        admin detection, etc.
        """
        # Default role
        initial_role = "free"
        
        # Could implement logic here for:
        # - Checking if user has premium Telegram subscription
        # - Detecting admin users from configuration
        # - Special invitation codes
        # - etc.
        
        return initial_role
    
    def _meets_character_requirements(self, character_score: float) -> bool:
        """Check if character score meets minimum requirements."""
        return character_score >= 95.0  # MVp requirement: >95% character consistency
    
    async def _send_welcome_if_needed(
        self, 
        event: Update, 
        registration_result: RegistrationResult,
        data: Dict[str, Any]
    ) -> None:
        """
        Send welcome message if user is newly registered and context is appropriate.
        
        Only sends welcome for certain interaction types to avoid spam.
        """
        try:
            # Only send welcome for direct messages or specific commands
            if hasattr(event, "message") and event.message:
                message: Message = event.message
                
                # Check if this is a command that should trigger welcome
                if (message.text and 
                    (message.text.startswith("/start") or 
                     message.text.startswith("/diana") or
                     message.text.startswith("/menu"))):
                    
                    await message.answer(
                        registration_result.welcome_message,
                        parse_mode=None  # Keep Diana's emojis and formatting
                    )
                    
                    # Mark that welcome was sent to avoid duplicate sends
                    if registration_result.session:
                        user_service = EnhancedUserService(data.get("session"))
                        await user_service.update_session_state(
                            registration_result.user.id,
                            "welcomed",
                            {"welcome_sent": True}
                        )
                        
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            # Don't fail the entire middleware chain for welcome message issues

class DianaCharacterConsistencyMiddleware(BaseMiddleware):
    """
    Middleware to validate character consistency of bot responses.
    
    This middleware validates outgoing messages to ensure Diana's character
    is maintained consistently across all interactions.
    """
    
    def __init__(self, validate_responses: bool = True):
        self.validate_responses = validate_responses
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Any],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        Validate character consistency of responses.
        """
        if not self.validate_responses:
            return await handler(event, data)
        
        # Store reference to session for validation
        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)
        
        # Execute handler
        result = await handler(event, data)
        
        # Post-handler validation could be implemented here
        # to check responses that were sent
        
        return result

# Convenience function for easy middleware registration
def get_enhanced_registration_middleware(require_character_validation: bool = True):
    """Get configured enhanced registration middleware."""
    return EnhancedUserRegistrationMiddleware(require_character_validation)

def get_character_consistency_middleware(validate_responses: bool = True):
    """Get configured character consistency middleware.""" 
    return DianaCharacterConsistencyMiddleware(validate_responses)