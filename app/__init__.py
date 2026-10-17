"""
MedLoc - Application Factory
Inicializa la aplicación Flask usando el patrón Application Factory.
"""
from flask import Flask
from .extensions import db, cors
from .config import config_by_name


def create_app(config_name: str = "default") -> Flask:
    """
    Crea y configura la instancia de la aplicación Flask.

    Args:
        config_name: Nombre del entorno de configuración ('default', 'development', 'production').

    Returns:
        La instancia de Flask configurada.
    """
    app = Flask(__name__)

    # Cargar configuración desde el objeto de config correspondiente
    app.config.from_object(config_by_name[config_name])

    # Inicializar extensiones con la app
    db.init_app(app)

    # CORS: permite peticiones desde el frontend (React en dev y producción)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Registrar manejadores globales de error (respuestas JSON estandarizadas)
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Registrar Blueprints
    _register_blueprints(app)

    return app


def _register_blueprints(app: Flask) -> None:
    """Registra todos los blueprints de la aplicación."""
    from .routes.auth import auth_bp
    from .routes.usuarios import usuarios_bp
    from .routes.farmacias import farmacias_bp
    from .routes.medicamentos import medicamentos_bp
    from .routes.inventario import inventario_bp
    from .routes.reservas import reservas_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(usuarios_bp, url_prefix="/api/v1/usuarios")
    app.register_blueprint(farmacias_bp, url_prefix="/api/v1/farmacias")
    app.register_blueprint(medicamentos_bp, url_prefix="/api/v1/medicamentos")
    app.register_blueprint(inventario_bp, url_prefix="/api/v1/inventario")
    app.register_blueprint(reservas_bp, url_prefix="/api/v1/reservas")
