"""
MedLoc - Servicio de negocio para Farmacias.
"""
from __future__ import annotations
import uuid
from datetime import time
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError
from ..models.farmacia import Farmacia
from ..extensions import db


class FarmaciaService:
    """Operaciones CRUD para la entidad Farmacia."""

    # ── Campos permitidos para actualización ──────────────────────────────────
    CAMPOS_ACTUALIZABLES = {
        "nombre_sucursal",
        "nit",
        "direccion",
        "hora_apertura",
        "hora_cierre",
        "latitud",
        "longitud",
        "activa",
        "id_administrador",
    }

    @staticmethod
    def _parse_time(value: str | time | None) -> time | None:
        """Convierte HH:MM/HH:MM:SS a un valor TIME de PostgreSQL."""
        if value in (None, "") or isinstance(value, time):
            return value
        try:
            return time.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError("La hora debe tener el formato HH:MM.") from exc

    @staticmethod
    def obtener_todas(solo_activas: bool = False) -> list[Farmacia]:
        """
        Retorna todas las farmacias ordenadas por nombre.
        Si solo_activas=True, filtra solo las activas.
        """
        query = db.select(Farmacia).order_by(Farmacia.nombre_sucursal)
        if solo_activas:
            query = query.where(Farmacia.activa.is_(True))
        return db.session.execute(query).scalars().all()

    @staticmethod
    def obtener_por_id(farmacia_id: str | uuid.UUID) -> Farmacia | None:
        """Busca una farmacia por UUID."""
        return db.session.get(Farmacia, farmacia_id)

    @staticmethod
    def crear(datos: dict) -> tuple[Farmacia | None, str | None]:
        """
        Crea una nueva farmacia.
        Retorna (farmacia, None) o (None, mensaje_error).
        """
        try:
            nueva = Farmacia(
                nombre_sucursal=datos["nombre_sucursal"],
                nit=datos["nit"],
                direccion=datos["direccion"],
                hora_apertura=FarmaciaService._parse_time(datos.get("hora_apertura")),
                hora_cierre=FarmaciaService._parse_time(datos.get("hora_cierre")),
                latitud=datos.get("latitud"),
                longitud=datos.get("longitud"),
                activa=datos.get("activa", True),
                id_administrador=datos.get("id_administrador"),
                imagen_url=datos.get("imagen_url"),
            )
            db.session.add(nueva)
            db.session.commit()
            db.session.refresh(nueva)
            return nueva, None
        except ValueError as exc:
            db.session.rollback()
            return None, str(exc)
        except IntegrityError:
            db.session.rollback()
            return None, f"El NIT '{datos['nit']}' ya está registrado."

    @staticmethod
    def actualizar(
        farmacia: Farmacia, datos: dict
    ) -> tuple[Farmacia | None, str | None]:
        """
        Actualiza los campos de una farmacia existente.
        Solo se aplican campos presentes en CAMPOS_ACTUALIZABLES.
        """
        for campo in FarmaciaService.CAMPOS_ACTUALIZABLES:
            if campo not in datos:
                continue
            valor = datos[campo]
            # Convertir coordenadas a Decimal para precisión
            if campo in ("latitud", "longitud") and valor is not None:
                try:
                    valor = Decimal(str(valor))
                except InvalidOperation:
                    return None, f"El campo '{campo}' debe ser un número decimal válido."
            if campo in ("hora_apertura", "hora_cierre") and valor == "":
                valor = None
            if campo in ("hora_apertura", "hora_cierre"):
                try:
                    valor = FarmaciaService._parse_time(valor)
                except ValueError as exc:
                    return None, str(exc)
            setattr(farmacia, campo, valor)

        try:
            db.session.commit()
            db.session.refresh(farmacia)
            return farmacia, None
        except IntegrityError:
            db.session.rollback()
            return None, "El NIT proporcionado ya pertenece a otra farmacia."

    @staticmethod
    def to_dict(farmacia: Farmacia) -> dict:
        """Serializa una Farmacia a diccionario JSON-safe."""
        return {
            "id": str(farmacia.id),
            "id_administrador": (
                str(farmacia.id_administrador) if farmacia.id_administrador else None
            ),
            "nombre_sucursal": farmacia.nombre_sucursal,
            "nit": farmacia.nit,
            "direccion": farmacia.direccion,
            "hora_apertura": (
                farmacia.hora_apertura.isoformat() if farmacia.hora_apertura else None
            ),
            "hora_cierre": (
                farmacia.hora_cierre.isoformat() if farmacia.hora_cierre else None
            ),
            "latitud": float(farmacia.latitud) if farmacia.latitud else None,
            "longitud": float(farmacia.longitud) if farmacia.longitud else None,
            "activa": farmacia.activa,
            "imagen_url": farmacia.imagen_url,
        }
