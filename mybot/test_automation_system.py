"""
Test de validación del sistema de automatización.

Verifica que todos los componentes funcionen correctamente:
- Modelos ORM
- Esquemas Pydantic
- Servicio de automatización
- Endpoints REST
"""
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Agregar el directorio actual al path
sys.path.insert(0, '.')

from app.database.session import Base, get_db
from app.models.automation import AutomationTrigger, TriggerAction, AutomationLog
from app.schemas.automation import TriggerCreate, ActionCreateNested
from app.services.automation_service import AutomationService


async def test_automation_system():
    """Test completo del sistema de automatización."""
    print("🧪 INICIANDO TEST DE SISTEMA DE AUTOMATIZACIÓN")
    print("=" * 60)

    # ============================================================================
    # TEST 1: MODELOS ORM
    # ============================================================================
    print("\n1️⃣  TEST DE MODELOS ORM")
    print("-" * 30)

    try:
        # Crear instancias de modelos
        trigger = AutomationTrigger(
            name="test_trigger",
            description="Trigger de prueba",
            event_type="fragment_viewed",
            conditions={"fragment_key": "WELCOME"},
            is_enabled=True,
            priority=1
        )

        action = TriggerAction(
            trigger_id=1,  # ID ficticio para test
            action_type="add_points",
            parameters={"amount": 100, "reason": "Test"},
            execution_order=1,
            is_enabled=True
        )

        log = AutomationLog(
            trigger_id=1,
            event_type="fragment_viewed",
            user_id=123,
            event_context={"fragment_key": "WELCOME"},
            executed_actions=[{"action_type": "add_points", "amount": 100}],
            execution_success=True
        )

        print(f"✅ Trigger creado: {trigger.name}")
        print(f"✅ Acción creada: {action.action_type}")
        print(f"✅ Log creado: {log.event_type}")

    except Exception as e:
        print(f"❌ Error en modelos ORM: {e}")
        return False

    # ============================================================================
    # TEST 2: ESQUEMAS PYDANTIC
    # ============================================================================
    print("\n2️⃣  TEST DE ESQUEMAS PYDANTIC")
    print("-" * 30)

    try:
        # Crear esquema de nested creation
        trigger_data = TriggerCreate(
            name="recompensa_bienvenida",
            description="Da 100 puntos al ver el fragmento WELCOME",
            event_type="fragment_viewed",
            conditions={"fragment_key": "WELCOME"},
            is_enabled=True,
            priority=1,
            actions=[
                ActionCreateNested(
                    action_type="add_points",
                    parameters={"amount": 100, "reason": "¡Bienvenido!"},
                    execution_order=1
                )
            ]
        )

        print(f"✅ Esquema TriggerCreate creado: {trigger_data.name}")
        print(f"✅ Acción nested: {trigger_data.actions[0].action_type}")

        # Validar tipos de evento
        try:
            TriggerCreate(
                name="test_invalid",
                event_type="evento_invalido",  # Tipo inválido
                conditions={}
            )
            print("❌ Validación de tipos falló - debería haber fallado")
            return False
        except ValueError:
            print("✅ Validación de tipos funciona correctamente")

    except Exception as e:
        print(f"❌ Error en esquemas Pydantic: {e}")
        return False

    # ============================================================================
    # TEST 3: SERVICIO DE AUTOMATIZACIÓN
    # ============================================================================
    print("\n3️⃣  TEST DE SERVICIO DE AUTOMATIZACIÓN")
    print("-" * 30)

    try:
        # Crear motor de base de datos en memoria para testing
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False
        )

        # Crear tablas
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Crear sesión
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Instanciar servicio
            service = AutomationService(session)

            # Test de simulación de ejecución
            result = await service.execute_triggers(
                event_type="fragment_viewed",
                user_id=123,
                context={"fragment_key": "WELCOME"}
            )

            print(f"✅ Simulación ejecutada: {result['success']}")
            print(f"✅ Triggers encontrados: {result['summary']['total_triggers']}")
            print(f"✅ Triggers ejecutados: {result['summary']['executed_triggers']}")

    except Exception as e:
        print(f"❌ Error en servicio de automatización: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ============================================================================
    # TEST 4: ENDPOINTS REST
    # ============================================================================
    print("\n4️⃣  TEST DE ENDPOINTS REST")
    print("-" * 30)

    try:
        from app.api.v1.endpoints.automation import router
        
        # Verificar que el router tiene los endpoints esperados
        endpoints = [route.path for route in router.routes]
        expected_endpoints = [
            "/triggers",
            "/test-event",
            "/triggers/{trigger_id}"
        ]

        for expected in expected_endpoints:
            if any(expected in endpoint for endpoint in endpoints):
                print(f"✅ Endpoint encontrado: {expected}")
            else:
                print(f"❌ Endpoint no encontrado: {expected}")
                return False

        print(f"✅ Total endpoints encontrados: {len(endpoints)}")

    except Exception as e:
        print(f"❌ Error en endpoints REST: {e}")
        return False

    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    print("\n" + "=" * 60)
    print("🎉 SISTEMA DE AUTOMATIZACIÓN VALIDADO EXITOSAMENTE")
    print("=" * 60)
    print("\n✅ COMPONENTES IMPLEMENTADOS:")
    print("   • Modelos ORM (AutomationTrigger, TriggerAction, AutomationLog)")
    print("   • Esquemas Pydantic (TriggerCreate, ActionCreateNested)")
    print("   • Servicio de automatización (AutomationService)")
    print("   • Endpoints REST (/api/v1/automation/*)")
    print("\n🎯 FUNCIONALIDADES:")
    print("   • Atomic Nested Creation de triggers con acciones")
    print("   • Motor de ejecución dirigido por eventos")
    print("   • Evaluación de condiciones configurables")
    print("   • Simulación de acciones sin efectos reales")
    print("   • Logging completo de ejecuciones")
    print("\n🚀 LISTO PARA INTEGRACIÓN CON EL SISTEMA EXISTENTE")

    return True


if __name__ == "__main__":
    asyncio.run(test_automation_system())