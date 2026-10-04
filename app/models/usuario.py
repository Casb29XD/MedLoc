import uuid
from datetime import datetime, timezone
"""
MedLoc - Modelo de Usuario
La generación del UUID y el timestamp de creación son delegados
a Supabase (PostgreSQL) mediante server_default.
"""
import enum
from sqlalchemy import Column, String, Enum as SAEnum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..extensions import db


class RolUsuario(str, enum.Enum):
    """Roles posibles para un usuario dentro de MedLoc."""

    PACIENTE = "paciente"
    ADMINISTRADOR = "administrador"
    FARMACEUTICO = "farmaceutico"


class Usuario(db.Model):
    """
    Representa un usuario registrado en MedLoc.

    Nota: La autenticación (contraseña, sesión, JWT) es gestionada
    nativamente por Supabase Auth. Este modelo almacena únicamente
    los datos de perfil de la aplicación.
    """

    __tablename__ = "usuarios"

    # ── Clave Primaria ────────────────────────────────────────────────────────
    # gen_random_uuid() es una función nativa de PostgreSQL/Supabase.
    # server_default garantiza que la BD genera el valor, no Python.
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
        comment="UUID generado automáticamente por PostgreSQL",
    )

    # ── Campos de Perfil ──────────────────────────────────────────────────────
    nombre_completo = Column(
        String(150),
        nullable=False,
        comment="Nombre completo del usuario",
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Correo electrónico único del usuario",
    )
    rol = Column(
        SAEnum(RolUsuario, name="rol_usuario_enum", create_type=True),
        nullable=False,
        default=RolUsuario.PACIENTE,
        comment="Rol del usuario dentro de la plataforma",
    )

    # ── Timestamp (delegado a Supabase) ───────────────────────────────────────
    # now() registra la fecha/hora del servidor al momento del INSERT.
    # FetchedValue le indica a SQLAlchemy que NO intente generar este valor.
    fecha_creacion = Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc), server_default=text("now()"),
        comment="Fecha de creación registrada automáticamente por la BD",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    farmacias_administradas = relationship(
        "Farmacia",
        back_populates="administrador",
        lazy="dynamic",
    )
    reservas = relationship(
        "Reserva",
        back_populates="usuario",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.email} [{self.rol}]>"
