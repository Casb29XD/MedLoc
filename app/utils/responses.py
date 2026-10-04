"""
MedLoc - Utilidades de respuesta HTTP estandarizada.
Todas las respuestas de la API siguen el mismo envelope JSON:

Éxito:
  { "status": "success", "data": {...}, "message": "..." }

Error:
  { "status": "error", "message": "...", "errors": {...} }
"""
from __future__ import annotations
from typing import Any
from flask import jsonify


# ── Respuestas de éxito ───────────────────────────────────────────────────────

def success_response(data: Any = None, message: str = "OK", status_code: int = 200):
    """
    Retorna una respuesta JSON de éxito.

    Args:
        data:        Payload principal (dict, list, None).
        message:     Mensaje descriptivo del resultado.
        status_code: Código HTTP (200, 201, etc.).
    """
    body = {"status": "success", "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def created_response(data: Any, message: str = "Recurso creado exitosamente"):
    """Shortcut para respuestas 201 Created."""
    return success_response(data=data, message=message, status_code=201)


def no_content_response():
    """Respuesta 204 No Content (ej. DELETE exitoso)."""
    return "", 204


# ── Respuestas de error ───────────────────────────────────────────────────────

def error_response(message: str, status_code: int = 400, errors: dict | None = None):
    """
    Retorna una respuesta JSON de error.

    Args:
        message:     Descripción humana del error.
        status_code: Código HTTP (400, 404, 409, 422, 500, etc.).
        errors:      Diccionario de errores de campo (para validaciones).
    """
    body: dict = {"status": "error", "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def not_found_response(resource: str = "Recurso"):
    """Shortcut para 404 Not Found."""
    return error_response(f"{resource} no encontrado.", 404)


def conflict_response(message: str = "El recurso ya existe."):
    """Shortcut para 409 Conflict (ej. email duplicado)."""
    return error_response(message, 409)


def validation_error_response(errors: dict):
    """Shortcut para 422 Unprocessable Entity con detalle de campos."""
    return error_response("Error de validación en los datos enviados.", 422, errors)


def server_error_response(detail: str = ""):
    """Shortcut para 500 Internal Server Error."""
    msg = "Error interno del servidor."
    if detail:
        msg += f" Detalle: {detail}"
    return error_response(msg, 500)
