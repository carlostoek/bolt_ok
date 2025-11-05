#!/usr/bin/env python3
"""
Script unificado para gestión de usuarios y narrativa.

Este script combina las funcionalidades de:
- Reiniciar progreso narrativo de usuarios (parcial o total)
- Eliminar usuarios completamente de la base de datos
- Limpiar fragmentos narrativos de la base de datos para cambio de narrativa

OPCIONES DISPONIBLES:
1. Ver información de un usuario
2. Reiniciar progreso narrativo de un usuario (mantiene el usuario)
3. Reiniciar progreso narrativo de TODOS los usuarios
4. Eliminar usuario completamente (usuario + todos sus datos)
5. Limpiar TODOS los fragmentos narrativos (para cambio de narrativa)
6. Ver estadísticas generales

Uso:
    # Modo interactivo:
    python scripts/manage_users.py

    # Ver información de un usuario:
    python scripts/manage_users.py --info <user_id>

    # Reiniciar progreso narrativo de un usuario:
    python scripts/manage_users.py --reset-narrative <user_id>

    # Eliminar usuario completamente:
    python scripts/manage_users.py --delete-user <user_id>

    # Limpiar todos los fragmentos narrativos:
    python scripts/manage_users.py --clear-fragments
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import init_db, get_session_factory
from database.models import (
    User, UserMissionEntry, UserPurchase, UserAchievement,
    UserLorePiece, ButtonReaction, UserReward, UserMilestone,
    UserBadge, UserStats, UserChallengeProgress
)
from database.narrative_models import UserNarrativeState, StoryFragment, NarrativeChoice
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# FUNCIONES DE INFORMACIÓN Y ESTADÍSTICAS
# ============================================================================

async def get_user_info(session: AsyncSession, user_id: int) -> dict:
    """Obtiene información completa del usuario."""
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
        "fragments_visited": narrative_state.fragments_visited if narrative_state else 0,
        "current_fragment": narrative_state.current_fragment_key if narrative_state else None
    }


async def show_user_info(session: AsyncSession, user_id: int):
    """Muestra información detallada de un usuario."""
    info = await get_user_info(session, user_id)

    if not info:
        logger.error(f"❌ Usuario {user_id} no encontrado")
        return False

    user = info["user"]
    print("\n" + "="*70)
    print(f"📋 INFORMACIÓN DEL USUARIO {user_id}")
    print("="*70)
    print(f"👤 Username: {user.username or 'N/A'}")
    print(f"👤 Nombre: {user.first_name or 'N/A'}")
    print(f"💎 Puntos: {user.points}")
    print(f"⭐ Nivel: {user.level}")
    print(f"🎭 Rol: {user.role}")
    print(f"\n📊 DATOS RELACIONADOS:")
    print(f"   ✅ Misiones completadas: {info['missions_completed']}")
    print(f"   🛒 Compras realizadas: {info['purchases']}")
    print(f"   📜 Fragmentos narrativos desbloqueados: {info['lore_pieces']}")
    print(f"   📖 Progreso narrativo: {'Sí' if info['has_narrative_progress'] else 'No'}")
    if info['has_narrative_progress']:
        print(f"   📍 Fragmento actual: {info['current_fragment']}")
        print(f"   🗺️  Fragmentos visitados: {info['fragments_visited']}")
    print("="*70 + "\n")
    return True


async def show_general_stats(session: AsyncSession):
    """Muestra estadísticas generales del sistema."""
    # Contar usuarios
    users_result = await session.execute(select(User))
    total_users = len(users_result.scalars().all())

    # Contar usuarios con progreso narrativo
    narrative_result = await session.execute(select(UserNarrativeState))
    users_with_narrative = len(narrative_result.scalars().all())

    # Contar fragmentos narrativos
    fragments_result = await session.execute(select(StoryFragment))
    total_fragments = len(fragments_result.scalars().all())

    # Contar decisiones narrativas
    choices_result = await session.execute(select(NarrativeChoice))
    total_choices = len(choices_result.scalars().all())

    print("\n" + "="*70)
    print("📊 ESTADÍSTICAS GENERALES DEL SISTEMA")
    print("="*70)
    print(f"👥 Total de usuarios: {total_users}")
    print(f"📖 Usuarios con progreso narrativo: {users_with_narrative}")
    print(f"📚 Total de fragmentos narrativos en BD: {total_fragments}")
    print(f"🔀 Total de decisiones narrativas en BD: {total_choices}")
    print("="*70 + "\n")


# ============================================================================
# FUNCIONES DE REINICIO DE PROGRESO NARRATIVO
# ============================================================================

async def reset_user_narrative(session: AsyncSession, user_id: int) -> bool:
    """Reinicia el progreso narrativo de un usuario específico."""
    # Verificar que el usuario existe
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"❌ Usuario {user_id} no encontrado")
        return False

    logger.info(f"🔄 Reiniciando progreso narrativo para usuario {user_id}...")

    # Eliminar estado narrativo
    stmt = delete(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
    result = await session.execute(stmt)

    await session.commit()

    if result.rowcount > 0:
        logger.info(f"✅ Progreso narrativo reiniciado para usuario {user_id}")
    else:
        logger.info(f"ℹ️  Usuario {user_id} no tenía progreso narrativo")

    return True


async def reset_all_narratives(session: AsyncSession) -> bool:
    """Reinicia el progreso narrativo de TODOS los usuarios."""
    logger.info("🔄 Reiniciando progreso narrativo para TODOS los usuarios...")

    result = await session.execute(
        text("DELETE FROM user_narrative_states")
    )
    deleted_count = result.rowcount

    await session.commit()

    logger.info(f"✅ Progreso narrativo reiniciado para {deleted_count} usuarios")
    return True


# ============================================================================
# FUNCIONES DE ELIMINACIÓN DE USUARIOS
# ============================================================================

async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """
    Elimina un usuario y todos sus datos relacionados de forma permanente.

    Args:
        session: Sesión de base de datos
        user_id: ID del usuario a eliminar

    Returns:
        True si se eliminó exitosamente, False si no se encontró
    """
    # Verificar que el usuario existe
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"❌ Usuario {user_id} no encontrado")
        return False

    logger.info(f"🗑️  Eliminando usuario {user_id} ({user.username or user.first_name})...")

    deleted_counts = {}

    # Eliminar todos los datos relacionados
    tables = [
        (UserMissionEntry, "missions"),
        (UserPurchase, "purchases"),
        (UserAchievement, "achievements"),
        (UserLorePiece, "lore_pieces"),
        (UserNarrativeState, "narrative_state"),
        (ButtonReaction, "reactions"),
        (UserReward, "rewards"),
        (UserMilestone, "milestones"),
        (UserBadge, "badges"),
        (UserStats, "stats"),
        (UserChallengeProgress, "challenges")
    ]

    for model, name in tables:
        stmt = delete(model).where(model.user_id == user_id)
        result = await session.execute(stmt)
        deleted_counts[name] = result.rowcount

    # Eliminar usuario
    await session.delete(user)
    deleted_counts["user"] = 1

    await session.commit()

    # Mostrar resumen
    logger.info("\n📊 Resumen de eliminación:")
    for key, count in deleted_counts.items():
        if count > 0:
            logger.info(f"   {key}: {count}")

    logger.info(f"\n✅ Usuario {user_id} eliminado completamente")
    return True


# ============================================================================
# FUNCIONES DE LIMPIEZA DE FRAGMENTOS NARRATIVOS
# ============================================================================

async def clear_all_fragments(session: AsyncSession) -> bool:
    """
    Elimina TODOS los fragmentos narrativos y decisiones de la base de datos.
    Esta función es útil cuando necesitas cambiar completamente de narrativa.

    ADVERTENCIA: Esta operación también reiniciará el progreso de todos los usuarios
    ya que los fragmentos quedarán inválidos.
    """
    logger.info("🧹 Iniciando limpieza completa de fragmentos narrativos...")

    # Primero, reiniciar todos los estados narrativos de usuarios
    logger.info("   Paso 1/3: Reiniciando estados narrativos de usuarios...")
    result1 = await session.execute(text("DELETE FROM user_narrative_states"))
    users_reset = result1.rowcount
    logger.info(f"      ✓ {users_reset} estados de usuario reiniciados")

    # Eliminar todas las decisiones narrativas
    logger.info("   Paso 2/3: Eliminando decisiones narrativas...")
    result2 = await session.execute(text("DELETE FROM narrative_choices"))
    choices_deleted = result2.rowcount
    logger.info(f"      ✓ {choices_deleted} decisiones eliminadas")

    # Eliminar todos los fragmentos
    logger.info("   Paso 3/3: Eliminando fragmentos narrativos...")
    result3 = await session.execute(text("DELETE FROM story_fragments"))
    fragments_deleted = result3.rowcount
    logger.info(f"      ✓ {fragments_deleted} fragmentos eliminados")

    await session.commit()

    print("\n" + "="*70)
    print("✅ LIMPIEZA COMPLETA DE NARRATIVA FINALIZADA")
    print("="*70)
    print(f"📊 Resumen:")
    print(f"   - Fragmentos eliminados: {fragments_deleted}")
    print(f"   - Decisiones eliminadas: {choices_deleted}")
    print(f"   - Estados de usuario reiniciados: {users_reset}")
    print("\n⚠️  La base de datos está lista para una nueva narrativa.")
    print("   Puedes cargar los nuevos fragmentos cuando estés listo.")
    print("="*70 + "\n")

    return True


# ============================================================================
# MODO INTERACTIVO
# ============================================================================

async def interactive_mode():
    """Modo interactivo con menú de opciones."""
    session_factory = get_session_factory()

    while True:
        print("\n" + "="*70)
        print("🛠️  GESTIÓN DE USUARIOS Y NARRATIVA")
        print("="*70)
        print("\n📋 OPCIONES DISPONIBLES:\n")
        print("  1️⃣  Ver información de un usuario")
        print("  2️⃣  Reiniciar progreso narrativo de un usuario")
        print("  3️⃣  Reiniciar progreso narrativo de TODOS los usuarios")
        print("  4️⃣  Eliminar usuario completamente")
        print("  5️⃣  Limpiar TODOS los fragmentos narrativos (cambio de narrativa)")
        print("  6️⃣  Ver estadísticas generales")
        print("  0️⃣  Salir")
        print("\n" + "="*70)

        choice = input("\n👉 Selecciona una opción (0-6): ").strip()

        if choice == "0":
            print("\n👋 ¡Hasta luego!")
            break

        elif choice == "1":
            # Ver información de un usuario
            try:
                user_id = int(input("\n👤 Ingresa el ID del usuario: ").strip())
                async with session_factory() as session:
                    await show_user_info(session, user_id)
            except ValueError:
                logger.error("❌ ID inválido")

        elif choice == "2":
            # Reiniciar progreso narrativo de un usuario
            try:
                user_id = int(input("\n👤 Ingresa el ID del usuario: ").strip())
                async with session_factory() as session:
                    await show_user_info(session, user_id)
                    confirm = input("\n⚠️  ¿Reiniciar progreso narrativo de este usuario? (SI/no): ").strip()
                    if confirm.upper() == "SI":
                        await reset_user_narrative(session, user_id)
                    else:
                        logger.info("❌ Operación cancelada")
            except ValueError:
                logger.error("❌ ID inválido")

        elif choice == "3":
            # Reiniciar progreso narrativo de TODOS
            async with session_factory() as session:
                await show_general_stats(session)
                confirm = input("\n⚠️  ¿Reiniciar progreso narrativo de TODOS los usuarios? (escribe 'SI TODOS'): ").strip()
                if confirm == "SI TODOS":
                    await reset_all_narratives(session)
                else:
                    logger.info("❌ Operación cancelada")

        elif choice == "4":
            # Eliminar usuario completamente
            try:
                user_id = int(input("\n👤 Ingresa el ID del usuario: ").strip())
                async with session_factory() as session:
                    await show_user_info(session, user_id)
                    confirm = input("\n⚠️  ¿ELIMINAR COMPLETAMENTE este usuario? (escribe 'ELIMINAR'): ").strip()
                    if confirm == "ELIMINAR":
                        await delete_user(session, user_id)
                    else:
                        logger.info("❌ Operación cancelada")
            except ValueError:
                logger.error("❌ ID inválido")

        elif choice == "5":
            # Limpiar todos los fragmentos
            async with session_factory() as session:
                await show_general_stats(session)
                print("\n⚠️  ADVERTENCIA: Esta operación eliminará:")
                print("   - TODOS los fragmentos narrativos de la base de datos")
                print("   - TODAS las decisiones narrativas")
                print("   - Reiniciará el progreso de TODOS los usuarios")
                print("\n   Esta operación es útil cuando vas a cambiar de narrativa.")
                confirm = input("\n⚠️  ¿Continuar con la limpieza completa? (escribe 'LIMPIAR TODO'): ").strip()
                if confirm == "LIMPIAR TODO":
                    await clear_all_fragments(session)
                else:
                    logger.info("❌ Operación cancelada")

        elif choice == "6":
            # Ver estadísticas
            async with session_factory() as session:
                await show_general_stats(session)

        else:
            logger.error("❌ Opción inválida")

        input("\n⏎ Presiona Enter para continuar...")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

async def main():
    """Función principal del script."""
    await init_db()

    # Modo con argumentos
    if len(sys.argv) > 1:
        session_factory = get_session_factory()

        if sys.argv[1] in ["--help", "-h"]:
            print(__doc__)
            return

        elif sys.argv[1] == "--info":
            if len(sys.argv) < 3:
                logger.error("❌ Debes proporcionar un user_id")
                logger.info("Uso: python scripts/manage_users.py --info <user_id>")
                return

            user_id = int(sys.argv[2])
            async with session_factory() as session:
                await show_user_info(session, user_id)

        elif sys.argv[1] == "--reset-narrative":
            if len(sys.argv) < 3:
                logger.error("❌ Debes proporcionar un user_id")
                logger.info("Uso: python scripts/manage_users.py --reset-narrative <user_id>")
                return

            user_id = int(sys.argv[2])
            async with session_factory() as session:
                await reset_user_narrative(session, user_id)

        elif sys.argv[1] == "--delete-user":
            if len(sys.argv) < 3:
                logger.error("❌ Debes proporcionar un user_id")
                logger.info("Uso: python scripts/manage_users.py --delete-user <user_id>")
                return

            user_id = int(sys.argv[2])
            async with session_factory() as session:
                await show_user_info(session, user_id)
                confirm = input("\n⚠️  ¿ELIMINAR COMPLETAMENTE este usuario? (escribe 'ELIMINAR'): ").strip()
                if confirm == "ELIMINAR":
                    await delete_user(session, user_id)
                else:
                    logger.info("❌ Operación cancelada")

        elif sys.argv[1] == "--clear-fragments":
            async with session_factory() as session:
                await show_general_stats(session)
                print("\n⚠️  ADVERTENCIA: Esta operación eliminará TODOS los fragmentos narrativos")
                confirm = input("\n⚠️  ¿Continuar? (escribe 'LIMPIAR TODO'): ").strip()
                if confirm == "LIMPIAR TODO":
                    await clear_all_fragments(session)
                else:
                    logger.info("❌ Operación cancelada")

        elif sys.argv[1] == "--stats":
            async with session_factory() as session:
                await show_general_stats(session)

        else:
            logger.error(f"❌ Opción desconocida: {sys.argv[1]}")
            logger.info("Usa --help para ver las opciones disponibles")

    else:
        # Modo interactivo
        await interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        sys.exit(1)
