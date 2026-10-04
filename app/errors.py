"""
MedLoc - Manejadores globales de errores HTTP.
Registra respuestas JSON estandarizadas para errores comunes
(404, 405, 422, 500) en lugar del HTML por defecto de Flask.
"""
from flask import Flask
from .utils.responses import error_response


def register_error_handlers(app: Flask) -> None:
    """Adjunta manejadores de error a la instancia de Flask."""

    @app.errorhandler(400)
    def bad_request(e):
        return error_response(f"Solicitud malformada: {e.description}", 400)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("La ruta solicitada no existe en este servidor.", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("Método HTTP no permitido para esta ruta.", 405)

    @app.errorhandler(409)
    def conflict(e):
        return error_response(str(e.description), 409)

    @app.errorhandler(500)
    def internal_error(e):
        return error_response("Error interno del servidor.", 500)
