"""Rutas de la API para la gestión de Reservas."""
import secrets
from flask import Blueprint, request
from ..models.reserva import DetalleReserva, EstadoReserva, Reserva
from ..models.inventario import Inventario
from ..models.medicamento import Medicamento
from ..extensions import db
from ..utils.responses import (
    success_response,
    created_response,
    not_found_response,
    validation_error_response,
    server_error_response,
)

reservas_bp = Blueprint("reservas", __name__)


@reservas_bp.route("/", methods=["POST"])
def crear_reserva():
    """Crea una reserva para un medicamento disponible en una farmacia."""
    datos = request.get_json(silent=True) or {}
    usuario_id = datos.get("id_usuario")
    farmacia_id = datos.get("id_farmacia")
    medicamento_id = datos.get("id_medicamento")
    cantidad = datos.get("cantidad", 1)

    if not all((usuario_id, farmacia_id, medicamento_id)):
        return validation_error_response({
            "reserva": "Se requieren id_usuario, id_farmacia e id_medicamento."
        })
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        return validation_error_response({"cantidad": "La cantidad debe ser un entero positivo."})
    if cantidad < 1:
        return validation_error_response({"cantidad": "La cantidad debe ser un entero positivo."})

    try:
        inventario = db.session.execute(
            db.select(Inventario).where(
                Inventario.id_farmacia == farmacia_id,
                Inventario.id_medicamento == medicamento_id,
            )
        ).scalar_one_or_none()
        medicamento = db.session.get(Medicamento, medicamento_id)
        if not inventario or not medicamento:
            return not_found_response("Medicamento en el inventario")
        if inventario.stock_actual < cantidad:
            return validation_error_response({"cantidad": "No hay unidades suficientes disponibles."})

        reserva = Reserva(
            id_usuario=usuario_id,
            id_farmacia=farmacia_id,
            estado=EstadoReserva.PENDIENTE,
            codigo_retiro=str(secrets.randbelow(900000) + 100000),
        )
        inventario.stock_actual -= cantidad
        reserva.detalles.append(DetalleReserva(
            id_medicamento=medicamento_id,
            cantidad=cantidad,
            precio_congelado=inventario.precio_unitario,
        ))
        db.session.add(reserva)
        db.session.commit()
        db.session.refresh(reserva)
        return created_response(data=_to_dict(reserva), message="Reserva creada exitosamente.")
    except Exception as exc:
        db.session.rollback()
        return server_error_response(str(exc))


def _to_dict(reserva: Reserva) -> dict:
    return {
        "id": str(reserva.id),
        "id_usuario": str(reserva.id_usuario),
        "id_farmacia": str(reserva.id_farmacia),
        "estado": reserva.estado.value,
        "fecha_reserva": reserva.fecha_reserva.isoformat(),
        "codigo_retiro": reserva.codigo_retiro,
        "cliente": reserva.usuario.nombre_completo if reserva.usuario else "Cliente",
        "email_cliente": reserva.usuario.email if reserva.usuario else None,
        "detalles": [
            {
                "id_medicamento": str(detalle.id_medicamento),
                "medicamento": (
                    f"{detalle.medicamento.nombre_comercial}"
                    f"{' ' + detalle.medicamento.concentracion if detalle.medicamento.concentracion else ''}"
                ),
                "cantidad": detalle.cantidad,
                "precio": float(detalle.precio_congelado),
            }
            for detalle in reserva.detalles
        ],
    }


@reservas_bp.route("/", methods=["GET"])
def listar_reservas():
    """Lista reservas de una farmacia mediante ?farmacia_id=<uuid>."""
    farmacia_id = request.args.get("farmacia_id", "").strip()
    if not farmacia_id:
        return validation_error_response({"farmacia_id": "El parámetro 'farmacia_id' es requerido."})

    try:
        reservas = db.session.execute(
            db.select(Reserva)
            .where(Reserva.id_farmacia == farmacia_id)
            .order_by(Reserva.fecha_reserva.desc())
        ).scalars().unique().all()
        return success_response(
            data=[_to_dict(reserva) for reserva in reservas],
            message=f"{len(reservas)} reserva(s) encontrada(s).",
        )
    except Exception as exc:
        return server_error_response(str(exc))


@reservas_bp.route("/<uuid:reserva_id>/estado", methods=["PATCH"])
def actualizar_estado(reserva_id):
    """Actualiza el estado y repone stock cuando se cancela una reserva."""
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        return not_found_response("Reserva")

    datos = request.get_json(silent=True) or {}
    estado = datos.get("estado", "")
    try:
        nuevo_estado = EstadoReserva(estado)
        estado_anterior = reserva.estado

        if nuevo_estado == EstadoReserva.CANCELADA and estado_anterior != EstadoReserva.CANCELADA:
            for detalle in reserva.detalles:
                inventario = db.session.execute(
                    db.select(Inventario)
                    .where(
                        Inventario.id_farmacia == reserva.id_farmacia,
                        Inventario.id_medicamento == detalle.id_medicamento,
                    )
                    .with_for_update()
                ).scalar_one_or_none()
                if inventario:
                    inventario.stock_actual += detalle.cantidad

        reserva.estado = nuevo_estado
        db.session.commit()
        db.session.refresh(reserva)
        return success_response(data=_to_dict(reserva), message="Estado de reserva actualizado.")
    except ValueError:
        db.session.rollback()
        return validation_error_response({
            "estado": f"Estado inválido. Valores permitidos: {[item.value for item in EstadoReserva]}"
        })
    except Exception as exc:
        db.session.rollback()
        return server_error_response(str(exc))
