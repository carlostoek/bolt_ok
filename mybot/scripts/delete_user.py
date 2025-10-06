#!/usr/bin/env python3
"""
Script para eliminar usuarios de la base de datos.

Permite eliminar un usuario y todos sus datos relacionados de forma segura.

ADVERTENCIA: Esta acción es irreversible. Elimina:
- Usuario y perfil
- Progreso narrativo
- Misiones completadas
- Compras
- Lore pieces desbloqueados
- Reacciones
- Todos los datos relacionados

Uso:
    python scripts/delete_user.py <user_id>
    python scripts/delete_user.py 123456789

    # Modo interactivo (pregunta confirmación):
    python scripts/delete_user.py

    # Eliminar múltiples usuarios:
    python scripts/delete_user.py 123456789 987654321 555555555

    # Ver información del usuario antes de eliminar:
    python scripts/delete_user.py --info 123456789
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import init_db, get_session_factory
from database.models import (
    User, UserMissionEntry, UserPurchase, UserAchievement,
    UserLorePiece, ButtonReaction, UserReward, UserMilestone,
    UserBadge, UserStats, UserChallengeProgress
)
from database.narrative_models import UserNarrativeState
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_user_info(session: AsyncSession, user_id: int) -> dict:
    """Obtiene información del usuario para mostrar antes de eliminar."""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Contar datos relacionados
    missions_stmt = select(UserMissionEntry).where(UserMissionEntry.user_id == user_id)
    missions_result = await session.execute(missions_stmt)
    missions_count = len(missions_result.scalars().all())

    purchases_stmt = select(UserPurchase).where(UserPurchase.user_id == user_id)
    purchases_result = await session.execute(purchases_stmt)
    purchases_count = len(purchases_result.scalars().all())

    lore_stmt = select(UserLorePiece).where(UserLorePiece.user_id == user_id)
    lore_result = await session.execute(lore_stmt)
    lore_count = len(lore_result.scalars().all())

    narrative_stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
    narrative_result = await session.execute(narrative_stmt)
    narrative_state = narrative_result.scalar_one_or_none()

    return {
        "user": user,
        "missions_completed": missions_count,
        "purchases": purchases_count,
        "lore_pieces": lore_count,
        "has_narrative_progress": narrative_state is not None,
        "fragments_visited": narrative_state.fragments_visited if narrative_state else 0
    }


async def delete_user(session: AsyncSession, user_id: int, dry_run: bool = False) -> bool:
    """
    Elimina un usuario y todos sus datos relacionados.

    Args:
        session: Sesión de base de datos
        user_id: ID del usuario a eliminar
        dry_run: Si es True, solo muestra qué se eliminaría sin hacerlo

    Returns:
        True si se eliminó exitosamente, False si no se encontró
    """
    # Verificar que el usuario existe
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"❌ Usuario {user_id} no encontrado en la base de datos")
        return False

    logger.info(f"👤 Usuario encontrado: {user.username or user.first_name or user_id}")
    logger.info(f"   Puntos: {user.points}")
    logger.info(f"   Nivel: {user.level}")
    logger.info(f"   Rol: {user.role}")

    if dry_run:
        logger.info("\n🔍 Modo DRY RUN - No se eliminará nada\n")

    # Contar y eliminar datos relacionados
    deleted_counts = {}

    # 1. Missions
    stmt = delete(UserMissionEntry).where(UserMissionEntry.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["missions"] = result.rowcount
    else:
        count_stmt = select(UserMissionEntry).where(UserMissionEntry.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["missions"] = len(result.scalars().all())

    # 2. Purchases
    stmt = delete(UserPurchase).where(UserPurchase.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["purchases"] = result.rowcount
    else:
        count_stmt = select(UserPurchase).where(UserPurchase.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["purchases"] = len(result.scalars().all())

    # 3. Achievements
    stmt = delete(UserAchievement).where(UserAchievement.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["achievements"] = result.rowcount
    else:
        count_stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["achievements"] = len(result.scalars().all())

    # 4. Lore Pieces
    stmt = delete(UserLorePiece).where(UserLorePiece.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["lore_pieces"] = result.rowcount
    else:
        count_stmt = select(UserLorePiece).where(UserLorePiece.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["lore_pieces"] = len(result.scalars().all())

    # 5. Narrative State
    stmt = delete(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["narrative_state"] = result.rowcount
    else:
        count_stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["narrative_state"] = len(result.scalars().all())

    # 6. Message Reactions
    stmt = delete(ButtonReaction).where(ButtonReaction.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["reactions"] = result.rowcount
    else:
        count_stmt = select(ButtonReaction).where(ButtonReaction.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["reactions"] = len(result.scalars().all())

    # 7. User Rewards
    stmt = delete(UserReward).where(UserReward.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["rewards"] = result.rowcount
    else:
        count_stmt = select(UserReward).where(UserReward.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["rewards"] = len(result.scalars().all())

    # 8. User Milestones
    stmt = delete(UserMilestone).where(UserMilestone.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["milestones"] = result.rowcount
    else:
        count_stmt = select(UserMilestone).where(UserMilestone.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["milestones"] = len(result.scalars().all())

    # 9. User Badges
    stmt = delete(UserBadge).where(UserBadge.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["badges"] = result.rowcount
    else:
        count_stmt = select(UserBadge).where(UserBadge.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["badges"] = len(result.scalars().all())

    # 10. User Stats
    stmt = delete(UserStats).where(UserStats.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["stats"] = result.rowcount
    else:
        count_stmt = select(UserStats).where(UserStats.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["stats"] = len(result.scalars().all())

    # 11. User Challenge Progress
    stmt = delete(UserChallengeProgress).where(UserChallengeProgress.user_id == user_id)
    if not dry_run:
        result = await session.execute(stmt)
        deleted_counts["challenges"] = result.rowcount
    else:
        count_stmt = select(UserChallengeProgress).where(UserChallengeProgress.user_id == user_id)
        result = await session.execute(count_stmt)
        deleted_counts["challenges"] = len(result.scalars().all())

    # 12. Usuario principal
    if not dry_run:
        await session.delete(user)
        deleted_counts["user"] = 1
    else:
        deleted_counts["user"] = 1

    # Commit cambios
    if not dry_run:
        await session.commit()

    # Mostrar resumen
    logger.info("\n📊 Resumen de eliminación:")
    logger.info(f"   Misiones completadas: {deleted_counts['missions']}")
    logger.info(f"   Compras: {deleted_counts['purchases']}")
    logger.info(f"   Logros: {deleted_counts['achievements']}")
    logger.info(f"   Fragmentos narrativos: {deleted_counts['lore_pieces']}")
    logger.info(f"   Estado narrativo: {deleted_counts['narrative_state']}")
    logger.info(f"   Reacciones: {deleted_counts['reactions']}")
    logger.info(f"   Recompensas: {deleted_counts['rewards']}")
    logger.info(f"   Milestones: {deleted_counts['milestones']}")
    logger.info(f"   Badges: {deleted_counts['badges']}")
    logger.info(f"   Stats: {deleted_counts['stats']}")
    logger.info(f"   Challenges: {deleted_counts['challenges']}")
    logger.info(f"   Usuario: {deleted_counts['user']}")

    if dry_run:
        logger.info("\n⚠️  DRY RUN - Ningún dato fue eliminado")
    else:
        logger.info(f"\n✅ Usuario {user_id} eliminado exitosamente")

    return True


async def interactive_mode():
    """Modo interactivo: pregunta al usuario qué quiere hacer."""
    print("\n" + "="*60)
    print("   ELIMINACIÓN DE USUARIOS - MODO INTERACTIVO")
    print("="*60)

    user_id_input = input("\n👤 Ingresa el ID del usuario a eliminar (o 'exit' para salir): ")

    if user_id_input.lower() == 'exit':
        print("Cancelado.")
        return

    try:
        user_id = int(user_id_input)
    except ValueError:
        print("❌ Error: El ID debe ser un número entero")
        return

    # Inicializar DB
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as session:
        # Mostrar información del usuario
        info = await get_user_info(session, user_id)

        if not info:
            print(f"❌ Usuario {user_id} no encontrado")
            return

        user = info["user"]
        print(f"\n📋 Información del usuario:")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username or 'N/A'}")
        print(f"   Nombre: {user.first_name or 'N/A'}")
        print(f"   Puntos: {user.points}")
        print(f"   Nivel: {user.level}")
        print(f"   Rol: {user.role}")
        print(f"\n📊 Datos relacionados:")
        print(f"   Misiones completadas: {info['missions_completed']}")
        print(f"   Compras: {info['purchases']}")
        print(f"   Fragmentos narrativos: {info['lore_pieces']}")
        print(f"   Fragmentos visitados: {info['fragments_visited']}")

        confirm = input(f"\n⚠️  ¿Estás seguro de eliminar este usuario? (escribe 'SI' para confirmar): ")

        if confirm != "SI":
            print("❌ Cancelado")
            return

        # Eliminar
        await delete_user(session, user_id, dry_run=False)


async def main():
    """Función principal del script."""
    if len(sys.argv) == 1:
        # Modo interactivo
        await interactive_mode()
        return

    # Modo con argumentos
    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print(__doc__)
        return

    # Modo --info
    if sys.argv[1] == "--info":
        if len(sys.argv) < 3:
            print("Error: Debes proporcionar un user_id")
            print("Uso: python scripts/delete_user.py --info <user_id>")
            return

        user_id = int(sys.argv[2])
        await init_db()
        session_factory = get_session_factory()

        async with session_factory() as session:
            info = await get_user_info(session, user_id)
            if not info:
                print(f"❌ Usuario {user_id} no encontrado")
                return

            user = info["user"]
            print(f"\n📋 Usuario {user_id}:")
            print(f"   Username: {user.username or 'N/A'}")
            print(f"   Nombre: {user.first_name or 'N/A'}")
            print(f"   Puntos: {user.points}")
            print(f"   Nivel: {user.level}")
            print(f"   Rol: {user.role}")
            print(f"\n📊 Datos relacionados:")
            print(f"   Misiones completadas: {info['missions_completed']}")
            print(f"   Compras: {info['purchases']}")
            print(f"   Fragmentos narrativos: {info['lore_pieces']}")
            print(f"   Fragmentos visitados: {info['fragments_visited']}")
        return

    # Modo con user_ids directos
    user_ids = [int(uid) for uid in sys.argv[1:]]

    await init_db()
    session_factory = get_session_factory()

    for user_id in user_ids:
        async with session_factory() as session:
            await delete_user(session, user_id, dry_run=False)
            print("")  # Línea en blanco entre usuarios


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)
