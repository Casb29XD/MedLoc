"""
MedLoc - Servicio de negocio para Inventario.
La PK de inventario es compuesta: (id_farmacia, id_medicamento).
"""
from __future__ import annotations
import uuid
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError
from ..models.inventario import Inventario
from ..extensions import db


class InventarioService:
    """Operaciones CRUD para la entidad Inventario."""

    @staticmethod
    def obtener_por_farmacia(farmacia_id: str | uuid.UUID) -> list[Inventario]:
        """Retorna todos los ítems de inventario de una farmacia."""
        return (
            db.session.execute(
                db.select(Inventario)
                .where(Inventario.id_farmacia == farmacia_id)
                .order_by(Inventario.id_medicamento)
            )
            .scalars()
            .all()
        )

    @staticmethod
    def obtener_item(
        farmacia_id: str | uuid.UUID, medicamento_id: str | uuid.UUID
    ) -> Inventario | None:
        """Busca un ítem de inventario por su PK compuesta."""
        return db.session.get(Inventario, (farmacia_id, medicamento_id))

    @staticmethod
    def crear_o_actualizar(datos: dict) -> tuple[Inventario | None, str | None, bool]:
        """
        Crea un nuevo ítem de inventario o actualiza uno existente (UPSERT).
        Retorna (inventario, None, creado) donde 'creado' indica si fue INSERT (True)
        o UPDATE (False).
        """
        farmacia_id = datos["id_farmacia"]
        medicamento_id = datos["id_medicamento"]

        # Validar precio
        try:
            precio = Decimal(str(datos["precio_unitario"]))
            if precio < 0:
                return None, "El precio_unitario no puede ser negativo.", False
        except InvalidOperation:
            return None, "El precio_unitario debe ser un número válido.", False

        # Validar stock
        stock = datos.get("stock_actual", 0)
        if not isinstance(stock, int) or stock < 0:
            return None, "El stock_actual debe ser un entero no negativo.", False

        existente = InventarioService.obtener_item(farmacia_id, medicamento_id)

        try:
            if existente:
                # UPDATE
                existente.stock_actual = stock
                existente.precio_unitario = precio
                db.session.commit()
                db.session.refresh(existente)
                return existente, None, False
            else:
                # INSERT
                nuevo = Inventario(
                    id_farmacia=farmacia_id,
                    id_medicamento=medicamento_id,
                    stock_actual=stock,
                    precio_unitario=precio,
                )
                db.session.add(nuevo)
                db.session.commit()
                db.session.refresh(nuevo)
                return nuevo, None, True
        except IntegrityError:
            db.session.rollback()
            return None, (
                "Error de integridad: verifica que la farmacia y el medicamento existan."
            ), False

    @staticmethod
    def actualizar_stock(
        inventario: Inventario, cantidad_delta: int
    ) -> tuple[Inventario | None, str | None]:
        """
        Incrementa o reduce el stock en 'cantidad_delta' unidades.
        Usa delta (ej. +10 para agregar, -5 para descontar).
        Previene stock negativo.
        """
        nuevo_stock = inventario.stock_actual + cantidad_delta
        if nuevo_stock < 0:
            return None, (
                f"Stock insuficiente. Disponible: {inventario.stock_actual} unidades."
            )
        inventario.stock_actual = nuevo_stock
        db.session.commit()
        db.session.refresh(inventario)
        return inventario, None

    @staticmethod
    def actualizar_precio(
        inventario: Inventario, nuevo_precio: float | str
    ) -> tuple[Inventario | None, str | None]:
        """Actualiza solo el precio unitario de un ítem de inventario."""
        try:
            precio = Decimal(str(nuevo_precio))
            if precio < 0:
                return None, "El precio_unitario no puede ser negativo."
        except InvalidOperation:
            return None, "El precio_unitario debe ser un número válido."

        inventario.precio_unitario = precio
        db.session.commit()
        db.session.refresh(inventario)
        return inventario, None

    @staticmethod
    def to_dict(inventario: Inventario) -> dict:
        """Serializa un ítem de Inventario a diccionario JSON-safe."""
        return {
            "id_farmacia": str(inventario.id_farmacia),
            "id_medicamento": str(inventario.id_medicamento),
            "stock_actual": inventario.stock_actual,
            "precio_unitario": float(inventario.precio_unitario),
            "ultima_actualizacion": (
                inventario.ultima_actualizacion.isoformat()
                if inventario.ultima_actualizacion
                else None
            ),
        }
