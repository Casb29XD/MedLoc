"""
MedLoc - Servicio de negocio para Medicamentos.
"""
from __future__ import annotations
import uuid
from sqlalchemy.exc import IntegrityError
from ..models.medicamento import Medicamento
from ..extensions import db


class MedicamentoService:
    """Operaciones CRUD para la entidad Medicamento."""

    # ── Campos permitidos para actualización ──────────────────────────────────
    CAMPOS_ACTUALIZABLES = {
        "nombre_comercial",
        "principio_activo",
        "concentracion",
        "presentacion",
        "laboratorio",
    }

    @staticmethod
    def obtener_todos(buscar: str | None = None) -> list[Medicamento]:
        """
        Retorna todos los medicamentos.
        Si se provee 'buscar', filtra por nombre_comercial o principio_activo (ILIKE).
        """
        query = db.select(Medicamento).order_by(Medicamento.nombre_comercial)
        if buscar:
            termino = f"%{buscar}%"
            query = query.where(
                db.or_(
                    Medicamento.nombre_comercial.ilike(termino),
                    Medicamento.principio_activo.ilike(termino),
                )
            )
        return db.session.execute(query).scalars().all()

    @staticmethod
    def obtener_por_id(medicamento_id: str | uuid.UUID) -> Medicamento | None:
        """Busca un medicamento por UUID."""
        return db.session.get(Medicamento, medicamento_id)

    @staticmethod
    def crear(datos: dict) -> tuple[Medicamento | None, str | None]:
        """
        Crea un nuevo medicamento en el catálogo.
        Retorna (medicamento, None) o (None, mensaje_error).
        """
        try:
            nuevo = Medicamento(
                nombre_comercial=datos["nombre_comercial"],
                principio_activo=datos["principio_activo"],
                concentracion=datos.get("concentracion"),
                presentacion=datos.get("presentacion"),
                laboratorio=datos.get("laboratorio"),
                imagen_url=datos.get("imagen_url"),
            )
            db.session.add(nuevo)
            db.session.commit()
            db.session.refresh(nuevo)
            return nuevo, None
        except IntegrityError:
            db.session.rollback()
            return None, "Error de integridad al crear el medicamento."

    @staticmethod
    def actualizar(
        medicamento: Medicamento, datos: dict
    ) -> tuple[Medicamento | None, str | None]:
        """
        Actualiza los campos del catálogo de un medicamento.
        Solo se aplican los campos presentes en CAMPOS_ACTUALIZABLES.
        """
        for campo in MedicamentoService.CAMPOS_ACTUALIZABLES:
            if campo in datos:
                setattr(medicamento, campo, datos[campo])

        try:
            db.session.commit()
            db.session.refresh(medicamento)
            return medicamento, None
        except IntegrityError:
            db.session.rollback()
            return None, "Error de integridad al actualizar el medicamento."

    @staticmethod
    def to_dict(medicamento: Medicamento) -> dict:
        """Serializa un Medicamento a diccionario JSON-safe."""
        return {
            "id": str(medicamento.id),
            "nombre_comercial": medicamento.nombre_comercial,
            "principio_activo": medicamento.principio_activo,
            "concentracion": medicamento.concentracion,
            "presentacion": medicamento.presentacion,
            "laboratorio": medicamento.laboratorio,
            "imagen_url": medicamento.imagen_url,
        }
