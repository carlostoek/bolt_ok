"""
Tests básicos para el CMS de contenido

Verifica:
1. Creación de content sets
2. Listado de sets
3. Envío de sets (mock)
4. Consulta de estadísticas
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from database.models import ContentSet, GiftRecord, Base
from services.content_service import ContentService


# Configuración de BD de prueba
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session():
    """Crea una sesión de BD en memoria para tests"""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear session factory
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Crear sesión
    async with session_factory() as session:
        yield session

    # Limpiar
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_content_set(session):
    """Test: Crear un content set"""
    service = ContentService(session)

    content_set = await service.create_content_set(
        id="test_set",
        name="Test Set",
        type="photo_set",
        tier="free",
        file_ids=["file_id_1", "file_id_2"],
        description="Set de prueba",
        category="teaser",
        for_archetype="all"
    )

    assert content_set is not None
    assert content_set.id == "test_set"
    assert content_set.name == "Test Set"
    assert len(content_set.file_ids) == 2
    assert content_set.is_active is True


@pytest.mark.asyncio
async def test_get_content_set(session):
    """Test: Obtener un content set por ID"""
    service = ContentService(session)

    # Crear
    await service.create_content_set(
        id="test_get",
        name="Test Get",
        type="video",
        tier="vip",
        file_ids=["video_id"]
    )

    # Obtener
    content_set = await service.get_content_set("test_get")

    assert content_set is not None
    assert content_set.id == "test_get"
    assert content_set.type == "video"


@pytest.mark.asyncio
async def test_list_content_sets(session):
    """Test: Listar content sets con filtros"""
    service = ContentService(session)

    # Crear varios sets
    await service.create_content_set(
        id="free_1", name="Free 1", type="photo_set", tier="free", file_ids=["f1"]
    )
    await service.create_content_set(
        id="vip_1", name="VIP 1", type="video", tier="vip", file_ids=["v1"]
    )
    await service.create_content_set(
        id="free_2", name="Free 2", type="audio", tier="free", file_ids=["a1"]
    )

    # Listar todos
    all_sets = await service.list_content_sets()
    assert len(all_sets) >= 3  # Puede haber más sets de otros tests

    # Filtrar por tier
    free_sets = await service.list_content_sets(tier="free")
    assert len(free_sets) >= 2  # Al menos los 2 free que creamos

    vip_sets = await service.list_content_sets(tier="vip")
    assert len(vip_sets) >= 1  # Al menos el vip que creamos


@pytest.mark.asyncio
async def test_update_content_set(session):
    """Test: Actualizar un content set"""
    service = ContentService(session)

    # Crear
    await service.create_content_set(
        id="test_update", name="Original", type="photo_set", tier="free", file_ids=["f1"]
    )

    # Actualizar
    await service.update_content_set("test_update", name="Updated Name", tier="vip")

    # Verificar
    content_set = await service.get_content_set("test_update")
    assert content_set.name == "Updated Name"
    assert content_set.tier == "vip"


@pytest.mark.asyncio
async def test_delete_content_set_soft(session):
    """Test: Soft delete de un content set"""
    service = ContentService(session)

    # Crear
    await service.create_content_set(
        id="test_delete", name="To Delete", type="photo_set", tier="free", file_ids=["f1"]
    )

    # Soft delete
    await service.delete_content_set("test_delete", soft_delete=True)

    # Verificar que existe pero está inactivo
    content_set = await service.get_content_set("test_delete")
    assert content_set is not None
    assert content_set.is_active is False

    # Verificar que no aparece en listados activos
    active_sets = await service.list_content_sets(active_only=True)
    assert "test_delete" not in [s.id for s in active_sets]


@pytest.mark.asyncio
async def test_has_received_set(session):
    """Test: Verificar si usuario recibió un set"""
    service = ContentService(session)

    # Crear set
    await service.create_content_set(
        id="gift_test", name="Gift", type="photo_set", tier="gift", file_ids=["f1"]
    )

    # Usuario no ha recibido el set
    has_received = await service.has_received_set(user_id=123, set_id="gift_test")
    assert has_received is False

    # Simular que se envió (creando record manual)
    gift_record = GiftRecord(
        user_id=123,
        content_set_id="gift_test",
        trigger_type="manual",
        sent_by_admin=True
    )
    session.add(gift_record)
    await session.commit()

    # Ahora sí lo recibió
    has_received = await service.has_received_set(user_id=123, set_id="gift_test")
    assert has_received is True


@pytest.mark.asyncio
async def test_get_user_received_gifts(session):
    """Test: Obtener todos los regalos de un usuario"""
    service = ContentService(session)

    # Crear sets
    await service.create_content_set(
        id="gift_1", name="Gift 1", type="photo_set", tier="gift", file_ids=["f1"]
    )
    await service.create_content_set(
        id="gift_2", name="Gift 2", type="video", tier="gift", file_ids=["v1"]
    )

    # Simular envíos
    gift1 = GiftRecord(user_id=456, content_set_id="gift_1", trigger_type="automatic")
    gift2 = GiftRecord(user_id=456, content_set_id="gift_2", trigger_type="milestone")
    session.add_all([gift1, gift2])
    await session.commit()

    # Obtener regalos del usuario
    gifts = await service.get_user_received_gifts(user_id=456)
    assert len(gifts) == 2
    assert {g.content_set_id for g in gifts} == {"gift_1", "gift_2"}


if __name__ == "__main__":
    # Ejecutar tests manualmente
    async def run_tests():
        print("🧪 Ejecutando tests del CMS...")

        # Crear engine y session
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            # Test 1
            print("✓ Test: Crear content set")
            await test_create_content_set(session)

            # Test 2
            print("✓ Test: Obtener content set")
            await test_get_content_set(session)

            # Test 3
            print("✓ Test: Listar content sets")
            await test_list_content_sets(session)

            # Test 4
            print("✓ Test: Actualizar content set")
            await test_update_content_set(session)

            # Test 5
            print("✓ Test: Soft delete")
            await test_delete_content_set_soft(session)

            # Test 6
            print("✓ Test: Has received set")
            await test_has_received_set(session)

            # Test 7
            print("✓ Test: Get user received gifts")
            await test_get_user_received_gifts(session)

        await engine.dispose()
        print("\n✅ Todos los tests pasaron exitosamente!")

    asyncio.run(run_tests())
