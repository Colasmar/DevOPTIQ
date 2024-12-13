from Code.models import Activity
from Code.app import app, db

with app.app_context():
    try:
        # Compter le nombre d'entrées dans la table
        count = Activity.query.count()
        print(f"Nombre d'activités dans la base : {count}")

        # Récupérer toutes les activités si elles existent
        activities = Activity.query.all()
        if activities:
            for activity in activities:
                print(f"ID : {activity.id}, Nom : {activity.name}")
        else:
            print("Aucune activité trouvée.")
    except Exception as e:
        print(f"Erreur lors de la lecture : {e}")
