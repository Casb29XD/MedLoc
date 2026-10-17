"""
MedLoc - Rutas de Autenticación
=================================
POST /api/v1/auth/login   → Iniciar sesión (devuelve datos del usuario)
POST /api/v1/auth/logout  → Cerrar sesión (placeholder, sesión en cliente)
GET  /api/v1/auth/me      → Obtener usuario actual por email
"""
from flask import Blueprint, request
from ..services.usuario_service import UsuarioService
from ..utils.responses import (
    success_response,
    not_found_response,
    validation_error_response,
    server_error_response,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/v1/auth/login
    Verifica que el usuario exista en la BD y retorna su perfil.

    Nota: La verificación de contraseña real es gestionada por Supabase Auth.
    Este endpoint valida la existencia del usuario y retorna su perfil
    para que el frontend pueda establecer la sesión.

    Body JSON requerido:
      - email     (str)
      - password  (str)
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    email = datos.get("email", "").strip().lower()
    password = datos.get("password", "")

    if not email or not password:
        return validation_error_response({
            "credenciales": "El email y la contraseña son requeridos."
        })

    try:
        usuario = UsuarioService.obtener_por_email(email)
        if not usuario:
            return not_found_response("Usuario")

        # Retornar el perfil del usuario (sin contraseña)
        return success_response(
            data=UsuarioService.to_dict(usuario),
            message="Inicio de sesión exitoso.",
        )
    except Exception as e:
        return server_error_response(str(e))


@auth_bp.route("/me", methods=["GET"])
def me():
    """
    GET /api/v1/auth/me?email=<email>
    Retorna el perfil del usuario por email.
    Usado para sincronizar la sesión del cliente con la BD.
    """
    email = request.args.get("email", "").strip().lower()
    if not email:
        return validation_error_response({"email": "El parámetro 'email' es requerido."})

    try:
        usuario = UsuarioService.obtener_por_email(email)
        if not usuario:
            return not_found_response("Usuario")
        return success_response(
            data=UsuarioService.to_dict(usuario),
            message="Usuario encontrado.",
        )
    except Exception as e:
        return server_error_response(str(e))


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/v1/auth/register
    Registra un nuevo usuario en la BD.

    Body JSON requerido:
      - nombre_completo  (str)
      - email            (str)
      - rol              (str: "paciente" | "administrador" | "farmaceutico")
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    nombre = datos.get("nombre_completo", "").strip()
    email = datos.get("email", "").strip().lower()
    rol = datos.get("rol", "paciente")

    errores = {}
    if not nombre:
        errores["nombre_completo"] = "El nombre es requerido."
    if not email or "@" not in email:
        errores["email"] = "Se requiere un email válido."
    if errores:
        return validation_error_response(errores)

    # Verificar si el email ya existe
    if UsuarioService.obtener_por_email(email):
        return validation_error_response({
            "email": f"Ya existe una cuenta con el correo '{email}'."
        })

    usuario, error = UsuarioService.crear({
        "nombre_completo": nombre,
        "email": email,
        "rol": rol,
    })
    if error:
        return validation_error_response({"email": error})

    from ..utils.responses import created_response
    return created_response(
        data=UsuarioService.to_dict(usuario),
        message="Cuenta creada exitosamente.",
    )
