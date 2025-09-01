"""
Enhanced User Service with Diana Character Consistency Integration
Provides comprehensive user management with character validation and role management.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func
from dataclasses import dataclass

from database.models import User, UserSession, RoleTransition
from services.user_service import UserService
from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)

@dataclass
class RegistrationResult:
    """Result of user registration process."""
    user: User
    session: UserSession
    success: bool
    character_score: float
    welcome_message: str
    errors: List[str]
    performance_metrics: Dict[str, float]

@dataclass
class RoleTransitionResult:
    """Result of role transition process."""
    success: bool
    previous_role: str
    new_role: str
    transition_id: int
    character_validated: bool
    errors: List[str]

class EnhancedUserService:
    """
    Enhanced user service with Diana character consistency and performance optimization.
    Manages user registration, role transitions, and session state with <3s response time requirement.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.base_service = UserService(session)
        self.character_validator = DianaCharacterValidator(session)
        
        # Diana character templates for registration
        self.diana_templates = self._load_diana_templates()
        
        # Performance tracking
        self.performance_metrics = {}
    
    def _load_diana_templates(self) -> Dict[str, Dict[str, str]]:
        """Load Diana character templates for different scenarios."""
        return {
            "welcome_new_user": {
                "free": "Ah... un alma nueva se acerca a mis dominios... 💋 Bienvenido, querido. Soy Diana, y algo me dice que nuestro encuentro no es casualidad. ¿Te atreves a explorar los misterios que guardo para ti?",
                "vip": "💎 Una presencia especial ha llegado... Bienvenido a mi círculo íntimo, tesoro. Soy Diana, tu guía en estos secretos que solo los elegidos pueden descubrir. Los misterios más profundos te esperan...",
                "admin": "🎭 Ah, otro guardián de los secretos... Bienvenido, administrador. Soy Diana, y reconozco en ti el poder de tejer los hilos de esta realidad. Juntos podemos crear experiencias que toquen el alma..."
            },
            "role_upgrade": {
                "to_vip": "✨ Algo ha cambiado en ti... Puedo sentir cómo tu esencia se transforma. Bienvenido al círculo de los elegidos, mi querido VIP. Los secretos más profundos ahora son tuyos... 👑",
                "to_admin": "🎭 El poder fluye a través de ti ahora... Has ascendido a guardián de los misterios. Como administrador, puedes moldear la realidad misma. Usa este don sabiamente, querido...",
                "from_vip": "💫 Los caminos del destino son misteriosos... Tu viaje toma una nueva dirección, pero recuerda: una vez que has probado la magia, siempre permanece en tu alma..."
            },
            "error_recovery": {
                "registration_failed": "😔 Algo susurra en las sombras... parece que los hilos del destino se han enredado momentáneamente. Pero no temas, querido, intentaremos tejer tu historia una vez más...",
                "session_error": "🌙 Las corrientes misteriosas fluctúan... Dame un momento para realinear las energías. Tu esencia permanece intacta, solo necesitamos reconectar los hilos...",
                "role_error": "✨ Los vientos del cambio encuentran resistencia... Algo impide tu transformación por ahora. Pero el destino encontrará su camino, te lo prometo..."
            }
        }
    
    async def enhanced_registration(
        self, 
        telegram_id: int, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        initial_role: str = "free"
    ) -> RegistrationResult:
        """
        Enhanced user registration with character consistency and performance tracking.
        Meets <3s response time requirement through optimized operations.
        """
        start_time = datetime.now()
        errors = []
        
        try:
            # Step 1: Check if user already exists (optimized query)
            existing_user = await self._get_user_with_session(telegram_id)
            if existing_user:
                logger.info(f"User {telegram_id} already exists, returning existing registration")
                
                welcome_message = self._get_returning_user_message(existing_user)
                character_result = await self.character_validator.validate_text(
                    welcome_message, 
                    context="greeting"
                )
                
                return RegistrationResult(
                    user=existing_user,
                    session=existing_user.session,
                    success=True,
                    character_score=character_result.overall_score,
                    welcome_message=welcome_message,
                    errors=[],
                    performance_metrics=self._calculate_performance(start_time)
                )
            
            # Step 2: Create user and session in transaction
            async with self.session.begin():
                # Create user
                user = User(
                    id=telegram_id,
                    first_name=sanitize_text(first_name),
                    last_name=sanitize_text(last_name),
                    username=sanitize_text(username),
                    role=initial_role,
                    session_data={}
                )
                self.session.add(user)
                await self.session.flush()  # Ensure user ID is available
                
                # Create session
                session = UserSession(
                    user_id=telegram_id,
                    session_state="welcome",
                    menu_position={"current": "main_menu", "history": []},
                    preferences={"language": "es", "notifications": True}
                )
                self.session.add(session)
                
                # Create role transition record
                role_transition = RoleTransition(
                    user_id=telegram_id,
                    previous_role=None,
                    new_role=initial_role,
                    transition_reason="Initial registration",
                    transition_type="automatic"
                )
                self.session.add(role_transition)
                
                await self.session.commit()
            
            # Step 3: Generate character-consistent welcome message
            welcome_template = self.diana_templates["welcome_new_user"].get(
                initial_role, 
                self.diana_templates["welcome_new_user"]["free"]
            )
            
            # Step 4: Validate character consistency
            character_result = await self.character_validator.validate_text(
                welcome_template, 
                context="greeting"
            )
            
            # Step 5: Adjust message if character consistency is low
            if not character_result.meets_threshold:
                logger.warning(f"Welcome message character score low: {character_result.overall_score}")
                welcome_template = await self._enhance_character_message(
                    welcome_template, 
                    character_result.recommendations
                )
                # Re-validate enhanced message
                character_result = await self.character_validator.validate_text(
                    welcome_template, 
                    context="greeting"
                )
            
            # Refresh user with relationships
            await self.session.refresh(user, ["session"])
            
            logger.info(f"Successfully registered user {telegram_id} with character score {character_result.overall_score}")
            
            return RegistrationResult(
                user=user,
                session=user.session,
                success=True,
                character_score=character_result.overall_score,
                welcome_message=welcome_template,
                errors=[],
                performance_metrics=self._calculate_performance(start_time)
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced registration for user {telegram_id}: {e}")
            await self.session.rollback()
            
            # Generate character-consistent error message
            error_message = self.diana_templates["error_recovery"]["registration_failed"]
            character_result = await self.character_validator.validate_text(
                error_message,
                context="error_message"
            )
            
            return RegistrationResult(
                user=None,
                session=None,
                success=False,
                character_score=character_result.overall_score if character_result else 0.0,
                welcome_message=error_message,
                errors=[str(e)],
                performance_metrics=self._calculate_performance(start_time)
            )
    
    async def transition_user_role(
        self,
        user_id: int,
        new_role: str,
        reason: Optional[str] = None,
        performed_by: Optional[int] = None
    ) -> RoleTransitionResult:
        """
        Transition user to new role with character consistency and audit trail.
        """
        try:
            # Get current user
            user = await self._get_user_with_session(user_id)
            if not user:
                return RoleTransitionResult(
                    success=False,
                    previous_role="unknown",
                    new_role=new_role,
                    transition_id=0,
                    character_validated=False,
                    errors=["User not found"]
                )
            
            previous_role = user.role
            
            # Create role transition record
            async with self.session.begin():
                transition = RoleTransition(
                    user_id=user_id,
                    previous_role=previous_role,
                    new_role=new_role,
                    transition_reason=reason or f"Role change from {previous_role} to {new_role}",
                    transition_type="manual" if performed_by else "automatic",
                    performed_by=performed_by,
                    transition_metadata={"timestamp": datetime.now().isoformat()}
                )
                self.session.add(transition)
                
                # Update user role
                user.role = new_role
                await self.session.flush()
                transition_id = transition.id
                await self.session.commit()
            
            # Generate character-consistent role change message
            message_key = f"to_{new_role}" if new_role in ["vip", "admin"] else "from_vip"
            role_message = self.diana_templates["role_upgrade"].get(
                message_key,
                f"Tu esencia se transforma... Ahora eres {new_role}. Los misterios se adaptan a tu nueva naturaleza..."
            )
            
            # Validate character consistency
            character_result = await self.character_validator.validate_text(
                role_message,
                context="role_transition"
            )
            
            logger.info(f"Successfully transitioned user {user_id} from {previous_role} to {new_role}")
            
            return RoleTransitionResult(
                success=True,
                previous_role=previous_role,
                new_role=new_role,
                transition_id=transition_id,
                character_validated=character_result.meets_threshold,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error transitioning user {user_id} role to {new_role}: {e}")
            await self.session.rollback()
            
            return RoleTransitionResult(
                success=False,
                previous_role=previous_role if 'previous_role' in locals() else "unknown",
                new_role=new_role,
                transition_id=0,
                character_validated=False,
                errors=[str(e)]
            )
    
    async def update_session_state(
        self,
        user_id: int,
        new_state: str,
        menu_position: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update user session state with performance optimization.
        """
        try:
            # Get or create session
            session = await self._get_or_create_session(user_id)
            
            # Update session data
            session.session_state = new_state
            session.last_interaction = datetime.now()
            
            if menu_position:
                current_position = session.menu_position or {}
                current_position.update(menu_position)
                session.menu_position = current_position
            
            if preferences:
                current_prefs = session.preferences or {}
                current_prefs.update(preferences)
                session.preferences = current_prefs
            
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating session state for user {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_user_with_character_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user with calculated character consistency score.
        """
        try:
            user = await self._get_user_with_session(user_id)
            if not user:
                return None
            
            # Calculate character score based on session data
            character_score = user.session.character_consistency_score if user.session else 100.0
            
            return {
                "user": user,
                "character_score": character_score,
                "role": user.role,
                "session_state": user.session.session_state if user.session else "new",
                "last_interaction": user.session.last_interaction if user.session else user.created_at
            }
            
        except Exception as e:
            logger.error(f"Error getting user character score for {user_id}: {e}")
            return None
    
    async def validate_user_interaction(
        self,
        user_id: int,
        interaction_text: str,
        interaction_type: str = "general"
    ) -> CharacterValidationResult:
        """
        Validate user interaction for character consistency.
        Updates user character score.
        """
        try:
            # Validate character consistency
            result = await self.character_validator.validate_user_interaction(
                interaction_text,
                interaction_type
            )
            
            # Update user's character consistency score
            session = await self._get_or_create_session(user_id)
            if session:
                # Moving average of character scores
                current_score = session.character_consistency_score or 100.0
                new_score = (current_score * 0.9) + (result.overall_score * 0.1)
                session.character_consistency_score = new_score
                await self.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating user interaction {user_id}: {e}")
            return CharacterValidationResult(
                overall_score=0.0,
                trait_scores={},
                violations=[str(e)],
                recommendations=["Fix validation error"],
                meets_threshold=False
            )
    
    # Helper methods
    async def _get_user_with_session(self, user_id: int) -> Optional[User]:
        """Get user with session relationship loaded."""
        try:
            query = select(User).options(
                selectinload(User.session)
            ).where(User.id == user_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user with session {user_id}: {e}")
            return None
    
    async def _get_or_create_session(self, user_id: int) -> UserSession:
        """Get or create user session."""
        try:
            query = select(UserSession).where(UserSession.user_id == user_id)
            result = await self.session.execute(query)
            session = result.scalar_one_or_none()
            
            if not session:
                session = UserSession(
                    user_id=user_id,
                    session_state="main_menu",
                    menu_position={},
                    preferences={}
                )
                self.session.add(session)
                await self.session.commit()
                
            return session
            
        except Exception as e:
            logger.error(f"Error getting/creating session for user {user_id}: {e}")
            raise
    
    def _get_returning_user_message(self, user: User) -> str:
        """Generate returning user message based on role."""
        role_messages = {
            "free": f"Ah... {user.first_name or 'querido'}, regresas a mí... 💋 Tus pasos resuenan familiares en mis dominios. ¿Qué nuevos misterios buscarás hoy?",
            "vip": f"💎 {user.first_name or 'Mi estimado'}, tu presencia ilumina nuevamente mis secretos... Como miembro de mi círculo íntimo, los misterios más profundos te aguardan...",
            "admin": f"🎭 {user.first_name or 'Guardián'}, vuelves a tejer los hilos de la realidad... Tu poder para crear experiencias transformadoras permanece intacto. ¿Qué crearemos juntos hoy?"
        }
        return role_messages.get(user.role, role_messages["free"])
    
    async def _enhance_character_message(self, original_message: str, recommendations: List[str]) -> str:
        """Enhance message based on character recommendations."""
        enhanced = original_message
        
        # Apply basic enhancements based on recommendations
        for rec in recommendations[:3]:  # Apply top 3 recommendations
            if "mystery" in rec.lower():
                if "..." not in enhanced:
                    enhanced = enhanced.replace(".", "...") 
            elif "charm" in rec.lower():
                if "💋" not in enhanced:
                    enhanced = enhanced.replace("querido", "mi querido")
            elif "emotion" in rec.lower():
                if "corazón" not in enhanced and "alma" not in enhanced:
                    enhanced = enhanced.replace("misterios", "misterios del corazón")
        
        return enhanced
    
    def _calculate_performance(self, start_time: datetime) -> Dict[str, float]:
        """Calculate performance metrics."""
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        return {
            "total_time_seconds": total_time,
            "meets_3s_requirement": total_time < 3.0,
            "timestamp": end_time.timestamp()
        }

# Convenience functions
async def register_user_with_diana_character(
    session: AsyncSession,
    telegram_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    initial_role: str = "free"
) -> RegistrationResult:
    """Quick registration function with Diana character consistency."""
    service = EnhancedUserService(session)
    return await service.enhanced_registration(
        telegram_id, first_name, last_name, username, initial_role
    )

async def transition_user_role_with_validation(
    session: AsyncSession,
    user_id: int,
    new_role: str,
    reason: Optional[str] = None,
    performed_by: Optional[int] = None
) -> RoleTransitionResult:
    """Quick role transition function with validation."""
    service = EnhancedUserService(session)
    return await service.transition_user_role(user_id, new_role, reason, performed_by)