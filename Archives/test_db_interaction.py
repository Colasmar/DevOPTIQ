import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Vérifier le chemin actuel
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

print(f"DEBUG: Chemins dans sys.path :")
for path in sys.path:
    print(f"  - {path}")

try:
    from Code.extensions import db
    from Code.models.models import Activity
except ImportError as e:
    print(f"ERREUR : Import échoué. Détails : {e}")
    sys.exit(1)

def create_app():
    """Configure et initialise l'application Flask."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(project_root, 'Code', 'instance', 'optiq.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

app = create_app()

with app.app_context():
    try:
        # Créer une activité pour tester l'insertion
        new_activity = Activity(name="Test Activity")
        db.session.add(new_activity)
        db.session.commit()
        print("DEBUG : Activité ajoutée avec succès.")

        # Lire les activités pour vérifier l'insertion
        activities = Activity.query.all()
        print(f"DEBUG : Activités récupérées ({len(activities)}) :")
        for activity in activities:
            print(f"  - ID: {activity.id}, Name: {activity.name}")

        # Mettre à jour l'activité
        activity_to_update = Activity.query.filter_by(name="Test Activity").first()
        if activity_to_update:
            activity_to_update.name = "Updated Activity"
            db.session.commit()
            print("DEBUG : Activité mise à jour avec succès.")

        # Supprimer l'activité
        activity_to_delete = Activity.query.filter_by(name="Updated Activity").first()
        if activity_to_delete:
            db.session.delete(activity_to_delete)
            db.session.commit()
            print("DEBUG : Activité supprimée avec succès.")

    except Exception as e:
        print(f"ERREUR : Une erreur s'est produite lors de l'interaction avec la base. Détails : {e}")
