"""
MedLoc - Script de Diagnóstico de Conexión a Supabase
======================================================
Verifica paso a paso:
  1. Carga correcta del .env
  2. Conexión raw a PostgreSQL (psycopg2)
  3. Integración Flask + SQLAlchemy
  4. Creación de todas las tablas en Supabase
  5. Operación CRUD básica de smoke-test

Ejecutar con:
    .\\venv\\Scripts\\python.exe check_connection.py
"""
import sys
import os

# ── Colores ANSI para la consola ──────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg: str)   -> None: print(f"  {GREEN}[OK]{RESET}  {msg}")
def fail(msg: str) -> None: print(f"  {RED}[FAIL]{RESET}  {msg}")
def info(msg: str) -> None: print(f"  {CYAN}[INFO]{RESET}  {msg}")
def step(msg: str) -> None: print(f"\n{BOLD}{CYAN}>> {msg}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Cargar variables de entorno
# ══════════════════════════════════════════════════════════════════════════════
step("PASO 1 — Cargando variables de entorno desde .env")
try:
    from dotenv import load_dotenv
    load_dotenv()
    ok("python-dotenv instalado y .env cargado")
except ImportError as e:
    fail(f"python-dotenv no instalado: {e}")
    sys.exit(1)

DATABASE_URL  = os.environ.get("DATABASE_URL", "")
SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY", "")

placeholders = ["[PROJECT-REF]", "[PASSWORD]", "[TU-ANON-KEY]"]

for var_name, var_value in [
    ("DATABASE_URL",  DATABASE_URL),
    ("SUPABASE_URL",  SUPABASE_URL),
    ("SUPABASE_KEY",  SUPABASE_KEY),
]:
    if not var_value:
        fail(f"{var_name} está vacía — revisa tu .env")
        sys.exit(1)
    if any(p in var_value for p in placeholders):
        fail(f"{var_name} todavía tiene un placeholder de plantilla: {var_value[:60]}...")
        sys.exit(1)
    masked = var_value[:20] + "..." if len(var_value) > 20 else var_value
    ok(f"{var_name} cargada → {masked}")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Conexión raw con psycopg2
# ══════════════════════════════════════════════════════════════════════════════
step("PASO 2 — Conexión directa a PostgreSQL (psycopg2)")
try:
    import psycopg2
    # Convertir la URI de SQLAlchemy a DSN de psycopg2
    # Supabase añade ?pgbouncer=true&connection_limit=1 — psycopg2 no los soporta en la URI
    dsn_raw = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    dsn = dsn_raw.split("?")[0]  # Eliminar todos los query params
    info(f"DSN limpio (sin query params): {dsn[:50]}...")
    conn = psycopg2.connect(dsn, connect_timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    pg_version = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    ok(f"Conexion psycopg2 exitosa")
    info(f"PostgreSQL: {pg_version[:60]}")
except ImportError:
    fail("psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    fail(f"Error de conexión psycopg2: {e}")
    print(f"\n  {YELLOW}Posibles causas:{RESET}")
    print("    • DATABASE_URL incorrecta (usuario, contraseña, host, puerto)")
    print("    • El pooler de Supabase no acepta conexiones desde tu IP")
    print("    • Falta habilitar 'Allow all IPs' en Supabase → Settings → Database")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — Flask + SQLAlchemy
# ══════════════════════════════════════════════════════════════════════════════
step("PASO 3 — Inicializando Flask + SQLAlchemy")
try:
    from app import create_app
    flask_app = create_app("development")
    ok("Application Factory ejecutada correctamente")
except Exception as e:
    fail(f"Error en create_app(): {e}")
    sys.exit(1)


# ==============================================================================
# PASO 4 — Crear tablas en Supabase
# ==============================================================================
step("PASO 4 — Creando / verificando tablas en Supabase (db.create_all)")
try:
    from app.extensions import db
    # Importar todos los modelos para que SQLAlchemy los registre en su metadata
    import app.models  # noqa: F401

    with flask_app.app_context():
        db.create_all()

    ok("Todas las tablas creadas / ya existentes en Supabase")
    info("Tablas registradas en SQLAlchemy metadata:")
    from app.extensions import db as _db
    with flask_app.app_context():
        for table in _db.metadata.sorted_tables:
            info(f"  -> {table.name}")
except Exception as e:
    fail(f"Error en db.create_all(): {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 5 — Smoke test CRUD (INSERT + SELECT + DELETE)
# ══════════════════════════════════════════════════════════════════════════════
step("PASO 5 — Smoke test: INSERT → SELECT → DELETE en tabla 'usuarios'")
try:
    from app.models.usuario import Usuario, RolUsuario

    TEST_EMAIL = "__medloc_test_connection__@test.internal"

    with flask_app.app_context():
        # Limpiar posible resto de una prueba anterior
        existing = db.session.execute(
            db.select(Usuario).where(Usuario.email == TEST_EMAIL)
        ).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        # INSERT — el UUID y fecha_creacion los genera Supabase
        test_user = Usuario(
            nombre_completo="Test de Conexión MedLoc",
            email=TEST_EMAIL,
            rol=RolUsuario.PACIENTE,
        )
        db.session.add(test_user)
        db.session.commit()
        db.session.refresh(test_user)  # Leer UUID y timestamp generados por la BD

        ok(f"INSERT exitoso — UUID generado por Supabase: {test_user.id}")
        ok(f"Timestamp generado por Supabase: {test_user.fecha_creacion}")

        # SELECT
        retrieved = db.session.get(Usuario, test_user.id)
        assert retrieved is not None, "El usuario no se encontró tras el INSERT"
        ok(f"SELECT exitoso — Nombre: {retrieved.nombre_completo}")

        # DELETE (limpiar dato de prueba)
        db.session.delete(retrieved)
        db.session.commit()
        ok("DELETE exitoso — dato de prueba eliminado")

except Exception as e:
    fail(f"Error en smoke test CRUD: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO FINAL
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"{GREEN}{BOLD}  [OK]  CONEXION VERIFICADA - MedLoc listo para el desarrollo{RESET}")
print(f"{'='*60}\n")
