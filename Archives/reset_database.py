import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Configuration dynamique des chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, 'Code') not in sys.path:
    sys.path.insert(0, os.path.join(project_root, 'Code'))

# Diagnostic des chemins
print("DEBUG: sys.path contient :")
for path in sys.path:
    print(f"  - {path}")

try:
    from Code.extensions import db
    from Code.models.models import Activity, Data, Connection
    print("DEBUG: Importation des modules réussie.")
except ModuleNotFoundError as e:
    print(f"ERREUR : Problème lors de l'importation. Détails : {e}")
    sys.exit(1)

# Création de l'application Flask
def create_app():
    app = Flask(__name__)
    db_path = os.path.abspath("Code/instance/optiq.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    print(f"DEBUG: Chemin de la base de données : {db_path}")
    if not os.path.exists(db_path):
        print("ERREUR : Le fichier de base de données est introuvable.")
        sys.exit(1)

    db.init_app(app)
    return app

# Réinitialisation de la base
app = create_app()
with app.app_context():
    try:
        # Supprimer les tables inutiles
        db.session.execute(text("DROP TABLE IF EXISTS relation;"))
        db.session.execute(text("DROP TABLE IF EXISTS relations;"))
        db.session.commit()
        print("INFO : Tables inutiles supprimées avec succès.")

        # Effacer les données des tables nécessaires
        db.session.query(Connection).delete()
        db.session.query(Data).delete()
        db.session.query(Activity).delete()
        db.session.commit()
        print("INFO : Toutes les données ont été supprimées des tables nécessaires.")
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR : Une erreur s'est produite lors de la réinitialisation des bases. Détails : {e}")
