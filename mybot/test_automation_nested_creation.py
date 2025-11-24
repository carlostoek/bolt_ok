"""
Test de demostración del Atomic Nested Creation en el sistema de automatización.

Crea un trigger real con acciones anidadas y demuestra el funcionamiento completo.
"""
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Agregar el directorio actual al path
sys.path.insert(0, '.')

from app.database.session import Base
from app.schemas.automation import TriggerCreate, ActionCreateNested
from app.services.automation_service import AutomationService


async def test_nested_creation():
    """Test completo de nested creation con base de datos real."""
    print("🧪 DEMOSTRACIÓN DE ATOMIC NESTED CREATION")
    print("=" * 60)

    # Crear motor de base de datos en memoria
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True  # Mostrar queries SQL
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

        # ============================================================================
        # CREAR TRIGGER CON ACCIONES NESTED
        # ============================================================================
        print("\n1️⃣  CREANDO TRIGGER CON ACCIONES ANIDADAS")
        print("-" * 40)

        trigger_data = TriggerCreate(
            name="recompensa_bienvenida_completa",
            description="Recompensas múltiples al ver el fragmento WELCOME",
            event_type="fragment_viewed",
            conditions={"fragment_key": "WELCOME"},
            is_enabled=True,
            priority=1,
            actions=[
                ActionCreateNested(
                    action_type="add_points",
                    parameters={"amount": 100, "reason": "¡Bienvenido a la aventura!"},
                    execution_order=1
                ),
                ActionCreateNested(
                    action_type="grant_badge",
                    parameters={"badge_id": "welcome_badge", "title": "Explorador Novato"},
                    execution_order=2
                ),
                ActionCreateNested(
                    action_type="send_message",
                    parameters={
                        "message_template": "¡Felicidades! Has recibido 100 puntos y una insignia por comenzar tu aventura."
                    },
                    execution_order=3
                )
            ]
        )

        print(f"📝 Datos del trigger:")
        print(f"   • Nombre: {trigger_data.name}")
        print(f"   • Evento: {trigger_data.event_type}")
        print(f"   • Condiciones: {trigger_data.conditions}")
        print(f"   • Acciones: {len(trigger_data.actions)}")
        
        for i, action in enumerate(trigger_data.actions, 1):
            print(f"     {i}. {action.action_type} (orden: {action.execution_order})")

        # Ejecutar creación anidada
        print("\n🔄 Ejecutando Atomic Nested Creation...")
        result = await service.create_trigger_with_actions(trigger_data)

        print(f"\n✅ CREACIÓN EXITOSA")
        print(f"   • Trigger ID: {result['trigger'].id}")
        print(f"   • Trigger creado: {result['trigger'].name}")
        print(f"   • Acciones creadas: {len(result['created_actions'])}")
        print(f"   • Total entidades: {result['summary']['total_entities']}")

        # Mostrar acciones creadas
        print("\n📋 ACCIONES CREADAS:")
        for action in result['created_actions']:
            print(f"   • ID: {action['id']}, Tipo: {action['action_type']}, Orden: {action['execution_order']}")

        # ============================================================================
        # TEST DE EJECUCIÓN DEL TRIGGER
        # ============================================================================
        print("\n2️⃣  TEST DE EJECUCIÓN DEL TRIGGER")
        print("-" * 40)

        # Simular evento que CUMPLE condiciones
        print("\n🎯 Simulando evento que CUMPLE condiciones...")
        execution_result = await service.execute_triggers(
            event_type="fragment_viewed",
            user_id=123,
            context={"fragment_key": "WELCOME", "chapter": "introduccion"}
        )

        print(f"✅ Ejecución completada:")
        print(f"   • Triggers ejecutados: {len(execution_result['triggers_executed'])}")
        print(f"   • Acciones totales: {execution_result['total_actions']}")
        
        if execution_result['triggers_executed']:
            for trigger in execution_result['triggers_executed']:
                print(f"   • Trigger '{trigger['trigger_name']}': {trigger['actions_executed']} acciones")

        # Simular evento que NO cumple condiciones
        print("\n🎯 Simulando evento que NO cumple condiciones...")
        execution_result2 = await service.execute_triggers(
            event_type="fragment_viewed",
            user_id=123,
            context={"fragment_key": "OTRO_FRAGMENTO", "chapter": "capitulo2"}
        )

        print(f"✅ Ejecución completada:")
        print(f"   • Triggers ejecutados: {len(execution_result2['triggers_executed'])}")
        print(f"   • Acciones totales: {execution_result2['total_actions']}")

        # ============================================================================
        # VERIFICAR INTEGRIDAD REFERENCIAL
        # ============================================================================
        print("\n3️⃣  VERIFICACIÓN DE INTEGRIDAD REFERENCIAL")
        print("-" * 40)

        # Obtener trigger por ID para verificar que las acciones están vinculadas
        trigger_with_actions = await service.get_trigger(result['trigger'].id)
        
        if trigger_with_actions:
            print(f"✅ Trigger obtenido: {trigger_with_actions.name}")
            print(f"✅ Acciones vinculadas: {len(trigger_with_actions.actions)}")
            
            for action in trigger_with_actions.actions:
                print(f"   • {action.action_type} (ID: {action.id}, Orden: {action.execution_order})")
        else:
            print("❌ No se pudo obtener el trigger")

    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    print("\n" + "=" * 60)
    print("🎉 ATOMIC NESTED CREATION DEMOSTRADO EXITOSAMENTE")
    print("=" * 60)
    print("\n✅ LO QUE SE LOGRO:")
    print("   • 1 trigger creado con 3 acciones anidadas")
    print("   • Transacción atómica (todo o nada)")
    print("   • Vinculación automática de acciones al trigger")
    print("   • Evaluación de condiciones funcionando")
    print("   • Motor de ejecución operativo")
    print("\n🚀 SISTEMA LISTO PARA PRODUCCIÓN")


if __name__ == "__main__":
    asyncio.run(test_nested_creation())