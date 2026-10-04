import uuid
from datetime import datetime, timezone
"""
MedLoc - Modelo de Inventario
Tabla intermedia (asociación) entre Farmacia y Medicamento.
Usa una Primary Key compuesta (id_farmacia, id_medicamento).
"""
from sqlalchemy import Column, Integer, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..extensions import db


class Inventario(db.Model):
    """
    Registra el stock de un medicamento específico en una farmacia específica.
    La clave primaria compuesta garantiza que no haya duplicados por par
    (farmacia, medicamento).
    """

    __tablename__ = "inventario"

    # ── Clave Primaria Compuesta ──────────────────────────────────────────────
    id_farmacia = Column(
        UUID(as_uuid=True),
        ForeignKey("farmacias.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Referencia a la farmacia",
    )
    id_medicamento = Column(
        UUID(as_uuid=True),
        ForeignKey("medicamentos.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Referencia al medicamento",
    )

    # ── Datos del Inventario ──────────────────────────────────────────────────
    stock_actual = Column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Unidades disponibles actualmente",
    )
    precio_unitario = Column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="Precio de venta al público por unidad",
    )

    # ── Timestamp (delegado a Supabase) ───────────────────────────────────────
    # now() se ejecuta en cada INSERT y UPDATE a nivel de BD.
    # Para actualizaciones automáticas en UPDATE, se recomienda usar
    # un TRIGGER en Supabase (ver documentación del proyecto).
    ultima_actualizacion = Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc), server_default=text("now()"),
        comment="Última vez que se actualizó el inventario (gestionado por la BD)",
    )

    # ── Relaciones ────────────────────────────────────────────────────────────
    farmacia = relationship("Farmacia", back_populates="inventario")
    medicamento = relationship("Medicamento", back_populates="inventario")

    def __repr__(self) -> str:
        return (
            f"<Inventario farmacia={self.id_farmacia} "
            f"medicamento={self.id_medicamento} stock={self.stock_actual}>"
        )
