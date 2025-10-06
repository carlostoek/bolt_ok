"""
Script para crear content sets por defecto del journey

Crea los 3 content sets mínimos necesarios:
- day_1_welcome (obligatorio)
- day_7_vip_teaser (opcional)
- day_30_vip_gift (opcional)

NOTA: Los file_ids deben ser reemplazados por IDs reales de Telegram.
Este script crea placeholders que deben ser actualizados desde el admin panel.
"""
import asyncio
import os
import sys

# Set minimal env vars BEFORE any imports
if not os.environ.get('BOT_TOKEN'):
    os.environ['BOT_TOKEN'] = 'script_token'

# Agregar path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.setup import init_db, get_session_factory
from services.content_service import ContentService


async def create_default_content_sets():
    """Crea los content sets por defecto del journey"""

    # Inicializar BD
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as session:
        content_service = ContentService(session)

        print("🔄 Creando content sets por defecto del journey...\n")

        # 1. Day 1 Welcome (OBLIGATORIO)
        try:
            existing = await content_service.get_content_set("day_1_welcome")
            if existing:
                print("✓ day_1_welcome ya existe")
            else:
                await content_service.create_content_set(
                    id="day_1_welcome",
                    name="Primera Mirada - Bienvenida",
                    type="photo_set",
                    tier="gift",
                    file_ids=[],  # Placeholder - debe ser llenado desde admin
                    description="Set de bienvenida para nuevos usuarios (Day 1)",
                    category="welcome",
                    for_archetype="all"
                )
                print("✅ day_1_welcome creado (sin archivos - agregar desde admin panel)")
        except Exception as e:
            print(f"❌ Error creando day_1_welcome: {e}")

        # 2. Day 7 VIP Teaser (OPCIONAL)
        try:
            existing = await content_service.get_content_set("day_7_vip_teaser")
            if existing:
                print("✓ day_7_vip_teaser ya existe")
            else:
                await content_service.create_content_set(
                    id="day_7_vip_teaser",
                    name="Teaser VIP - Día 7",
                    type="photo_set",
                    tier="gift",
                    file_ids=[],  # Placeholder
                    description="Teaser para oferta VIP día 7 (opcional)",
                    category="teaser",
                    for_archetype="all"
                )
                print("✅ day_7_vip_teaser creado (OPCIONAL - sin archivos)")
        except Exception as e:
            print(f"⚠️  Error creando day_7_vip_teaser (opcional): {e}")

        # 3. Day 30 VIP Gift (OPCIONAL)
        try:
            existing = await content_service.get_content_set("day_30_vip_gift")
            if existing:
                print("✓ day_30_vip_gift ya existe")
            else:
                await content_service.create_content_set(
                    id="day_30_vip_gift",
                    name="Regalo Especial - Mes 1",
                    type="photo_set",
                    tier="gift",
                    file_ids=[],  # Placeholder
                    description="Regalo para VIPs al mes de suscripción (opcional)",
                    category="gift",
                    for_archetype="all"
                )
                print("✅ day_30_vip_gift creado (OPCIONAL - sin archivos)")
        except Exception as e:
            print(f"⚠️  Error creando day_30_vip_gift (opcional): {e}")

        print("\n🎉 Content sets del journey creados!")
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Accede al admin panel: /admin → CMS Journey")
        print("2. Ve a 'Ver Sets' y selecciona cada set")
        print("3. Edita cada set y sube los archivos reales (fotos/videos)")
        print("4. Los sets sin archivos no se enviarán (sistema tolerante a errores)")


if __name__ == "__main__":
    asyncio.run(create_default_content_sets())
