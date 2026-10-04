import uuid
from datetime import datetime, timezone
"""
MedLoc - Modelo de Medicamento
"""
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..extensions import db


class Medicamento(db.Model):
    """Representa un medicamento en el catálogo de MedLoc."""

    __tablename__ = "medicamentos"

    # ── Clave Primaria ────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
        comment="UUID generado automáticamente por PostgreSQL",
    )

    # ── Datos del Medicamento ─────────────────────────────────────────────────
    nombre_comercial = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Nombre de marca del medicamento",
    )
    principio_activo = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Sustancia farmacológica activa (DCI)",
    )
    concentracion = Column(
        String(50),
        nullable=True,
        comment="Concentración del principio activo (ej. '500mg', '10mg/mL')",
    )
    presentacion = Column(
        String(100),
        nullable=True,
        comment="Forma farmacéutica (ej. 'Tabletas', 'Jarabe', 'Ampolla')",
    )
    imagen_url = Column(
        String(500),
        nullable=True,
        comment="URL de la imagen del medicamento",
    )

    laboratorio = Column(
        String(150),
        nullable=True,
        comment="Laboratorio fabricante",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    inventario = relationship(
        "Inventario",
        back_populates="medicamento",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    detalles_reserva = relationship(
        "DetalleReserva",
        back_populates="medicamento",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Medicamento {self.nombre_comercial} ({self.principio_activo})>"
