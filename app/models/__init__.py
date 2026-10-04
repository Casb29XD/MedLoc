"""
MedLoc - Registro central de modelos.
Importar todos los modelos aquí para que SQLAlchemy los registre
en su metadata y `db.create_all()` los detecte correctamente.
"""
from .usuario import Usuario, RolUsuario
from .farmacia import Farmacia
from .medicamento import Medicamento
from .inventario import Inventario
from .reserva import Reserva, DetalleReserva, EstadoReserva

__all__ = [
    "Usuario",
    "RolUsuario",
    "Farmacia",
    "Medicamento",
    "Inventario",
    "Reserva",
    "DetalleReserva",
    "EstadoReserva",
]
