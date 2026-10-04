import uuid
import json

def test_inventario_flujo_completo(client):
    """Prueba el Upsert, actualizar stock (delta) y precio en Inventario."""
    # 1. Crear una Farmacia
    uid = str(uuid.uuid4())[:6]
    res_f = client.post("/api/v1/farmacias/", json={"nombre_sucursal": f"InvFarma_TEST_{uid}", "nit": f"INV_T_{uid}", "direccion": "Calle Inv"})
    f_id = res_f.get_json()["data"]["id"]
    
    # 2. Crear un Medicamento
    res_m = client.post("/api/v1/medicamentos/", json={"nombre_comercial": f"InvMed_TEST_{uid}", "principio_activo": "InvAct_TEST"})
    m_id = res_m.get_json()["data"]["id"]
    
    # 3. Upsert Inventario (INSERT)
    res_i1 = client.post("/api/v1/inventario/", json={
        "id_farmacia": f_id,
        "id_medicamento": m_id,
        "precio_unitario": 5000.0,
        "stock_actual": 10
    })
    assert res_i1.status_code == 201
    
    # 4. Upsert Inventario (UPDATE) - Mismo Payload con distinto precio
    res_i2 = client.post("/api/v1/inventario/", json={
        "id_farmacia": f_id,
        "id_medicamento": m_id,
        "precio_unitario": 6000.0,
        "stock_actual": 10
    })
    assert res_i2.status_code == 200
    assert res_i2.get_json()["data"]["precio_unitario"] == 6000.0
    
    # 5. Incrementar stock
    res_stock = client.patch(f"/api/v1/inventario/{f_id}/{m_id}/stock", json={"delta": 5})
    assert res_stock.status_code == 200
    assert res_stock.get_json()["data"]["stock_actual"] == 15
    
    # 6. Reducir stock
    res_stock2 = client.patch(f"/api/v1/inventario/{f_id}/{m_id}/stock", json={"delta": -20})
    # Debe fallar porque 15 - 20 = -5
    assert res_stock2.status_code == 409
    
    # 7. Cambiar solo precio
    res_precio = client.patch(f"/api/v1/inventario/{f_id}/{m_id}/precio", json={"precio_unitario": 4500})
    assert res_precio.status_code == 200
    assert res_precio.get_json()["data"]["precio_unitario"] == 4500.0
