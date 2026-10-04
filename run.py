"""
MedLoc - Punto de entrada de la aplicación.
Ejecutar con: flask run  o  python run.py
"""
import os
from app import create_app

# Determinar el entorno desde la variable de entorno (por defecto: development)
config_name = os.environ.get("FLASK_ENV", "development")

app = create_app(config_name)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=(config_name == "development"),
    )
