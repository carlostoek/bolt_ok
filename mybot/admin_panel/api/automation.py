"""
Blueprint API para gestión de triggers/automatización
"""
from flask import Blueprint

automation_bp = Blueprint('automation', __name__, url_prefix='/api/v1/automation')

# TODO: Implementar endpoints