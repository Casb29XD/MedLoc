import uuid
from datetime import datetime, timezone
"""
MedLoc - Modelo de Farmacia
"""
from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..extensions import db


class Farmacia(db.Model):
    """Representa una sucursal de farmacia registrada en MedLoc."""

    __tablename__ = "farmacias"

    # ── Clave Primaria ────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
        comment="UUID generado automáticamente por PostgreSQL",
    )

    # ── Clave Foránea ─────────────────────────────────────────────────────────
    id_administrador = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Usuario administrador responsable de la farmacia",
    )

    # ── Campos de la Farmacia ─────────────────────────────────────────────────
    nombre_sucursal = Column(
        String(200),
        nullable=False,
        comment="Nombre de la sucursal",
    )
    nit = Column(
        String(20),
        nullable=False,
        unique=True,
        comment="Número de Identificación Tributaria",
    )
    direccion = Column(
        String(300),
        nullable=False,
        comment="Dirección física de la farmacia",
    )

    # Coordenadas geográficas con precisión de hasta 8 decimales
    latitud = Column(
        Numeric(precision=10, scale=8),
        nullable=True,
        comment="Latitud geográfica (WGS84)",
    )
    longitud = Column(
        Numeric(precision=11, scale=8),
        nullable=True,
        comment="Longitud geográfica (WGS84)",
    )

    imagen_url = Column(
        String(500),
        nullable=True,
        comment="URL de la imagen de la farmacia",
    )

    activa = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Indica si la farmacia está operativa",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    administrador = relationship(
        "Usuario",
        back_populates="farmacias_administradas",
    )
    inventario = relationship(
        "Inventario",
        back_populates="farmacia",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    reservas = relationship(
        "Reserva",
        back_populates="farmacia",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Farmacia {self.nombre_sucursal} (NIT: {self.nit})>"
