from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func
from admin_panel.extensions import db
from database.models import ShopItem, ProductFile, UserPurchase
import logging

shop_bp = Blueprint('shop_api', __name__)
logger = logging.getLogger(__name__)

@shop_bp.route('/products', methods=['GET'])
def list_products():
    """Lista productos con filtros y paginación"""
    try:
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filtros
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        is_active = request.args.get('is_active', '').strip()
        is_vip_only = request.args.get('is_vip_only', '').strip()
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        
        # Ordenamiento
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Query base
        query = ShopItem.query
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    ShopItem.name.ilike(f'%{search}%'),
                    ShopItem.description.ilike(f'%{search}%')
                )
            )
        
        if category:
            query = query.filter(ShopItem.category == category)
        
        if is_active:
            query = query.filter(ShopItem.is_active == (is_active.lower() == 'true'))
        
        if is_vip_only:
            query = query.filter(ShopItem.is_vip_only == (is_vip_only.lower() == 'true'))
        
        if min_price is not None:
            query = query.filter(ShopItem.price >= min_price)
        
        if max_price is not None:
            query = query.filter(ShopItem.price <= max_price)
        
        # Ordenamiento
        if hasattr(ShopItem, sort_by):
            column = getattr(ShopItem, sort_by)
            query = query.order_by(column.desc() if sort_order == 'desc' else column.asc())
        
        # Paginación
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serializar
        products = [{
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'is_vip_only': item.is_vip_only,
            'category': item.category,
            'is_active': item.is_active,
            'stock': item.stock,
            'files_count': len(item.files) if hasattr(item, 'files') else 0,
            'created_at': item.created_at.isoformat() if item.created_at else None
        } for item in paginated.items]
        
        return jsonify({
            'success': True,
            'data': products,
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
        logger.error(f"Error listing products: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list products'
        }), 500


@shop_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Obtener detalles de un producto"""
    try:
        product = ShopItem.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        # Incluir archivos
        files = []
        if hasattr(product, 'files'):
            files = [{
                'id': f.id,
                'file_url': f.file_url,
                'file_type': f.file_type,
                'display_order': f.display_order
            } for f in sorted(product.files, key=lambda x: x.display_order)]
        
        return jsonify({
            'success': True,
            'data': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'is_vip_only': product.is_vip_only,
                'category': product.category,
                'is_active': product.is_active,
                'stock': product.stock,
                'files': files,
                'created_at': product.created_at.isoformat() if product.created_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get product'
        }), 500


@shop_bp.route('/products', methods=['POST'])
def create_product():
    """Crear nuevo producto"""
    try:
        data = request.get_json()
        
        # Validaciones
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Name is required',
                'field': 'name'
            }), 400
        
        if data.get('price') is None or data.get('price') < 0:
            return jsonify({
                'success': False,
                'error': 'Valid price is required',
                'field': 'price'
            }), 400
        
        # Crear producto
        product = ShopItem(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            is_vip_only=data.get('is_vip_only', False),
            category=data.get('category', 'content'),
            is_active=data.get('is_active', True),
            stock=data.get('stock')
        )
        
        db.session.add(product)
        db.session.flush()  # Para obtener el ID
        
        # Crear archivos asociados si existen
        files_data = data.get('files', [])
        for file_data in files_data:
            if file_data.get('file_url'):
                product_file = ProductFile(
                    product_id=product.id,
                    file_url=file_data['file_url'],
                    file_type=file_data.get('file_type', 'other'),
                    display_order=file_data.get('display_order', 0)
                )
                db.session.add(product_file)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product created successfully',
            'data': {
                'id': product.id,
                'name': product.name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating product: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create product'
        }), 500


@shop_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Actualizar producto existente"""
    try:
        product = ShopItem.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        data = request.get_json()
        
        # Actualizar campos
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'is_vip_only' in data:
            product.is_vip_only = data['is_vip_only']
        if 'category' in data:
            product.category = data['category']
        if 'is_active' in data:
            product.is_active = data['is_active']
        if 'stock' in data:
            product.stock = data['stock']
        
        # Actualizar archivos si se proporcionan
        if 'files' in data:
            # Eliminar archivos existentes
            if hasattr(product, 'files'):
                for f in product.files:
                    db.session.delete(f)
            
            # Crear nuevos archivos
            for file_data in data['files']:
                if file_data.get('file_url'):
                    product_file = ProductFile(
                        product_id=product.id,
                        file_url=file_data['file_url'],
                        file_type=file_data.get('file_type', 'other'),
                        display_order=file_data.get('display_order', 0)
                    )
                    db.session.add(product_file)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update product'
        }), 500


@shop_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Eliminar producto"""
    try:
        product = ShopItem.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        # Verificar si tiene compras asociadas
        if hasattr(product, 'purchases') and len(product.purchases) > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete product with existing purchases'
            }), 409
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting product: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete product'
        }), 500