from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func, desc, and_
from datetime import datetime, timedelta
from admin_panel.extensions import db
from database.models import (
    User, UserPurchase, ShopItem, UserNarrativeState, 
    ProductFile, ConfigEntry
)
from database.narrative_models import StoryFragment, UserNarrativeState as NarrativeState
import logging

users_bp = Blueprint('users_api', __name__)
logger = logging.getLogger(__name__)


@users_bp.route('/users', methods=['GET'])
def list_users():
    """Lista de usuarios con filtros avanzados"""
    try:
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filtros
        search = request.args.get('search', '').strip()
        role = request.args.get('role', '').strip()
        min_besitos = request.args.get('min_besitos', type=int)
        max_besitos = request.args.get('max_besitos', type=int)
        is_blocked = request.args.get('is_blocked', '').strip()
        days_inactive = request.args.get('days_inactive', type=int)
        
        # Ordenamiento
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Query base
        query = User.query
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%'),
                    User.id.like(f'%{search}%')
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        if min_besitos is not None:
            query = query.filter(User.points >= min_besitos)
        
        if max_besitos is not None:
            query = query.filter(User.points <= max_besitos)
        
        if is_blocked:
            query = query.filter(User.is_blocked == (is_blocked.lower() == 'true'))
        
        if days_inactive:
            cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
            query = query.filter(User.last_activity_at < cutoff_date)
        
        # Ordenamiento
        if hasattr(User, sort_by):
            column = getattr(User, sort_by)
            query = query.order_by(column.desc() if sort_order == 'desc' else column.asc())
        
        # Paginación
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serializar
        users = []
        for user in paginated.items:
            # Calcular compras totales
            total_purchases = UserPurchase.query.filter_by(user_id=user.id).count()
            
            # Calcular total gastado
            total_spent = db.session.query(
                func.sum(ShopItem.price)
            ).join(
                UserPurchase,
                UserPurchase.shop_item_id == ShopItem.id
            ).filter(
                UserPurchase.user_id == user.id
            ).scalar() or 0
            
            users.append({
                'id': user.id,
                'telegram_id': user.id,
                'telegram_username': user.username or 'Sin username',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Sin nombre',
                'role': user.role or 'free',
                'besitos': user.points,
                'is_blocked': user.is_blocked,
                'last_activity': user.last_activity_at.isoformat() if user.last_activity_at else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'total_purchases': total_purchases,
                'total_spent': int(total_spent)
            })
        
        return jsonify({
            'success': True,
            'data': users,
            'pagination': {
                'current_page': paginated.page,
                'per_page': paginated.per_page,
                'total_items': paginated.total,
                'total_pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list users'
        }), 500


@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Obtener detalles completos de un usuario"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Información de compras
        purchases = UserPurchase.query.filter_by(user_id=user.id).all()
        purchase_data = []
        total_spent = 0
        
        for purchase in purchases:
            product = ShopItem.query.get(purchase.shop_item_id)
            if product:
                purchase_data.append({
                    'id': purchase.id,
                    'product_name': product.name,
                    'price': product.price,
                    'purchased_at': purchase.purchased_at.isoformat() if purchase.purchased_at else None
                })
                total_spent += product.price
        
        # Información narrativa
        narrative_state = NarrativeState.query.filter_by(user_id=user.id).first()
        narrative_data = None
        
        if narrative_state:
            current_fragment = StoryFragment.query.filter_by(
                key=narrative_state.current_fragment_key
            ).first()
            
            narrative_data = {
                'current_fragment_key': narrative_state.current_fragment_key,
                'current_fragment_text': current_fragment.text[:100] + '...' if current_fragment else None,
                'started_at': narrative_state.narrative_started_at.isoformat() if narrative_state.narrative_started_at else None,
                'last_interaction': narrative_state.last_activity_at.isoformat() if narrative_state.last_activity_at else None
            }
        
        # Estadísticas
        days_since_registration = (datetime.utcnow() - user.created_at).days if user.created_at else 0
        days_since_activity = (datetime.utcnow() - user.last_activity_at).days if user.last_activity_at else 999
        
        return jsonify({
            'success': True,
            'data': {
                'id': user.id,
                'telegram_id': user.id,
                'telegram_username': user.username or 'Sin username',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Sin nombre',
                'role': user.role or 'free',
                'besitos': user.points,
                'is_blocked': user.is_blocked,
                'last_activity': user.last_activity_at.isoformat() if user.last_activity_at else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'purchases': purchase_data,
                'total_purchases': len(purchase_data),
                'total_spent': total_spent,
                'narrative': narrative_data,
                'stats': {
                    'days_since_registration': days_since_registration,
                    'days_since_activity': days_since_activity,
                    'is_active': days_since_activity < 7
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user details'
        }), 500


@users_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Actualizar información del usuario"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        
        # Actualizar campos permitidos
        if 'besitos' in data:
            user.points = max(0, int(data['besitos']))
        
        if 'role' in data and data['role'] in ['free', 'vip']:
            user.role = data['role']
        
        if 'is_blocked' in data:
            user.is_blocked = bool(data['is_blocked'])
        
        db.session.commit()
        
        # Log de la acción
        logger.info(f"User {user_id} updated: {data}")
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': {
                'id': user.id,
                'besitos': user.points,
                'role': user.role,
                'is_blocked': user.is_blocked
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update user'
        }), 500


@users_bp.route('/users/<int:user_id>/add-besitos', methods=['POST'])
def add_besitos(user_id):
    """Añadir o quitar besitos manualmente"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        amount = data.get('amount', 0)
        
        if not isinstance(amount, int):
            return jsonify({
                'success': False,
                'error': 'Amount must be an integer'
            }), 400
        
        # Actualizar besitos
        previous_amount = user.points
        user.points = max(0, user.points + amount)
        
        db.session.commit()
        
        # Log
        logger.info(f"Besitos adjusted for user {user_id}: {previous_amount} -> {user.points} (change: {amount})")
        
        return jsonify({
            'success': True,
            'message': f'Besitos {"añadidos" if amount > 0 else "restados"} correctamente',
            'data': {
                'previous_amount': previous_amount,
                'new_amount': user.points,
                'change': amount
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding besitos to user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to add besitos'
        }), 500


@users_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
def change_role(user_id):
    """Cambiar rol del usuario (Free ↔ VIP)"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        new_role = data.get('role', '').lower()
        
        if new_role not in ['free', 'vip']:
            return jsonify({
                'success': False,
                'error': 'Invalid role. Must be "free" or "vip"'
            }), 400
        
        previous_role = user.role
        user.role = new_role
        
        db.session.commit()
        
        # Log
        logger.info(f"Role changed for user {user_id}: {previous_role} -> {new_role}")
        
        return jsonify({
            'success': True,
            'message': f'Rol cambiado a {new_role.upper()} correctamente',
            'data': {
                'previous_role': previous_role,
                'new_role': new_role
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing role for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to change role'
        }), 500


@users_bp.route('/users/<int:user_id>/toggle-block', methods=['POST'])
def toggle_block(user_id):
    """Bloquear/desbloquear usuario"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        user.is_blocked = not user.is_blocked
        
        db.session.commit()
        
        logger.info(f"User {user_id} {'blocked' if user.is_blocked else 'unblocked'}")
        
        return jsonify({
            'success': True,
            'message': f'Usuario {"bloqueado" if user.is_blocked else "desbloqueado"} correctamente',
            'data': {
                'is_blocked': user.is_blocked
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling block for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to toggle block status'
        }), 500


@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Eliminar usuario (con precaución)"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Eliminar relaciones primero
        UserPurchase.query.filter_by(user_id=user.id).delete()
        NarrativeState.query.filter_by(user_id=user.id).delete()
        
        # Eliminar usuario
        db.session.delete(user)
        db.session.commit()
        
        logger.warning(f"User {user_id} deleted permanently")
        
        return jsonify({
            'success': True,
            'message': 'Usuario eliminado correctamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete user'
        }), 500


@users_bp.route('/users/stats', methods=['GET'])
def get_users_stats():
    """Estadísticas rápidas de usuarios"""
    try:
        total_users = User.query.count()
        vip_users = User.query.filter_by(role='vip').count()
        blocked_users = User.query.filter_by(is_blocked=True).count()
        
        # Usuarios activos (últimos 7 días)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = User.query.filter(User.last_activity_at >= week_ago).count()
        
        # Promedio de besitos
        avg_besitos = db.session.query(func.avg(User.points)).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'vip_users': vip_users,
                'free_users': total_users - vip_users,
                'blocked_users': blocked_users,
                'active_users_week': active_users,
                'avg_besitos': round(avg_besitos, 2)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get users stats'
        }), 500


@users_bp.route('/users/bulk-action', methods=['POST'])
def bulk_action():
    """Acciones masivas sobre múltiples usuarios"""
    try:
        data = request.get_json()
        
        user_ids = data.get('user_ids', [])
        action = data.get('action', '')
        value = data.get('value')
        
        if not user_ids:
            return jsonify({
                'success': False,
                'error': 'No users specified'
            }), 400
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            return jsonify({
                'success': False,
                'error': 'No users found'
            }), 404
        
        affected_count = 0
        
        if action == 'add_besitos' and isinstance(value, int):
            for user in users:
                user.points = max(0, user.points + value)
                affected_count += 1
        
        elif action == 'change_role' and value in ['free', 'vip']:
            for user in users:
                user.role = value
                affected_count += 1
        
        elif action == 'block':
            for user in users:
                user.is_blocked = True
                affected_count += 1
        
        elif action == 'unblock':
            for user in users:
                user.is_blocked = False
                affected_count += 1
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action'
            }), 400
        
        db.session.commit()
        
        logger.info(f"Bulk action '{action}' applied to {affected_count} users")
        
        return jsonify({
            'success': True,
            'message': f'Acción aplicada a {affected_count} usuarios',
            'data': {
                'affected_count': affected_count,
                'action': action
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in bulk action: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to execute bulk action'
        }), 500