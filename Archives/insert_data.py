import os
import sys
from sqlalchemy import text

# Ajouter le chemin parent et le dossier Code à sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Code.app import app
from Code.extensions import db

with app.app_context():
    print("Insertion de données dans 'activities'...")
    try:
        db.session.execute(
            text("INSERT INTO activities (name, description) VALUES ('Test Activity', 'Description de test');")
        )
        db.session.commit()
        print("Données insérées avec succès.")
    except Exception as e:
        print("Erreur lors de l'insertion des données :", e)
