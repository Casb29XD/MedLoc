"""
MedLoc - Rutas de Autenticación con Supabase Auth
===================================================
POST /api/v1/auth/login    → Iniciar sesión (valida credenciales con Supabase Auth y retorna token JWT + perfil)
POST /api/v1/auth/register → Registrar nuevo usuario en Supabase Auth y en la BD
GET  /api/v1/auth/me       → Obtener usuario actual por email
POST /api/v1/auth/logout   → Cerrar sesión
"""
import json
import urllib.request
import urllib.error
from flask import Blueprint, request, current_app
from ..extensions import db
from ..services.usuario_service import UsuarioService
from ..utils.responses import (
    success_response,
    created_response,
    not_found_response,
    validation_error_response,
    server_error_response,
)

auth_bp = Blueprint("auth", __name__)


def _autenticar_con_supabase(email: str, password: str):
    """
    Autentica contra la API oficial de Supabase Auth (GoTrue).
    Retorna (data_dict, None) si es exitoso, o (None, error_str) si falla.
    """
    url = f"{current_app.config['SUPABASE_URL']}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": current_app.config["SUPABASE_KEY"],
        "Content-Type": "application/json",
    }
    body = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, headers=headers, data=body, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            msg = err_data.get("msg") or err_data.get("error_description") or "Credenciales inválidas"
        except Exception:
            msg = "Credenciales inválidas"
        return None, msg
    except Exception as e:
        return None, f"Error conectando a Supabase Auth: {str(e)}"


def _registrar_en_supabase_auth(user_id: str, email: str, password: str, nombre_completo: str):
    """
    Crea el registro de credenciales en las tablas internas auth.users y auth.identities
    de Supabase con el hash bcrypt nativo y confirmación automática de correo.
    """
    # 1. Insertar en auth.users
    db.session.execute(
        db.text("""
            INSERT INTO auth.users (
                id,
                instance_id,
                aud,
                role,
                email,
                encrypted_password,
                email_confirmed_at,
                recovery_sent_at,
                last_sign_in_at,
                raw_app_meta_data,
                raw_user_meta_data,
                created_at,
                updated_at,
                confirmation_token,
                email_change,
                email_change_token_new,
                recovery_token
            ) VALUES (
                :id,
                '00000000-0000-0000-0000-000000000000',
                'authenticated',
                'authenticated',
                :email,
                crypt(:password, gen_salt('bf')),
                NOW(),
                NULL,
                NULL,
                '{"provider":"email","providers":["email"]}',
                jsonb_build_object('nombre_completo', :nombre),
                NOW(),
                NOW(),
                '',
                '',
                '',
                ''
            )
            ON CONFLICT (id) DO UPDATE SET
                encrypted_password = crypt(:password, gen_salt('bf')),
                email_confirmed_at = NOW(),
                updated_at = NOW()
        """),
        {"id": str(user_id), "email": email, "password": password, "nombre": nombre_completo},
    )

    # 2. Insertar en auth.identities para permitir login email/password
    db.session.execute(
        db.text("""
            INSERT INTO auth.identities (
                id,
                user_id,
                identity_data,
                provider,
                provider_id,
                last_sign_in_at,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                :id,
                jsonb_build_object('sub', :id, 'email', :email),
                'email',
                :id,
                NOW(),
                NOW(),
                NOW()
            )
            ON CONFLICT (provider_id, provider) DO UPDATE SET
                identity_data = jsonb_build_object('sub', :id, 'email', :email),
                updated_at = NOW()
        """),
        {"id": str(user_id), "email": email},
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/v1/auth/login
    Valida las credenciales contra Supabase Auth.
    Si son válidas, retorna el perfil del usuario enriquecido con el token JWT de sesión.

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
            "credenciales": "El correo y la contraseña son requeridos."
        })

    # 1. Validar contra Supabase Auth
    token_data, error_msg = _autenticar_con_supabase(email, password)
    if not token_data:
        return validation_error_response({
            "credenciales": "Correo o contraseña incorrectos."
        })

    # 2. Obtener el perfil del usuario desde public.usuarios
    try:
        usuario = UsuarioService.obtener_por_email(email)
        if not usuario:
            return not_found_response("Usuario en la base de datos de MedLoc")

        user_dict = UsuarioService.to_dict(usuario)
        user_dict["token"] = token_data.get("access_token")
        user_dict["refresh_token"] = token_data.get("refresh_token")
        user_dict["expires_in"] = token_data.get("expires_in")

        return success_response(
            data=user_dict,
            message="Inicio de sesión exitoso.",
        )
    except Exception as e:
        return server_error_response(str(e))


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/v1/auth/register
    Registra un nuevo usuario en la base de datos de MedLoc y en Supabase Auth.

    Body JSON requerido:
      - nombre_completo  (str)
      - email            (str)
      - password         (str)
      - rol              (str: "paciente" | "administrador" | "farmaceutico")
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    nombre = datos.get("nombre_completo", "").strip()
    email = datos.get("email", "").strip().lower()
    password = datos.get("password", "")
    rol = datos.get("rol", "paciente")

    errores = {}
    if not nombre:
        errores["nombre_completo"] = "El nombre es requerido."
    if not email or "@" not in email:
        errores["email"] = "Se requiere un email válido."
    if not password or len(password) < 6:
        errores["password"] = "La contraseña debe tener al menos 6 caracteres."
    if errores:
        return validation_error_response(errores)

    # Verificar si el email ya existe
    if UsuarioService.obtener_por_email(email):
        return validation_error_response({
            "email": f"Ya existe una cuenta con el correo '{email}'."
        })

    try:
        # 1. Crear en public.usuarios
        usuario, error = UsuarioService.crear({
            "nombre_completo": nombre,
            "email": email,
            "rol": rol,
        })
        if error:
            return validation_error_response({"email": error})

        # 2. Registrar en auth.users y auth.identities de Supabase
        _registrar_en_supabase_auth(str(usuario.id), email, password, nombre)
        db.session.commit()

        # 3. Autenticar inmediatamente para devolver el token JWT
        token_data, _ = _autenticar_con_supabase(email, password)
        user_dict = UsuarioService.to_dict(usuario)
        if token_data:
            user_dict["token"] = token_data.get("access_token")
            user_dict["refresh_token"] = token_data.get("refresh_token")

        return created_response(
            data=user_dict,
            message="Cuenta creada e inicio de sesión exitoso.",
        )
    except Exception as e:
        db.session.rollback()
        return server_error_response(str(e))


@auth_bp.route("/me", methods=["GET"])
def me():
    """
    GET /api/v1/auth/me?email=<email>
    Retorna el perfil del usuario por email.
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


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/v1/auth/logout
    Cierra la sesión (el frontend limpia su almacenamiento local).
    """
    return success_response(data=None, message="Sesión cerrada exitosamente.")
