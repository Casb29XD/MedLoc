"""Rutas de la API para la gestión de Reservas."""
from flask import Blueprint, request
from ..models.reserva import EstadoReserva, Reserva
from ..extensions import db
from ..utils.responses import (
    success_response,
    not_found_response,
    validation_error_response,
    server_error_response,
)

reservas_bp = Blueprint("reservas", __name__)


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
    """Actualiza el estado de una reserva."""
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        return not_found_response("Reserva")

    datos = request.get_json(silent=True) or {}
    estado = datos.get("estado", "")
    try:
        reserva.estado = EstadoReserva(estado)
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
