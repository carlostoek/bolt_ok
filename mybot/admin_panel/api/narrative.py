"""
Blueprint API para gestión de narrativa
Endpoints para crear, listar, actualizar y eliminar fragmentos narrativos
"""
import sys
from pathlib import Path

# Añadir ruta del bot al PYTHONPATH
BOT_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BOT_PATH))

from flask import Blueprint, request, jsonify
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime

# Importar extensiones
from admin_panel.extensions import db

# Importar modelos
from database.models import ShopItem
from database.narrative_models import StoryFragment, NarrativeChoice

# Importar servicios
from admin_panel.services.validation_service import (
    ValidationService, 
    ValidationError, 
    handle_validation_error
)

# Configurar logging
logger = logging.getLogger(__name__)

# Crear blueprint
narrative_bp = Blueprint('narrative', __name__, url_prefix='/api/v1/narrative')


# ==================== ENDPOINT: CREATE FRAGMENT (NESTED) ====================

@narrative_bp.route('/fragments', methods=['POST'])
def create_fragment():
    """
    Crea un fragmento narrativo con nested creation de producto y decisiones
    
    Request Body:
    {
        "key": "CAP10_INTRO",
        "text": "Entraste a la habitación oscura...",
        "image_url": "https://...",  // opcional
        "min_besitos": 0,
        "required_role": null,
        "reward_besitos": 10,
        
        // OPCIÓN 1: Referencia a producto existente
        "unlock_product_id": 42,
        
        // OPCIÓN 2: Crear producto al vuelo (NESTED)
        "unlock_product": {
            "name": "Acceso Capítulo 10",
            "description": "Desbloquea el capítulo completo",
            "price": 50,
            "is_vip_only": false
        },
        
        // OPCIÓN 3: Crear decisiones inline
        "choices": [
            {
                "text": "Entrar sigilosamente",
                "destination_fragment_key": "CAP10_SIGILO",
                "required_besitos": 0
            }
        ],
        
        // Auto-avance si no hay decisiones
        "auto_next_fragment_key": null
    }
    
    Response Success (201):
    {
        "success": true,
        "data": {
            "fragment": {
                "id": 156,
                "key": "CAP10_INTRO",
                "text": "Entraste a la habitación oscura...",
                "unlock_product_id": 87
            },
            "created_product": {
                "id": 87,
                "name": "Acceso Capítulo 10"
            },
            "created_choices": [
                {"id": 201, "text": "Entrar sigilosamente"}
            ]
        },
        "warnings": [],
        "message": "Fragmento creado con 1 producto y 1 decisión"
    }
    
    Response Error (400):
    {
        "success": false,
        "error": "Fragment with key 'CAP10_INTRO' already exists",
        "field": "key",
        "code": "DUPLICATE_KEY"
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
        required_fields = ['key', 'text']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}',
                    'field': field,
                    'code': 'REQUIRED_FIELD'
                }), 400
        
        # 3. Crear servicio de validación
        validator = ValidationService(db.session)
        
        # 4. Validar datos completos (nested validation)
        try:
            validated, warnings = validator.validate_nested_fragment_creation(data)
            logger.info(f"✓ Datos validados para fragmento: {data['key']}")
            if warnings:
                logger.warning(f"Warnings: {warnings}")
        except ValidationError as e:
            logger.warning(f"✗ Validación fallida: {e.message}")
            return jsonify(handle_validation_error(e)), 400
        
        # 5. NESTED CREATION: Crear producto si viene inline
        created_product = None
        unlock_product_id = data.get('unlock_product_id')
        
        if data.get('unlock_product'):
            product_data = data['unlock_product']
            
            new_product = ShopItem(
                name=product_data['name'],
                description=product_data.get('description'),
                price=product_data['price'],
                is_vip_only=product_data.get('is_vip_only', False),
                stock_limit=product_data.get('stock_limit'),
                max_purchases_per_user=product_data.get('max_purchases_per_user', 1),
                is_active=True,
                available_from=product_data.get('available_from'),
                available_until=product_data.get('available_until')
            )
            
            db.session.add(new_product)
            db.session.flush()  # Genera ID sin commit
            
            unlock_product_id = new_product.id
            created_product = {
                'id': new_product.id,
                'name': new_product.name,
                'price': new_product.price
            }
            
            logger.info(f"✓ Producto creado inline: {new_product.name} (ID: {new_product.id})")
        
        # 6. Crear el fragmento principal
        fragment = StoryFragment(
            key=data['key'],
            text=data['text'],
            image_url=data.get('image_url'),
            min_besitos=data.get('min_besitos', 0),
            required_role=data.get('required_role'),
            reward_besitos=data.get('reward_besitos', 0),
            auto_next_fragment_key=data.get('auto_next_fragment_key')
        )
        
        db.session.add(fragment)
        db.session.flush()  # Genera ID sin commit
        
        logger.info(f"✓ Fragmento creado: {fragment.key} (ID: {fragment.id})")
        
        # 7. Vincular producto de desbloqueo al fragmento (si existe)
        if unlock_product_id:
            # Actualizar el producto para que desbloquee este fragmento
            product = db.session.get(ShopItem, unlock_product_id)
            if product:
                product.unlocks_fragment_key = fragment.key
                logger.info(f"✓ Producto {unlock_product_id} vinculado a fragmento {fragment.key}")
        
        # 8. NESTED CREATION: Crear decisiones (choices)
        created_choices = []
        
        if data.get('choices'):
            for choice_data in data['choices']:
                # Determinar destino (puede ser key existente o nested)
                destination_key = choice_data.get('destination_fragment_key')
                
                # Si hay fragmento nested, crearlo primero
                if choice_data.get('destination_fragment'):
                    dest_data = choice_data['destination_fragment']
                    dest_fragment = StoryFragment(
                        key=dest_data['key'],
                        text=dest_data['text'],
                        image_url=dest_data.get('image_url'),
                        min_besitos=dest_data.get('min_besitos', 0),
                        required_role=dest_data.get('required_role'),
                        reward_besitos=dest_data.get('reward_besitos', 0)
                    )
                    db.session.add(dest_fragment)
                    db.session.flush()
                    destination_key = dest_fragment.key
                    logger.info(f"✓ Fragmento destino creado inline: {dest_fragment.key}")
                
                # Crear la decisión
                choice = NarrativeChoice(
                    source_fragment_id=fragment.id,
                    destination_fragment_key=destination_key,
                    text=choice_data['text'],
                    required_besitos=choice_data.get('required_besitos', 0),
                    required_role=choice_data.get('required_role')
                )
                
                db.session.add(choice)
                db.session.flush()
                
                created_choices.append({
                    'id': choice.id,
                    'text': choice.text,
                    'destination': destination_key
                })
                
                logger.info(f"✓ Decisión creada: '{choice.text}' -> {destination_key}")
        
        # 9. COMMIT ATÓMICO - Todo o nada
        db.session.commit()
        
        logger.info(f"✅ Transacción completada exitosamente para fragmento {fragment.key}")
        
        # 10. Construir mensaje de respuesta
        message_parts = [f"Fragmento '{fragment.key}' creado"]
        if created_product:
            message_parts.append(f"con 1 producto")
        if created_choices:
            message_parts.append(f"y {len(created_choices)} decisión(es)")
        
        # 11. Retornar respuesta exitosa
        return jsonify({
            'success': True,
            'data': {
                'fragment': {
                    'id': fragment.id,
                    'key': fragment.key,
                    'text': fragment.text[:100] + ('...' if len(fragment.text) > 100 else ''),
                    'image_url': fragment.image_url,
                    'min_besitos': fragment.min_besitos,
                    'reward_besitos': fragment.reward_besitos,
                    'unlock_product_id': unlock_product_id,
                    'choices_count': len(created_choices)
                },
                'created_product': created_product,
                'created_choices': created_choices
            },
            'warnings': warnings,
            'message': ' '.join(message_parts)
        }), 201
    
    except ValidationError as e:
        # Rollback en caso de error de validación
        db.session.rollback()
        logger.error(f"❌ Error de validación: {e.message}")
        return jsonify(handle_validation_error(e)), 400
    
    except IntegrityError as e:
        # Rollback en caso de error de integridad (ej: duplicate key)
        db.session.rollback()
        logger.error(f"❌ Error de integridad: {str(e.orig)}")
        
        # Parsear mensaje de error de SQLite/PostgreSQL
        error_msg = str(e.orig)
        if 'UNIQUE constraint' in error_msg or 'unique constraint' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'A fragment with this key already exists or a product with this name already exists',
                'code': 'DUPLICATE_ENTRY',
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


# ==================== ENDPOINT: LIST FRAGMENTS ====================





@narrative_bp.route('/fragments', methods=['GET'])


def list_fragments():


    """


    Lista fragmentos narrativos con filtros, búsqueda y paginación


    


    Query Parameters:


    - page: int (default: 1) - Número de página


    - per_page: int (default: 20, max: 100) - Items por página


    - search: str - Búsqueda en key y text


    - is_locked: bool - Filtrar por fragmentos bloqueados


    - required_role: str - Filtrar por rol requerido ('free', 'vip', null)


    - has_choices: bool - Filtrar fragmentos con/sin decisiones


    - min_besitos_min: int - Besitos mínimos >= valor


    - min_besitos_max: int - Besitos mínimos <= valor


    - sort_by: str - Campo para ordenar (key, created_at, min_besitos)


    - sort_order: str - Orden (asc, desc)


    - include: str - Relaciones a incluir (comma-separated: choices,unlock_product)


    


    Response Success (200):


    {


        "success": true,


        "data": [


            {


                "id": 156,


                "key": "CAP10_INTRO",


                "text": "Entraste a la habitación oscura...",


                "image_url": "https://...",


                "min_besitos": 0,


                "reward_besitos": 10,


                "required_role": null,


                "is_locked": true,


                "unlock_product_id": 87,


                "choices_count": 2,


                "created_at": "2024-11-29T10:30:00",


                "unlock_product": {  // Solo si include=unlock_product


                    "id": 87,


                    "name": "Acceso Capítulo 10",


                    "price": 50


                },


                "choices": [  // Solo si include=choices


                    {


                        "id": 201,


                        "text": "Entrar sigilosamente",


                        "destination_fragment_key": "CAP10_SIGILO"


                    }


                ]


            }


        ],


        "pagination": {


            "page": 1,


            "per_page": 20,


            "total": 45,


            "total_pages": 3,


            "has_next": true,


            "has_prev": false


        },


        "filters_applied": {


            "search": null,


            "is_locked": null,


            "required_role": null


        }


    }


    """


    


    try:


        # 1. Obtener parámetros de query


        page = request.args.get('page', 1, type=int)


        per_page = request.args.get('per_page', 20, type=int)


        search = request.args.get('search', type=str)


        is_locked_str = request.args.get('is_locked', type=str)  # 'true', 'false', o None


        required_role = request.args.get('required_role', type=str)


        has_choices_str = request.args.get('has_choices', type=str)


        min_besitos_min = request.args.get('min_besitos_min', type=int)


        min_besitos_max = request.args.get('min_besitos_max', type=int)


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


        query = select(StoryFragment)


        


        # 4. Aplicar filtros


        filters_applied = {}


        


        # Filtro: Búsqueda en key y text


        if search:


            search_term = f"%{search}%"


            query = query.where(


                or_(StoryFragment.key.ilike(search_term), StoryFragment.text.ilike(search_term))


            )


            filters_applied['search'] = search


            logger.info(f"Aplicando filtro de búsqueda: {search}")


        


        # Filtro: is_locked (fragmentos con unlock_product_id)


        if is_locked_str is not None:


            is_locked = is_locked_str.lower() == 'true'


            if is_locked:


                query = query.join(ShopItem, StoryFragment.key == ShopItem.unlocks_fragment_key)


            else:


                query = query.outerjoin(ShopItem, StoryFragment.key == ShopItem.unlocks_fragment_key).where(ShopItem.id.is_(None))


            filters_applied['is_locked'] = is_locked





        # Filtro: required_role


        if required_role is not None:


            if required_role.lower() == 'null' or required_role == '':


                query = query.where(StoryFragment.required_role.is_(None))


                filters_applied['required_role'] = None


            else:


                query = query.where(StoryFragment.required_role == required_role)


                filters_applied['required_role'] = required_role


        


        # Filtro: min_besitos range


        if min_besitos_min is not None:


            query = query.where(StoryFragment.min_besitos >= min_besitos_min)


            filters_applied['min_besitos_min'] = min_besitos_min


        


        if min_besitos_max is not None:


            query = query.where(StoryFragment.min_besitos <= min_besitos_max)


            filters_applied['min_besitos_max'] = min_besitos_max


        


        # Filtro: has_choices (fragmentos con/sin decisiones)


        if has_choices_str is not None:


            from sqlalchemy import exists


            has_choices = has_choices_str.lower() == 'true'


            


            if has_choices:


                query = query.where(exists().where(NarrativeChoice.source_fragment_id == StoryFragment.id))


            else:


                query = query.where(~exists().where(NarrativeChoice.source_fragment_id == StoryFragment.id))


            filters_applied['has_choices'] = has_choices


        


        # 5. Aplicar ordenamiento


        valid_sort_fields = {


            'key': StoryFragment.key,


            'created_at': StoryFragment.created_at,


            'min_besitos': StoryFragment.min_besitos,


            'reward_besitos': StoryFragment.reward_besitos


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


        


        logger.info(f"Ordenando por {sort_by} {sort_order}")


        


        # 6. Contar total (antes de paginación)


        count_query = select(func.count()).select_from(query.subquery())


        total = db.session.execute(count_query).scalar()


        


        # 7. Aplicar paginación


        offset = (page - 1) * per_page


        query = query.offset(offset).limit(per_page)


        


        # 8. Eager loading (si se solicita)


        include_list = [i.strip() for i in include.split(',') if i.strip()]


        


        if 'choices' in include_list:


            from sqlalchemy.orm import selectinload


            query = query.options(selectinload(StoryFragment.choices))


            logger.info("Eager loading: choices")


        


        if 'unlock_product' in include_list:


            from sqlalchemy.orm import joinedload


            query = query.options(joinedload(StoryFragment.unlock_product))


            logger.info("Eager loading: unlock_product")


        


        # 9. Ejecutar query


        result = db.session.execute(query)


        fragments = result.scalars().all()


        


        logger.info(f"✓ Encontrados {len(fragments)} fragmentos (total: {total})")


        


        # 10. Serializar resultados


        data = []


        for fragment in fragments:


            unlock_product = fragment.unlock_product


            fragment_dict = {


                'id': fragment.id,


                'key': fragment.key,


                'text': fragment.text,


                'image_url': fragment.image_url,


                'min_besitos': fragment.min_besitos,


                'reward_besitos': fragment.reward_besitos,


                'required_role': fragment.required_role,


                'is_locked': unlock_product is not None,


                'unlock_product_id': unlock_product.id if unlock_product else None,


                'auto_next_fragment_key': fragment.auto_next_fragment_key,


                'created_at': fragment.created_at.isoformat() if fragment.created_at else None


            }


            


            if 'choices' in include_list:


                fragment_dict['choices_count'] = len(fragment.choices)


                fragment_dict['choices'] = [


                    {


                        'id': choice.id,


                        'text': choice.text,


                        'destination_fragment_key': choice.destination_fragment_key,


                        'required_besitos': choice.required_besitos,


                        'required_role': choice.required_role


                    }


                    for choice in fragment.choices


                ]


            else:


                choices_count = db.session.execute(


                    select(func.count()).where(NarrativeChoice.source_fragment_id == fragment.id)


                ).scalar()


                fragment_dict['choices_count'] = choices_count


            


            if 'unlock_product' in include_list and unlock_product:


                fragment_dict['unlock_product'] = {


                    'id': unlock_product.id,


                    'name': unlock_product.name,


                    'price': unlock_product.price,


                    'description': unlock_product.description,


                    'is_vip_only': unlock_product.is_vip_only


                }


            


            data.append(fragment_dict)


        


        # 11. Calcular paginación


        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0


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


            'pagination': pagination,


            'filters_applied': filters_applied


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








# ==================== ENDPOINT: GET SINGLE FRAGMENT ====================





@narrative_bp.route('/fragments/<string:fragment_key>', methods=['GET'])


def get_fragment(fragment_key):


    """


    Obtiene un fragmento específico por su key con todas sus relaciones


    


    Path Parameters:


    - fragment_key: str - Key del fragmento (ej: "CAP10_INTRO")


    


    Query Parameters:


    - include: str - Relaciones a incluir (comma-separated: choices,unlock_product,statistics)


    


    Response Success (200):


    {


        "success": true,


        "data": {


            "id": 156,


            "key": "CAP10_INTRO",


            "text": "Entraste a la habitación oscura...",


            "image_url": "https://...",


            "min_besitos": 0,


            "reward_besitos": 10,


            "required_role": null,


            "unlock_product_id": 87,


            "auto_next_fragment_key": "CAP10_NEXT",


            "created_at": "2024-11-29T10:30:00",


            "unlock_product": {...},


            "choices": [...],


            "statistics": {


                "views": 342,


                "unique_viewers": 289


            }


        }


    }


    


    Response Error (404):


    {


        "success": false,


        "error": "Fragment with key 'INVALID_KEY' not found",


        "code": "FRAGMENT_NOT_FOUND"


    }


    """


    


    try:


        # 1. Obtener parámetros


        include = request.args.get('include', '', type=str)


        include_list = [i.strip() for i in include.split(',') if i.strip()]


        


        # 2. Construir query con eager loading si se solicita


        query = select(StoryFragment).where(StoryFragment.key == fragment_key)


        


        if 'choices' in include_list:


            from sqlalchemy.orm import selectinload


            query = query.options(selectinload(StoryFragment.choices))


        


        if 'unlock_product' in include_list:


            from sqlalchemy.orm import joinedload


            query = query.options(joinedload(StoryFragment.unlock_product))


        


        # 3. Ejecutar query


        result = db.session.execute(query)


        fragment = result.scalar_one_or_none()


        


        if not fragment:


            logger.warning(f"⚠️  Fragmento no encontrado: {fragment_key}")


            return jsonify({


                'success': False,


                'error': f"Fragment with key '{fragment_key}' not found",


                'code': 'FRAGMENT_NOT_FOUND'


            }), 404


        


        logger.info(f"✓ Fragmento encontrado: {fragment_key} (ID: {fragment.id})")


        


        # 4. Serializar fragmento


        unlock_product = fragment.unlock_product


        fragment_dict = {


            'id': fragment.id,


            'key': fragment.key,


            'text': fragment.text,


            'image_url': fragment.image_url,


            'min_besitos': fragment.min_besitos,


            'reward_besitos': fragment.reward_besitos,


            'required_role': fragment.required_role,


            'unlock_product_id': unlock_product.id if unlock_product else None,


            'auto_next_fragment_key': fragment.auto_next_fragment_key,


            'created_at': fragment.created_at.isoformat() if fragment.created_at else None


        }


        


        # 5. Incluir relaciones si se solicitaron


        if 'choices' in include_list:


            fragment_dict['choices'] = [


                {


                    'id': choice.id,


                    'text': choice.text,


                    'destination_fragment_key': choice.destination_fragment_key,


                    'required_besitos': choice.required_besitos,


                    'required_role': choice.required_role


                }


                for choice in fragment.choices


            ]


        


        if 'unlock_product' in include_list and unlock_product:


            fragment_dict['unlock_product'] = {


                'id': unlock_product.id,


                'name': unlock_product.name,


                'price': unlock_product.price,


                'description': unlock_product.description,


                'is_vip_only': unlock_product.is_vip_only


            }


        


        # 6. Incluir estadísticas si se solicitó


        if 'statistics' in include_list:


            # TODO: Implementar cuando exista tabla de estadísticas


            # Por ahora, retornar datos mock


            fragment_dict['statistics'] = {


                'views': 0,


                'unique_viewers': 0,


                'note': 'Statistics not yet implemented'


            }


        


        # 7. Retornar respuesta


        return jsonify({


            'success': True,


            'data': fragment_dict


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

