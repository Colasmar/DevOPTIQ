import os
import sys
from sqlalchemy import text  # Import nécessaire pour les requêtes textuelles

# Ajout dynamique des répertoires nécessaires dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Code.app import app
from Code.extensions import db

with app.app_context():
    print("DEBUG : Connexion à la base...")
    try:
        # Vérification des tables disponibles
        tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
        print("Tables disponibles :", [table[0] for table in tables])

        # Vérification des données dans 'activities'
        activities = db.session.execute(text("SELECT * FROM activities;")).fetchall()
        print("Données dans 'activities' :", activities)
    except Exception as e:
        print("Erreur lors de la connexion ou de la requête :", e)
