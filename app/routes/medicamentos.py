"""
MedLoc - Rutas de Medicamentos
===============================
GET    /api/v1/medicamentos/              → Listar (con búsqueda ?q=)
POST   /api/v1/medicamentos/              → Crear medicamento
GET    /api/v1/medicamentos/<id>          → Obtener por ID
PATCH  /api/v1/medicamentos/<id>          → Actualizar datos del catálogo
"""
from flask import Blueprint, request
from ..services.medicamento_service import MedicamentoService
from ..utils.responses import (
    success_response,
    created_response,
    not_found_response,
    conflict_response,
    validation_error_response,
    server_error_response,
)

medicamentos_bp = Blueprint("medicamentos", __name__)

CAMPOS_REQUERIDOS_CREAR = {"nombre_comercial", "principio_activo"}


def _validar_crear(datos: dict) -> dict | None:
    errores = {}
    for campo in CAMPOS_REQUERIDOS_CREAR:
        if not datos.get(campo, "").strip():
            errores[campo] = f"El campo '{campo}' es requerido y no puede estar vacío."
    return errores or None


@medicamentos_bp.route("/", methods=["GET"])
def listar_medicamentos():
    """
    GET /api/v1/medicamentos/?q=<termino>
    Lista todos los medicamentos. Si se envía ?q=, filtra por nombre o principio activo.
    """
    try:
        buscar = request.args.get("q", "").strip() or None
        medicamentos = MedicamentoService.obtener_todos(buscar=buscar)
        return success_response(
            data=[MedicamentoService.to_dict(m) for m in medicamentos],
            message=f"{len(medicamentos)} medicamento(s) encontrado(s).",
        )
    except Exception as e:
        return server_error_response(str(e))


@medicamentos_bp.route("/", methods=["POST"])
def crear_medicamento():
    """
    POST /api/v1/medicamentos/
    Agrega un nuevo medicamento al catálogo.

    Body JSON requerido:
      - nombre_comercial  (str)
      - principio_activo  (str)

    Body JSON opcional:
      - concentracion     (str, ej. "500mg")
      - presentacion      (str, ej. "Tabletas")
      - laboratorio       (str)
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    errores = _validar_crear(datos)
    if errores:
        return validation_error_response(errores)

    medicamento, error = MedicamentoService.crear(datos)
    if error:
        return conflict_response(error)

    return created_response(
        data=MedicamentoService.to_dict(medicamento),
        message="Medicamento agregado al catálogo exitosamente.",
    )


@medicamentos_bp.route("/<uuid:medicamento_id>", methods=["GET"])
def obtener_medicamento(medicamento_id):
    """
    GET /api/v1/medicamentos/<uuid>
    Retorna el detalle de un medicamento del catálogo.
    """
    medicamento = MedicamentoService.obtener_por_id(medicamento_id)
    if not medicamento:
        return not_found_response("Medicamento")
    return success_response(
        data=MedicamentoService.to_dict(medicamento),
        message="Medicamento encontrado.",
    )


@medicamentos_bp.route("/<uuid:medicamento_id>", methods=["PATCH"])
def actualizar_medicamento(medicamento_id):
    """
    PATCH /api/v1/medicamentos/<uuid>
    Actualiza los datos del catálogo de un medicamento.

    Campos actualizables:
      - nombre_comercial
      - principio_activo
      - concentracion
      - presentacion
      - laboratorio

    Nota: El precio se actualiza a nivel de Inventario, no de Medicamento.
    """
    medicamento = MedicamentoService.obtener_por_id(medicamento_id)
    if not medicamento:
        return not_found_response("Medicamento")

    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    campos_validos = {
        k: v for k, v in datos.items()
        if k in MedicamentoService.CAMPOS_ACTUALIZABLES
    }
    if not campos_validos:
        return validation_error_response({
            "campos": (
                f"No se enviaron campos actualizables. "
                f"Permitidos: {sorted(MedicamentoService.CAMPOS_ACTUALIZABLES)}"
            )
        })

    medicamento_actualizado, error = MedicamentoService.actualizar(medicamento, campos_validos)
    if error:
        return conflict_response(error)

    return success_response(
        data=MedicamentoService.to_dict(medicamento_actualizado),
        message="Medicamento actualizado exitosamente.",
    )
