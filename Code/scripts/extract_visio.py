import os
import sys
from vsdx import VisioFile
from flask import Flask
from Code.extensions import db  # Corrigé pour respecter la structure
from Code.models.models import Activity, Relation  # Corrigé pour respecter la structure

# Ajouter dynamiquement le répertoire 'Code' dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))  # Racine du projet
code_dir = os.path.join(project_root, 'Code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

def create_app():
    """Initialise l'application Flask et configure la base de données."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(current_dir, '..', 'instance', 'optiq.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def import_from_visio(vsdx_path):
    """Importe les données d'un fichier Visio dans la base SQLite."""
    if not os.path.exists(vsdx_path):
        print(f"Erreur : Le fichier Visio '{vsdx_path}' est introuvable.")
        return

    with VisioFile(vsdx_path) as visio:
        for page in visio.pages:
            print(f"Analyse de la page : {page.name}")
            for shape in page.child_shapes:
                shape_text = shape.text.strip() if shape.text else None

                # Ignorer les formes sans texte pertinent
                if not shape_text:
                    continue

                # Ajouter ou mettre à jour une activité
                activity = _create_or_update_activity(shape_text)

                # Analyser les connexions
                for connection in shape.connects:
                    source_text = shape_text
                    target_text = connection.to_shape.text.strip() if connection.to_shape and connection.to_shape.text else None

                    if target_text:
                        _create_or_update_relation(source_text, target_text)

def _create_or_update_activity(activity_text):
    """Ajoute ou met à jour une activité dans la base."""
    existing = Activity.query.filter_by(name=activity_text).first()
    if not existing:
        new_activity = Activity(name=activity_text)
        db.session.add(new_activity)
        db.session.commit()
        print(f"Nouvelle activité ajoutée : {activity_text}")
        return new_activity
    else:
        print(f"Activité existante trouvée : {activity_text}")
        return existing

def _create_or_update_relation(source_text, target_text):
    """Ajoute ou met à jour une relation entre deux activités."""
    source_activity = Activity.query.filter_by(name=source_text).first()
    target_activity = Activity.query.filter_by(name=target_text).first()

    if not source_activity or not target_activity:
        print(f"Impossible de créer la relation : Source '{source_text}' ou Target '{target_text}' non trouvée.")
        return

    # Vérifier si la relation existe déjà
    existing_relation = Relation.query.filter_by(source_id=source_activity.id, target_id=target_activity.id).first()
    if not existing_relation:
        new_relation = Relation(
            source_id=source_activity.id,
            target_id=target_activity.id,
            type="unknown",  # Ajustez selon les données (trigger/nourishing)
            description=f"Relation entre {source_text} et {target_text}"
        )
        db.session.add(new_relation)
        db.session.commit()
        print(f"Nouvelle relation ajoutée : {source_text} -> {target_text}")
    else:
        print(f"Relation existante entre {source_text} et {target_text}.")

if __name__ == "__main__":
    # Initialiser l'application Flask
    app = create_app()

    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()
        print("Tables créées ou mises à jour avec succès.")

        # Chemin du fichier Visio
        vsdx_file = os.path.join(os.path.dirname(__file__), "../example.vsdx")
        if os.path.exists(vsdx_file):
            import_from_visio(vsdx_file)
        else:
            print(f"Erreur : Le fichier '{vsdx_file}' est introuvable.")
