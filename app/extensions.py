"""
Extensiones de Flask instanciadas sin app para evitar imports circulares.
Se inicializan con `extension.init_app(app)` en el Application Factory.
"""
from flask_sqlalchemy import SQLAlchemy

# Instancia global de SQLAlchemy (sin app ligada aún)
db = SQLAlchemy()
