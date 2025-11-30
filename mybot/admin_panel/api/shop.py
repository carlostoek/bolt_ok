"""
Blueprint API para gestión de tienda
"""
from flask import Blueprint

shop_bp = Blueprint('shop', __name__, url_prefix='/api/v1/shop')

# TODO: Implementar endpoints