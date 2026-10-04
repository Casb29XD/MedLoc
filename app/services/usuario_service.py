"""
MedLoc - Servicio de negocio para Usuarios.
Encapsula la lógica de acceso a datos y reglas de negocio,
manteniendo las rutas limpias de lógica compleja.
"""
from __future__ import annotations
import uuid
from sqlalchemy.exc import IntegrityError
from ..models.usuario import Usuario, RolUsuario
from ..extensions import db


class UsuarioService:
    """Operaciones CRUD para la entidad Usuario."""

    # ── Campos permitidos para actualización ──────────────────────────────────
    CAMPOS_ACTUALIZABLES = {"nombre_completo", "rol"}

    @staticmethod
    def obtener_todos() -> list[Usuario]:
        """Retorna todos los usuarios ordenados por fecha de creación desc."""
        return (
            db.session.execute(
                db.select(Usuario).order_by(Usuario.fecha_creacion.desc())
            )
            .scalars()
            .all()
        )

    @staticmethod
    def obtener_por_id(usuario_id: str | uuid.UUID) -> Usuario | None:
        """Busca un usuario por su UUID. Retorna None si no existe."""
        return db.session.get(Usuario, usuario_id)

    @staticmethod
    def obtener_por_email(email: str) -> Usuario | None:
        """Busca un usuario por correo electrónico."""
        return db.session.execute(
            db.select(Usuario).where(Usuario.email == email)
        ).scalar_one_or_none()

    @staticmethod
    def crear(datos: dict) -> tuple[Usuario | None, str | None]:
        """
        Crea un nuevo usuario.
        Retorna (usuario, None) en éxito o (None, mensaje_error) en fallo.
        """
        try:
            nuevo = Usuario(
                nombre_completo=datos["nombre_completo"],
                email=datos["email"],
                rol=RolUsuario(datos.get("rol", RolUsuario.PACIENTE.value)),
            )
            db.session.add(nuevo)
            db.session.commit()
            db.session.refresh(nuevo)  # Obtener UUID y timestamp de Supabase
            return nuevo, None
        except IntegrityError:
            db.session.rollback()
            return None, f"El email '{datos['email']}' ya está registrado."

    @staticmethod
    def actualizar(usuario: Usuario, datos: dict) -> tuple[Usuario | None, str | None]:
        """
        Actualiza los campos permitidos de un usuario.
        Solo se modifican los campos presentes en CAMPOS_ACTUALIZABLES.
        Retorna (usuario, None) en éxito o (None, mensaje_error) en fallo.
        """
        for campo in UsuarioService.CAMPOS_ACTUALIZABLES:
            if campo in datos:
                valor = datos[campo]
                # Convertir el rol al enum si viene como string
                if campo == "rol":
                    try:
                        valor = RolUsuario(valor)
                    except ValueError:
                        roles_validos = [r.value for r in RolUsuario]
                        return None, f"Rol inválido. Valores permitidos: {roles_validos}"
                setattr(usuario, campo, valor)

        try:
            db.session.commit()
            db.session.refresh(usuario)
            return usuario, None
        except IntegrityError:
            db.session.rollback()
            return None, "Error de integridad al actualizar el usuario."

    @staticmethod
    def to_dict(usuario: Usuario) -> dict:
        """Serializa un Usuario a diccionario JSON-safe."""
        return {
            "id": str(usuario.id),
            "nombre_completo": usuario.nombre_completo,
            "email": usuario.email,
            "rol": usuario.rol.value if usuario.rol else None,
            "fecha_creacion": (
                usuario.fecha_creacion.isoformat() if usuario.fecha_creacion else None
            ),
        }
