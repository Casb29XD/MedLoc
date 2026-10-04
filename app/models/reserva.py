import uuid
from datetime import datetime, timezone
"""
MedLoc - Modelos de Reserva y DetalleReserva
"""
import enum
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum
from ..extensions import db


class EstadoReserva(str, enum.Enum):
    """Ciclo de vida de una reserva de medicamentos."""

    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    LISTA_PARA_RETIRO = "lista_para_retiro"
    RETIRADA = "retirada"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"


class Reserva(db.Model):
    """
    Representa una solicitud de reserva de medicamentos hecha por un usuario
    en una farmacia determinada.
    """

    __tablename__ = "reservas"

    # ── Clave Primaria ────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
        comment="UUID generado automáticamente por PostgreSQL",
    )

    # ── Claves Foráneas ───────────────────────────────────────────────────────
    id_usuario = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Usuario que realizó la reserva",
    )
    id_farmacia = Column(
        UUID(as_uuid=True),
        ForeignKey("farmacias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Farmacia donde se retirará la reserva",
    )

    # ── Datos de la Reserva ───────────────────────────────────────────────────
    estado = Column(
        SAEnum(EstadoReserva, name="estado_reserva_enum", create_type=True),
        nullable=False,
        default=EstadoReserva.PENDIENTE,
        server_default=text("'pendiente'"),
        comment="Estado actual de la reserva",
    )
    fecha_reserva = Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc), server_default=text("now()"),
        comment="Fecha y hora de creación de la reserva (gestionado por la BD)",
    )
    codigo_retiro = Column(
        String(20),
        nullable=True,
        unique=True,
        comment="Código alfanumérico único para retirar la reserva en la farmacia",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    usuario = relationship("Usuario", back_populates="reservas")
    farmacia = relationship("Farmacia", back_populates="reservas")
    detalles = relationship(
        "DetalleReserva",
        back_populates="reserva",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Reserva {self.id} [{self.estado}]>"


class DetalleReserva(db.Model):
    """
    Línea de detalle de una reserva: un medicamento específico con su
    cantidad y precio congelado al momento de la reserva.
    La PK compuesta (id_reserva, id_medicamento) evita duplicados por línea.
    """

    __tablename__ = "detalle_reservas"

    # ── Clave Primaria Compuesta ──────────────────────────────────────────────
    id_reserva = Column(
        UUID(as_uuid=True),
        ForeignKey("reservas.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Reserva a la que pertenece este detalle",
    )
    id_medicamento = Column(
        UUID(as_uuid=True),
        ForeignKey("medicamentos.id", ondelete="RESTRICT"),
        primary_key=True,
        comment="Medicamento reservado",
    )

    # ── Datos del Detalle ─────────────────────────────────────────────────────
    cantidad = Column(
        Integer,
        nullable=False,
        comment="Número de unidades reservadas",
    )
    precio_congelado = Column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="Precio unitario al momento de la reserva (inmutable)",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    reserva = relationship("Reserva", back_populates="detalles")
    medicamento = relationship("Medicamento", back_populates="detalles_reserva")

    def __repr__(self) -> str:
        return (
            f"<DetalleReserva reserva={self.id_reserva} "
            f"medicamento={self.id_medicamento} cantidad={self.cantidad}>"
        )
