"""
Extensiones de Flask instanciadas sin app para evitar imports circulares.
Se inicializan con `extension.init_app(app)` en el Application Factory.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Instancia global de SQLAlchemy (sin app ligada aún)
db = SQLAlchemy()

# CORS: permite peticiones cross-origin desde el frontend
cors = CORS()
