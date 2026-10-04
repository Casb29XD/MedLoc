"""
MedLoc - Rutas de Inventario
=============================
GET    /api/v1/inventario/<farmacia_id>                          → Stock de una farmacia
POST   /api/v1/inventario/                                       → Crear/actualizar ítem (UPSERT)
GET    /api/v1/inventario/<farmacia_id>/<medicamento_id>         → Ítem específico
PATCH  /api/v1/inventario/<farmacia_id>/<medicamento_id>/stock   → Ajustar cantidad
PATCH  /api/v1/inventario/<farmacia_id>/<medicamento_id>/precio  → Actualizar precio
"""
from flask import Blueprint, request
from ..services.inventario_service import InventarioService
from ..utils.responses import (
    success_response,
    created_response,
    not_found_response,
    conflict_response,
    validation_error_response,
    server_error_response,
)

inventario_bp = Blueprint("inventario", __name__)


@inventario_bp.route("/farmacia/<uuid:farmacia_id>", methods=["GET"])
def listar_inventario_farmacia(farmacia_id):
    """
    GET /api/v1/inventario/farmacia/<uuid>
    Retorna el inventario completo (todos los medicamentos y stocks) de una farmacia.
    """
    try:
        items = InventarioService.obtener_por_farmacia(farmacia_id)
        return success_response(
            data=[InventarioService.to_dict(i) for i in items],
            message=f"{len(items)} ítem(s) en el inventario de la farmacia.",
        )
    except Exception as e:
        return server_error_response(str(e))


@inventario_bp.route("/", methods=["POST"])
def upsert_inventario():
    """
    POST /api/v1/inventario/
    Crea un nuevo ítem de inventario o actualiza el stock y precio si ya existe (UPSERT).

    Body JSON requerido:
      - id_farmacia       (uuid)
      - id_medicamento    (uuid)
      - precio_unitario   (number, >= 0)

    Body JSON opcional:
      - stock_actual      (int, >= 0, default: 0)
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    errores = {}
    for campo in ("id_farmacia", "id_medicamento", "precio_unitario"):
        if campo not in datos or datos[campo] is None:
            errores[campo] = f"El campo '{campo}' es requerido."
    if errores:
        return validation_error_response(errores)

    inventario, error, creado = InventarioService.crear_o_actualizar(datos)
    if error:
        return validation_error_response({"datos": error})

    if creado:
        return created_response(
            data=InventarioService.to_dict(inventario),
            message="Ítem de inventario creado exitosamente.",
        )
    return success_response(
        data=InventarioService.to_dict(inventario),
        message="Inventario actualizado exitosamente.",
    )


@inventario_bp.route("/<uuid:farmacia_id>/<uuid:medicamento_id>", methods=["GET"])
def obtener_item_inventario(farmacia_id, medicamento_id):
    """
    GET /api/v1/inventario/<farmacia_uuid>/<medicamento_uuid>
    Retorna el stock y precio de un medicamento específico en una farmacia.
    """
    item = InventarioService.obtener_item(farmacia_id, medicamento_id)
    if not item:
        return not_found_response("Ítem de inventario")
    return success_response(
        data=InventarioService.to_dict(item),
        message="Ítem de inventario encontrado.",
    )


@inventario_bp.route("/<uuid:farmacia_id>/<uuid:medicamento_id>/stock", methods=["PATCH"])
def actualizar_stock(farmacia_id, medicamento_id):
    """
    PATCH /api/v1/inventario/<farmacia_uuid>/<medicamento_uuid>/stock
    Ajusta el stock de un medicamento en una farmacia.

    Body JSON requerido:
      - delta  (int)  → Unidades a SUMAR (+) o DESCONTAR (-).
                        Ej: {"delta": 50}  → suma 50 unidades
                            {"delta": -10} → descuenta 10 unidades
    """
    item = InventarioService.obtener_item(farmacia_id, medicamento_id)
    if not item:
        return not_found_response("Ítem de inventario")

    datos = request.get_json(silent=True)
    if not datos or "delta" not in datos:
        return validation_error_response({
            "delta": "Se requiere el campo 'delta' (entero positivo o negativo)."
        })

    delta = datos["delta"]
    if not isinstance(delta, int):
        return validation_error_response({"delta": "El campo 'delta' debe ser un número entero."})

    item_actualizado, error = InventarioService.actualizar_stock(item, delta)
    if error:
        return conflict_response(error)

    return success_response(
        data=InventarioService.to_dict(item_actualizado),
        message=(
            f"Stock {'incrementado' if delta >= 0 else 'reducido'} exitosamente. "
            f"Stock actual: {item_actualizado.stock_actual} unidades."
        ),
    )


@inventario_bp.route("/<uuid:farmacia_id>/<uuid:medicamento_id>/precio", methods=["PATCH"])
def actualizar_precio(farmacia_id, medicamento_id):
    """
    PATCH /api/v1/inventario/<farmacia_uuid>/<medicamento_uuid>/precio
    Actualiza el precio unitario de un medicamento en una farmacia específica.

    Body JSON requerido:
      - precio_unitario  (number, >= 0)
    """
    item = InventarioService.obtener_item(farmacia_id, medicamento_id)
    if not item:
        return not_found_response("Ítem de inventario")

    datos = request.get_json(silent=True)
    if not datos or "precio_unitario" not in datos:
        return validation_error_response({
            "precio_unitario": "Se requiere el campo 'precio_unitario'."
        })

    item_actualizado, error = InventarioService.actualizar_precio(item, datos["precio_unitario"])
    if error:
        return validation_error_response({"precio_unitario": error})

    return success_response(
        data=InventarioService.to_dict(item_actualizado),
        message=f"Precio actualizado a ${float(item_actualizado.precio_unitario):,.2f}.",
    )
