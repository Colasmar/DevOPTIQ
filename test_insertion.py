from Code.models import Activity
from Code.app import app, db

with app.app_context():
    try:
        # Création d'un nouvel enregistrement
        new_activity = Activity(name="Test Activity")
        db.session.add(new_activity)
        db.session.commit()
        print("Insertion réussie dans la base de données.")
    except Exception as e:
        print(f"Erreur lors de l'insertion : {e}")
