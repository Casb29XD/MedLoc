"""
MedLoc - Rutas de Farmacias
============================
GET    /api/v1/farmacias/              → Listar (?activas=true para filtrar)
POST   /api/v1/farmacias/              → Crear farmacia
GET    /api/v1/farmacias/<id>          → Obtener por ID
PATCH  /api/v1/farmacias/<id>          → Actualizar datos de la farmacia
"""
from flask import Blueprint, request
from ..services.farmacia_service import FarmaciaService
from ..utils.responses import (
    success_response,
    created_response,
    not_found_response,
    conflict_response,
    validation_error_response,
    server_error_response,
)

farmacias_bp = Blueprint("farmacias", __name__)

CAMPOS_REQUERIDOS_CREAR = {"nombre_sucursal", "nit", "direccion"}


def _validar_crear(datos: dict) -> dict | None:
    errores = {}
    for campo in CAMPOS_REQUERIDOS_CREAR:
        if not str(datos.get(campo, "")).strip():
            errores[campo] = f"El campo '{campo}' es requerido y no puede estar vacío."
    return errores or None


@farmacias_bp.route("/", methods=["GET"])
def listar_farmacias():
    """
    GET /api/v1/farmacias/?activas=true
    Lista todas las farmacias. Con ?activas=true retorna solo las activas.
    """
    try:
        solo_activas = request.args.get("activas", "").lower() == "true"
        farmacias = FarmaciaService.obtener_todas(solo_activas=solo_activas)
        return success_response(
            data=[FarmaciaService.to_dict(f) for f in farmacias],
            message=f"{len(farmacias)} farmacia(s) encontrada(s).",
        )
    except Exception as e:
        return server_error_response(str(e))


@farmacias_bp.route("/", methods=["POST"])
def crear_farmacia():
    """
    POST /api/v1/farmacias/
    Registra una nueva farmacia.

    Body JSON requerido:
      - nombre_sucursal   (str)
      - nit               (str, único)
      - direccion         (str)

    Body JSON opcional:
      - id_administrador  (uuid)
      - latitud           (float)
      - longitud          (float)
      - activa            (bool, default: true)
    """
    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    errores = _validar_crear(datos)
    if errores:
        return validation_error_response(errores)

    farmacia, error = FarmaciaService.crear(datos)
    if error:
        return conflict_response(error)

    return created_response(
        data=FarmaciaService.to_dict(farmacia),
        message="Farmacia registrada exitosamente.",
    )


@farmacias_bp.route("/<uuid:farmacia_id>", methods=["GET"])
def obtener_farmacia(farmacia_id):
    """
    GET /api/v1/farmacias/<uuid>
    Retorna el detalle de una farmacia.
    """
    farmacia = FarmaciaService.obtener_por_id(farmacia_id)
    if not farmacia:
        return not_found_response("Farmacia")
    return success_response(
        data=FarmaciaService.to_dict(farmacia),
        message="Farmacia encontrada.",
    )


@farmacias_bp.route("/<uuid:farmacia_id>", methods=["PATCH"])
def actualizar_farmacia(farmacia_id):
    """
    PATCH /api/v1/farmacias/<uuid>
    Actualiza los datos de una farmacia existente.

    Campos actualizables:
      - nombre_sucursal
      - nit
      - direccion
      - latitud
      - longitud
      - activa            (bool: true/false para activar/desactivar)
      - id_administrador  (uuid)
    """
    farmacia = FarmaciaService.obtener_por_id(farmacia_id)
    if not farmacia:
        return not_found_response("Farmacia")

    datos = request.get_json(silent=True)
    if not datos:
        return validation_error_response({"body": "Se requiere un body JSON válido."})

    campos_validos = {
        k: v for k, v in datos.items()
        if k in FarmaciaService.CAMPOS_ACTUALIZABLES
    }
    if not campos_validos:
        return validation_error_response({
            "campos": (
                f"No se enviaron campos actualizables. "
                f"Permitidos: {sorted(FarmaciaService.CAMPOS_ACTUALIZABLES)}"
            )
        })

    farmacia_actualizada, error = FarmaciaService.actualizar(farmacia, campos_validos)
    if error:
        return conflict_response(error) if "NIT" in error else validation_error_response({"coordenadas": error})

    return success_response(
        data=FarmaciaService.to_dict(farmacia_actualizada),
        message="Farmacia actualizada exitosamente.",
    )
