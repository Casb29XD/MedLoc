import uuid
import json

def test_crear_farmacia(client, db):
    """Prueba crear una farmacia y listarla."""
    # Necesitamos un admin válido para relacionarlo (opcional, pero buena práctica)
    res_user = client.post("/api/v1/usuarios/", json={"nombre_completo": "Admin F", "email": "adminf@test.com"})
    admin_id = res_user.get_json()["data"]["id"]
    
    uid = str(uuid.uuid4())[:6]
    payload = {
        "nombre_sucursal": f"Farma_TEST_{uid}",
        "nit": f"800-1_T_{uid}",
        "direccion": "Calle Falsa 123",
        "latitud": 10.1234,
        "longitud": -74.1234,
        "id_administrador": admin_id
    }
    res = client.post("/api/v1/farmacias/", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["data"]["nit"] == f"800-1_T_{uid}"
    
    farmacia_id = data["data"]["id"]
    
    # Verificar obtener por ID
    res_get = client.get(f"/api/v1/farmacias/{farmacia_id}")
    assert res_get.status_code == 200
    assert res_get.get_json()["data"]["nombre_sucursal"] == f"Farma_TEST_{uid}"

def test_farmacia_desactivar_y_listar(client):
    """Prueba desactivar una farmacia y verificar filtros de listado."""
    uid = str(uuid.uuid4())[:6]
    client.post("/api/v1/farmacias/", json={"nombre_sucursal": f"F1_TEST_{uid}", "nit": f"111_T_{uid}", "direccion": "D1"})
    res = client.post("/api/v1/farmacias/", json={"nombre_sucursal": f"F2_TEST_{uid}", "nit": f"222_T_{uid}", "direccion": "D2"})
    f2_id = res.get_json()["data"]["id"]
    
    # Desactivar la segunda farmacia
    client.patch(f"/api/v1/farmacias/{f2_id}", json={"activa": False})
    
    # Listar todas
    res_all = client.get("/api/v1/farmacias/")
    assert res_all.status_code == 200
    
    # Listar solo activas
    res_activas = client.get("/api/v1/farmacias/?activas=true")
    activas = res_activas.get_json()["data"]
    # Comprobar que f2_id NO está en las activas porque la desactivamos
    assert f2_id not in [f["id"] for f in activas]
