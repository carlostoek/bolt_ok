"""
Extensiones de Flask compartidas
Se inicializan aquí para evitar import circular
"""
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Instancia de SQLAlchemy (se inicializa en app.py)
db = SQLAlchemy()

# Instancia de CORS (se inicializa en app.py)
cors = CORS()