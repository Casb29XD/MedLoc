import json
import uuid

def test_crear_medicamento_y_buscar(client):
    """Prueba crear y luego buscar un medicamento con ?q="""
    uid = str(uuid.uuid4())[:8]
    client.post("/api/v1/medicamentos/", json={
        "nombre_comercial": f"Aspirina_TEST_{uid}",
        "principio_activo": "Acido_TEST",
        "concentracion": "100mg"
    })
    
    client.post("/api/v1/medicamentos/", json={
        "nombre_comercial": f"Dolex_TEST_{uid}",
        "principio_activo": "Para_TEST"
    })
    
    # Búsqueda que coincida
    res1 = client.get(f"/api/v1/medicamentos/?q=Aspirina_TEST_{uid}")
    assert res1.status_code == 200
    data1 = res1.get_json()["data"]
    assert len(data1) >= 1
    assert any(m["nombre_comercial"] == f"Aspirina_TEST_{uid}" for m in data1)
    
    # Búsqueda que coincida con el principio activo
    res2 = client.get("/api/v1/medicamentos/?q=Para_TEST")
    assert res2.status_code == 200
    assert len(res2.get_json()["data"]) >= 1

def test_actualizar_medicamento(client):
    """Prueba actualizar detalles de un medicamento."""
    uid = str(uuid.uuid4())[:8]
    res = client.post("/api/v1/medicamentos/", json={
        "nombre_comercial": f"Temp_TEST_{uid}",
        "principio_activo": "Temp Activo_TEST"
    })
    med_id = res.get_json()["data"]["id"]
    
    res_up = client.patch(f"/api/v1/medicamentos/{med_id}", json={"laboratorio": "Bayer"})
    assert res_up.status_code == 200
    assert res_up.get_json()["data"]["laboratorio"] == "Bayer"
