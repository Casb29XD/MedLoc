import os
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models.usuario import Usuario, RolUsuario
from app.models.farmacia import Farmacia
from app.models.medicamento import Medicamento
from app.models.inventario import Inventario

def run_seed():
    """
    Inyecta datos iniciales (semilla) en la base de datos Supabase
    para que la aplicación tenga información útil desde el inicio.
    """
    app = create_app('development')
    with app.app_context():
        print(">> Iniciando carga de datos semilla (seeding)...")

        # 1. Usuarios
        admin1 = db.session.execute(db.select(Usuario).where(Usuario.email == "admin.central@medloc.com")).scalar_one_or_none()
        if not admin1:
            admin1 = Usuario(nombre_completo="Admin Central", email="admin.central@medloc.com", rol=RolUsuario.ADMINISTRADOR)
            db.session.add(admin1)

        paciente1 = db.session.execute(db.select(Usuario).where(Usuario.email == "juan.paciente@correo.com")).scalar_one_or_none()
        if not paciente1:
            paciente1 = Usuario(nombre_completo="Juan Perez", email="juan.paciente@correo.com", rol=RolUsuario.PACIENTE)
            db.session.add(paciente1)

        db.session.commit()
        db.session.refresh(admin1)
        db.session.refresh(paciente1)

        # Sincronizar con Supabase Auth
        for u_obj, pwd in [(admin1, "usuario1"), (paciente1, "usuario2")]:
            db.session.execute(db.text("""
                INSERT INTO auth.users (
                    id, instance_id, aud, role, email, encrypted_password,
                    email_confirmed_at, recovery_sent_at, last_sign_in_at,
                    raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
                    confirmation_token, email_change, email_change_token_new, recovery_token
                ) VALUES (
                    :id, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated',
                    :email, crypt(:password, gen_salt('bf')), NOW(), NULL, NULL,
                    '{"provider":"email","providers":["email"]}',
                    jsonb_build_object('nombre_completo', :nombre),
                    NOW(), NOW(), '', '', '', ''
                )
                ON CONFLICT (id) DO UPDATE SET
                    encrypted_password = crypt(:password, gen_salt('bf')),
                    email_confirmed_at = NOW(),
                    updated_at = NOW()
            """), {"id": str(u_obj.id), "email": u_obj.email, "password": pwd, "nombre": u_obj.nombre_completo})

            db.session.execute(db.text("""
                INSERT INTO auth.identities (
                    id, user_id, identity_data, provider, provider_id,
                    last_sign_in_at, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :id, jsonb_build_object('sub', :id, 'email', :email),
                    'email', :id, NOW(), NOW(), NOW()
                )
                ON CONFLICT (provider_id, provider) DO UPDATE SET
                    identity_data = jsonb_build_object('sub', :id, 'email', :email),
                    updated_at = NOW()
            """), {"id": str(u_obj.id), "email": u_obj.email})
        db.session.commit()
        print("  [OK] Usuarios quemados en public.usuarios y Supabase auth.users.")

        # 2. Farmacias
        farma1 = db.session.execute(db.select(Farmacia).where(Farmacia.nit == "900111222-1")).scalar_one_or_none()
        if not farma1:
            farma1 = Farmacia(
                nombre_sucursal="Farmacia Salud Norte", 
                nit="900111222-1", 
                direccion="Av Norte #45-12, Bogotá", 
                latitud=Decimal("4.7110"), 
                longitud=Decimal("-74.0721"), 
                id_administrador=admin1.id
            )
            db.session.add(farma1)
        
        farma2 = db.session.execute(db.select(Farmacia).where(Farmacia.nit == "800999888-2")).scalar_one_or_none()
        if not farma2:
            farma2 = Farmacia(
                nombre_sucursal="Farmacia Central del Sur", 
                nit="800999888-2", 
                direccion="Calle Sur #12-34, Medellín", 
                latitud=Decimal("6.2442"), 
                longitud=Decimal("-75.5812"), 
                id_administrador=admin1.id
            )
            db.session.add(farma2)

        db.session.commit()
        db.session.refresh(farma1)
        db.session.refresh(farma2)
        print("  [OK] Farmacias quemadas.")

        # 3. Medicamentos
        meds_data = [
            {"nombre": "Acetaminofén", "activo": "Paracetamol", "conc": "500mg", "pres": "Tabletas", "lab": "Genfar"},
            {"nombre": "Advil", "activo": "Ibuprofeno", "conc": "400mg", "pres": "Cápsulas", "lab": "Pfizer"},
            {"nombre": "Amoxidal", "activo": "Amoxicilina", "conc": "500mg", "pres": "Cápsulas", "lab": "Bayer"},
            {"nombre": "Clarityne", "activo": "Loratadina", "conc": "10mg", "pres": "Tabletas", "lab": "Bayer"},
            {"nombre": "Omeprazol", "activo": "Omeprazol", "conc": "20mg", "pres": "Cápsulas", "lab": "Lafrancol"},
        ]
        meds = []
        for md in meds_data:
            m = db.session.execute(db.select(Medicamento).where(Medicamento.nombre_comercial == md["nombre"])).scalar_one_or_none()
            if not m:
                m = Medicamento(nombre_comercial=md["nombre"], principio_activo=md["activo"], concentracion=md["conc"], presentacion=md["pres"], laboratorio=md["lab"])
                db.session.add(m)
            meds.append(m)
        db.session.commit()
        for m in meds: db.session.refresh(m)
        print("  [OK] Medicamentos comunes quemados.")

        # 4. Inventario (Asignar 2 medicamentos a Farma 1 y 3 a Farma 2)
        inv_data = [
            (farma1.id, meds[0].id, 150, "2500.00"),
            (farma1.id, meds[1].id, 80,  "5400.00"),
            (farma2.id, meds[2].id, 45,  "12000.00"),
            (farma2.id, meds[3].id, 200, "8500.00"),
            (farma2.id, meds[4].id, 12,  "3200.00"),
        ]
        for f_id, m_id, stock, precio in inv_data:
            inv = db.session.get(Inventario, (f_id, m_id))
            if not inv:
                inv = Inventario(id_farmacia=f_id, id_medicamento=m_id, stock_actual=stock, precio_unitario=Decimal(precio))
                db.session.add(inv)
        db.session.commit()
        print("  [OK] Stock de inventario quemado.")

        print("\n>> Seeding completado con éxito! Tu base de datos ya tiene información.")

if __name__ == '__main__':
    run_seed()
