"""
Blueprint API para datos de referencia (dropdowns, selectores)
Endpoints ligeros que retornan solo ID y nombre para poblar UI
"""
import sys
from pathlib import Path

# Añadir ruta del bot al PYTHONPATH
BOT_PATH = Path(__file__).parent.parent.parent / 'bot'
sys.path.insert(0, str(BOT_PATH))

from flask import Blueprint, request, jsonify
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
import logging

# Importar extensiones
from admin_panel.extensions import db

# Importar modelos
from database.models import ShopItem, User
from database.narrative_models import StoryFragment
from database.automation_models import AutomationTrigger

# Configurar logging
logger = logging.getLogger(__name__)

# Crear blueprint
references_bp = Blueprint('references', __name__, url_prefix='/api/v1/references')


# ==================== ENDPOINT: PRODUCTS REFERENCE ====================

@references_bp.route('/products', methods=['GET'])
def get_products_reference():
    """
    Retorna lista simplificada de productos para dropdowns
    
    Query Parameters:
    - search: str - Búsqueda en nombre
    - is_active: bool - Filtrar por activos/inactivos
    - limit: int (default: 100, max: 500) - Límite de resultados
    
    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "id": 42,
                "name": "Acceso Capítulo 10",
                "price": 50,
                "is_active": true
            },
            {
                "id": 43,
                "name": "Pack VIP Mensual",
                "price": 100,
                "is_active": true
            }
        ],
        "total": 2
    }
    """
    
    try:
        # 1. Obtener parámetros
        search = request.args.get('search', type=str)
        is_active = request.args.get('is_active', type=str)
        limit = request.args.get('limit', 100, type=int)
        
        # Validar límite
        if limit < 1 or limit > 500:
            return jsonify({
                'success': False,
                'error': 'limit must be between 1 and 500',
                'code': 'INVALID_VALUE'
            }), 400
        
        # 2. Construir query
        query = select(ShopItem).order_by(ShopItem.name.asc())
        
        # Aplicar filtros
        if search:
            search_term = f"%{search}%"
            query = query.where(ShopItem.name.ilike(search_term))
        
        if is_active is not None:
            if is_active.lower() == 'true':
                query = query.where(ShopItem.is_active == True)
            elif is_active.lower() == 'false':
                query = query.where(ShopItem.is_active == False)
        
        # Aplicar límite
        query = query.limit(limit)
        
        # 3. Ejecutar query
        result = db.session.execute(query)
        products = result.scalars().all()
        
        # 4. Serializar (solo campos necesarios para dropdown)
        data = [
            {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'is_active': product.is_active
            }
            for product in products
        ]
        
        logger.info(f"✓ Retornando {len(data)} productos para referencia")
        
        # 5. Retornar respuesta
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
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


# ==================== ENDPOINT: FRAGMENTS REFERENCE ====================

@references_bp.route('/fragments', methods=['GET'])
def get_fragments_reference():
    """
    Retorna lista simplificada de fragmentos para dropdowns
    
    Query Parameters:
    - search: str - Búsqueda en key
    - limit: int (default: 100, max: 500)
    
    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "id": 156,
                "key": "CAP10_INTRO",
                "text_preview": "Entraste a la habitación...",
                "is_locked": true
            }
        ],
        "total": 1
    }
    """
    
    try:
        # 1. Obtener parámetros
        search = request.args.get('search', type=str)
        limit = request.args.get('limit', 100, type=int)
        
        # Validar límite
        if limit < 1 or limit > 500:
            return jsonify({
                'success': False,
                'error': 'limit must be between 1 and 500',
                'code': 'INVALID_VALUE'
            }), 400
        
        # 2. Construir query
        query = select(StoryFragment).order_by(StoryFragment.key.asc())
        
        # Aplicar filtros
        if search:
            search_term = f"%{search}%"
            query = query.where(StoryFragment.key.ilike(search_term))
        
        # Aplicar límite
        query = query.limit(limit)
        
        # 3. Ejecutar query
        result = db.session.execute(query)
        fragments = result.scalars().all()
        
        # 4. Serializar (solo campos necesarios)
        data = [
            {
                'id': fragment.id,
                'key': fragment.key,
                'text_preview': (fragment.text[:50] + '...') if fragment.text and len(fragment.text) > 50 else (fragment.text or ''),
                'is_locked': fragment.unlock_product is not None
            }
            for fragment in fragments
        ]
        
        logger.info(f"✓ Retornando {len(data)} fragmentos para referencia")
        
        # 5. Retornar respuesta
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
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


# ==================== ENDPOINT: TRIGGERS REFERENCE ====================

@references_bp.route('/triggers', methods=['GET'])
def get_triggers_reference():
    """
    Retorna lista simplificada de triggers para dropdowns
    
    Query Parameters:
    - search: str - Búsqueda en nombre
    - enabled: bool - Filtrar por habilitados
    - limit: int (default: 100, max: 500)
    
    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "Regalo de Bienvenida",
                "event_type": "USER_CREATED",
                "enabled": true
            }
        ],
        "total": 1
    }
    """
    
    try:
        # 1. Obtener parámetros
        search = request.args.get('search', type=str)
        enabled = request.args.get('enabled', type=str)
        limit = request.args.get('limit', 100, type=int)
        
        # Validar límite
        if limit < 1 or limit > 500:
            return jsonify({
                'success': False,
                'error': 'limit must be between 1 and 500',
                'code': 'INVALID_VALUE'
            }), 400
        
        # 2. Construir query
        query = select(AutomationTrigger).order_by(AutomationTrigger.name.asc())
        
        # Aplicar filtros
        if search:
            search_term = f"%{search}%"
            query = query.where(AutomationTrigger.name.ilike(search_term))
        
        if enabled is not None:
            if enabled.lower() == 'true':
                query = query.where(AutomationTrigger.enabled == True)
            elif enabled.lower() == 'false':
                query = query.where(AutomationTrigger.enabled == False)
        
        # Aplicar límite
        query = query.limit(limit)
        
        # 3. Ejecutar query
        result = db.session.execute(query)
        triggers = result.scalars().all()
        
        # 4. Serializar
        data = [
            {
                'id': trigger.id,
                'name': trigger.name,
                'event_type': trigger.trigger_event_type,
                'enabled': trigger.enabled
            }
            for trigger in triggers
        ]
        
        logger.info(f"✓ Retornando {len(data)} triggers para referencia")
        
        # 5. Retornar respuesta
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
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


# ==================== ENDPOINT: EVENT TYPES ====================

@references_bp.route('/event-types', methods=['GET'])
def get_event_types():
    """
    Retorna lista de tipos de eventos válidos para triggers
    (datos estáticos, no requiere BD)
    
    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "value": "FRAGMENT_VIEWED",
                "label": "Fragment Viewed",
                "description": "Cuando un usuario ve un fragmento específico",
                "required_fields": ["fragment_key"]
            },
            {
                "value": "USER_CREATED",
                "label": "User Created",
                "description": "Cuando un nuevo usuario se registra",
                "required_fields": []
            }
        ]
    }
    """
    
    event_types = [
        {
            'value': 'FRAGMENT_VIEWED',
            'label': 'Fragment Viewed',
            'description': 'Cuando un usuario ve un fragmento específico',
            'required_fields': ['fragment_key']
        },
        {
            'value': 'PRODUCT_PURCHASED',
            'label': 'Product Purchased',
            'description': 'Cuando un usuario compra un producto',
            'required_fields': ['product_id']
        },
        {
            'value': 'MISSION_COMPLETED',
            'label': 'Mission Completed',
            'description': 'Cuando un usuario completa una misión',
            'required_fields': ['mission_id']
        },
        {
            'value': 'USER_CREATED',
            'label': 'User Created',
            'description': 'Cuando un nuevo usuario se registra',
            'required_fields': []
        },
        {
            'value': 'POINTS_THRESHOLD',
            'label': 'Points Threshold',
            'description': 'Cuando un usuario alcanza un umbral de puntos',
            'required_fields': ['points_threshold']
        },
        {
            'value': 'LEVEL_UP',
            'label': 'Level Up',
            'description': 'Cuando un usuario sube de nivel',
            'required_fields': ['level_threshold']
        }
    ]
    
    return jsonify({
        'success': True,
        'data': event_types
    }), 200


# ==================== ENDPOINT: ACTION TYPES ====================

@references_bp.route('/action-types', methods=['GET'])
def get_action_types():
    """
    Retorna lista de tipos de acciones válidas para triggers
    (datos estáticos, no requiere BD)
    
    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "value": "GIVE_PRODUCT",
                "label": "Give Product",
                "description": "Añadir un producto al inventario del usuario",
                "required_fields": ["product_id"]
            }
        ]
    }
    """
    
    action_types = [
        {
            'value': 'GIVE_PRODUCT',
            'label': 'Give Product',
            'description': 'Añadir un producto al inventario del usuario',
            'required_fields': ['product_id']
        },
        {
            'value': 'GRANT_VIP',
            'label': 'Grant VIP',
            'description': 'Otorgar días de membresía VIP',
            'required_fields': ['amount']
        },
        {
            'value': 'UNLOCK_FRAGMENT',
            'label': 'Unlock Fragment',
            'description': 'Desbloquear un fragmento narrativo',
            'required_fields': ['fragment_key']
        },
        {
            'value': 'UNLOCK_LORE',
            'label': 'Unlock Lore',
            'description': 'Desbloquear una pieza de lore',
            'required_fields': ['lore_piece_id']
        },
        {
            'value': 'ADD_POINTS',
            'label': 'Add Points',
            'description': 'Añadir puntos (besitos) al usuario',
            'required_fields': ['amount']
        },
        {
            'value': 'SUBTRACT_POINTS',
            'label': 'Subtract Points',
            'description': 'Restar puntos al usuario',
            'required_fields': ['amount']
        },
        {
            'value': 'SEND_MESSAGE',
            'label': 'Send Message',
            'description': 'Enviar un mensaje de Telegram al usuario',
            'required_fields': ['message_template']
        },
        {
            'value': 'SET_ROLE',
            'label': 'Set Role',
            'description': 'Cambiar el rol del usuario',
            'required_fields': ['role_name']
        },
        {
            'value': 'ADD_TO_GROUP',
            'label': 'Add to Group',
            'description': 'Añadir usuario a un grupo/canal',
            'required_fields': ['group_id']
        },
        {
            'value': 'COMPLETE_MISSION',
            'label': 'Complete Mission',
            'description': 'Marcar una misión como completada',
            'required_fields': ['mission_id']
        }
    ]
    
    return jsonify({
        'success': True,
        'data': action_types
    }), 200


# ==================== ENDPOINT: ROLES ====================

@references_bp.route('/roles', methods=['GET'])
def get_roles():
    """
    Retorna lista de roles válidos en el sistema
    (datos estáticos)
    
    Response Success (200):
    {
        "success": true,
        "data": [
            {
                "value": "free",
                "label": "Free User"
            },
            {
                "value": "vip",
                "label": "VIP User"
            },
            {
                "value": "admin",
                "label": "Administrator"
            }
        ]
    }
    """
    
    roles = [
        {'value': 'free', 'label': 'Free User'},
        {'value': 'vip', 'label': 'VIP User'},
        {'value': 'admin', 'label': 'Administrator'}
    ]
    
    return jsonify({
        'success': True,
        'data': roles
    }), 200


# ==================== ENDPOINT: STATISTICS ====================

@references_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Retorna estadísticas generales del sistema
    (útil para dashboard)
    
    Response Success (200):
    {
        "success": true,
        "data": {
            "total_fragments": 45,
            "total_products": 12,
            "total_triggers": 5,
            "total_users": 523,
            "active_triggers": 4
        }
    }
    """
    
    try:
        # Contar fragmentos
        total_fragments = db.session.execute(
            select(func.count()).select_from(StoryFragment)
        ).scalar()
        
        # Contar productos
        total_products = db.session.execute(
            select(func.count()).select_from(ShopItem)
        ).scalar()
        
        # Contar triggers
        total_triggers = db.session.execute(
            select(func.count()).select_from(AutomationTrigger)
        ).scalar()
        
        # Contar triggers activos
        active_triggers = db.session.execute(
            select(func.count()).select_from(AutomationTrigger).where(
                AutomationTrigger.enabled == True
            )
        ).scalar()
        
        # Contar usuarios
        total_users = db.session.execute(
            select(func.count()).select_from(User)
        ).scalar()
        
        statistics = {
            'total_fragments': total_fragments,
            'total_products': total_products,
            'total_triggers': total_triggers,
            'active_triggers': active_triggers,
            'total_users': total_users
        }
        
        logger.info(f"✓ Retornando estadísticas del sistema")
        
        return jsonify({
            'success': True,
            'data': statistics
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


# ==================== ENDPOINT: VALIDATE KEY ====================

@references_bp.route('/validate/fragment-key', methods=['POST'])
def validate_fragment_key():
    """
    Valida que una key de fragmento sea única (para validación en tiempo real)
    
    Request Body:
    {
        "key": "CAP10_INTRO",
        "exclude_id": 156  // Opcional, para edición
    }
    
    Response Success (200):
    {
        "success": true,
        "available": true,
        "suggestion": null
    }
    
    Response cuando ya existe (200):
    {
        "success": true,
        "available": false,
        "existing_fragment": {
            "id": 100,
            "key": "CAP10_INTRO"
        },
        "suggestion": "CAP10_INTRO_V2"
    }
    """
    
    try:
        data = request.get_json()
        
        if not data or 'key' not in data:
            return jsonify({
                'success': False,
                'error': 'Field "key" is required',
                'code': 'REQUIRED_FIELD'
            }), 400
        
        key = data['key']
        exclude_id = data.get('exclude_id')
        
        # Buscar fragmento existente
        query = select(StoryFragment).where(StoryFragment.key == key)
        
        if exclude_id:
            query = query.where(StoryFragment.id != exclude_id)
        
        existing = db.session.execute(query).scalar_one_or_none()
        
        if existing:
            # Key ya existe, sugerir alternativa
            suggestion = f"{key}_V2"
            
            return jsonify({
                'success': True,
                'available': False,
                'existing_fragment': {
                    'id': existing.id,
                    'key': existing.key
                },
                'suggestion': suggestion
            }), 200
        else:
            # Key disponible
            return jsonify({
                'success': True,
                'available': True,
                'suggestion': None
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