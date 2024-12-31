from Code.extensions import db
from Code.models.models import Activity
from app import app

with app.app_context():
    activities = [
        Activity(name="Activité 1"),
        Activity(name="Activité 2"),
        Activity(name="Activité 3")
    ]
    db.session.add_all(activities)
    db.session.commit()
    print("Activités ajoutées avec succès !")
