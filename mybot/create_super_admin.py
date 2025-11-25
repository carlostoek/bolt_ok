"""
Script para crear un usuario super admin para testing.

Este script crea un usuario con rol super_admin que puede ser usado
para probar el sistema de autenticación.
"""
import asyncio
import logging
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_super_admin():
    """Crea un usuario super admin si no existe."""
    async with AsyncSessionLocal() as session:
        # Verificar si ya existe un super admin
        result = await session.execute(
            select(User).where(User.role == UserRole.SUPER_ADMIN)
        )
        existing_super_admin = result.scalar_one_or_none()
        
        if existing_super_admin:
            logger.info(f"Super admin ya existe: {existing_super_admin}")
            return existing_super_admin
        
        # Crear nuevo super admin
        super_admin = User(
            id=100000000,  # ID de Telegram fijo para el super admin
            username="superadmin",
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            is_banned=False,
            is_vip=True,
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
    print("\nPara hacer login:")
    print("URL: POST /api/v1/auth/login")
    print("Body (form-data):")
    print("  username: superadmin")
    print("  password: admin123")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())