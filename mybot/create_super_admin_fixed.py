"""
Script para crear un usuario super admin para testing usando los modelos de database.

Este script crea un usuario con rol super_admin que puede ser usado
para probar el sistema de autenticación.
"""
import asyncio
import logging
from sqlalchemy import select

# Use the database models that match the actual database schema
from database.models import User
from database.setup import get_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_super_admin():
    """Crea un usuario super admin si no existe."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Verificar si ya existe un super admin
        result = await session.execute(
            select(User).where(User.role == "super_admin")
        )
        existing_super_admin = result.scalar_one_or_none()
        
        if existing_super_admin:
            logger.info(f"Super admin ya existe: {existing_super_admin}")
            return existing_super_admin
        
        # Crear nuevo super admin usando la estructura de la base de datos real
        super_admin = User(
            id=100000000,  # ID de Telegram fijo para el super admin
            username="superadmin",
            first_name="Super",
            last_name="Admin",
            role="super_admin",
            is_admin=True,
            points=1000,
            level=10
        )
        
        session.add(super_admin)
        await session.commit()
        await session.refresh(super_admin)
        
        logger.info(f"Super admin creado: {super_admin}")
        return super_admin


async def main():
    """Función principal."""
    # Initialize database first
    from database.setup import init_db
    await init_db()
    
    logger.info("Creando super admin...")
    admin = await create_super_admin()
    logger.info(f"Super admin listo: ID={admin.id}, Username={admin.username}, Role={admin.role}")
    
    # Mostrar información de login
    print("\n" + "="*50)
    print("SUPER ADMIN CREADO EXITOSAMENTE")
    print("="*50)
    print(f"User ID: {admin.id}")
    print(f"Username: {admin.username}")
    print(f"Role: {admin.role}")
    print(f"Is Admin: {admin.is_admin}")
    print("\nPara hacer login:")
    print("URL: POST /api/v1/auth/login")
    print("Body (form-data):")
    print("  username: superadmin")
    print("  password: admin123")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())