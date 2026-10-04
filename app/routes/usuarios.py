"""
MedLoc - Rutas de Usuarios
==========================
GET    /api/v1/usuarios              → Listar todos los usuarios
POST   /api/v1/usuarios              → Crear nuevo usuario
GET    /api/v1/usuarios/<id>         → Obtener usuario por ID
PATCH  /api/v1/usuarios/<id>         → Actualizar info del usuario
"""
from flask import Blueprint, request
from ..services.usuario_service import UsuarioService
from ..utils.responses import (
    success_response,
    created_response,
    not_found_response,
    conflict_response,
    validation_error_response,
    server_error_response,
)

usuarios_bp = Blueprint("usuarios", __name__)

# ── Campos requeridos para la creación ────────────────────────────────────────
CAMPOS_REQUERIDOS_CREAR = {"nombre_completo", "email"}


def _validar_crear(datos: dict) -> dict | None:
    """
    Valida los datos de entrada para crear un usuario.
    Retorna un dict de errores o None si todo es válido.
    """
    errores = {}
    for campo in CAMPOS_REQUERIDOS_CREAR:
        if not datos.get(campo, "").strip():
            errores[campo] = f"El campo '{campo}' es requerido y no puede estar vacío."
    if not errores and "@" not in datos.get("email", ""):
        errores["email"] = "El formato del email no es válido."
    return errores or None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@usuarios_bp.route("/", methods=["GET"])
def listar_usuarios():
    """
    GET /api/v1/usuarios/
    Lista todos los usuarios registrados.
    """
    try:
        usuarios = UsuarioService.obtener_todos()
        return success_response(
            data=[UsuarioService.to_dict(u) for u in usuarios],
            message=f"{len(usuarios)} usuario(s) encontrado(s).",
        )
    except Exception as e:
        return server_error_response(str(e))


@usuarios_bp.route("/", methods=["POST"])
def crear_usuario():
    """
    POST /api/v1/usuarios/
    Crea un nuevo usuario.

    Body JSON requerido:
      - nombre_completo (str)
      - email           (str)

    Body JSON opcional:
      - rol             (str: "paciente" | "administrador" | "farmaceutico")
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    errores = _validar_crear(datos)
    if errores:
        return validation_error_response(errores)

    usuario, error = UsuarioService.crear(datos)
    if error:
        return conflict_response(error)

    return created_response(
        data=UsuarioService.to_dict(usuario),
        message="Usuario creado exitosamente.",
    )


@usuarios_bp.route("/<uuid:usuario_id>", methods=["GET"])
def obtener_usuario(usuario_id):
    """
    GET /api/v1/usuarios/<uuid>
    Retorna el perfil de un usuario por su UUID.
    """
    usuario = UsuarioService.obtener_por_id(usuario_id)
    if not usuario:
        return not_found_response("Usuario")
    return success_response(
        data=UsuarioService.to_dict(usuario),
        message="Usuario encontrado.",
    )


@usuarios_bp.route("/<uuid:usuario_id>", methods=["PATCH"])
def actualizar_usuario(usuario_id):
    """
    PATCH /api/v1/usuarios/<uuid>
    Actualiza los campos editables del perfil de un usuario.

    Campos actualizables:
      - nombre_completo (str)
      - rol             (str: "paciente" | "administrador" | "farmaceutico")

    Nota: El email no es editable para mantener consistencia con Supabase Auth.
    """
    usuario = UsuarioService.obtener_por_id(usuario_id)
    if not usuario:
        return not_found_response("Usuario")

    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    # Filtrar solo campos actualizables — ignorar silenciosamente el resto
    campos_validos = {
        k: v for k, v in datos.items()
        if k in UsuarioService.CAMPOS_ACTUALIZABLES
    }
    if not campos_validos:
        return validation_error_response({
            "campos": (
                f"No se enviaron campos actualizables. "
                f"Permitidos: {sorted(UsuarioService.CAMPOS_ACTUALIZABLES)}"
            )
        })

    usuario_actualizado, error = UsuarioService.actualizar(usuario, campos_validos)
    if error:
        return validation_error_response({"rol": error})

    return success_response(
        data=UsuarioService.to_dict(usuario_actualizado),
        message="Perfil de usuario actualizado exitosamente.",
    )
