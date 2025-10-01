"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from constants.keyboards import main_menu_keyboard
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory 
from utils.user_roles import clear_role_cache, is_admin
from services.tenant_service import TenantService
from utils.localization import get_text
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """
    Enhanced start command with intelligent routing based on user status.
    Provides seamless experience for new and returning users.
    """
    try:
        user_id = message.from_user.id
        logger.info(f"Start command received from user {user_id}")
        
        # Clear any cached role for fresh check
        clear_role_cache(user_id)
        
        # Get or create user
        user = await session.get(User, user_id)
        is_new_user = user is None
        
        if not user:
            user = User(
                id=user_id,
                username=sanitize_text(message.from_user.username),
                first_name=sanitize_text(message.from_user.first_name),
                last_name=sanitize_text(message.from_user.last_name),
            )
            session.add(user)
            await session.commit()
            logger.info(f"Created new user: {user_id}")
        else:
            # Update user info if changed
            updated = False
            new_username = sanitize_text(message.from_user.username)
            new_first_name = sanitize_text(message.from_user.first_name)
            new_last_name = sanitize_text(message.from_user.last_name)
            
            if user.username != new_username:
                user.username = new_username
                updated = True
            if user.first_name != new_first_name:
                user.first_name = new_first_name
                updated = True
            if user.last_name != new_last_name:
                user.last_name = new_last_name
                updated = True
                
            if updated:
                await session.commit()
                logger.info(f"Updated user info: {user_id}")
        
        # Check if this is an admin
        if await is_admin(user_id, session):
            logger.info(f"Admin user {user_id} accessing start command")
            tenant_service = TenantService(session)
            
            # Initialize tenant for admin
            init_result = await tenant_service.initialize_tenant(user_id)
            if not init_result["success"]:
                logger.error(f"Failed to initialize tenant for admin {user_id}: {init_result['error']}")
                await message.answer(get_text("start_handler.admin_init_error"))
                return

            # Admin menu
            try:
                text, keyboard = await menu_factory.create_menu("admin_main", user_id, session, message.bot)
                welcome_prefix = get_text("start_handler.admin_welcome")
                text = welcome_prefix + text.split('\n\n', 1)[-1]

                await menu_manager.show_menu(
                    message,
                    text,
                    keyboard,
                    session,
                    "admin_main",
                    delete_origin_message=True
                )
                
                # Show reply keyboard
                await message.answer(
                    get_text("start_handler.admin_panel_activated"),
                    reply_markup=main_menu_keyboard
                )
                
            except Exception as e:
                logger.error(f"Error creating admin menu for {user_id}: {e}")
                await message.answer(get_text("start_handler.admin_menu_error"))
            return
        
        # Regular user logic
        logger.info(f"Regular user {user_id} accessing start command")
        try:
            text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)
            
            is_vip = "suscripción vip" in text.lower() or "experiencia premium" in text.lower()

            if is_new_user:
                welcome_key = "start_handler.vip_welcome" if is_vip else "start_handler.user_welcome"
                welcome_prefix = get_text(welcome_key)
                text = welcome_prefix + text
            else:
                welcome_key = "start_handler.vip_welcome_back" if is_vip else "start_handler.user_welcome_back"
                welcome_prefix = get_text(welcome_key)
                text = welcome_prefix + text.split('\n\n', 1)[-1]
            
            await menu_manager.show_menu(
                message,
                text,
                keyboard,
                session,
                "main",
                delete_origin_message=True
            )
            
            # Show reply keyboard
            await message.answer(
                get_text("start_handler.main_menu_activated"),
                reply_markup=main_menu_keyboard
            )

        except Exception as e:
            logger.error(f"Error creating main menu for user {user_id}: {e}")
            await message.answer(get_text("start_handler.main_menu_error"))

    except Exception as e:
        logger.error(f"Critical error in start command: {e}", exc_info=True)
        await message.answer(get_text("start_handler.system_error"))
