from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, and_, select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from admin_panel.extensions import db
from database.models import User, ShopItem, UserPurchase, ProductFile
from database.narrative_models import StoryFragment, UserNarrativeState
import logging

analytics_bp = Blueprint('analytics_api', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/overview', methods=['GET'])
def get_overview():
    """Métricas generales del dashboard"""
    try:
        # Total de usuarios
        total_users = db.session.execute(
            select(func.count()).select_from(User)
        ).scalar()

        # Usuarios VIP
        vip_users = db.session.execute(
            select(func.count()).select_from(User).where(User.role == 'vip')
        ).scalar()

        # Besitos en circulación
        total_besitos = db.session.execute(
            select(func.sum(User.points))
        ).scalar() or 0

        # Total de ventas (en besitos)
        total_sales = db.session.execute(
            select(func.sum(UserPurchase.price_paid))
        ).scalar() or 0

        # Fragmentos publicados
        total_fragments = db.session.execute(
            select(func.count()).select_from(StoryFragment)
        ).scalar()

        # Productos activos
        active_products = db.session.execute(
            select(func.count()).select_from(ShopItem).where(ShopItem.is_active == True)
        ).scalar()

        # Usuarios activos (últimos 7 días)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.session.execute(
            select(func.count()).select_from(User).where(User.last_activity_at >= week_ago)
        ).scalar()

        # Total de compras
        total_purchases = db.session.execute(
            select(func.count()).select_from(UserPurchase)
        ).scalar()

        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'vip_users': vip_users,
                'total_besitos': int(total_besitos),
                'total_sales': int(total_sales),
                'total_fragments': total_fragments,
                'active_products': active_products,
                'active_users_week': active_users,
                'total_purchases': total_purchases
            }
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener resumen: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener resumen: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/users/activity', methods=['GET'])
def get_user_activity():
    """Actividad de usuarios en los últimos 30 días"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Agrupar por día
        activity = db.session.query(
            func.date(User.last_activity_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.last_activity_at >= start_date
        ).group_by(
            func.date(User.last_activity_at)
        ).order_by('date').all()

        # Formatear datos
        labels = []
        data = []
        for record in activity:
            labels.append(record.date.strftime('%Y-%m-%d') if record.date else 'Unknown')
            data.append(record.count)

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'values': data
            }
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener actividad de usuarios: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener actividad de usuarios: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/users/distribution', methods=['GET'])
def get_user_distribution():
    """Distribución de usuarios por rol"""
    try:
        distribution = db.session.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()

        labels = []
        data = []
        for record in distribution:
            role_name = record.role or 'free'
            labels.append(role_name.upper())
            data.append(record.count)

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'values': data
            }
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener distribución de usuarios: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener distribución de usuarios: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/products/top-selling', methods=['GET'])
def get_top_selling_products():
    """Productos más vendidos"""
    try:
        limit = request.args.get('limit', 10, type=int)

        top_products = db.session.query(
            ShopItem.name,
            func.count(UserPurchase.id).label('sales_count'),
            func.sum(ShopItem.price).label('revenue')
        ).join(
            UserPurchase,
            UserPurchase.shop_item_id == ShopItem.id
        ).group_by(
            ShopItem.id,
            ShopItem.name
        ).order_by(
            desc('sales_count')
        ).limit(limit).all()

        labels = []
        sales = []
        revenue = []

        for product in top_products:
            labels.append(product.name)
            sales.append(product.sales_count)
            revenue.append(int(product.revenue or 0))

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'sales': sales,
                'revenue': revenue
            }
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener productos más vendidos: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener productos más vendidos: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/fragments/top-visited', methods=['GET'])
def get_top_visited_fragments():
    """Fragmentos más visitados"""
    try:
        limit = request.args.get('limit', 10, type=int)

        top_fragments = db.session.query(
            StoryFragment.key,
            StoryFragment.text,
            func.count(UserNarrativeState.id).label('visit_count')
        ).join(
            UserNarrativeState,
            UserNarrativeState.current_fragment_key == StoryFragment.key
        ).group_by(
            StoryFragment.key,
            StoryFragment.text
        ).order_by(
            desc('visit_count')
        ).limit(limit).all()

        labels = []
        visits = []

        for fragment in top_fragments:
            # Usar key como label, limitar texto si es muy largo
            label = fragment.key
            labels.append(label)
            visits.append(fragment.visit_count)

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'values': visits
            }
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener fragmentos más visitados: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener fragmentos más visitados: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/sales/trend', methods=['GET'])
def get_sales_trend():
    """Tendencia de ventas (últimos 30 días)"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)

        sales_trend = db.session.query(
            func.date(UserPurchase.purchased_at).label('date'),
            func.count(UserPurchase.id).label('count'),
            func.sum(ShopItem.price).label('revenue')
        ).join(
            ShopItem,
            ShopItem.id == UserPurchase.shop_item_id
        ).filter(
            UserPurchase.purchased_at >= start_date
        ).group_by(
            func.date(UserPurchase.purchased_at)
        ).order_by('date').all()

        labels = []
        counts = []
        revenues = []

        for record in sales_trend:
            labels.append(record.date.strftime('%Y-%m-%d') if record.date else 'Unknown')
            counts.append(record.count)
            revenues.append(int(record.revenue or 0))

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'sales_count': counts,
                'revenue': revenues
            }
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener tendencia de ventas: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener tendencia de ventas: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/recent/purchases', methods=['GET'])
def get_recent_purchases():
    """Últimas compras realizadas"""
    try:
        limit = request.args.get('limit', 10, type=int)

        recent = db.session.query(
            UserPurchase.id,
            UserPurchase.purchased_at,
            User.username,
            ShopItem.name.label('product_name'),
            ShopItem.price
        ).join(
            User,
            User.id == UserPurchase.user_id
        ).join(
            ShopItem,
            ShopItem.id == UserPurchase.shop_item_id
        ).order_by(
            desc(UserPurchase.purchased_at)
        ).limit(limit).all()

        purchases = []
        for purchase in recent:
            purchases.append({
                'id': purchase.id,
                'date': purchase.purchased_at.strftime('%Y-%m-%d %H:%M') if purchase.purchased_at else 'Unknown',
                'username': purchase.username or 'Unknown',
                'product': purchase.product_name,
                'price': purchase.price
            })

        return jsonify({
            'success': True,
            'data': purchases
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener compras recientes: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener compras recientes: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/products/ranking', methods=['GET'])
def get_products_ranking():
    """Ranking de productos por ventas"""
    try:
        limit = request.args.get('limit', 5, type=int)

        ranking = db.session.query(
            ShopItem.id,
            ShopItem.name,
            ShopItem.price,
            func.count(UserPurchase.id).label('sales_count'),
            func.sum(ShopItem.price).label('total_revenue')
        ).outerjoin(
            UserPurchase,
            UserPurchase.shop_item_id == ShopItem.id
        ).group_by(
            ShopItem.id,
            ShopItem.name,
            ShopItem.price
        ).order_by(
            desc('sales_count')
        ).limit(limit).all()

        products = []
        for product in ranking:
            products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'sales_count': product.sales_count,
                'total_revenue': int(product.total_revenue or 0)
            })

        return jsonify({
            'success': True,
            'data': products
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener ranking de productos: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener ranking de productos: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@analytics_bp.route('/fragments/ranking', methods=['GET'])
def get_fragments_ranking():
    """Ranking de fragmentos por visitas"""
    try:
        limit = request.args.get('limit', 5, type=int)

        ranking = db.session.query(
            StoryFragment.key,
            StoryFragment.text,
            func.count(UserNarrativeState.id).label('visit_count')
        ).outerjoin(
            UserNarrativeState,
            UserNarrativeState.current_fragment_key == StoryFragment.key
        ).group_by(
            StoryFragment.key,
            StoryFragment.text
        ).order_by(
            desc('visit_count')
        ).limit(limit).all()

        fragments = []
        for fragment in ranking:
            fragments.append({
                'key': fragment.key,
                'text': fragment.text[:100] + '...' if len(fragment.text) > 100 else fragment.text,
                'visit_count': fragment.visit_count
            })

        return jsonify({
            'success': True,
            'data': fragments
        }), 200

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al obtener ranking de fragmentos: {e}")
        return jsonify({'success': False, 'error': 'Error de base de datos'}), 500
    except Exception as e:
        logger.error(f"Error inesperado al obtener ranking de fragmentos: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500