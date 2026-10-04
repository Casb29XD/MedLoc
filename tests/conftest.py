import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope='session')
def flask_app():
    app_instance = create_app('development')
    with app_instance.app_context():
        import app.models
        yield app_instance

@pytest.fixture
def client(flask_app):
    return flask_app.test_client()

@pytest.fixture(autouse=True)
def db(flask_app):
    """
    Usa conexiones separadas forzando limpieza manual sin interferir con las peticiones.
    """
    with flask_app.app_context():
        yield _db
        # Teardown
        _db.session.execute(_db.text("DELETE FROM inventario WHERE id_farmacia IN (SELECT id FROM farmacias WHERE nombre_sucursal LIKE '%_TEST%')"))
        _db.session.execute(_db.text("DELETE FROM farmacias WHERE nombre_sucursal LIKE '%_TEST%'"))
        _db.session.execute(_db.text("DELETE FROM medicamentos WHERE nombre_comercial LIKE '%_TEST%'"))
        _db.session.execute(_db.text("DELETE FROM usuarios WHERE email LIKE '%@test.com%'"))
        _db.session.commit()
