"""
Blueprint API para gestión de automatización (triggers y acciones)
Endpoints para crear, listar y gestionar triggers configurables
"""
import sys
from pathlib import Path

# Añadir ruta del bot al PYTHONPATH
BOT_PATH = Path(__file__).parent.parent.parent / 'bot'
sys.path.insert(0, str(BOT_PATH))

from flask import Blueprint, request, jsonify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime

# Importar extensiones
from admin_panel.extensions import db

# Importar modelos
from database.automation_models import AutomationTrigger, TriggerAction, TriggerExecutionLog

# Importar servicios
from admin_panel.services.validation_service import (
    ValidationService,
    ValidationError,
    handle_validation_error
)

# Configurar logging
logger = logging.getLogger(__name__)

# Crear blueprint
automation_bp = Blueprint('automation', __name__, url_prefix='/api/v1/automation')


# ==================== ENDPOINT: CREATE TRIGGER ====================

@automation_bp.route('/triggers', methods=['POST'])
def create_trigger():
    """
    Crea un trigger configurable con sus acciones asociadas

    Request Body:
    {
        "name": "Regalo de Bienvenida",
        "description": "Otorga kit inicial cuando usuario se registra",
        "enabled": true,
        "trigger_event_type": "USER_CREATED",

        // Campos específicos según el tipo de trigger
        "fragment_key": null,           // Para FRAGMENT_VIEWED
        "product_id": null,             // Para PRODUCT_PURCHASED
        "mission_id": null,             // Para MISSION_COMPLETED
        "points_threshold": null,       // Para POINTS_THRESHOLD
        "level_threshold": null,        // Para LEVEL_UP

        // Condiciones adicionales (opcional)
        "conditions": {
            "user_role": "free",        // Solo para usuarios free
            "first_time_only": true,    // Solo la primera vez
            "max_activations": 1,       // Máximo 1 vez por usuario
            "cooldown_hours": 24        // Esperar 24h entre activaciones
        },

        // Acciones a ejecutar (mínimo 1)
        "actions": [
            {
                "action_type": "GIVE_PRODUCT",
                "product_id": 42,
                "execution_order": 0
            },
            {
                "action_type": "ADD_POINTS",
                "amount": 50,
                "execution_order": 1
            },
            {
                "action_type": "SEND_MESSAGE",
                "message_template": "¡Bienvenido {user_name}! Has recibido tu kit inicial.",
                "execution_order": 2
            }
        ]
    }

    Response Success (201):
    {
        "success": true,
        "data": {
            "trigger": {
                "id": 1,
                "name": "Regalo de Bienvenida",
                "enabled": true,
                "trigger_event_type": "USER_CREATED",
                "actions_count": 3
            },
            "actions": [
                {
                    "id": 1,
                    "action_type": "GIVE_PRODUCT",
                    "product_id": 42
                },
                {
                    "id": 2,
                    "action_type": "ADD_POINTS",
                    "amount": 50
                },
                {
                    "id": 3,
                    "action_type": "SEND_MESSAGE",
                    "message_template": "¡Bienvenido {user_name}!..."
                }
            ]
        },
        "warnings": [],
        "message": "Trigger 'Regalo de Bienvenida' creado con 3 acciones"
    }

    Response Error (400):
    {
        "success": false,
        "error": "A trigger with name 'Regalo de Bienvenida' already exists",
        "field": "name",
        "code": "DUPLICATE_NAME"
    }
    """

    try:
        # 1. Obtener datos del request
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_BODY'
            }), 400

        # 2. Validar campos requeridos básicos
        required_fields = ['name', 'trigger_event_type', 'actions']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}',
                    'field': field,
                    'code': 'REQUIRED_FIELD'
                }), 400

        # Validar que actions sea una lista no vacía
        if not isinstance(data['actions'], list) or len(data['actions']) == 0:
            return jsonify({
                'success': False,
                'error': 'Field "actions" must be a non-empty array',
                'field': 'actions',
                'code': 'INVALID_VALUE'
            }), 400

        # 3. Crear servicio de validación
        validator = ValidationService(db.session)

        # 4. Validar datos completos (nested validation)
        try:
            validated, warnings = validator.validate_nested_trigger_creation(data)
            logger.info(f"✓ Datos validados para trigger: {data['name']}")
            if warnings:
                logger.warning(f"Warnings: {warnings}")
        except ValidationError as e:
            logger.warning(f"✗ Validación fallida: {e.message}")
            return jsonify(handle_validation_error(e)), 400

        # 5. Crear el trigger principal
        trigger = AutomationTrigger(
            name=data['name'],
            description=data.get('description'),
            enabled=data.get('enabled', True),
            trigger_event_type=data['trigger_event_type'],
            fragment_key=data.get('fragment_key'),
            mission_id=data.get('mission_id'),
            product_id=data.get('product_id'),
            points_threshold=data.get('points_threshold'),
            level_threshold=data.get('level_threshold'),
            conditions=data.get('conditions'),
            total_activations=0
        )

        db.session.add(trigger)
        db.session.flush()  # Genera ID sin commit

        logger.info(f"✓ Trigger creado: {trigger.name} (ID: {trigger.id})")

        # 6. Crear las acciones asociadas
        created_actions = []

        for action_data in data['actions']:
            action = TriggerAction(
                trigger_id=trigger.id,
                action_type=action_data['action_type'],
                product_id=action_data.get('product_id'),
                fragment_key=action_data.get('fragment_key'),
                lore_piece_id=action_data.get('lore_piece_id'),
                mission_id=action_data.get('mission_id'),
                amount=action_data.get('amount'),
                role_name=action_data.get('role_name'),
                group_id=action_data.get('group_id'),
                message_template=action_data.get('message_template'),
                execution_order=action_data.get('execution_order', 0),
                action_metadata=action_data.get('action_metadata')
            )

            db.session.add(action)
            db.session.flush()

            created_actions.append({
                'id': action.id,
                'action_type': action.action_type,
                'product_id': action.product_id,
                'fragment_key': action.fragment_key,
                'lore_piece_id': action.lore_piece_id,
                'mission_id': action.mission_id,
                'amount': action.amount,
                'role_name': action.role_name,
                'group_id': action.group_id,
                'message_template': action.message_template,
                'execution_order': action.execution_order,
                'action_metadata': action.action_metadata
            })

            logger.info(f"✓ Acción creada: {action.action_type} (ID: {action.id}, orden: {action.execution_order})")

        # 7. COMMIT ATÓMICO - Todo o nada
        db.session.commit()

        logger.info(f"✅ Transacción completada exitosamente para trigger {trigger.name}")

        # 8. Construir respuesta
        message = f"Trigger '{trigger.name}' creado con {len(created_actions)} acción(es)"

        return jsonify({
            'success': True,
            'data': {
                'trigger': {
                    'id': trigger.id,
                    'name': trigger.name,
                    'description': trigger.description,
                    'enabled': trigger.enabled,
                    'trigger_event_type': trigger.trigger_event_type,
                    'fragment_key': trigger.fragment_key,
                    'mission_id': trigger.mission_id,
                    'product_id': trigger.product_id,
                    'points_threshold': trigger.points_threshold,
                    'level_threshold': trigger.level_threshold,
                    'conditions': trigger.conditions,
                    'actions_count': len(created_actions),
                    'total_activations': trigger.total_activations,
                    'last_activated_at': trigger.last_activated_at.isoformat() if trigger.last_activated_at else None,
                    'created_at': trigger.created_at.isoformat()
                },
                'actions': created_actions
            },
            'warnings': warnings,
            'message': message
        }), 201

    except ValidationError as e:
        # Rollback en caso de error de validación
        db.session.rollback()
        logger.error(f"❌ Error de validación: {e.message}")
        return jsonify(handle_validation_error(e)), 400

    except IntegrityError as e:
        # Rollback en caso de error de integridad (ej: duplicate name)
        db.session.rollback()
        logger.error(f"❌ Error de integridad: {str(e.orig)}")

        error_msg = str(e.orig)
        if 'UNIQUE constraint' in error_msg or 'unique constraint' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'A trigger with this name already exists',
                'code': 'DUPLICATE_NAME',
                'details': error_msg
            }), 409
        else:
            return jsonify({
                'success': False,
                'error': 'Database integrity error',
                'code': 'INTEGRITY_ERROR',
                'details': error_msg
            }), 400

    except SQLAlchemyError as e:
        # Rollback en caso de cualquier error de BD
        db.session.rollback()
        logger.error(f"❌ Error de base de datos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500

    except Exception as e:
        # Rollback en caso de error inesperado
        db.session.rollback()
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500


# ==================== ENDPOINT: LIST TRIGGERS ====================

@automation_bp.route('/triggers', methods=['GET'])
def list_triggers():
    """
    Lista triggers con filtros y paginación

    Query Parameters:
    - page: int (default: 1)
    - per_page: int (default: 20, max: 100)
    - enabled: bool - Filtrar por habilitados/deshabilitados
    - event_type: str - Filtrar por tipo de evento
    - search: str - Búsqueda en nombre y descripción
    - sort_by: str - Campo para ordenar (name, created_at, total_activations)
    - sort_order: str - Orden (asc, desc)
    - include: str - Incluir acciones (include=actions)

    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "Regalo de Bienvenida",
                "description": "...",
                "enabled": true,
                "trigger_event_type": "USER_CREATED",
                "actions_count": 3,
                "total_activations": 152,
                "last_activated_at": "2024-11-29T10:30:00",
                "created_at": "2024-11-20T08:00:00",
                "actions": [...]  // Solo si include=actions
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 5,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
    """

    try:
        # 1. Obtener parámetros de query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        enabled = request.args.get('enabled', type=str)
        event_type = request.args.get('event_type', type=str)
        search = request.args.get('search', type=str)
        sort_by = request.args.get('sort_by', 'created_at', type=str)
        sort_order = request.args.get('sort_order', 'desc', type=str)
        include = request.args.get('include', '', type=str)

        # 2. Validar parámetros
        if page < 1:
            return jsonify({
                'success': False,
                'error': 'Page must be >= 1',
                'field': 'page',
                'code': 'INVALID_VALUE'
            }), 400

        if per_page < 1 or per_page > 100:
            return jsonify({
                'success': False,
                'error': 'per_page must be between 1 and 100',
                'field': 'per_page',
                'code': 'INVALID_VALUE'
            }), 400

        # 3. Construir query base
        query = select(AutomationTrigger)

        # 4. Aplicar filtros
        if enabled is not None:
            if enabled.lower() == 'true':
                query = query.where(AutomationTrigger.enabled == True)
            elif enabled.lower() == 'false':
                query = query.where(AutomationTrigger.enabled == False)

        if event_type:
            query = query.where(AutomationTrigger.trigger_event_type == event_type)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (AutomationTrigger.name.ilike(search_term)) |
                (AutomationTrigger.description.ilike(search_term))
            )

        # 5. Aplicar ordenamiento
        valid_sort_fields = {
            'name': AutomationTrigger.name,
            'created_at': AutomationTrigger.created_at,
            'total_activations': AutomationTrigger.total_activations
        }

        if sort_by not in valid_sort_fields:
            return jsonify({
                'success': False,
                'error': f'Invalid sort_by field. Must be one of: {", ".join(valid_sort_fields.keys())}',
                'field': 'sort_by',
                'code': 'INVALID_VALUE'
            }), 400

        sort_field = valid_sort_fields[sort_by]

        if sort_order.lower() == 'desc':
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # 6. Contar total
        count_query = select(db.func.count()).select_from(query.subquery())
        total = db.session.execute(count_query).scalar()

        # 7. Aplicar paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # 8. Eager loading de acciones si se solicita
        include_list = [i.strip() for i in include.split(',') if i.strip()]

        if 'actions' in include_list:
            from sqlalchemy.orm import selectinload
            query = query.options(selectinload(AutomationTrigger.actions))

        # 9. Ejecutar query
        result = db.session.execute(query)
        triggers = result.scalars().all()

        logger.info(f"✓ Encontrados {len(triggers)} triggers (total: {total})")

        # 10. Serializar resultados
        data = []
        for trigger in triggers:
            trigger_dict = {
                'id': trigger.id,
                'name': trigger.name,
                'description': trigger.description,
                'enabled': trigger.enabled,
                'trigger_event_type': trigger.trigger_event_type,
                'fragment_key': trigger.fragment_key,
                'mission_id': trigger.mission_id,
                'product_id': trigger.product_id,
                'points_threshold': trigger.points_threshold,
                'level_threshold': trigger.level_threshold,
                'conditions': trigger.conditions,
                'total_activations': trigger.total_activations,
                'last_activated_at': trigger.last_activated_at.isoformat() if trigger.last_activated_at else None,
                'created_at': trigger.created_at.isoformat() if trigger.created_at else None
            }

            # Contar o incluir acciones
            if 'actions' in include_list:
                trigger_dict['actions_count'] = len(trigger.actions)
                trigger_dict['actions'] = [
                    {
                        'id': action.id,
                        'action_type': action.action_type,
                        'product_id': action.product_id,
                        'fragment_key': action.fragment_key,
                        'lore_piece_id': action.lore_piece_id,
                        'mission_id': action.mission_id,
                        'amount': action.amount,
                        'role_name': action.role_name,
                        'group_id': action.group_id,
                        'message_template': action.message_template,
                        'execution_order': action.execution_order,
                        'action_metadata': action.action_metadata
                    }
                    for action in sorted(trigger.actions, key=lambda a: a.execution_order)
                ]
            else:
                # Query separado para contar
                actions_count = db.session.execute(
                    select(db.func.count()).where(
                        TriggerAction.trigger_id == trigger.id
                    )
                ).scalar()
                trigger_dict['actions_count'] = actions_count

            data.append(trigger_dict)

        # 11. Calcular paginación
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1

        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        }

        # 12. Retornar respuesta
        return jsonify({
            'success': True,
            'data': data,
            'pagination': pagination
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de base de datos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500

    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500


# ==================== ENDPOINT: GET SINGLE TRIGGER ====================

@automation_bp.route('/triggers/<int:trigger_id>', methods=['GET'])
def get_trigger(trigger_id):
    """
    Obtiene un trigger específico por ID con sus acciones

    Path Parameters:
    - trigger_id: int - ID del trigger

    Query Parameters:
    - include: str - Incluir logs (include=logs)

    Response Success (200):
    {
        "success": true,
        "data": {
            "id": 1,
            "name": "Regalo de Bienvenida",
            "enabled": true,
            "trigger_event_type": "USER_CREATED",
            "actions": [...],
            "execution_logs": [...]  // Solo si include=logs
        }
    }

    Response Error (404):
    {
        "success": false,
        "error": "Trigger with ID 999 not found",
        "code": "TRIGGER_NOT_FOUND"
    }
    """

    try:
        # 1. Obtener parámetros
        include = request.args.get('include', '', type=str)
        include_list = [i.strip() for i in include.split(',') if i.strip()]

        # 2. Construir query con eager loading
        query = select(AutomationTrigger).where(AutomationTrigger.id == trigger_id)

        # Siempre cargar las acciones para un trigger individual
        from sqlalchemy.orm import selectinload
        query = query.options(selectinload(AutomationTrigger.actions))

        if 'logs' in include_list:
            query = query.options(selectinload(AutomationTrigger.execution_logs))

        # 3. Ejecutar query
        result = db.session.execute(query)
        trigger = result.scalar_one_or_none()

        if not trigger:
            logger.warning(f"⚠️  Trigger no encontrado: {trigger_id}")
            return jsonify({
                'success': False,
                'error': f"Trigger with ID {trigger_id} not found",
                'code': 'TRIGGER_NOT_FOUND'
            }), 404

        logger.info(f"✓ Trigger encontrado: {trigger.name} (ID: {trigger.id})")

        # 4. Serializar trigger
        trigger_dict = {
            'id': trigger.id,
            'name': trigger.name,
            'description': trigger.description,
            'enabled': trigger.enabled,
            'trigger_event_type': trigger.trigger_event_type,
            'fragment_key': trigger.fragment_key,
            'mission_id': trigger.mission_id,
            'product_id': trigger.product_id,
            'points_threshold': trigger.points_threshold,
            'level_threshold': trigger.level_threshold,
            'conditions': trigger.conditions,
            'total_activations': trigger.total_activations,
            'last_activated_at': trigger.last_activated_at.isoformat() if trigger.last_activated_at else None,
            'created_at': trigger.created_at.isoformat() if trigger.created_at else None,
            'updated_at': trigger.updated_at.isoformat() if trigger.updated_at else None
        }

        # 5. Incluir acciones (siempre)
        trigger_dict['actions'] = [
            {
                'id': action.id,
                'action_type': action.action_type,
                'product_id': action.product_id,
                'fragment_key': action.fragment_key,
                'lore_piece_id': action.lore_piece_id,
                'mission_id': action.mission_id,
                'amount': action.amount,
                'role_name': action.role_name,
                'group_id': action.group_id,
                'message_template': action.message_template,
                'execution_order': action.execution_order,
                'action_metadata': action.action_metadata,
                'created_at': action.created_at.isoformat()
            }
            for action in sorted(trigger.actions, key=lambda a: a.execution_order)
        ]

        # 6. Incluir logs si se solicitó
        if 'logs' in include_list:
            trigger_dict['execution_logs'] = [
                {
                    'id': log.id,
                    'user_id': log.user_id,
                    'success': log.success,
                    'error_message': log.error_message,
                    'actions_executed': log.actions_executed,
                    'execution_time_ms': log.execution_time_ms,
                    'executed_at': log.executed_at.isoformat()
                }
                for log in trigger.execution_logs[-10:]  # Últimos 10 logs
            ]

        # 7. Retornar respuesta
        return jsonify({
            'success': True,
            'data': trigger_dict
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"❌ Error de base de datos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500

    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500


# ==================== ENDPOINT: UPDATE TRIGGER ====================

@automation_bp.route('/triggers/<int:trigger_id>', methods=['PATCH'])
def update_trigger(trigger_id):
    """
    Actualiza un trigger existente (actualización parcial)

    Path Parameters:
    - trigger_id: int - ID del trigger

    Request Body (todos los campos son opcionales):
    {
        "name": "Nuevo nombre",
        "description": "Nueva descripción",
        "enabled": false,
        "conditions": {...}
    }

    Response Success (200):
    {
        "success": true,
        "data": {
            "id": 1,
            "name": "Nuevo nombre",
            ...
        },
        "message": "Trigger updated successfully"
    }
    """

    try:
        # 1. Obtener datos del request
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'MISSING_BODY'
            }), 400

        # 2. Buscar el trigger
        trigger = db.session.get(AutomationTrigger, trigger_id)

        if not trigger:
            return jsonify({
                'success': False,
                'error': f"Trigger with ID {trigger_id} not found",
                'code': 'TRIGGER_NOT_FOUND'
            }), 404

        # 3. Validar nombre único si se está cambiando
        if 'name' in data and data['name'] != trigger.name:
            validator = ValidationService(db.session)
            try:
                validator.validate_trigger_name_unique(data['name'], exclude_id=trigger_id)
            except ValidationError as e:
                return jsonify(handle_validation_error(e)), 400

        # 4. Actualizar campos permitidos
        updatable_fields = [
            'name', 'description', 'enabled', 'fragment_key', 'mission_id',
            'product_id', 'points_threshold', 'level_threshold', 'conditions'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(trigger, field, data[field])
                logger.info(f"✓ Campo '{field}' actualizado para trigger {trigger_id}")

        # 5. Actualizar timestamp
        trigger.updated_at = datetime.utcnow()

        # 6. Commit
        db.session.commit()

        logger.info(f"✅ Trigger {trigger_id} actualizado exitosamente")

        # 7. Retornar trigger actualizado
        return jsonify({
            'success': True,
            'data': trigger.to_dict(),
            'message': 'Trigger updated successfully'
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"❌ Error de integridad: {str(e.orig)}")
        return jsonify({
            'success': False,
            'error': 'Database integrity error',
            'code': 'INTEGRITY_ERROR'
        }), 400

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"❌ Error de base de datos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500


# ==================== ENDPOINT: DELETE TRIGGER ====================

@automation_bp.route('/triggers/<int:trigger_id>', methods=['DELETE'])
def delete_trigger(trigger_id):
    """
    Elimina un trigger y todas sus acciones asociadas

    Path Parameters:
    - trigger_id: int - ID del trigger

    Response Success (200):
    {
        "success": true,
        "message": "Trigger deleted successfully"
    }
    """

    try:
        # 1. Buscar el trigger
        trigger = db.session.get(AutomationTrigger, trigger_id)

        if not trigger:
            return jsonify({
                'success': False,
                'error': f"Trigger with ID {trigger_id} not found",
                'code': 'TRIGGER_NOT_FOUND'
            }), 404

        trigger_name = trigger.name

        # 2. Eliminar trigger (cascade eliminará las acciones automáticamente)
        db.session.delete(trigger)
        db.session.commit()

        logger.info(f"✅ Trigger '{trigger_name}' (ID: {trigger_id}) eliminado exitosamente")

        # 3. Retornar confirmación
        return jsonify({
            'success': True,
            'message': f"Trigger '{trigger_name}' deleted successfully"
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"❌ Error de base de datos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }), 500

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500