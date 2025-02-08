import os
import sys
from flask import Flask
from sqlalchemy import inspect

# Détection du répertoire actuel et du projet
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # Ajustement ici

# Ajout des chemins au sys.path
sys.path.insert(0, os.path.join(project_root, "Code"))
sys.path.insert(0, project_root)

print("DEBUG: Structure des chemins sys.path :")
for path in sys.path:
    print(f"  - {path}")

# Vérification des fichiers critiques
critical_files = [
    {"name": "extensions.py", "path": os.path.join(project_root, "Code", "extensions.py")},
    {"name": "models.py", "path": os.path.join(project_root, "Code", "models", "models.py")}
]

print("DEBUG: Vérification des fichiers critiques...")
for file in critical_files:
    exists = os.path.exists(file["path"])
    print(f"  - {file['name']} : {'Présent' if exists else 'Manquant'} (Path : {file['path']})")

if any(not os.path.exists(file["path"]) for file in critical_files):
    print("ERREUR : Fichiers critiques manquants.")
    sys.exit(1)

# Tentative d'import des modules
try:
    from extensions import db
    from models.models import Activity, Data, Connection
    print("DEBUG: Import des modules réussi.")
except ImportError as e:
    print(f"ERREUR : Import des modules échoué : {e}")
    sys.exit(1)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(project_root, 'Code', 'instance', 'optiq.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def inspect_tables():
    """Inspecte la structure des tables dans la base."""
    inspector = inspect(db.engine)
    for table_name in inspector.get_table_names():
        print(f"Table: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"  Column: {column['name']} ({column['type']})")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        inspect_tables()
try:
    from models.models import Activity, Data, Connection
    print("DEBUG : Import réussi pour Activity, Data, Connection.")
except ImportError as e:
    print(f"ERREUR : Import échoué : {e}")
    sys.exit(1)
