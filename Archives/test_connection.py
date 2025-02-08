import os
import sys
from sqlalchemy import text, inspect  # Import de inspect pour récupérer les noms de tables

# Ajouter dynamiquement le répertoire racine du projet dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Code.extensions import db
from flask import Flask

app = Flask(__name__)

# Configuration de la base de données
instance_path = os.path.join(project_root, 'Code', 'instance')
db_path = os.path.join(instance_path, 'optiq.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de la base
db.init_app(app)

with app.app_context():
    try:
        # Test de connexion
        db.session.execute(text('SELECT 1'))
        print("Connexion réussie.")

        # Récupérer les noms des tables
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if tables:
            print("Tables détectées :", tables)
        else:
            print("Aucune table détectée dans la base.")
    except Exception as e:
        print(f"Erreur de connexion : {e}")
