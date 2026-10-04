import json
import uuid

def test_listar_usuarios(client):
    """Prueba GET usuarios."""
    res = client.get("/api/v1/usuarios/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert isinstance(data["data"], list)

def test_crear_usuario_exito(client):
    """Prueba POST para crear un usuario válido."""
    uid = str(uuid.uuid4())[:8]
    payload = {
        "nombre_completo": f"Test Unitario {uid}",
        "email": f"unit_{uid}@test.com",
        "rol": "administrador"
    }
    res = client.post("/api/v1/usuarios/", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert "id" in data["data"]

def test_crear_usuario_duplicado(client):
    """Prueba que falla al intentar crear un usuario con el mismo email."""
    uid = str(uuid.uuid4())[:8]
    payload = {"nombre_completo": "Test", "email": f"unico_{uid}@test.com"}
    client.post("/api/v1/usuarios/", json=payload)
    
    # Segundo intento
    res2 = client.post("/api/v1/usuarios/", json=payload)
    assert res2.status_code == 409
    assert "ya está registrado" in res2.get_json()["message"]

def test_actualizar_usuario(client):
    """Prueba PATCH para actualizar el nombre y rol de un usuario."""
    uid = str(uuid.uuid4())[:8]
    # Crear usuario primero
    res1 = client.post("/api/v1/usuarios/", json={"nombre_completo": "Old Name", "email": f"update_{uid}@test.com"})
    user_id = res1.get_json()["data"]["id"]
    
    # Actualizar
    res2 = client.patch(f"/api/v1/usuarios/{user_id}", json={"nombre_completo": "New Name", "rol": "paciente"})
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["data"]["nombre_completo"] == "New Name"
    assert data2["data"]["rol"] == "paciente"
