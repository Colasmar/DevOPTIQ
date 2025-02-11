import os
import sys

# Ajouter dynamiquement le répertoire racine du projet dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importer les modules nécessaires
try:
    from Code.extensions import db
    from Code.models.models import Activity, Data, Connection
except ImportError as e:
    print(f"Erreur d'import : {e}")
    print("DEBUG : Voici les chemins dans sys.path :")
    for path in sys.path:
        print(f"  - {path}")
    sys.exit(1)

from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Code/instance/optiq.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

app = create_app()
with app.app_context():
    # Ajouter une activité
    new_activity = Activity(name="Analyse des besoins", description="Identifier les besoins des clients.")
    db.session.add(new_activity)

    # Ajouter une donnée déclenchante
    new_data = Data(name="Demande client", type="déclenchante", description="Déclenche l'analyse des besoins.")
    db.session.add(new_data)

    # Ajouter une connexion entre la donnée et l'activité
    connection = Connection(source_id=new_data.id, target_id=new_activity.id, type="input", description="Lien entre la demande et l'analyse.")
    db.session.add(connection)

    # Enregistrer toutes les modifications
    db.session.commit()

    # Vérifier les résultats
    activities = Activity.query.all()
    data = Data.query.all()
    connections = Connection.query.all()

    for activity in activities:
        print(f"Activity: {activity.name} - {activity.description}")

    for datum in data:
        print(f"Data: {datum.name} ({datum.type}) - {datum.description}")

    for conn in connections:
        print(f"Connection: {conn.type} - Source ID: {conn.source_id}, Target ID: {conn.target_id}")
