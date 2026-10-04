"""
MedLoc - Configuración de la aplicación.
Carga variables de entorno desde el archivo .env usando python-dotenv.
"""
import os
from dotenv import load_dotenv

# Cargar el archivo .env desde la raíz del proyecto
load_dotenv()


class Config:
    """Configuración base compartida por todos los entornos."""

    # ── Seguridad ────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")

    # ── Base de Datos (Supabase / PostgreSQL) ────────────────────────────────
    # ── Normalización de la DATABASE_URL ─────────────────────────────────────
    # Supabase puede proveer la URL en varios formatos. Normalizamos para que
    # SQLAlchemy siempre use el driver psycopg2 y sin query params incompat.
    #
    # Formatos de entrada posibles:
    #   postgresql://...?pgbouncer=true          → viene del dashboard Supabase
    #   postgresql+psycopg2://...?pgbouncer=true → ya tiene driver especificado
    _raw_url: str = os.environ.get("DATABASE_URL", "")

    @staticmethod
    def _normalize_db_url(url: str) -> str:
        """Normaliza la DATABASE_URL para compatibilidad con psycopg2."""
        if not url:
            return ""
        # 1. Eliminar query params (?pgbouncer=true, etc.)
        url = url.split("?")[0]
        # 2. Asegurar el prefijo correcto para SQLAlchemy + psycopg2
        if url.startswith("postgresql+psycopg2://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url

    SQLALCHEMY_DATABASE_URI: str = _normalize_db_url.__func__(
        os.environ.get("DATABASE_URL", "")
    )
    # Deshabilitar el seguimiento de modificaciones (consume memoria extra)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    # Opciones del motor: reconectar automáticamente si la conexión se pierde
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,  # Reciclar conexiones cada 5 minutos
    }

    # ── Supabase (para uso directo con la API REST / Storage) ────────────────
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")


class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo."""

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True  # Mostrar queries SQL en consola


class ProductionConfig(Config):
    """Configuración para entorno de producción."""

    DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False


class TestingConfig(Config):
    """Configuración para entorno de pruebas."""

    TESTING: bool = True
    # En tests se puede usar SQLite en memoria para mayor velocidad
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )


# Mapeo de nombre → clase de configuración
config_by_name: dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
