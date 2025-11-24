"""
Servicio de lógica de negocio para el sistema de automatización dirigido por eventos.

Motor de ejecución que reemplaza la lógica hardcodeada con automatizaciones configurables.
"""
import logging
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_

from app.models.automation import (
    AutomationTrigger, 
    TriggerAction, 
    AutomationLog,
    TriggerEventType,
    ActionType
)
from app.schemas.automation import (
    TriggerCreate,
    TriggerUpdate,
    TriggerResponse,
    TriggerCreateResponse,
    ActionCreateNested,
    ActionUpdate
)
from app.core.exceptions import (
    DatabaseException,
    DuplicateKeyException,
    TriggerNotFoundException,
    NestedCreationException
)

logger = logging.getLogger(__name__)


class AutomationService:
    """
    Servicio para gestionar automatizaciones dirigidas por eventos.

    Implementa:
    - Creación transaccional de triggers con acciones
    - Motor de ejecución de eventos
    - Evaluación de condiciones
    - Simulación de acciones
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db

    async def create_trigger_with_actions(
        self,
        data: TriggerCreate
    ) -> Dict[str, Any]:
        """
        Crea un trigger de automatización con todas sus acciones anidadas.

        PATRÓN ATOMIC NESTED CREATION:
        1. Crear trigger principal → flush() → obtener ID
        2. Crear acciones nested → flush() → obtener IDs
        3. Commit único y atómico

        Args:
            data: Esquema de creación con soporte de nested entities

        Returns:
            Dict con el trigger creado y resumen de acciones

        Raises:
            DuplicateKeyException: Si el nombre del trigger ya existe
            NestedCreationException: Si falla la creación de acciones
            DatabaseException: Si falla el commit de la transacción
        """
        try:
            logger.info(f"→ Iniciando creación de trigger: '{data.name}'")

            # Variables para tracking
            created_actions: List[TriggerAction] = []

            # ================================================================
            # PASO 1: CREAR TRIGGER PRINCIPAL
            # ================================================================
            logger.info(f"  → Creando trigger principal: '{data.name}'")

            try:
                trigger = AutomationTrigger(
                    name=data.name,
                    description=data.description,
                    event_type=data.event_type,
                    conditions=data.conditions or {},
                    is_enabled=data.is_enabled,
                    priority=data.priority
                )

                self.db.add(trigger)
                await self.db.flush()  # ← CRÍTICO: Obtener ID sin commit

                logger.info(f"    ✓ Trigger creado con ID: {trigger.id}")

            except IntegrityError as e:
                if "unique constraint" in str(e).lower():
                    raise DuplicateKeyException(data.name)
                raise DatabaseException(f"Error de integridad: {str(e)}")

            # ================================================================
            # PASO 2: CREAR ACCIONES NESTED
            # ================================================================
            if data.actions:
                logger.info(f"  → Procesando {len(data.actions)} acciones...")

                for idx, action_data in enumerate(data.actions, start=1):
                    try:
                        action = TriggerAction(
                            trigger_id=trigger.id,
                            action_type=action_data.action_type,
                            parameters=action_data.parameters or {},
                            execution_order=action_data.execution_order,
                            is_enabled=action_data.is_enabled
                        )

                        self.db.add(action)
                        created_actions.append(action)

                        logger.info(
                            f"    ✓ Acción #{idx} creada: '{action.action_type}' "
                            f"(orden: {action.execution_order})"
                        )

                    except Exception as e:
                        raise NestedCreationException(
                            f"Error en acción #{idx}: {str(e)}",
                            nested_entity="acción"
                        )

            # ================================================================
            # PASO 3: COMMIT ÚNICO Y ATÓMICO
            # ================================================================
            logger.info("  → Ejecutando commit atómico...")
            await self.db.commit()
            logger.info("    ✅ COMMIT EXITOSO - Todas las entidades creadas")

            # ================================================================
            # PASO 4: REFRESH PARA CARGAR RELACIONES
            # ================================================================
            await self.db.refresh(trigger, ['actions'])

            # ================================================================
            # CONSTRUIR RESPUESTA CON RESUMEN
            # ================================================================
            return {
                "success": True,
                "trigger": TriggerResponse.model_validate(trigger),
                "created_actions": [
                    {
                        "id": action.id,
                        "action_type": action.action_type,
                        "execution_order": action.execution_order
                    }
                    for action in created_actions
                ],
                "summary": {
                    "trigger_created": True,
                    "actions_created": len(created_actions),
                    "total_entities": 1 + len(created_actions)
                }
            }

        except (DuplicateKeyException, NestedCreationException, DatabaseException):
            # Re-raise las excepciones específicas
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error inesperado al crear trigger: {str(e)}")
            raise DatabaseException(f"Error inesperado: {str(e)}")

    async def execute_triggers(
        self,
        event_type: str,
        user_id: int,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta todos los triggers activos para un tipo de evento específico.

        Este es el CEREBRO del sistema de automatización:
        1. Busca triggers activos para el event_type
        2. Evalúa las condiciones de cada trigger
        3. Si cumple, ejecuta las acciones asociadas
        4. Registra logs de ejecución

        Args:
            event_type: Tipo de evento que se está ejecutando
            user_id: ID del usuario que dispara el evento
            context: Contexto adicional del evento (ej: fragment_key, product_id, etc.)

        Returns:
            Dict con resumen de ejecución
        """
        context = context or {}
        executed_triggers = []
        total_actions = 0

        try:
            logger.info(
                f"→ Ejecutando triggers para evento: '{event_type}' "
                f"(usuario: {user_id}, contexto: {context})"
            )

            # ================================================================
            # PASO 1: BUSCAR TRIGGERS ACTIVOS
            # ================================================================
            stmt = select(AutomationTrigger).where(
                and_(
                    AutomationTrigger.event_type == event_type,
                    AutomationTrigger.is_enabled == True
                )
            ).order_by(AutomationTrigger.priority.desc())

            result = await self.db.execute(stmt)
            triggers = result.scalars().all()

            logger.info(f"  → Encontrados {len(triggers)} triggers activos")

            # ================================================================
            # PASO 2: EVALUAR CADA TRIGGER
            # ================================================================
            for trigger in triggers:
                try:
                    # Evaluar condiciones del trigger
                    conditions_met = await self._evaluate_conditions(
                        trigger.conditions, 
                        context
                    )

                    if not conditions_met:
                        logger.info(f"    ⏭️  Trigger '{trigger.name}' no cumple condiciones")
                        continue

                    logger.info(f"    ✅ Trigger '{trigger.name}' cumple condiciones")

                    # ========================================================
                    # PASO 3: EJECUTAR ACCIONES DEL TRIGGER
                    # ========================================================
                    trigger_actions = []
                    
                    # Ordenar acciones por execution_order
                    sorted_actions = sorted(
                        trigger.actions, 
                        key=lambda a: a.execution_order
                    )

                    for action in sorted_actions:
                        if not action.is_enabled:
                            logger.info(f"      ⏭️  Acción '{action.action_type}' deshabilitada")
                            continue

                        # Simular ejecución de la acción
                        action_result = await self._simulate_action_execution(
                            action, 
                            user_id, 
                            context
                        )

                        trigger_actions.append(action_result)
                        total_actions += 1

                        logger.info(
                            f"      🎯 Acción ejecutada: '{action.action_type}' "
                            f"→ {action_result['simulation']}"
                        )

                    # ========================================================
                    # PASO 4: REGISTRAR LOG DE EJECUCIÓN
                    # ========================================================
                    log_entry = AutomationLog(
                        trigger_id=trigger.id,
                        event_type=event_type,
                        user_id=user_id,
                        event_context=context,
                        executed_actions=trigger_actions,
                        execution_success=True
                    )

                    self.db.add(log_entry)
                    await self.db.flush()

                    executed_triggers.append({
                        "trigger_id": trigger.id,
                        "trigger_name": trigger.name,
                        "actions_executed": len(trigger_actions),
                        "log_id": log_entry.id
                    })

                except Exception as e:
                    logger.error(f"    ❌ Error ejecutando trigger '{trigger.name}': {str(e)}")
                    
                    # Registrar log de error
                    error_log = AutomationLog(
                        trigger_id=trigger.id,
                        event_type=event_type,
                        user_id=user_id,
                        event_context=context,
                        executed_actions=[],
                        execution_success=False,
                        error_message=str(e)
                    )
                    self.db.add(error_log)

            # ================================================================
            # PASO 5: COMMIT DE TODOS LOS LOGS
            # ================================================================
            await self.db.commit()

            logger.info(
                f"✅ Ejecución completada: {len(executed_triggers)} triggers, "
                f"{total_actions} acciones ejecutadas"
            )

            return {
                "success": True,
                "event_type": event_type,
                "user_id": user_id,
                "triggers_executed": executed_triggers,
                "total_actions": total_actions,
                "summary": {
                    "total_triggers": len(triggers),
                    "executed_triggers": len(executed_triggers),
                    "total_actions": total_actions
                }
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error general ejecutando triggers: {str(e)}")
            raise DatabaseException(f"Error ejecutando triggers: {str(e)}")

    async def _evaluate_conditions(
        self, 
        conditions: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> bool:
        """
        Evalúa las condiciones de un trigger contra el contexto del evento.

        Args:
            conditions: Condiciones definidas en el trigger
            context: Contexto del evento actual

        Returns:
            True si todas las condiciones se cumplen, False en caso contrario
        """
        if not conditions:
            return True  # Sin condiciones = siempre se ejecuta

        for key, expected_value in conditions.items():
            if key not in context or context.get(key) != expected_value:
                logger.debug(
                    f"      Condición falló: la clave '{key}' no está en el contexto o el valor no coincide. "
                    f"Contexto: {context.get(key)}, Esperado: {expected_value}"
                )
                return False

        return True

    async def _simulate_action_execution(
        self, 
        action: TriggerAction, 
        user_id: int, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simula la ejecución de una acción (sin efectos reales por ahora).

        En producción, aquí se conectaría con los servicios reales.

        Args:
            action: Acción a ejecutar
            user_id: ID del usuario
            context: Contexto del evento

        Returns:
            Dict con resultado de la simulación
        """
        action_type = action.action_type
        parameters = action.parameters or {}

        simulation_messages = {
            ActionType.GIVE_PRODUCT.value: f"Dar producto ID {parameters.get('product_id')} al usuario {user_id}",
            ActionType.GRANT_VIP.value: f"Conceder VIP al usuario {user_id} por {parameters.get('duration_days', 7)} días",
            ActionType.SEND_MESSAGE.value: f"Enviar mensaje al usuario {user_id}: '{parameters.get('message_template', 'Mensaje predeterminado')}'",
            ActionType.ADD_POINTS.value: f"Agregar {parameters.get('amount', 0)} puntos al usuario {user_id}",
            ActionType.UNLOCK_FRAGMENT.value: f"Desbloquear fragmento '{parameters.get('fragment_key')}' para usuario {user_id}",
            ActionType.GRANT_BADGE.value: f"Otorgar insignia '{parameters.get('badge_id')}' al usuario {user_id}",
            ActionType.TRIGGER_NARRATIVE.value: f"Disparar narrativa '{parameters.get('narrative_key')}' para usuario {user_id}",
            ActionType.EXECUTE_WEBHOOK.value: f"Ejecutar webhook a {parameters.get('webhook_url')} con datos del usuario {user_id}"
        }

        simulation_message = simulation_messages.get(
            action_type, 
            f"Acción '{action_type}' ejecutada para usuario {user_id}"
        )

        return {
            "action_id": action.id,
            "action_type": action_type,
            "parameters": parameters,
            "simulation": simulation_message,
            "user_id": user_id,
            "executed_at": "SIMULATED"  # En producción sería datetime.utcnow()
        }

    # ============================================================================
    # MÉTODOS CRUD ESTÁNDAR
    # ============================================================================

    async def get_trigger(self, trigger_id: int) -> Optional[TriggerResponse]:
        """Obtiene un trigger por su ID."""
        try:
            stmt = select(AutomationTrigger).where(AutomationTrigger.id == trigger_id)
            result = await self.db.execute(stmt)
            trigger = result.scalar_one_or_none()

            if trigger:
                return TriggerResponse.model_validate(trigger)
            return None

        except Exception as e:
            logger.error(f"Error obteniendo trigger {trigger_id}: {str(e)}")
            raise DatabaseException(f"Error obteniendo trigger: {str(e)}")

    async def get_all_triggers(
        self,
        event_type: Optional[str] = None,
        is_enabled: Optional[bool] = None
    ) -> List[TriggerResponse]:
        """Obtiene todos los triggers con filtros opcionales."""
        try:
            stmt = select(AutomationTrigger)

            # Aplicar filtros
            if event_type is not None:
                stmt = stmt.where(AutomationTrigger.event_type == event_type)
            
            if is_enabled is not None:
                stmt = stmt.where(AutomationTrigger.is_enabled == is_enabled)

            result = await self.db.execute(stmt)
            triggers = result.scalars().all()

            return [TriggerResponse.model_validate(trigger) for trigger in triggers]

        except Exception as e:
            logger.error(f"Error obteniendo triggers: {str(e)}")
            raise DatabaseException(f"Error obteniendo triggers: {str(e)}")

    async def update_trigger(
        self,
        trigger_id: int,
        data: TriggerUpdate
    ) -> Optional[TriggerResponse]:
        """Actualiza un trigger existente."""
        try:
            stmt = select(AutomationTrigger).where(AutomationTrigger.id == trigger_id)
            result = await self.db.execute(stmt)
            trigger = result.scalar_one_or_none()

            if not trigger:
                return None

            # Actualizar campos
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(trigger, field, value)

            await self.db.commit()
            await self.db.refresh(trigger)

            return TriggerResponse.model_validate(trigger)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error actualizando trigger {trigger_id}: {str(e)}")
            raise DatabaseException(f"Error actualizando trigger: {str(e)}")

    async def delete_trigger(self, trigger_id: int) -> bool:
        """Elimina un trigger."""
        try:
            stmt = select(AutomationTrigger).where(AutomationTrigger.id == trigger_id)
            result = await self.db.execute(stmt)
            trigger = result.scalar_one_or_none()

            if not trigger:
                return False

            await self.db.delete(trigger)
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error eliminando trigger {trigger_id}: {str(e)}")
            raise DatabaseException(f"Error eliminando trigger: {str(e)}")