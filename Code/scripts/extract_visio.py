import os
import sys
import csv
from vsdx import VisioFile
from flask import Flask

# Ajouter dynamiquement le répertoire racine du projet dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))  # Racine du projet
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import après avoir ajouté le chemin
try:
    from Code.extensions import db
    from Code.models.models import Activity, Relation
except ImportError as e:
    print(f"Erreur d'import : {e}")
    print("Chemins disponibles dans sys.path :")
    for path in sys.path:
        print(path)
    sys.exit(1)

def create_app():
    """Initialise l'application Flask et configure la base de données."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(os.path.join(project_root, 'Code', 'instance', 'optiq.db')).replace('\\', '/')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def import_from_visio(vsdx_path):
    """Importe les données d'un fichier Visio dans la base SQLite."""
    if not os.path.exists(vsdx_path):
        print(f"Erreur : Le fichier Visio '{vsdx_path}' est introuvable.")
        return

    activities = []

    with VisioFile(vsdx_path) as visio:
        for page in visio.pages:
            print(f"Analyse de la page : {page.name}")
            for shape in page.child_shapes:
                # Diagnostic : afficher les informations clés
                shape_text = shape.text.strip() if shape.text else "None"
                shape_name = getattr(shape, 'shape_name', 'None')
                layer_name = getattr(shape, 'layer', 'None')

                print(f"Shape Text: {shape_text}")
                print(f"Shape Name: {shape_name}")
                print(f"Layer Name: {layer_name}")

                # Exclure les formes sans texte ou dans certains calques
                if shape_text == "None" or layer_name == "Légende":
                    continue

                # Ajouter ou mettre à jour une activité
                activity = _create_or_update_activity(shape_text)
                activities.append(activity)

    # Exporter les données pour vérification
    _export_data_to_csv(activities)


def _create_or_update_activity(activity_text):
    """Ajoute ou met à jour une activité dans la base."""
    normalized_text = activity_text.strip().lower()
    existing = Activity.query.filter_by(name=normalized_text).first()
    if not existing:
        new_activity = Activity(name=normalized_text)
        db.session.add(new_activity)
        db.session.commit()
        print(f"Nouvelle activité ajoutée : {normalized_text}")
        return {"id": new_activity.id, "name": normalized_text}
    else:
        print(f"Activité existante trouvée : {normalized_text}")
        return {"id": existing.id, "name": normalized_text}

def _export_data_to_csv(activities):
    """Exporte les activités dans un fichier CSV."""
    export_path = os.path.join(project_root, 'exported_data.csv')
    with open(export_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Type", "ID", "Name"])

        for activity in activities:
            writer.writerow(["Activity", activity["id"], activity["name"]])

    print(f"Données exportées vers {export_path}")

if __name__ == "__main__":
    # Initialiser l'application Flask
    app = create_app()

    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()
        print("Tables créées ou mises à jour avec succès.")

        # Chemin du fichier Visio
        vsdx_file = os.path.abspath(os.path.join(project_root, 'Code', 'example.vsdx'))
        if os.path.exists(vsdx_file):
            import_from_visio(vsdx_file)
        else:
            print(f"Erreur : Le fichier '{vsdx_file}' est introuvable.")
