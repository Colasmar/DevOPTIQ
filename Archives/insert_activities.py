from Code.extensions import db
from Code.models.models import Activity, Relation
from app import app

def insert_data():
    activities = [
        {"name": "Treatment of RFQ", "description": "Processing RFQ data"},
        {"name": "Existing Part Available 2D Drawing", "description": "Review existing 2D drawing for compatibility"},
    ]
    relations = [
        {"source": "Treatment of RFQ", "target": "Existing Part Available 2D Drawing", "type": "trigger", "description": "RFQ triggers 2D drawing review"},
    ]

    with app.app_context():
        for activity_data in activities:
            activity = Activity(name=activity_data["name"], description=activity_data["description"])
            db.session.add(activity)

        db.session.commit()

        for relation_data in relations:
            source = Activity.query.filter_by(name=relation_data["source"]).first()
            target = Activity.query.filter_by(name=relation_data["target"]).first()
            if source and target:
                relation = Relation(source_id=source.id, target_id=target.id, type=relation_data["type"], description=relation_data["description"])
                db.session.add(relation)

        db.session.commit()
        print("Données insérées avec succès !")

if __name__ == "__main__":
    insert_data()
