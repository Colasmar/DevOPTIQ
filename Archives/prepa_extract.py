import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Correction des chemins pour éviter les erreurs d'importation
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(1, os.path.join(project_root, 'Code'))

# Importation des modules après la configuration des chemins
from extensions import db
from models.models import Activities, Connections, Data

# Configuration de l'application Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(current_dir, 'instance', 'optiq.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def reset_database():
    """Vider les tables nécessaires."""
    with app.app_context():
        try:
            db.session.query(Connections).delete()
            db.session.query(Data).delete()
            db.session.query(Activities).delete()
            db.session.commit()
            print("INFO : Toutes les données ont été supprimées des tables nécessaires.")
        except Exception as e:
            print(f"ERREUR : Une erreur s'est produite lors de la réinitialisation des bases. Détails : {e}")

def mock_extract_visio_data():
    """Simuler l'extraction des données d'un fichier Visio."""
    activities = [
        {"id": 1, "name": "Activity 1", "description": "Description of Activity 1"},
        {"id": 2, "name": "Activity 2", "description": "Description of Activity 2"},
    ]

    connections = [
        {"id": 1, "source_id": 1, "target_id": 2, "type": "trigger", "description": "Connection from 1 to 2"},
        {"id": 2, "source_id": 2, "target_id": 1, "type": "feedback", "description": "Connection from 2 to 1"},
    ]

    data = [
        {"id": 1, "name": "Data 1", "type": "input", "description": "Data description 1"},
        {"id": 2, "name": "Data 2", "type": "output", "description": "Data description 2"},
    ]

    return activities, connections, data

def populate_database():
    """Remplir les tables avec les données simulées."""
    with app.app_context():
        try:
            # Appel de la fonction de simulation d'extraction des données
            activities, connections, data = mock_extract_visio_data()

            # Ajouter les activités
            for activity in activities:
                new_activity = Activities(**activity)
                db.session.add(new_activity)

            # Ajouter les connexions
            for connection in connections:
                new_connection = Connections(**connection)
                db.session.add(new_connection)

            # Ajouter les données
            for datum in data:
                new_datum = Data(**datum)
                db.session.add(new_datum)

            db.session.commit()
            print("INFO : Les données ont été ajoutées avec succès.")
        except Exception as e:
            print(f"ERREUR : Une erreur s'est produite lors du remplissage des bases. Détails : {e}")

if __name__ == "__main__":
    print("DEBUG: sys.path contient :", sys.path)
    reset_database()
    populate_database()
