import sys, json, urllib.request, urllib.error
sys.path.insert(0, r"t:\MedLoc")
from app import create_app
from app.extensions import db
from dotenv import load_dotenv
import os

load_dotenv(r"t:\MedLoc\.env")
app = create_app('development')

user_passwords = [
    ("admin.central@medloc.com", "usuario1"),
    ("juan.paciente@correo.com", "usuario2"),
    ("alejandrosierra2904@gmail.com", "usuario3"),
    ("ana.torres@medloc.test", "usuario4"),
]

with app.app_context():
    print(">> Configurando credenciales en Supabase Auth...")
    for email, password in user_passwords:
        u = db.session.execute(
            db.text("SELECT id, nombre_completo FROM public.usuarios WHERE email = :email"),
            {"email": email}
        ).fetchone()
        
        if not u:
            print(f"  [SKIP] Usuario no encontrado en public.usuarios: {email}")
            continue
            
        uid = str(u[0])
        nombre = u[1]
        
        # Eliminar registros previos si existen
        db.session.execute(db.text("DELETE FROM auth.identities WHERE email = :email"), {"email": email})
        db.session.execute(db.text("DELETE FROM auth.users WHERE email = :email"), {"email": email})
        
        # Insertar en auth.users
        db.session.execute(db.text("""
            INSERT INTO auth.users (
                id,
                instance_id,
                aud,
                role,
                email,
                encrypted_password,
                email_confirmed_at,
                recovery_sent_at,
                last_sign_in_at,
                raw_app_meta_data,
                raw_user_meta_data,
                created_at,
                updated_at,
                confirmation_token,
                email_change,
                email_change_token_new,
                recovery_token
            ) VALUES (
                :id,
                '00000000-0000-0000-0000-000000000000',
                'authenticated',
                'authenticated',
                :email,
                crypt(:password, gen_salt('bf')),
                NOW(),
                NULL,
                NULL,
                '{"provider":"email","providers":["email"]}',
                jsonb_build_object('nombre_completo', :nombre),
                NOW(),
                NOW(),
                '',
                '',
                '',
                ''
            )
        """), {"id": uid, "email": email, "password": password, "nombre": nombre})
        
        # Insertar en auth.identities
        db.session.execute(db.text("""
            INSERT INTO auth.identities (
                id,
                user_id,
                identity_data,
                provider,
                provider_id,
                last_sign_in_at,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                :id,
                jsonb_build_object('sub', :id, 'email', :email),
                'email',
                :id,
                NOW(),
                NOW(),
                NOW()
            )
        """), {"id": uid, "email": email})
        
        print(f"  [OK] Usuario configurado en auth.users: {email} -> password: {password}")
        
    db.session.commit()
    print(">> Todos los usuarios sincronizados en auth.users con éxito.")

# Probar login en Supabase Auth para cada uno
print("\n>> Probando inicio de sesión en Supabase Auth REST:")
url = os.getenv("SUPABASE_URL") + "/auth/v1/token?grant_type=password"
headers = {"apikey": os.getenv("SUPABASE_KEY"), "Content-Type": "application/json"}

for email, password in user_passwords:
    body = json.dumps({"email": email, "password": password}).encode('utf-8')
    req = urllib.request.Request(url, headers=headers, data=body, method='POST')
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        token_sample = data.get("access_token")[:15] + "..."
        print(f"  [SUCCESS] {email} (pass: {password}) -> Token JWT: {token_sample}")
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] {email}: HTTP {e.code} -> {e.read().decode('utf-8')}")
