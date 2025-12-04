"""
Flask App Principal del Panel de Administración
"""
import sys
import os
from pathlib import Path

# Añadir ruta del bot al PYTHONPATH para importar sus modelos
BOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(BOT_PATH))

from flask import Flask, render_template, jsonify, request
import logging

# Importar extensiones
from admin_panel.extensions import db, cors
from admin_panel.config import config

# Importar blueprints (cuando existan)
from admin_panel.api.narrative import narrative_bp
from admin_panel.api.shop import shop_bp
from admin_panel.api.automation import automation_bp
from admin_panel.api.references import references_bp
from admin_panel.api.analytics import analytics_bp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """
    Factory para crear la aplicación Flask
    
    Args:
        config_name: Nombre de la configuración a usar ('development', 'production')
    
    Returns:
        Flask app configurada
    """
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    config[config_name].init_app(app) if hasattr(config[config_name], 'init_app') else None
    
    logger.info(f"🚀 Iniciando app con configuración: {config_name}")
    logger.info(f"📁 Base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Inicializar extensiones
    db.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {"origins": app.config['CORS_ORIGINS']}
    })
    
    # Importar modelos del bot (para que SQLAlchemy los conozca)
    with app.app_context():
        try:
            # The models are in the 'database' directory, relative to the project root.
            # Since BOT_PATH is the project root, we can import them directly.
            from database.models import User, ShopItem
            from database.narrative_models import StoryFragment, NarrativeChoice
            logger.info("✓ Modelos del bot importados correctamente")
        except ImportError as e:
            logger.error(f"❌ Error importando modelos del bot: {e}")
            logger.error("Verifica que la estructura del proyecto sea correcta")
    
    # Registrar blueprints de API
    app.register_blueprint(narrative_bp)
    app.register_blueprint(shop_bp, url_prefix='/api/v1/shop')
    app.register_blueprint(automation_bp)
    app.register_blueprint(references_bp)
    app.register_blueprint(analytics_bp, url_prefix='/api/v1/analytics')
    logger.info("✓ Blueprints de API registrados")
    
    # Registrar rutas de vistas (templates)
    register_template_routes(app)
    
    # Registrar manejadores de errores
    register_error_handlers(app)
    
    # Middleware de seguridad (IP whitelist básico)
    register_security_middleware(app)
    
    logger.info("✓ Aplicación Flask configurada exitosamente")
    
    return app


def register_template_routes(app):
    """Registra rutas que renderizan templates HTML"""
    
    @app.route('/')
    def index():
        """Página principal - Dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/narrative/fragments')
    def fragments_list():
        """Lista de fragmentos narrativos"""
        return render_template('fragments/list.html')
    
    @app.route('/narrative/fragments/new')
    def fragments_new():
        """Formulario para crear fragmento"""
        return render_template('fragments/new.html')
    
    @app.route('/narrative/fragments/<fragment_key>/edit')
    def fragments_edit(fragment_key):
        """Formulario para editar fragmento"""
        return render_template('fragments/edit.html', fragment_key=fragment_key)
    
    @app.route('/shop/products')
    def shop_products_list():
        """Lista de productos"""
        return render_template('shop/list.html')

    @app.route('/shop/products/new')
    def shop_products_new():
        """Formulario de creación de producto"""
        return render_template('shop/new.html')

    @app.route('/shop/products/<int:product_id>/edit')
    def shop_products_edit(product_id):
        """Formulario de edición de producto"""
        return render_template('shop/edit.html', product_id=product_id)
    
    @app.route('/automation/triggers')
    def triggers_list():
        """Lista de triggers configurables"""
        return render_template('automation/list.html')
    
    @app.route('/automation/triggers/new')
    def triggers_new():
        """Formulario para crear trigger"""
        return render_template('automation/new.html')
    
    logger.info("✓ Rutas de templates registradas")


def register_error_handlers(app):
    """Registra manejadores de errores HTTP"""
    
    @app.errorhandler(404)
    def not_found(error):
        """Maneja errores 404"""
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Resource not found',
                'path': request.path
            }), 404
        return render_template('base.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Maneja errores 500"""
        logger.error(f"Error interno: {error}")
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
        return render_template('base.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """Maneja errores 403 (acceso denegado)"""
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        return "Access Denied", 403
    
    logger.info("✓ Manejadores de errores registrados")


def register_security_middleware(app):
    """Registra middleware de seguridad básico"""
    
    @app.before_request
    def check_ip_whitelist():
        """Verifica que la IP esté en la whitelist (solo en producción)"""
        # En desarrollo, permitir todas las IPs
        if app.config['DEBUG']:
            return None
        
        client_ip = request.remote_addr
        allowed_ips = app.config['ADMIN_IPS']
        
        if client_ip not in allowed_ips:
            logger.warning(f"⚠️  Acceso denegado desde IP: {client_ip}")
            return jsonify({
                'success': False,
                'error': 'Access denied from your IP'
            }), 403
        
        return None
    
    logger.info("✓ Middleware de seguridad registrado")


if __name__ == '__main__':
    # Determinar entorno desde variable de entorno
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    
    # Iniciar servidor
    # Run in non-debug mode to prevent automatic restarts when launched as __main__
    app.run(
        host='127.0.0.1',
        port=os.getenv('FLASK_RUN_PORT', '5000'),
        debug=False # Force debug to False when run as main
    )